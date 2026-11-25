"""Isolated tenant protocol v1. No Kafka imports or continuity database access."""
import hashlib
import json
import re
import shutil
import sqlite3
from pathlib import Path

PROTOCOL = 'kaas-tenant-evidence-v1'
MAX_EVENT_BYTES = 16384
MAX_EVENTS = 1024
MAX_DATABASE_BYTES = 32 * 1024 * 1024
MIN_FREE_BYTES = 64 * 1024 * 1024
BASE = {'version', 'run_id', 'plan_sha256', 'client_id', 'event_id', 'type', 'at_ms', 'previous_event_sha256'}
# Exact emitter schemas, independently checked against the additive native engine.
FIELDS = {
 'fixture_start': {'job_start_ms','deadline_ms','mode'},
 'phase_start': {'phase','deadline_ms','positive_cutoff_ms'},
 'client_open': {'case_id','binding_id','client_role','topic','group_id','auto_commit','commit_on_close','write_settings_signature'},
 'close_skipped': {'case_id','binding_id','reason'},
 'client_close': {'case_id','binding_id','client_role','closed','within_reserve'},
 'group_state': {'case_id','group_id','topic','stage','committed_offset','log_end_offset','members','membership_observed'},
 'attempt_intent': {'case_id','id','topic','value_bytes','checksum','negative'},
 'not_sent': {'case_id','id','reason'},
 'send_outcome': {'case_id','id','topic','value_bytes','checksum','outcome','negative','category','failure_stage','typed','intent_event_id','acknowledged_at_ms','ack_bucket'},
 'case_start': {'case_id','case_kind','binding_id','topic','group_id','control_ids'},
 'unexpected_record': {'case_id','topic','observed_key_sha256','checksum'},
 'receipt': {'case_id','id','topic','group_id','value_bytes','checksum','partition','offset'},
 'durable_receipt_ack': {'case_id','id','receipt_event_id'},
 'commit_intent': {'case_id','id','receipt_event_id','durable_event_id','group_id','partition','offset'},
 'commit_uncertain': {'case_id','id','receipt_event_id'},
 'commit': {'case_id','id','receipt_event_id','durable_event_id','group_id','partition','offset'},
 'case_end': {'case_id','status'},
 'unexpected_access': {'case_id','topic','group_id','kind','observed_key_sha256','checksum'},
 'denial_result': {'case_id','status','category','failure_stage','typed','control_ids','write_path_control_id','consumer_write_confounded','confound_resolution'},
 'negative_state_violation': {'case_id','reason'},
 'group_state_unavailable': {'case_id','topic','group_id','reason'},
 'reconciliation_boundary': {'positive_cutoff_ms'},
 'fixture_stop': {'reason','status'},
 'fixture_terminal': {'status','elapsed_ms','closed','positive_cutoff_ms'},
}
OPTIONAL = {
 'send_outcome': {'category','failure_stage','typed','acknowledged_at_ms','ack_bucket'},
 'case_start': {'binding_id','control_ids'},
 'unexpected_access': {'observed_key_sha256','checksum'},
}

def digest(value): return hashlib.sha256(value).hexdigest()
def encode(value): return json.dumps(value, separators=(',', ':'), ensure_ascii=True).encode()
def unique_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj: raise ValueError('duplicate_key')
        obj[key] = value
    return obj
def parse(value): return json.loads(value, object_pairs_hook=unique_object, parse_constant=lambda _: (_ for _ in ()).throw(ValueError('constant')))

class Rejected(Exception):
    """Fixed diagnostic only; never contains request bytes or credentials."""

class Store:
    def __init__(self, path, run_id, plan_sha256, hook=None):
        if not re.fullmatch(r'r2-[A-Za-z0-9_-]{1,48}', run_id) or not re.fullmatch('[a-f0-9]{64}', plan_sha256): raise Rejected('identity')
        self.path, self.run_id, self.plan = Path(path), run_id, plan_sha256
        self.hook = hook or (lambda _: None)
        self.db = sqlite3.connect(path, timeout=1, isolation_level=None)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.execute('PRAGMA busy_timeout=1000')
        self.db.executescript('CREATE TABLE IF NOT EXISTS identity(run TEXT PRIMARY KEY, plan TEXT NOT NULL);'
          'CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY, id TEXT UNIQUE NOT NULL, sha TEXT NOT NULL, envelope BLOB NOT NULL, type TEXT NOT NULL);'
          'CREATE TABLE IF NOT EXISTS flags(name TEXT PRIMARY KEY,value BLOB NOT NULL);')
        try:
            with self.transaction():
                row = self.db.execute('SELECT run,plan FROM identity').fetchall()
                if row and row != [(run_id, plan_sha256)]: raise Rejected('identity_conflict')
                if not row: self.db.execute('INSERT INTO identity VALUES(?,?)', (run_id, plan_sha256))
        except BaseException:
            self.db.close()
            raise

    def transaction(self):
        from contextlib import contextmanager
        @contextmanager
        def tx():
            self.db.execute('BEGIN IMMEDIATE')
            try:
                yield
                self.db.execute('COMMIT')
            except BaseException:
                if self.db.in_transaction: self.db.execute('ROLLBACK')
                raise
        return tx()

    def validate(self, envelope):
        if not isinstance(envelope,dict) or set(envelope) != {'event_json','event_sha256'}: raise Rejected('envelope')
        raw, sha = envelope['event_json'], envelope['event_sha256']
        if not isinstance(raw,str) or len(raw.encode()) > MAX_EVENT_BYTES or not isinstance(sha,str) or digest(raw.encode()) != sha: raise Rejected('hash')
        try: e = parse(raw)
        except (ValueError, TypeError): raise Rejected('json') from None
        if not isinstance(e,dict) or e.get('type') not in FIELDS or not BASE <= set(e) or set(e) - BASE - FIELDS[e['type']]: raise Rejected('schema')
        if not (FIELDS[e['type']]-OPTIONAL.get(e['type'],set())) <= set(e): raise Rejected('required_field')
        if type(e['version']) is not int or e['version'] != 1 or e['run_id'] != self.run_id or e['plan_sha256'] != self.plan or e['client_id'] != 'tenant_fixture': raise Rejected('binding')
        if not isinstance(e['event_id'],str) or not re.fullmatch(re.escape(self.run_id)+r'/tenant_fixture/(0|[1-9][0-9]{0,3})',e['event_id']): raise Rejected('event_id')
        if type(e['at_ms']) is not int or not 0 <= e['at_ms'] <= 300000: raise Rejected('clock')
        for key, value in e.items():
            if value is None or type(value) in (int,bool): continue
            if key in ('control_ids',):
                if not isinstance(value,list) or len(value)>4 or any(not isinstance(v,str) or not re.fullmatch(r'positive-kaas-sbx-[ab]-(events|audit)',v) for v in value): raise Rejected('field')
            elif not isinstance(value,str) or len(value)>256 or not re.fullmatch(r'[A-Za-z0-9_./:-]+',value): raise Rejected('field')
        return e

    def headroom(self):
        used = sum(p.stat().st_size for p in (self.path, Path(str(self.path)+'-wal'), Path(str(self.path)+'-shm')) if p.exists())
        if used >= MAX_DATABASE_BYTES or shutil.disk_usage(self.path.parent).free < MIN_FREE_BYTES: raise Rejected('storage_budget')

    def event(self, envelope):
        e = self.validate(envelope)
        seq = int(e['event_id'].rsplit('/',1)[1])
        blob = encode(envelope) + b'\n'
        duplicate = False
        with self.transaction():
            old = self.db.execute('SELECT sha,envelope FROM events WHERE id=?',(e['event_id'],)).fetchone()
            if old:
                if old != (envelope['event_sha256'],blob): raise Rejected('conflict')
                duplicate = True
            else:
                self.headroom()
                if self.flag('seal') is not None: raise Rejected('sealed')
                if self.flag('stop') is not None and e['type']=='attempt_intent': raise Rejected('stopped')
                tail = self.db.execute('SELECT seq,sha,envelope,type FROM events ORDER BY seq DESC LIMIT 1').fetchone()
                if seq != (tail[0]+1 if tail else 0) or seq>=MAX_EVENTS or e['previous_event_sha256'] != (tail[1] if tail else None): raise Rejected('chain')
                if tail and tail[3]=='fixture_terminal': raise Rejected('terminal')
                if tail and e['at_ms'] < parse(parse(tail[2])['event_json'])['at_ms']: raise Rejected('clock')
                self.db.execute('INSERT INTO events VALUES(?,?,?,?,?)',(seq,e['event_id'],envelope['event_sha256'],blob,e['type']))
                self.hook('before_commit')
        self.hook('after_commit_before_response')
        # Success is constructed only after SQLite FULL commit returns.
        return (200 if duplicate else 201), {'ack':{'durable':True,'event_id':e['event_id'],'event_sha256':envelope['event_sha256']}}

    def flag(self,name):
        row=self.db.execute('SELECT value FROM flags WHERE name=?',(name,)).fetchone()
        return row[0] if row else None
    def stop(self):
        with self.transaction(): self.db.execute('INSERT OR IGNORE INTO flags VALUES(?,?)',('stop',b'true'))
        return {'stopped':True}
    def export(self): return b''.join(row[0] for row in self.db.execute('SELECT envelope FROM events ORDER BY seq'))
    def seal(self):
        with self.transaction():
            old=self.flag('seal')
            if old is not None:return parse(old)
            if self.flag('stop') is None:raise Rejected('stop_required')
            raw=self.export()
            terminal=self.db.execute("SELECT envelope FROM events WHERE type='fixture_terminal'").fetchall()
            # Seal attests bytes and freeze, not fixture acceptance or infrastructure survival.
            seal={'protocol':PROTOCOL,'run_id':self.run_id,'plan_sha256':self.plan,'export_sha256':digest(raw),'event_count':self.db.execute('SELECT COUNT(*) FROM events').fetchone()[0],'terminal_present':len(terminal)==1,'acceptance':'REQUIRES_INDEPENDENT_AUDIT'}
            self.db.execute('INSERT INTO flags VALUES(?,?)',('seal',encode(seal)))
            return seal
    def close(self): self.db.close()
