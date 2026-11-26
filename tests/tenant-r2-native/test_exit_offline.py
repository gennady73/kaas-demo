"""Actual k6 exit-status regressions using only synthetic iteration dependencies.

No native extension import/constructor, credentials, HTTP, Kafka or cluster API.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
BINARY = None


class ProcessExit(unittest.TestCase):
    def execute(self, outcome, legacy=False):
        source = (HERE / 'entrypoint.js').read_text()
        marker = 'export default function(){'
        self.assertEqual(source.count(marker), 1)
        body = source[source.index(marker):]
        if legacy:
            body = "export default function(){throw new Error('tenant_fixture_incomplete');}\n"
        engine = "throw new Error('PASSWORD_CANARY')" if outcome == 'throw' else "return {run_id:'OFFLINE_SYNTHETIC',status:'" + outcome + "',duration_ms:1,cleanup_complete:true}"
        harness = "import exec from 'k6/execution';\nexport const options={vus:1,iterations:1};\n"
        harness += "const native={now:()=>0},http={},gate={},writerToken='SYNTHETIC',plan={},sha=()=>'',sleep=()=>{};\n"
        harness += "const evidenceTransport=()=>({}),bindNative=()=>({});\nfunction runNativeTenantFixture(){" + engine + "}\n" + body
        with tempfile.TemporaryDirectory(prefix='r2-offline-exit-') as tmp:
            script = Path(tmp) / 'synthetic.js'; script.write_text(harness)
            config = Path(tmp) / 'config.json'; config.write_text('{}')
            result = subprocess.run([str(BINARY), '--config', str(config), '--quiet', 'run', str(script)], env={**os.environ, 'K6_NO_USAGE_REPORT': 'true'}, capture_output=True, text=True, timeout=20)
        self.assertNotIn('PASSWORD_CANARY', result.stdout + result.stderr)
        return result

    def test_legacy_throw_reproduces_false_success(self):
        self.assertEqual(self.execute('NATIVE_INCOMPLETE', legacy=True).returncode, 0)

    def test_incomplete_aborts_process(self):
        result = self.execute('NATIVE_INCOMPLETE')
        self.assertEqual(result.returncode, 108, result.stderr)

    def test_unexpected_exception_aborts_without_raw_error(self):
        result = self.execute('throw')
        self.assertEqual(result.returncode, 108, result.stderr)

    def test_complete_exits_zero(self):
        self.assertEqual(self.execute('NATIVE_COMPLETE').returncode, 0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', required=True, type=Path)
    args = parser.parse_args()
    BINARY = args.binary.resolve()
    unittest.main(argv=['offline_exit_regressions'], verbosity=2)
