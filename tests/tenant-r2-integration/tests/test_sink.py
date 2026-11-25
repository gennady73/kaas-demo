import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from offline_sink import Sink,canonical,digest

PLAN={'mode':'OFFLINE_ONLY','run_id':'offline-sink-test','execution_enabled':False,'deployment_enabled':False,'tests_enabled':False,'execution_ready':False}
def envelope(seq=0,previous=None,kind='fixture_start',**updates):
    e={'version':1,'run_id':PLAN['run_id'],'plan_sha256':digest(canonical(PLAN)),'client_id':'tenant_fixture','event_id':PLAN['run_id']+'/tenant_fixture/'+str(seq),'type':kind,'at_ms':seq,'previous_event_sha256':previous}
    e.update(updates);text=canonical(e)
    return canonical({'event_json':text,'event_sha256':digest(text)})

class Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'events.db';self.s=Sink(self.path,PLAN)
    def tearDown(self):
        self.s.close();self.temp.cleanup()
    def test_ack_after_commit_and_reopen(self):
        raw=envelope();r=self.s.persist(raw);self.assertTrue(r['ack']['durable']);self.s.close();self.s=Sink(self.path,PLAN);self.assertEqual(self.s.persist(raw)['status'],200)
    def test_same_id_conflict_rejected(self):
        self.s.persist(envelope())
        with self.assertRaisesRegex(ValueError,'conflict'):self.s.persist(envelope(kind='fixture_terminal'))
    def test_unknown_identity_or_plan_rejected(self):
        for update in [{'run_id':'other'},{'plan_sha256':'0'*64},{'client_id':'other'},{'version':True}]:
            with self.assertRaises(ValueError):self.s.persist(envelope(**update))
    def test_wrong_hash_rejected(self):
        d=json.loads(envelope());d['event_sha256']='0'*64
        with self.assertRaises(ValueError):self.s.persist(canonical(d))
    def test_gap_and_wrong_chain_rejected(self):
        for raw in [envelope(1),envelope(previous='0'*64)]:
            with self.assertRaises(ValueError):self.s.persist(raw)
    def test_stop_blocks_new_intents_allows_settlement(self):
        self.s.stop()
        with self.assertRaises(ValueError):self.s.persist(envelope(kind='attempt_intent'))
        self.assertEqual(self.s.persist(envelope(kind='send_outcome'))['status'],201)
    def test_terminal_export_and_no_late_write(self):
        raw=envelope(kind='fixture_terminal');self.s.persist(raw);text,seal=self.s.seal(100)
        self.assertEqual(text,raw+'\n');self.assertEqual(seal['export_sha256'],digest(text));self.assertTrue(seal['complete'])
        with self.assertRaises(ValueError):self.s.persist(envelope(1,json.loads(raw)['event_sha256']))
        self.assertEqual(self.s.persist(raw)['status'],200)
    def test_partial_export_is_incomplete(self):
        self.s.persist(envelope());self.assertFalse(self.s.seal(100)[1]['complete'])
    def test_seal_stable_after_reopen(self):
        self.s.persist(envelope(kind='fixture_terminal'));first=self.s.seal(100)
        self.s.close();self.s=Sink(self.path,PLAN)
        self.assertEqual(self.s.seal(200),first)
    def test_disk_failure_or_timeout_before_commit_never_acknowledges(self):
        for error in [OSError(28,'synthetic disk full'),TimeoutError('synthetic timeout')]:
            def fail(stage):
                if stage=='before_commit':raise error
            self.s.hook=fail
            with self.assertRaises(type(error)):self.s.persist(envelope())
            self.assertEqual(self.s.db.execute('SELECT COUNT(*) FROM event').fetchone()[0],0)
        self.s.hook=lambda _:None
        self.assertEqual(self.s.persist(envelope())['status'],201)
    def test_duplicate_keys_and_limits(self):
        for raw in ['{"event_json":"x","event_json":"y","event_sha256":"z"}','x'*32769]:
            with self.assertRaises(ValueError):self.s.persist(raw)
    def test_bad_clock(self):
        for v in [True,-1,300001,float('inf')]:
            with self.assertRaises(ValueError):self.s.persist(envelope(at_ms=v))
    def test_enabled_plan_refused(self):
        with self.assertRaises(ValueError):Sink(Path(self.temp.name)/'bad.db',{**PLAN,'execution_enabled':True})
    def test_registration_hash_conflict(self):
        with self.assertRaises(ValueError):Sink(self.path,{**PLAN,'extra':'changed'})
    def test_readonly_database_cannot_ack(self):
        self.s.db.execute('PRAGMA query_only=ON')
        with self.assertRaises(sqlite3.OperationalError):self.s.persist(envelope())
    def test_crash_before_commit_loses_unacked_event(self):self.crash('before_commit',False)
    def test_crash_after_commit_retry_recovers_lost_ack(self):self.crash('after_commit_before_response',True)
    def crash(self,point,persisted):
        self.s.close()
        script='''import os,sys,json
from offline_sink import Sink
s=Sink(sys.argv[1],json.loads(sys.argv[2]),hook=lambda p: os._exit(73) if p==sys.argv[4] else None)
s.persist(sys.argv[3])
'''
        p=subprocess.run([sys.executable,'-c',script,str(self.path),json.dumps(PLAN),envelope(),point],env={**os.environ,'PYTHONPATH':str(Path(__file__).resolve().parents[1])},capture_output=True,timeout=10)
        self.assertEqual(p.returncode,73)
        self.s=Sink(self.path,PLAN);self.assertEqual(self.s.persist(envelope())['status'],200 if persisted else 201)

if __name__=='__main__':unittest.main()
