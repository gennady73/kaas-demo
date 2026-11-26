"""Sink-only storage and loopback TLS checks; never constructs a Kafka client.

Run inside the authorized sink with a public service CA argument. Tokens stay in
the container. No events, stop or seal requests are sent.
"""
import argparse
import hashlib
import http.client
import json
import os
from pathlib import Path
import shutil
import socket
import sqlite3
import ssl
import tempfile


def verify(ca):
    data = Path('/var/lib/r2')
    database = data / 'evidence.sqlite'
    cfg = json.loads(Path('/etc/r2-sink/config.json').read_text())
    assert database.is_file()
    probe = None
    try:
        fd, probe = tempfile.mkstemp(prefix='.r2-readiness-', dir=data)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(b'R2_SINK_STORAGE_READINESS_ONLY\n')
            stream.flush()
            os.fsync(stream.fileno())
        assert Path(probe).read_bytes() == b'R2_SINK_STORAGE_READINESS_ONLY\n'
    finally:
        if probe is not None:
            Path(probe).unlink(missing_ok=True)
    directory_fd = os.open(data, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)
    db = sqlite3.connect('file:' + str(database) + '?mode=ro', uri=True, timeout=1)
    try:
        assert db.execute('PRAGMA quick_check').fetchall() == [('ok',)]
        assert db.execute('SELECT run,plan FROM identity').fetchall() == [(cfg['run_id'], cfg['plan_sha256'])]
        count = db.execute('SELECT COUNT(*) FROM events').fetchone()[0]
        flags = db.execute('SELECT COUNT(*) FROM flags').fetchone()[0]
        journal = db.execute('PRAGMA journal_mode').fetchone()[0]
    finally:
        db.close()
    assert count == 0 and flags == 0 and journal == 'wal'
    usage = shutil.disk_usage(data)
    assert usage.free >= 64 * 1024 * 1024
    host = 'kaas-r2-evidence.kaas-demo.svc'
    context = ssl.create_default_context(cadata=ca)
    context.minimum_version = ssl.TLSVersion.TLSv1_2

    def request(capability=None):
        with socket.create_connection(('127.0.0.1', 8443), timeout=5) as raw:
            with context.wrap_socket(raw, server_hostname=host) as channel:
                cert = channel.getpeercert(binary_form=True)
                headers = 'GET /v1/export HTTP/1.1\r\nHost: ' + host + '\r\nConnection: close\r\n'
                if capability is not None:
                    headers += 'Authorization: Bearer ' + capability + '\r\n'
                channel.sendall((headers + '\r\n').encode('ascii'))
                response = http.client.HTTPResponse(channel)
                response.begin()
                body = response.read(1024 * 1024 + 1)
                assert len(body) <= 1024 * 1024
                return response.status, len(body), channel.version(), hashlib.sha256(cert).hexdigest()

    anonymous = request()
    writer = request(Path('/auth/writer-token').read_text().strip())
    owner = request(Path('/owner-auth/owner-token').read_text().strip())
    assert anonymous[0] == 401 and writer[0] == 401 and owner[0] == 200 and owner[1] == 0
    mode = lambda p: {'uid': p.stat().st_uid, 'gid': p.stat().st_gid, 'mode': oct(p.stat().st_mode & 0o777)}
    return {'status': 'SINK_STORAGE_AND_TLS_PASS', 'runtime_uid': os.geteuid(),
            'runtime_gid': os.getegid(), 'supplementary_groups': os.getgroups(),
            'directory': mode(data), 'database': mode(database),
            'filesystem_write_fsync_read_unlink': 'PASS', 'filesystem_bytes': usage.total,
            'filesystem_free_bytes': usage.free, 'SQLite_quick_check': 'ok',
            'SQLite_journal_mode': journal, 'fixture_events': count, 'stop_or_seal_flags': flags,
            'TLS_verified_hostname': host, 'TLS_connection_address': '127.0.0.1:8443',
            'TLS_version': owner[2], 'peer_certificate_DER_sha256': owner[3],
            'anonymous_export_HTTP': anonymous[0], 'writer_export_HTTP': writer[0],
            'owner_export_HTTP': owner[0], 'export_bytes': owner[1],
            'Kafka_clients_or_producer_consumer_tests': False,
            'event_POST_or_stop_or_seal_sent': False,
            'network_policy_or_Service_path_verified': False,
            'restart_or_infrastructure_durability_verified': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--service-ca-pem', required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(verify(args.service_ca_pem), sort_keys=True))
    except Exception:
        print(json.dumps({'status': 'SINK_VERIFICATION_FAILED', 'credentials_in_output': False}))
        raise SystemExit(1)
