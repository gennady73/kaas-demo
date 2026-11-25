"""Isolated offline tenant sink protocol candidate. No HTTP server or credential access.

SQLite commit-before-ACK is tested for local process restart, not power-loss,
Kubernetes PVC survival, remote transport, access control or production custody.
"""
import hashlib
import json
import re
import sqlite3


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def parse(raw):
    def pairs(items):
        obj = {}
        for key, value in items:
            if key in obj:
                raise ValueError('duplicate_key')
            obj[key] = value
        return obj
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite')))


class Sink:
    def __init__(self, path, plan, hook=None):
        if plan.get('mode') != 'OFFLINE_ONLY' or any(plan.get(k) is not False for k in ('execution_enabled', 'deployment_enabled', 'tests_enabled', 'execution_ready')):
            raise ValueError('offline_plan_required')
        if not re.fullmatch(r'offline-[A-Za-z0-9_-]{1,80}', plan.get('run_id', '')):
            raise ValueError('offline_run_id_required')
        self.run = plan['run_id']
        self.plan_hash = digest(canonical(plan))
        self.hook = hook or (lambda _: None)
        self.db = sqlite3.connect(path, timeout=0.2)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.executescript('''CREATE TABLE IF NOT EXISTS run(id TEXT PRIMARY KEY, hash TEXT NOT NULL, stopped INTEGER NOT NULL DEFAULT 0, sealed INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS event(run TEXT NOT NULL, seq INTEGER NOT NULL, hash TEXT NOT NULL, raw TEXT NOT NULL, type TEXT NOT NULL, PRIMARY KEY(run,seq));
        CREATE TABLE IF NOT EXISTS export_seal(run TEXT PRIMARY KEY, raw TEXT NOT NULL);''')
        old = self.db.execute('SELECT hash FROM run WHERE id=?', (self.run,)).fetchone()
        if old and old[0] != self.plan_hash:
            self.db.close()
            raise ValueError('plan_conflict')
        self.db.execute('INSERT OR IGNORE INTO run(id,hash) VALUES(?,?)', (self.run, self.plan_hash))
        self.db.commit()

    def persist(self, raw):
        if not isinstance(raw, str) or len(raw.encode()) > 32768:
            raise ValueError('envelope_limit')
        envelope = parse(raw)
        if set(envelope) != {'event_json', 'event_sha256'}:
            raise ValueError('envelope_schema')
        text = envelope['event_json']
        if not isinstance(text, str) or digest(text) != envelope['event_sha256']:
            raise ValueError('event_hash')
        e = parse(text)
        required = {'version','run_id','plan_sha256','client_id','event_id','type','at_ms','previous_event_sha256'}
        if not required <= e.keys() or e['version'] != 1 or type(e['version']) is not int or e['run_id'] != self.run or e['plan_sha256'] != self.plan_hash or e['client_id'] != 'tenant_fixture':
            raise ValueError('event_identity')
        prefix = self.run + '/tenant_fixture/'
        suffix = e['event_id'][len(prefix):] if isinstance(e['event_id'], str) and e['event_id'].startswith(prefix) else ''
        if not re.fullmatch(r'0|[1-9][0-9]{0,5}', suffix) or type(e['at_ms']) not in (int,float) or not 0 <= e['at_ms'] <= 300000:
            raise ValueError('event_sequence_or_clock')
        seq = int(suffix)
        # Schema/semantic acceptance is the independent tenant auditor's responsibility.
        # This internal candidate preserves exact raw envelopes, never logs their content.
        try:
            self.db.execute('BEGIN IMMEDIATE')
            stopped, sealed = self.db.execute('SELECT stopped,sealed FROM run WHERE id=?', (self.run,)).fetchone()
            old = self.db.execute('SELECT hash,raw FROM event WHERE run=? AND seq=?', (self.run, seq)).fetchone()
            if old:
                if old != (envelope['event_sha256'], raw):
                    raise ValueError('event_conflict')
                self.db.rollback()
                return {'status':200,'ack':{'event_id':e['event_id'],'event_sha256':envelope['event_sha256'],'durable':True}}
            if sealed or stopped and e['type'] == 'attempt_intent':
                raise ValueError('admission_stopped')
            count = self.db.execute('SELECT COUNT(*) FROM event WHERE run=?', (self.run,)).fetchone()[0]
            previous = self.db.execute('SELECT hash FROM event WHERE run=? ORDER BY seq DESC LIMIT 1', (self.run,)).fetchone()
            if seq != count or e['previous_event_sha256'] != (previous[0] if previous else None):
                raise ValueError('chain_or_sequence')
            if count >= 2048:
                raise ValueError('event_quota')
            self.db.execute('INSERT INTO event VALUES(?,?,?,?,?)', (self.run,seq,envelope['event_sha256'],raw,e['type']))
            if e['type'] == 'fixture_stop':
                self.db.execute('UPDATE run SET stopped=1 WHERE id=?', (self.run,))
            self.hook('before_commit')
            self.db.commit()
            self.hook('after_commit_before_response')
        except BaseException:
            self.db.rollback()
            raise
        return {'status':201,'ack':{'event_id':e['event_id'],'event_sha256':envelope['event_sha256'],'durable':True}}

    def stop(self):
        self.db.execute('UPDATE run SET stopped=1 WHERE id=?',(self.run,))
        self.db.commit()

    def seal(self, elapsed_ms):
        if type(elapsed_ms) not in (int,float) or not 0 <= elapsed_ms <= 300000:
            raise ValueError('elapsed_limit')
        old = self.db.execute('SELECT raw FROM export_seal WHERE run=?',(self.run,)).fetchone()
        if old:
            rows = self.db.execute('SELECT raw FROM event WHERE run=? ORDER BY seq',(self.run,)).fetchall()
            return ''.join(row[0]+'\n' for row in rows), parse(old[0])
        with self.db:
            self.db.execute('UPDATE run SET stopped=1,sealed=1 WHERE id=?',(self.run,))
        rows = self.db.execute('SELECT raw,type FROM event WHERE run=? ORDER BY seq',(self.run,)).fetchall()
        text = ''.join(row[0]+'\n' for row in rows)
        terminal = parse(parse(rows[-1][0])['event_json']) if rows and rows[-1][1] == 'fixture_terminal' else None
        seal = {'mode':'OFFLINE_STUB_ONLY','run_id':self.run,'plan_sha256':self.plan_hash,
                'complete':bool(terminal),'observed_job_elapsed_ms':elapsed_ms,
                'export_sha256':digest(text),'event_count':len(rows),'client_event_counts':{'tenant_fixture':len(rows)}}
        with self.db:
            self.db.execute('INSERT INTO export_seal VALUES(?,?)',(self.run,canonical(seal)))
        # complete denotes transport collection only; auditor independently checks outcome/coverage.
        return text, seal

    def close(self):
        self.db.close()
