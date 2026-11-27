#!/usr/bin/env python3
"""Run only local fixture suites; never enables the runtime profile or calls oc."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import platform
import unittest

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]

class RecordedResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cases = []
    def addSuccess(self, test):
        super().addSuccess(test)
        self.cases.append({'id': test.id(), 'status': 'PASS'})
    def addFailure(self, test, error):
        super().addFailure(test, error)
        self.cases.append({'id': test.id(), 'status': 'FAIL', 'exception_type': error[0].__name__})
    def addError(self, test, error):
        super().addError(test, error)
        self.cases.append({'id': test.id(), 'status': 'ERROR', 'exception_type': error[0].__name__})
    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.cases.append({'id': test.id(), 'status': 'SKIP'})

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    files = list(HERE.glob('*.py')) + list(HERE.glob('*.java')) + [REPO / 'packaging/r3-auth-probe/source' / n for n in ['AuthMetadataProbe.java', 'run_probe.py', 'log4j2.properties', 'source-lock.json']]
    fingerprint = {str(p.relative_to(REPO)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
    with (args.output / 'tests.log').open('w') as log:
        result = unittest.TextTestRunner(stream=log, verbosity=2, resultclass=RecordedResult).run(
            unittest.defaultTestLoader.discover(str(HERE), pattern='test_*.py'))
    record = {'status': 'PASS_OFFLINE_FIXTURES_ONLY' if result.wasSuccessful() and not result.skipped else 'NONPASS',
              'completed_UTC': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'python': platform.python_version(),
              'tests_run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors), 'skipped': len(result.skipped),
              'cases': result.cases, 'source_fingerprints': fingerprint,
              'network_scope': 'Fake broker listeners bound only to127.0.0.1; Java fixture connects only to127.0.0.1. No sandbox API or real Kafka endpoint.',
              'synthetic_credentials_only': True, 'deployments': 0, 'external_notifications': False,
              'limits': 'Local JDK25/Python environment, exact extracted SDK jars, synthetic TLS/SCRAM server. Supervisor uses a stand-in java executable; no claim about target image launcher/SCC/mounts or deployed service.'}
    (args.output / 'result.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps({k: record[k] for k in ['status', 'tests_run', 'failures', 'errors', 'skipped']}))
    return 0 if record['status'] == 'PASS_OFFLINE_FIXTURES_ONLY' else 1

if __name__ == '__main__': raise SystemExit(main())
