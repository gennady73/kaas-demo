"""Local temporary SQLite/process faults only; no Kafka clients or network."""
import multiprocessing
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from store import Store, Rejected, digest, encode, parse

RUN='r2-local-check';PLAN='a'*64
def envelope(n=0,previous=None,kind='fixture_start'):
    event={'version':1,'run_id':RUN,'plan_sha256':PLAN,'client_id':'tenant_fixture','event_id':f'{RUN}/tenant_fixture/{n}','type':kind,'at_ms':n,'previous_event_sha256':previous}
    if kind=='fixture_start':event.update(job_start_ms=0,deadline_ms=300000,mode='NATIVE_CANDIDATE')
    if kind=='fixture_terminal':event.update(status='NATIVE_INCOMPLETE',elapsed_ms=n,closed=True,positive_cutoff_ms=None)
    if kind=='attempt_intent':event.update(case_id='positive-kaas-sbx-a-events',id=RUN+'/kaas-sbx-a/kaas-sbx-a-events/0/positive-kaas-sbx-a-events',topic='kaas-sbx-a-events',value_bytes=1000,checksum='a'*64,negative=False)
    raw=encode(event).decode();return {'event_json':raw,'event_sha256':digest(raw.encode())}

def crash(path,point):
    def hook(stage):
        if stage==point:os._exit(23)
    store=Store(path,RUN,PLAN,hook)
    store.event(envelope())
    os._exit(24)

class Checks(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'events.sqlite';self.s=Store(self.path,RUN,PLAN)
    def tearDown(self):self.s.close();self.tmp.cleanup()
    def test_commit_ack_reopen_and_exact_retry(self):
        self.assertEqual(self.s.event(envelope())[0],201);self.s.close();self.s=Store(self.path,RUN,PLAN)
        self.assertEqual(self.s.event(envelope())[0],200);self.assertEqual(len(self.s.export().splitlines()),1)
    def test_three_process_crash_boundaries(self):
        self.s.close()
        for point,expected in [('before_commit',0),('after_commit_before_response',1),('after_response',1)]:
            path=Path(self.tmp.name)/(point+'.sqlite')
            p=multiprocessing.get_context('fork').Process(target=crash,args=(str(path),point));p.start();p.join(5)
            self.assertFalse(p.is_alive());self.assertEqual(p.exitcode,23 if point!='after_response' else 24)
            store=Store(path,RUN,PLAN)
            self.assertEqual(len(store.export().splitlines()),expected)
            self.assertEqual(store.event(envelope())[0],200 if expected else 201);store.close()
        self.s=Store(self.path,RUN,PLAN)
    def test_conflict_hash_sequence_binding_unknown_schema(self):
        self.s.event(envelope())
        altered=envelope();e=parse(altered['event_json']);e['at_ms']=1;raw=encode(e);altered={'event_json':raw.decode(),'event_sha256':digest(raw)}
        with self.assertRaises(Rejected):self.s.event(altered)
        for mutate in [lambda x:x.update(event_sha256='b'*64),lambda x:x.update(unknown='canary')]:
            e=envelope();mutate(e)
            with self.assertRaises(Rejected):self.s.event(e)
        for n,prev in [(2,'a'*64),(1,None)]:
            with self.assertRaises(Rejected):self.s.event(envelope(n,prev))
        with self.assertRaises(Rejected):self.s.event(envelope(1,envelope()['event_sha256'],'unknown_event'))
    def test_stop_blocks_admission_and_seal_freezes(self):
        e=envelope();self.s.event(e);self.s.stop()
        with self.assertRaises(Rejected):self.s.event(envelope(1,e['event_sha256'],'attempt_intent'))
        terminal=envelope(1,e['event_sha256'],'fixture_terminal');self.s.event(terminal)
        seal=self.s.seal();self.assertTrue(seal['terminal_present']);self.assertEqual(seal['export_sha256'],digest(self.s.export()))
        self.assertEqual(seal,self.s.seal());self.assertEqual(self.s.event(terminal)[0],200)
        with self.assertRaises(Rejected):self.s.event(envelope(2,terminal['event_sha256']))
    def test_partial_seal_is_never_acceptance(self):
        with self.assertRaises(Rejected):self.s.seal()
        self.s.stop();seal=self.s.seal();self.assertFalse(seal['terminal_present']);self.assertEqual(seal['acceptance'],'REQUIRES_INDEPENDENT_AUDIT')
    def test_disk_full_readonly_and_budget_do_not_ack(self):
        for error in [sqlite3.OperationalError('database or disk is full'),sqlite3.OperationalError('attempt to write a readonly database')]:
            self.s.hook=lambda stage,error=error: (_ for _ in ()).throw(error) if stage=='before_commit' else None
            with self.assertRaises(sqlite3.OperationalError):self.s.event(envelope())
            self.assertEqual(self.s.export(),b'')
        self.s.hook=lambda _:None
        with patch.object(self.s,'headroom',side_effect=Rejected('storage_budget')):
            with self.assertRaises(Rejected):self.s.event(envelope())
        self.assertEqual(self.s.export(),b'')
    def test_identity_cannot_rebind_existing_database(self):
        with self.assertRaises(Rejected):Store(self.path,'r2-other',PLAN)
    def test_duplicate_json_keys_rejected(self):
        e=envelope();raw=e['event_json'][:-1]+',"version":1}';e={'event_json':raw,'event_sha256':digest(raw.encode())}
        with self.assertRaises(Rejected):self.s.event(e)
    def test_no_secret_or_payload_field(self):
        e=envelope();event=parse(e['event_json']);event['password']='synthetic-canary';raw=encode(event);e={'event_json':raw.decode(),'event_sha256':digest(raw)}
        with self.assertRaises(Rejected):self.s.event(e)
        self.assertNotIn(b'canary',self.s.export())

if __name__=='__main__':unittest.main()
