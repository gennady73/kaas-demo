"""Disabled candidate supervisor. No network calls except reviewed child Admin client.
Do not execute during offline preparation; the future profile must be explicitly armed.
"""
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import selectors
import signal
import subprocess
import time

ROOT = Path('/probe')
PASSWORD = Path('/credentials/principal/password')
CA = Path('/credentials/cluster-ca/ca.crt')
EVIDENCE = Path('/evidence')
ACTIVE_PROCESS = None
PHASES = ('positive_before', 'negative', 'positive_after')
OUTCOMES = {'OWN_METADATA_OK', 'BROKER_SASL_REJECTED', 'TLS_FAILURE', 'AUTHORIZATION_FAILURE',
            'TIMEOUT', 'OTHER_AUTHENTICATION_FAILURE', 'LOCAL_OR_UNPROVEN_SASL_FAILURE',
            'UNCLASSIFIED_FAILURE', 'INPUT_INVALID', 'METADATA_MISMATCH', 'CLOSE_FAILED'}

class Stop(Exception):
    pass

def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise Stop('DUPLICATE_JSON_KEY')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=lambda _: (_ for _ in ()).throw(Stop('INVALID_JSON_NUMBER')))

def file_bytes(path, maximum):
    with path.open('rb') as stream:
        data = stream.read(maximum + 1)
    if len(data) > maximum:
        raise Stop('INPUT_SIZE')
    return data

def source_lock():
    lock = strict_json(file_bytes(ROOT / 'source-lock.json', 8192))
    expected = {'AuthMetadataProbe.java', 'run_probe.py', 'log4j2.properties'}
    if set(lock['files']) != expected:
        raise Stop('SOURCE_LOCK_SHAPE')
    for name, digest in lock['files'].items():
        if not re.fullmatch(r'[0-9a-f]{64}', digest) or hashlib.sha256(file_bytes(ROOT / name, 65536)).hexdigest() != digest:
            raise Stop('SOURCE_DRIFT')
    return hashlib.sha256(file_bytes(ROOT / 'source-lock.json', 8192)).hexdigest()

def kill_group(process):
    # Any timeout/forced termination is nonpassing. Killing a wait never proves
    # SDK cancellation; termination itself must be externally observed later.
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=1)
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=1)
    except subprocess.TimeoutExpired:
        raise Stop('PROCESS_TERMINATION_UNCONFIRMED')

def child_phase(phase, supplied_password, sdk_version, deadline):
    global ACTIVE_PROCESS
    remaining = deadline - time.monotonic()
    if remaining < 3:
        raise Stop('OVERALL_DEADLINE')
    end = time.monotonic() + min(20, remaining - 2)
    command = ['java', '-Xms32m', '-Xmx128m', '-XX:MaxMetaspaceSize=128m',
               '-XX:ReservedCodeCacheSize=32m', '-XX:ActiveProcessorCount=1',
               '-Djava.io.tmpdir=/tmp', '-Dlog4j2.configurationFile=file:/probe/log4j2.properties',
               '-Dlog4j2.statusLoggerLevel=OFF', '--source', '17', '--class-path', '/opt/kafka/libs/*',
               '/probe/AuthMetadataProbe.java', phase, sdk_version]
    # No credentials in argv/environment/config files. Only this anonymous stdin
    # pipe carries the selected password. JVM options from the parent are removed.
    child_env = {'PATH': os.environ.get('PATH', '/usr/bin:/bin'), 'HOME': '/tmp', 'LANG': 'C.UTF-8'}
    if 'JAVA_HOME' in os.environ:
        child_env['JAVA_HOME'] = os.environ['JAVA_HOME']
    previous_mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGTERM, signal.SIGINT})
    try:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, start_new_session=True, env=child_env)
        ACTIVE_PROCESS = process
    finally:
        signal.pthread_sigmask(signal.SIG_SETMASK, previous_mask)
    streams = selectors.DefaultSelector()
    output = bytearray()
    error_count = 0
    try:
        process.stdin.write(supplied_password)
        process.stdin.close()
        for stream, tag in [(process.stdout, 'out'), (process.stderr, 'err')]:
            os.set_blocking(stream.fileno(), False)
            streams.register(stream, selectors.EVENT_READ, tag)
        while streams.get_map():
            if time.monotonic() >= end:
                raise Stop('PHASE_DEADLINE')
            for key, _ in streams.select(timeout=min(.1, max(0, end - time.monotonic()))):
                chunk = os.read(key.fileobj.fileno(), 4096)
                if not chunk:
                    streams.unregister(key.fileobj)
                    continue
                if key.data == 'out':
                    output.extend(chunk)
                    if len(output) > 8192:
                        raise Stop('OUTPUT_LIMIT')
                else:
                    error_count += len(chunk)  # Discard SDK text, never retain it.
                    if error_count > 65536:
                        raise Stop('OUTPUT_LIMIT')
        code = process.wait(timeout=max(.01, end - time.monotonic()))
        event = strict_json(output)
        if set(event) != {'schema', 'phase', 'outcome'} or event['schema'] != 'kaas-r3-auth-phase/v1' or event['phase'] != phase or event['outcome'] not in OUTCOMES:
            raise Stop('INVALID_PHASE_RESULT')
        expected_code = 0 if event['outcome'] == 'OWN_METADATA_OK' else (20 if event['outcome'] == 'BROKER_SASL_REJECTED' else 21)
        if code != expected_code or time.monotonic() > deadline:
            raise Stop('PHASE_EXIT_OR_DEADLINE')
        return {'phase': phase, 'outcome': event['outcome'], 'sdk_stderr_bytes_discarded': error_count}
    except Stop:
        kill_group(process)
        raise
    except Exception:
        kill_group(process)
        raise Stop('CHILD_PROCESS_ERROR') from None
    finally:
        ACTIVE_PROCESS = None
        streams.close()
        for stream in [process.stdout, process.stderr]:
            stream.close()
        output[:] = b''

def atomic_evidence(name, data):
    temp = EVIDENCE / ('.' + name + '.partial')
    target = EVIDENCE / name
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, target)
        parent = os.open(EVIDENCE, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(parent)
        finally:
            os.close(parent)
    except Exception:
        raise Stop('EVIDENCE_WRITE_FAILED') from None

def termination_evidence(data):
    # Kubernetes can bind-mount the termination file. Renaming over that mount
    # can fail with EBUSY; write this bounded nonsecret summary in place.
    fd = os.open(EVIDENCE / 'termination.json', os.O_WRONLY | os.O_TRUNC | os.O_NOFOLLOW)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        raise Stop('EVIDENCE_WRITE_FAILED') from None

def main():
    started = time.monotonic()
    deadline = started + 90
    record = {'schema': 'kaas-r3-auth-result/v1', 'status': 'NOT_RUN', 'reason': 'GATE_DISABLED',
              'events': [], 'application_value_bytes': 0, 'producer_consumer_operations': 0,
              'credential_values_or_hashes_recorded': False, 'external_notifications': False}
    exit_code = 100
    try:
        raw = file_bytes(ROOT / 'profile.json', 16384)
        profile = strict_json(raw)
        if profile.get('execution_enabled') is not True or profile.get('deployment_enabled') is not True:
            raise Stop('GATE_DISABLED')
        approval = os.environ.get('R3_AUTH_APPROVED_PROFILE_SHA256', '')
        if not re.fullmatch(r'[0-9a-f]{64}', approval) or hashlib.sha256(raw).hexdigest() != approval:
            raise Stop('PROFILE_APPROVAL_MISMATCH')
        if profile['case'] != 'R3-02-AUTH' or profile['external_notifications_enabled'] is not False or profile['protected_Jobs_must_remain_suspended'] is not True:
            raise Stop('SCOPE_MISMATCH')
        fixed = {'bootstrap': 'kaas-dev-kafka-bootstrap.kaas-kafka.svc:9093', 'principal': 'kaas-sbx-a-producer',
                 'topic': 'kaas-sbx-a-events', 'TLS': 'REQUIRED_CA_AND_HOSTNAME_VERIFICATION',
                 'SASL': 'SCRAM-SHA-512', 'credential_file': '/credentials/principal/password',
                 'cluster_CA_file': '/credentials/cluster-ca/ca.crt'}
        if profile['fixed_scope'] != fixed:
            raise Stop('SCOPE_MISMATCH')
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,63}', profile['run_id'] or '') or not isinstance(profile['authorization_reference'], str) or not profile['authorization_reference']:
            raise Stop('AUTHORIZATION_MISSING')
        now = time.time()
        if not (type(profile['window_start_epoch']) is int and type(profile['window_end_epoch']) is int and
                profile['window_start_epoch'] <= now < profile['window_end_epoch'] and 0 < profile['window_end_epoch'] - profile['window_start_epoch'] <= 600):
            raise Stop('WINDOW_MISMATCH')
        deadline = min(deadline, started + profile['window_end_epoch'] - now)
        version = profile['expected_sdk_version']
        jar = profile['expected_sdk_jar']
        if not isinstance(version, str) or version != '4.2.1.redhat-00003':
            raise Stop('SDK_IDENTITY_MISSING')
        if not isinstance(jar, str) or jar != 'kafka-clients-4.2.1.redhat-00003.jar':
            raise Stop('SDK_IDENTITY_MISSING')
        digest = profile['expected_sdk_jar_sha256']
        if not isinstance(digest, str) or not re.fullmatch(r'[0-9a-f]{64}', digest):
            raise Stop('SDK_IDENTITY_MISSING')
        jar_files = list(Path('/opt/kafka/libs').glob('kafka-clients-*.jar'))
        if len(jar_files) != 1 or jar_files[0].name != jar:
            raise Stop('SDK_IDENTITY_MISMATCH')
        jar_digest = hashlib.sha256()
        with jar_files[0].open('rb') as stream:
            for chunk in iter(lambda: stream.read(1048576), b''):
                jar_digest.update(chunk)
        if jar_digest.hexdigest() != digest:
            raise Stop('SDK_IDENTITY_MISMATCH')
        if not profile['runtime_image_reference'] or not re.fullmatch(r'.+@sha256:[0-9a-f]{64}', profile['runtime_image_reference']):
            raise Stop('IMAGE_IDENTITY_MISSING')
        record['source_lock_sha256'] = source_lock()
        record['run_id'] = profile['run_id']
        record['profile_sha256'] = approval
        record['runtime_image_reference_configured_not_attested'] = profile['runtime_image_reference']
        record['sdk_version_expected'] = version
        password = file_bytes(PASSWORD, 4096)
        if not password or any(c in password for c in [b'\n', b'\r', b'\x00']):
            raise Stop('CREDENTIAL_INPUT_INVALID')
        try:
            password.decode('utf-8', errors='strict')
        except UnicodeDecodeError:
            raise Stop('CREDENTIAL_INPUT_INVALID') from None
        # Fixed source facts, no arbitrary client endpoint/principal/topic inputs.
        ca_start = file_bytes(CA, 131072)
        if b'-----BEGIN CERTIFICATE-----' not in ca_start:
            raise Stop('TRUST_INPUT_INVALID')
        bad_password = secrets.token_urlsafe(32).encode('ascii')
        if hmac.compare_digest(password, bad_password):
            raise Stop('NEGATIVE_INPUT_COLLISION')
        for phase in PHASES:
            if not hmac.compare_digest(file_bytes(PASSWORD, 4096), password) or file_bytes(CA, 131072) != ca_start:
                raise Stop('CREDENTIAL_OR_TRUST_CHANGED')
            event = child_phase(phase, bad_password if phase == 'negative' else password, version, deadline)
            record['events'].append(event)
            wanted = 'BROKER_SASL_REJECTED' if phase == 'negative' else 'OWN_METADATA_OK'
            if event['outcome'] != wanted:
                record['status'] = 'FAIL' if phase == 'negative' and event['outcome'] in ['OWN_METADATA_OK', 'AUTHORIZATION_FAILURE'] else 'INCONCLUSIVE'
                raise Stop('UNEXPECTED_NEGATIVE_SUCCESS_OR_WRONG_LAYER' if phase == 'negative' else 'POSITIVE_CONTROL_FAILED')
        if not hmac.compare_digest(file_bytes(PASSWORD, 4096), password) or file_bytes(CA, 131072) != ca_start:
            raise Stop('CREDENTIAL_OR_TRUST_CHANGED')
        if time.monotonic() >= deadline:
            raise Stop('OVERALL_DEADLINE')
        record.update(status='AUTH_PAIR_OBSERVED', reason='CONTROLS_AND_BROKER_SASL_REJECTION')
        exit_code = 0
    except Stop as error:
        record['reason'] = str(error)  # Only local fixed enum strings reach Stop.
        if record['status'] == 'NOT_RUN' and record['events']:
            record['status'] = 'INCONCLUSIVE'
    except Exception:
        record.update(status='INCONCLUSIVE', reason='LOCAL_PRECONDITION_ERROR')
    record['elapsed_ms'] = round((time.monotonic() - started) * 1000)
    data = (json.dumps(record, sort_keys=True, separators=(',', ':')) + '\n').encode()
    if len(data) > 3000:
        record.update(status='INCONCLUSIVE', reason='RESULT_SIZE_LIMIT', events=[])
        exit_code = 101
        data = (json.dumps(record, sort_keys=True, separators=(',', ':')) + '\n').encode()
    try:
        atomic_evidence('result.json', data)
        termination_evidence(data)
        if exit_code == 0 and time.monotonic() >= deadline:
            raise Stop('OVERALL_DEADLINE')
    except Exception:
        print('{"schema":"kaas-r3-auth-result/v1","status":"INCONCLUSIVE","reason":"EVIDENCE_OR_FINAL_DEADLINE_FAILED"}', flush=True)
        return 101
    print(data.decode(), end='', flush=True)
    return exit_code

def external_stop(signum, frame):
    if ACTIVE_PROCESS is not None:
        try:
            os.killpg(ACTIVE_PROCESS.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    raise Stop('EXTERNAL_STOP')

if __name__ == '__main__':
    signal.signal(signal.SIGTERM, external_stop)
    signal.signal(signal.SIGINT, external_stop)
    try:
        code = main()
    except BaseException:
        print('{"schema":"kaas-r3-auth-result/v1","status":"INCONCLUSIVE","reason":"EXTERNAL_STOP_OR_SUPERVISOR_ERROR"}', flush=True)
        code = 101
    raise SystemExit(code)
