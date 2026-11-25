import tempfile
import unittest
from pathlib import Path
from store import Store
from test_store import RUN, PLAN, envelope
from verify_export import verify

class ExportChecks(unittest.TestCase):
    def test_stable_and_partial_export_have_separate_acceptance(self):
        with tempfile.TemporaryDirectory() as tmp:
            s=Store(Path(tmp)/'events.sqlite',RUN,PLAN)
            try:
                s.event(envelope());s.stop();seal=s.seal();raw=s.export()
                result=verify(raw,seal);self.assertEqual(result['byte_integrity'],'VERIFIED');self.assertFalse(result['terminal_present']);self.assertEqual(result['fixture_acceptance'],'NOT_ASSESSED')
                for bad in [raw[:-1],raw+raw]:
                    with self.assertRaises(ValueError):verify(bad,seal)
                with self.assertRaises(ValueError):verify(raw,{**seal,'event_count':2})
                with self.assertRaises(ValueError):verify(raw,{**seal,'run_id':'r2-other'})
            finally:s.close()
    def test_terminal_export_seal_does_not_claim_case_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            s=Store(Path(tmp)/'events.sqlite',RUN,PLAN)
            try:
                first=envelope();s.event(first);s.event(envelope(1,first['event_sha256'],'fixture_terminal'));s.stop()
                result=verify(s.export(),s.seal());self.assertTrue(result['terminal_present']);self.assertEqual(result['fixture_acceptance'],'NOT_ASSESSED')
            finally:s.close()
if __name__=='__main__':unittest.main()
