"""Collector persistence/migration regression checks; no Kafka or network traffic."""
import contextlib,importlib.util,io,json,hashlib,os,sqlite3,tempfile,unittest
from pathlib import Path
from unittest import mock
class CollectorChecks(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);(self.root/'token').write_text('offline-test-only');self.prior={k:os.environ.get(k) for k in ['CONTINUITY_DATA','CONTINUITY_TOKEN_FILE']};os.environ.update(CONTINUITY_DATA=str(self.root),CONTINUITY_TOKEN_FILE=str(self.root/'token'))
  self.m=self.load();self.run='offline-unit';self.plan={'run_id':self.run,'mode':'sandbox_continuity','execution_ready':True,'execution_enabled':True,'stage':'15m','clients':[f'{r}_{i}' for r in ['producer','consumer'] for i in range(4)]};raw=json.dumps(self.plan);self.digest=hashlib.sha256(raw.encode()).hexdigest();self.assertEqual(self.post('/register',{'plan_json':raw,'plan_sha256':self.digest})[0],201)
 def load(self):
  spec=importlib.util.spec_from_file_location('collector_check',Path(__file__).with_name('server.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
 def tearDown(self):
  for k,v in self.prior.items():
   if v is None:os.environ.pop(k,None)
   else:os.environ[k]=v
  self.tmp.cleanup()
 def post(self,path,body):
  raw=json.dumps(body).encode();h=object.__new__(self.m.Handler);h.path=path;h.headers={'Authorization':'Bearer offline-test-only','Content-Length':str(len(raw))};h.rfile=io.BytesIO(raw);out=[];h.reply=lambda status,obj:out.append((status,obj));h.do_POST();return out[0]
 def envelope(self,n=0,kind='client_ready'):
  e={'run_id':self.run,'plan_sha256':self.digest,'client_id':'producer_0','event_id':self.run+'/producer_0/'+str(n),'type':kind,'at_ms':n};raw=json.dumps(e);return {'event_json':raw,'event_sha256':hashlib.sha256(raw.encode()).hexdigest()}
 def test_commit_before_ack_and_idempotent_conflict(self):
  e=self.envelope();status,ack=self.post('/events',e);self.assertEqual(status,201);self.assertTrue(ack['durable'])
  with contextlib.closing(sqlite3.connect(self.m.DB)) as c:self.assertEqual(c.execute('SELECT count(*) FROM events').fetchone()[0],1);self.assertEqual(c.execute('SELECT count FROM client_counts').fetchone()[0],1)
  self.assertEqual(self.post('/events',e)[0],200);self.assertEqual(self.m.summary(self.run)['event_count'],1)
  self.assertEqual(self.post('/events',self.envelope(kind='heartbeat'))[0],409)
  e['event_sha256']='bad';self.assertEqual(self.post('/events',e)[0],400)
 def test_migration_reopen_and_transaction_rollback(self):
  self.post('/events',self.envelope());self.m=self.load();self.assertEqual(self.m.summary(self.run)['event_count'],1)
  with self.m.database() as c:
   c.execute('INSERT INTO events VALUES(?,?,?,?,?,?,?,?,?)',('rollback',self.run,self.digest,'producer_0',9,'heartbeat',9,'{}','x'));c.rollback()
  self.assertEqual(self.m.summary(self.run)['event_count'],1)
  with self.m.database() as c:c.execute('DROP TRIGGER event_counts_insert');c.execute('DELETE FROM client_counts');c.execute('DELETE FROM collector_schema');c.commit()
  self.m=self.load();self.assertEqual(self.m.summary(self.run)['event_count'],1);self.assertEqual(self.m.readiness(self.run)['ready_clients'],['producer_0'])
 def test_summary_uses_bounded_counter_reads(self):
  self.post('/events',self.envelope());queries=[];database=self.m.database
  @contextlib.contextmanager
  def traced():
   with database() as c:
    c.set_trace_callback(queries.append);yield c
  with mock.patch.object(self.m,'database',traced):self.assertEqual(self.m.summary(self.run)['event_count'],1)
  self.assertTrue(any('FROM client_counts' in q for q in queries))
  self.assertFalse(any('GROUP BY' in q.upper() or 'COUNT(*)' in q.upper() for q in queries))
 def test_accept_defers_handshake_to_worker(self):
  listener=object.__new__(self.m.EvidenceHTTPServer);listener.tls_context=mock.Mock();sock=mock.Mock()
  with mock.patch('http.server.ThreadingHTTPServer.get_request',return_value=(sock,('offline',1))):
   listener.get_request()
  listener.tls_context.wrap_socket.assert_called_once_with(sock,server_side=True,do_handshake_on_connect=False)
  self.assertGreaterEqual(listener.request_queue_size,8)
 def test_handshake_and_idle_timeouts_are_separate(self):
  h=object.__new__(self.m.Handler);h.connection=mock.Mock(spec=self.m.ssl.SSLSocket)
  with mock.patch('socketserver.StreamRequestHandler.setup'):h.setup()
  self.assertEqual(h.connection.settimeout.call_args_list,[mock.call(5),mock.call(180)])
  h.connection.do_handshake.assert_called_once()
  self.assertGreater(self.m.REQUEST_IDLE_SECONDS,2*30)
 def test_stop_blocks_attempt_but_preserves_receipts(self):
  self.post('/runs/'+self.run+'/stop',{'reason':'offline-test'});self.assertEqual(self.post('/events',self.envelope(kind='attempt'))[0],409);self.assertEqual(self.post('/events',self.envelope(kind='receipt'))[0],201);self.assertEqual(self.m.summary(self.run)['stopped'],'operator_stop')
if __name__=='__main__':unittest.main()
