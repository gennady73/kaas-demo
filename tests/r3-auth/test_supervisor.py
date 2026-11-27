"""Real local subprocess containment plus isolated gate/sequence/evidence cases."""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

PACKAGE = Path(__file__).resolve().parents[2] / 'packaging/r3-auth-probe'
SDK = Path(os.environ.get('AUTH_TEST_SDK_DIR', '/tmp/kaas-auth-compile/libs'))
FAKE_JAVA = r'''
import hashlib,json,os,signal,subprocess,sys,time
from pathlib import Path
root=Path(__file__).resolve().parent
mode=(root/'mode').read_text()
payload=sys.stdin.buffer.read()
phase=sys.argv[-2]
if mode=='sequence_inspect':
    original=(root.parent/'password').read_bytes()
    assert (payload!=original) if phase=='negative' else (payload==original)
    assert all(payload not in value.encode() for value in sys.argv)
    assert all(payload not in value.encode() for value in os.environ.values())
if mode=='environment':
    assert 'JAVA_TOOL_OPTIONS' not in os.environ
    assert 'JDK_JAVA_OPTIONS' not in os.environ
if mode in ('hang','orphan'):
    signal.signal(signal.SIGTERM,signal.SIG_IGN)
    child=subprocess.Popen([sys.executable,'-c','import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(60)'])
    (root/'pids').write_text(str(os.getpid())+' '+str(child.pid))
    if mode=='orphan': sys.exit(0)
    time.sleep(60)
if mode=='stderr':
    sys.stderr.buffer.write(payload+b' '+hashlib.sha256(payload).hexdigest().encode())
if mode=='raw_stdout':
    sys.stdout.buffer.write(payload+b' '+hashlib.sha256(payload).hexdigest().encode());sys.exit(0)
if mode in ('out_overflow','err_overflow'):
    stream=sys.stdout.buffer if mode=='out_overflow' else sys.stderr.buffer
    stream.write(b'x'*70000);stream.flush();time.sleep(60)
outcome='BROKER_SASL_REJECTED' if phase=='negative' else 'OWN_METADATA_OK'
if mode=='unexpected_success' and phase=='negative':outcome='OWN_METADATA_OK'
if mode=='positive_fail':outcome='TLS_FAILURE'
row={'schema':'kaas-r3-auth-phase/v1','phase':phase,'outcome':outcome}
if mode=='unknown_outcome':row['outcome']=payload.decode()
if mode=='wrong_phase':row['phase']='negative' if phase!='negative' else 'positive_before'
print(json.dumps(row),flush=True)
sys.exit(0 if mode=='wrong_exit' else (0 if outcome=='OWN_METADATA_OK' else (20 if outcome=='BROKER_SASL_REJECTED' else 21)))
'''

def live(pid):
    try:
        state = Path('/proc/' + str(pid) + '/stat').read_text().split(') ', 1)[1][0]
        return state not in ('Z', 'X')
    except FileNotFoundError:
        return False

class SupervisorTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('auth_supervisor_fixture', PACKAGE / 'source/run_probe.py')
        self.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.m)
        self.temp = tempfile.TemporaryDirectory(prefix='kaas-auth-supervisor-')
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.m.ROOT = self.work / 'source'
        self.m.ROOT.mkdir()
        for name in ['AuthMetadataProbe.java', 'run_probe.py', 'log4j2.properties', 'source-lock.json']:
            (self.m.ROOT / name).write_bytes((PACKAGE / 'source' / name).read_bytes())
        self.m.PASSWORD = self.work / 'password'
        self.password = b'SYNTHETIC-OFFLINE-SECRET-ONLY'
        self.m.PASSWORD.write_bytes(self.password)
        self.m.CA = self.work / 'ca.crt'
        self.m.CA.write_bytes(b'-----BEGIN CERTIFICATE-----\nSYNTHETIC\n')
        self.m.EVIDENCE = self.work / 'evidence'
        self.m.EVIDENCE.mkdir()
        (self.m.EVIDENCE / 'termination.json').touch()
        self.bin = self.work / 'bin'
        self.bin.mkdir()
        (self.bin / 'java').write_text('#!' + sys.executable + '\n' + FAKE_JAVA)
        (self.bin / 'java').chmod(0o700)
        self.mode('ok')
        self.profile = json.loads((PACKAGE / 'profile.disabled.json').read_text())
        self.profile.update(execution_enabled=True, deployment_enabled=True, run_id='offline-fixture',
                            authorization_reference='OFFLINE_LOCAL_ONLY', window_start_epoch=int(time.time()) - 1,
                            window_end_epoch=int(time.time()) + 120)
        self.write_profile()
        self.env = patch.dict(os.environ, {'PATH': str(self.bin) + os.pathsep + os.environ['PATH']})
        self.env.start()
        self.addCleanup(self.env.stop)
        # SDK path selection is fixture-only; deployed constant remains fixed.
        self.path_patch = patch.object(self.m, 'Path', side_effect=lambda x: SDK if x == '/opt/kafka/libs' else Path(x))
        self.path_patch.start()
        self.addCleanup(self.path_patch.stop)
        self.addCleanup(self.cleanup_processes)

    def mode(self, value): (self.bin / 'mode').write_text(value)

    def cleanup_processes(self):
        if (self.bin / 'pids').exists():
            for pid in map(int, (self.bin / 'pids').read_text().split()):
                try: os.kill(pid, signal.SIGKILL)
                except ProcessLookupError: pass

    def write_profile(self):
        raw = (json.dumps(self.profile) + '\n').encode()
        (self.m.ROOT / 'profile.json').write_bytes(raw)
        self.approval = hashlib.sha256(raw).hexdigest()

    def main(self):
        stream = io.StringIO()
        with patch.dict(os.environ, {'R3_AUTH_APPROVED_PROFILE_SHA256': self.approval}), contextlib.redirect_stdout(stream):
            code = self.m.main()
        text = stream.getvalue()
        self.assertNotIn(self.password.decode(), text)
        self.assertNotIn(hashlib.sha256(self.password).hexdigest(), text)
        for f in self.m.EVIDENCE.iterdir():
            self.assertNotIn(self.password, f.read_bytes())
            self.assertNotIn(hashlib.sha256(self.password).hexdigest().encode(), f.read_bytes())
        return code, json.loads(text)

    def phase(self, name='positive_before', seconds=10):
        return self.m.child_phase(name, self.password, '4.2.1.redhat-00003', time.monotonic() + seconds)

    def test_three_phase_sequence_and_matching_evidence(self):
        self.mode('sequence_inspect')
        code, record = self.main()
        self.assertEqual(code, 0)
        self.assertEqual(record['status'], 'AUTH_PAIR_OBSERVED')
        self.assertEqual([r['phase'] for r in record['events']], list(self.m.PHASES))
        self.assertEqual((self.m.EVIDENCE / 'result.json').read_bytes(), (self.m.EVIDENCE / 'termination.json').read_bytes())

    def test_disabled_profile_starts_no_child(self):
        self.profile['execution_enabled'] = False
        self.write_profile()
        with patch.object(self.m.subprocess, 'Popen', side_effect=AssertionError('child forbidden')):
            code, record = self.main()
        self.assertEqual(code, 100)
        self.assertEqual(record['reason'], 'GATE_DISABLED')

    def test_profile_hash_drift_stops(self):
        self.approval = '0' * 64
        self.assertEqual(self.main()[1]['reason'], 'PROFILE_APPROVAL_MISMATCH')

    def test_source_drift_stops_before_child(self):
        (self.m.ROOT / 'AuthMetadataProbe.java').write_text('changed')
        self.assertEqual(self.main()[1]['reason'], 'SOURCE_DRIFT')

    def test_protocol_contract_drift_stops(self):
        self.profile['protocol_contract']['Metadata_version'] = 5
        self.write_profile()
        self.assertEqual(self.main()[1]['reason'], 'PROTOCOL_CONTRACT_MISMATCH')

    def test_expired_window_stops(self):
        self.profile['window_end_epoch'] = int(time.time()) - 2
        self.write_profile()
        self.assertEqual(self.main()[1]['reason'], 'WINDOW_MISMATCH')

    def test_positive_failure_stops_before_negative(self):
        self.mode('positive_fail')
        code, record = self.main()
        self.assertNotEqual(code, 0)
        self.assertEqual(len(record['events']), 1)

    def test_unexpected_negative_success_stops_before_post_control(self):
        self.mode('unexpected_success')
        code, record = self.main()
        self.assertNotEqual(code, 0)
        self.assertEqual(record['status'], 'FAIL')
        self.assertEqual(len(record['events']), 2)

    def test_stderr_secret_and_hash_discarded(self):
        self.mode('stderr')
        code, record = self.main()
        self.assertEqual(code, 0)
        self.assertTrue(all(x['sdk_stderr_bytes_discarded'] > 0 for x in record['events']))

    def test_raw_stdout_secret_never_exported(self):
        self.mode('raw_stdout')
        code, record = self.main()
        self.assertNotEqual(code, 0)
        self.assertNotEqual(record['status'], 'AUTH_PAIR_OBSERVED')

    def test_unknown_outcome_never_exported(self):
        self.mode('unknown_outcome')
        self.assertNotEqual(self.main()[0], 0)

    def test_wrong_phase_fails_closed(self):
        self.mode('wrong_phase')
        with self.assertRaises(self.m.Stop): self.phase()

    def test_wrong_exit_code_fails_closed(self):
        self.mode('wrong_exit')
        with self.assertRaises(self.m.Stop): self.phase('negative')

    def test_output_overflow_stops_and_reaps(self):
        self.mode('out_overflow')
        with self.assertRaisesRegex(self.m.Stop, '^OUTPUT_LIMIT$'): self.phase()
        self.assertIsNone(self.m.ACTIVE_PROCESS)

    def test_stderr_overflow_stops_and_reaps(self):
        self.mode('err_overflow')
        with self.assertRaisesRegex(self.m.Stop, '^OUTPUT_LIMIT$'): self.phase()
        self.assertIsNone(self.m.ACTIVE_PROCESS)

    def containment(self, mode):
        self.mode(mode)
        started = time.monotonic()
        with self.assertRaisesRegex(self.m.Stop, '^PHASE_DEADLINE$'):
            self.phase(seconds=3.3)
        self.assertLess(time.monotonic() - started, 4)
        pids = list(map(int, (self.bin / 'pids').read_text().split()))
        limit = time.monotonic() + 2
        while any(live(p) for p in pids) and time.monotonic() < limit: time.sleep(.02)
        self.assertTrue(all(not live(p) for p in pids))
        self.assertIsNone(self.m.ACTIVE_PROCESS)

    def test_deadline_kills_parent_and_grandchild(self): self.containment('hang')
    def test_parent_exit_does_not_leave_pipe_holding_grandchild(self): self.containment('orphan')

    def test_external_stop_kills_active_process_group(self):
        self.mode('hang')
        process = subprocess.Popen([str(self.bin / 'java'), 'positive_before', 'version'], stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        process.stdin.close()
        self.m.ACTIVE_PROCESS = process
        try:
            limit = time.monotonic() + 3
            while not (self.bin / 'pids').exists() and time.monotonic() < limit: time.sleep(.02)
            pids = list(map(int, (self.bin / 'pids').read_text().split()))
            with self.assertRaisesRegex(self.m.Stop, '^EXTERNAL_STOP$'):
                self.m.external_stop(signal.SIGTERM, None)
            process.wait(timeout=2)
            time.sleep(.1)
            self.assertTrue(all(not live(p) for p in pids))
        finally:
            self.m.ACTIVE_PROCESS = None
            if process.poll() is None: os.killpg(process.pid, signal.SIGKILL); process.wait(timeout=2)
            process.stdout.close();process.stderr.close()

    def test_evidence_write_failure_is_nonzero(self):
        with patch.object(self.m, 'termination_evidence', side_effect=OSError()):
            code, record = self.main()
        self.assertEqual(code, 101)
        self.assertEqual(record['status'], 'INCONCLUSIVE')

    def test_parent_JVM_environment_is_not_inherited(self):
        self.mode('environment')
        with patch.dict(os.environ, {'JAVA_TOOL_OPTIONS': 'forbidden-fixture-value', 'JDK_JAVA_OPTIONS': 'forbidden'}):
            self.assertEqual(self.phase()['outcome'], 'OWN_METADATA_OK')

    def test_real_SIGTERM_delivery_is_nonpassing_and_kills_group(self):
        self.mode('hang')
        # Import and redirect fixture filesystem constants in a separate parent;
        # actual main/child/signal handlers are the unchanged production functions.
        driver = self.work / 'driver.py'
        driver.write_text("""
import importlib.util,sys,signal,json
from pathlib import Path
spec=importlib.util.spec_from_file_location('probe',sys.argv[1]);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
root=Path(sys.argv[2]);m.ROOT=root/'source';m.PASSWORD=root/'password';m.CA=root/'ca.crt';m.EVIDENCE=root/'evidence'
m.Path=lambda x:Path(sys.argv[3]) if x=='/opt/kafka/libs' else Path(x)
signal.signal(signal.SIGTERM,m.external_stop);signal.signal(signal.SIGINT,m.external_stop)
try:code=m.main()
except BaseException:
 print(json.dumps({'status':'INCONCLUSIVE','reason':'EXTERNAL_STOP_OR_SUPERVISOR_ERROR'}),flush=True);code=101
sys.exit(code)
""")
        env = dict(os.environ, R3_AUTH_APPROVED_PROFILE_SHA256=self.approval)
        process = subprocess.Popen([sys.executable, str(driver), str(PACKAGE / 'source/run_probe.py'), str(self.work), str(SDK)],
                                   env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            limit = time.monotonic() + 4
            while not (self.bin / 'pids').exists() and time.monotonic() < limit: time.sleep(.02)
            self.assertTrue((self.bin / 'pids').exists())
            pids = list(map(int, (self.bin / 'pids').read_text().split()))
            process.send_signal(signal.SIGTERM)
            out, err = process.communicate(timeout=3)
            self.assertNotEqual(process.returncode, 0)
            self.assertEqual(json.loads(out)['status'], 'INCONCLUSIVE')
            self.assertNotIn(self.password, out + err)
            limit = time.monotonic() + 2
            while any(live(p) for p in pids) and time.monotonic() < limit: time.sleep(.02)
            self.assertTrue(all(not live(p) for p in pids))
        finally:
            if process.poll() is None: process.kill();process.communicate(timeout=2)

    def test_credential_drift_stops_before_next_phase(self):
        real = self.m.child_phase
        def mutate(*args):
            result = real(*args)
            self.m.PASSWORD.write_bytes(b'different-synthetic')
            return result
        with patch.object(self.m, 'child_phase', side_effect=mutate):
            code, record = self.main()
        self.assertNotEqual(code, 0)
        self.assertEqual(record['reason'], 'CREDENTIAL_OR_TRUST_CHANGED')
        self.assertEqual(len(record['events']), 1)

if __name__ == '__main__': unittest.main(verbosity=2)
