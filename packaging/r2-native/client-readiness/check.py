"""Read-only client-path probe: DNS/TLS, Admin metadata and empty sink access.

No Producer/Consumer constructor, subscription, poll, group join or offset write.
"""
import datetime
import http.client
import json
from pathlib import Path
import re
import socket
import ssl
import subprocess


REPORT = {}

def run():
    result = {'status': 'CHECKING', 'observed_UTC': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'produce_consume_operations': 0, 'mutating_Admin_operations': 0, 'group_joins': 0}
    REPORT.update(result)
    REPORT['stage'] = 'bootstrap_DNS'
    ca = ssl.create_default_context(cafile='/credentials/cluster-ca/ca.crt')
    host = 'kaas-dev-kafka-bootstrap.kaas-kafka.svc'
    result['bootstrap_addresses'] = sorted({x[4][0] for x in socket.getaddrinfo(host, 9093, type=socket.SOCK_STREAM)})
    REPORT['stage'] = 'bootstrap_TLS'
    with socket.create_connection((host, 9093), timeout=5) as raw:
        with ca.wrap_socket(raw, server_hostname=host) as channel:
            cert = channel.getpeercert()
            result['bootstrap_TLS'] = {'version': channel.version(), 'certificate_not_after': cert['notAfter'], 'SAN': cert.get('subjectAltName')}
    REPORT['stage'] = 'sink_HTTPS'
    sink_ca = ssl.create_default_context(cafile='/evidence-trust/service-ca.crt')
    h = http.client.HTTPSConnection('kaas-r2-evidence.kaas-demo.svc', 8443, context=sink_ca, timeout=5)
    try:
        h.request('GET', '/v1/export'); response = h.getresponse(); response.read(2048)
        result['sink_unauthenticated_export_HTTP'] = response.status
        if response.status != 401: raise RuntimeError()
    finally:
        h.close()
    REPORT.update(result)
    REPORT['stage'] = 'native_Admin'
    native = subprocess.run(['/usr/local/bin/k6', '--log-format', 'raw', 'inspect', '/checks/admin.js'], capture_output=True, text=True, timeout=75)
    observations = []
    for line in (native.stdout + '\n' + native.stderr).splitlines():
        if line.startswith('R2_ADMIN '): observations.append(json.loads(line[len('R2_ADMIN '):]))
    result['native_Admin'] = observations
    if native.returncode or len(observations) != 5 or any(not x['result']['ok'] for x in observations):
        result['status'] = 'NATIVE_ADMIN_CHECK_FAILED'
        return result, 2
    REPORT.update(result)
    REPORT['stage'] = 'topic_health'
    health = subprocess.run(['java', '-Xms32m', '-Xmx128m', '-XX:MaxMetaspaceSize=128m', '-XX:ReservedCodeCacheSize=32m', '-XX:ActiveProcessorCount=1', '--source', '17', '--class-path', '/opt/kafka/libs/*', '/checks/TopicHealth.java'], capture_output=True, text=True, timeout=45)
    rows = [json.loads(line[len('R2_HEALTH '):]) for line in health.stdout.splitlines() if line.startswith('R2_HEALTH ')]
    result['topic_health'] = rows
    if health.returncode or len(rows) != 4 or any(x.get('leader', -1) < 0 or len(x.get('replicas', [])) != 2 or len(x.get('ISR', [])) != 2 for x in rows):
        result['status'] = 'TOPIC_HEALTH_CHECK_FAILED'
        return result, 2
    result['status'] = 'READONLY_CLIENT_PATH_AND_METADATA_PASS'
    return result, 0


if __name__ == '__main__':
    try:
        report, code = run()
    except Exception as error:
        report, code = dict(REPORT, status='READONLY_CHECK_FAILED', credentials_in_output=False, error_class=type(error).__name__), 2
    print(json.dumps(report, sort_keys=True), flush=True)
    raise SystemExit(code)
