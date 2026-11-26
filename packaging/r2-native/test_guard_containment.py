"""R3-11: shortened copy of process guard, inert local Python child only."""
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest

HERE = Path(__file__).resolve().parent
class GuardContainment(unittest.TestCase):
    def check_guard(self, ignore_term):
        source = (HERE/'build/client-guard.sh').read_text()
        command = 'exec timeout --signal=TERM --kill-after=5s 285s /usr/local/bin/k6 run /r2/entrypoint.js'
        self.assertEqual(source.count(command), 1)
        self.assertIsNotNone(shutil.which('timeout'))
        with tempfile.TemporaryDirectory(prefix='r3-guard-') as tmp:
            root = Path(tmp); ready = root/'ready'; stub = root/'inert.py'
            stub.write_text('import os,signal,time\n'+
                ('signal.signal(signal.SIGTERM,signal.SIG_IGN)\n' if ignore_term else '')+
                f'open({str(ready)!r},"w").write(str(os.getpid()))\nwhile True: time.sleep(0.05)\n')
            # Only this disposable copy is armed and accelerated. No k6 executable,
            # Kafka client, network or shipped guard is invoked/modified.
            (root/'cat').write_text('#!/bin/sh\nprintf true\n'); (root/'cat').chmod(0o700)
            import shlex
            local = command.replace('--kill-after=5s 285s', '--kill-after=0.2s 0.8s').replace(
                '/usr/local/bin/k6 run /r2/entrypoint.js', shlex.quote(sys.executable)+' '+shlex.quote(str(stub)))
            guard = root/'guard.sh';guard.write_text(source.replace(command,local))
            start = time.monotonic()
            p = subprocess.Popen(['sh',str(guard)],env={**os.environ,'PATH':str(root)+os.pathsep+os.environ['PATH']},
                stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
            try:
                p.communicate(timeout=5)
                self.assertTrue(ready.exists(), 'local stub must have started')
                self.assertEqual(p.returncode, -signal.SIGKILL if ignore_term else 124)
                self.assertLess(time.monotonic()-start, 4)
                proc = Path('/proc')/ready.read_text()/'stat'
                self.assertTrue(not proc.exists() or proc.read_text().split()[2]=='Z', 'stub still executing')
            finally:
                try: os.killpg(p.pid,signal.SIGKILL)
                except ProcessLookupError: pass
                p.wait(timeout=2)
    def test_term_stops_local_stub_and_never_reports_pass(self): self.check_guard(False)
    def test_kill_contains_term_ignoring_stub_and_never_reports_pass(self): self.check_guard(True)

if __name__=='__main__':unittest.main()
