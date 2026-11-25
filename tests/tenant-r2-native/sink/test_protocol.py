"""Handler checks with in-memory requests: no listeners, Kafka or credentials."""
import io
import tempfile
import unittest
from pathlib import Path
from server import handler
from store import Store, encode, parse
from test_store import envelope, RUN, PLAN

class ProtocolChecks(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.s=Store(Path(self.tmp.name)/'events.sqlite',RUN,PLAN)
        self.H=handler(self.s,'writer-synthetic-canary','owner-synthetic-canary')
    def tearDown(self):self.s.close();self.tmp.cleanup()
    def request(self,path,body=None,role='writer',method='POST'):
        h=object.__new__(self.H);h.path=path;raw=encode(body or {})
        h.headers={'Authorization':'Bearer '+role+'-synthetic-canary','Content-Length':str(len(raw))};h.rfile=io.BytesIO(raw)
        h.connection=type('Connection',(),{'settimeout':lambda self,n:None})()
        output=[];h.respond=lambda *args:output.append(args)
        h.dispatch(method);return output[0]
    def test_writer_can_persist_but_not_stop_export_or_seal(self):
        status,body=self.request('/v1/events',envelope());self.assertEqual(status,201);self.assertEqual(body['ack']['event_sha256'],envelope()['event_sha256'])
        for path,method in [('/v1/stop','POST'),('/v1/seal','POST'),('/v1/export','GET')]:self.assertEqual(self.request(path,role='writer',method=method)[0],401)
    def test_owner_cannot_write_and_unknown_routes_fail(self):
        self.assertEqual(self.request('/v1/events',envelope(),role='owner')[0],401)
        self.assertEqual(self.request('/events',envelope())[0],404)
        self.assertEqual(self.request('/register',{'mode':'sandbox_continuity'})[0],404)
    def test_export_seal_stop_byte_and_ack_protocol(self):
        self.request('/v1/events',envelope());self.assertEqual(self.request('/v1/stop',role='owner')[0],200)
        self.assertEqual(self.request('/v1/seal',role='owner')[0],200)
        result=self.request('/v1/export',role='owner',method='GET');self.assertEqual(result[0],200)
        self.assertEqual(parse(result[1].splitlines()[0]),envelope());self.assertEqual(result[2],'application/x-ndjson')
    def test_bad_hash_and_sink_failure_are_not_acknowledged(self):
        e=envelope();e['event_sha256']='x';status,body=self.request('/v1/events',e);self.assertEqual(status,409);self.assertNotIn('ack',body)
        self.s.hook=lambda _:(_ for _ in ()).throw(OSError('synthetic-secret-canary'))
        status,body=self.request('/v1/events',envelope());self.assertEqual(status,503);self.assertEqual(body,{'error':'unavailable'})

if __name__=='__main__':unittest.main()
