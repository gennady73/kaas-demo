"""Review regressions for byte verification and secret-free authentication failure."""
import tempfile
import unittest
from pathlib import Path
from store import Store, parse, encode, digest
from verify_export import verify
from test_store import RUN,PLAN,envelope
import test_protocol

class ReviewChecks(unittest.TestCase):
 def test_seal_boolean_negative_count_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   s=Store(Path(tmp)/'db',RUN,PLAN)
   try:
    s.event(envelope());s.stop();seal=s.seal();raw=s.export()
    for count in [True,-1]:
     with self.assertRaises(ValueError):verify(raw,{**seal,'event_count':count})
   finally:s.close()
 def test_rehashed_boolean_event_version_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   s=Store(Path(tmp)/'db',RUN,PLAN)
   try:
    e=envelope();s.event(e);s.stop();seal=s.seal()
    event=parse(e['event_json']);event['version']=True;raw_event=encode(event).decode();e={'event_json':raw_event,'event_sha256':digest(raw_event.encode())};raw=encode(e)+b'\n'
    with self.assertRaises(ValueError):verify(raw,{**seal,'export_sha256':digest(raw)})
   finally:s.close()
 def test_non_ascii_bearer_is_fixed_unauthorized(self):
  # Exercise the handler directly, without opening a listener.
  p=test_protocol.ProtocolChecks();p.setUp()
  try:
   result=p.request('/v1/events',envelope(),role='秘密')
   self.assertEqual(result,(401,{'error':'authentication'}))
  finally:p.tearDown()
if __name__=='__main__':unittest.main()
