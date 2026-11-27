"""Loopback-only TLS/SCRAM protocol fixtures. No sandbox credentials or endpoints."""
import base64
import hashlib
import hmac
import importlib.util
import io
import json
import os
from pathlib import Path
import secrets
import signal
import socket
import ssl
import struct
import subprocess
import tempfile
import threading
import time
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[2]
PACKAGE = REPO / 'packaging/r3-auth-probe'
JDK = Path(os.environ.get('AUTH_TEST_JDK', '/usr/lib/jvm/java-25-temurin-jdk'))
SDK = Path(os.environ.get('AUTH_TEST_SDK_DIR', '/tmp/kaas-auth-compile/libs'))
HOST = 'kaas-dev-kafka-bootstrap.kaas-kafka.svc'
S = lambda value: struct.pack('>h', len(value.encode())) + value.encode()
B = lambda value: struct.pack('>i', len(value)) + value
I = lambda value: struct.pack('>i', value)
H = lambda value: struct.pack('>h', value)

def take(sock, length):
    data = b''
    while len(data) < length:
        chunk = sock.recv(length - len(data))
        if not chunk:
            raise EOFError()
        data += chunk
    return data

class Broker:
    def __init__(self, ctx, mode, password, canary):
        self.ctx, self.mode, self.password, self.canary = ctx, mode, password, canary
        self.headers, self.errors = [], []
        self.sock = socket.socket()
        self.sock.bind(('127.0.0.1', 0))
        self.sock.listen(1)
        self.sock.settimeout(7)
        self.port = self.sock.getsockname()[1]
        self.thread = threading.Thread(target=self.serve, daemon=True)
        self.thread.start()

    def request(self, connection, expected):
        size = struct.unpack('>i', take(connection, 4))[0]
        assert 0 < size <= 1048576
        data = take(connection, size)
        api, version, corr, length = struct.unpack('>hhih', data[:10])
        assert (api, version) == expected
        assert data[10:10 + length] == b'kaas-r3-auth-metadata'
        assert corr == len(self.headers) + 1
        self.headers.append((api, version, corr))
        return corr, data[10 + length:]

    def send(self, connection, corr, body):
        payload = I(corr) + body
        connection.sendall(I(len(payload)) + payload)

    def auth(self, connection, corr, error=0, token=b'', suffix=b''):
        # A synthetic secret-like error string must never be exposed by client.
        message = S(self.canary) if error else H(-1)
        self.send(connection, corr, H(error) + message + B(token) + struct.pack('>q', 0) + suffix)

    def serve(self):
        try:
            raw, _ = self.sock.accept()
            raw.settimeout(7)
            with raw, self.ctx.wrap_socket(raw, server_side=True) as conn:
                corr, body = self.request(conn, (17, 1))
                assert body == S('SCRAM-SHA-512')
                if self.mode == 'oversize':
                    conn.sendall(I(1048577))
                    return
                if self.mode == 'truncated':
                    conn.sendall(I(100) + b'xx')
                    return
                if self.mode == 'timeout':
                    time.sleep(5.3)
                    return
                self.send(conn, corr, H(0) + I(1) + S('SCRAM-SHA-512'))
                corr, body = self.request(conn, (36, 1))
                token = body[4:]
                assert struct.unpack('>i', body[:4])[0] == len(token)
                assert token.startswith(b'n,,n=kaas-sbx-a-producer,r=')
                client_bare = token[3:]
                nonce = token.rsplit(b'r=', 1)[1]
                if self.mode == 'early58':
                    self.auth(conn, corr, error=58)
                    return
                salt = b'offline-synthetic-salt'
                server_nonce = nonce + b'loopback-server'
                if self.mode == 'bad_nonce':
                    server_nonce = b'wrong-nonce'
                iterations = 1000000000 if self.mode == 'iterations' else 4096
                first = b'r=' + server_nonce + b',s=' + base64.b64encode(salt) + b',i=' + str(iterations).encode()
                self.auth(conn, corr, token=first)
                if self.mode == 'iterations':
                    return
                try:
                    corr, body = self.request(conn, (36, 1))
                except EOFError:
                    if self.mode == 'bad_nonce':
                        return
                    raise
                final = body[4:]
                final_bare, proof64 = final.rsplit(b',p=', 1)
                auth = client_bare + b',' + first + b',' + final_bare
                salted = hashlib.pbkdf2_hmac('sha512', self.password, salt, 4096)
                client_key = hmac.digest(salted, b'Client Key', 'sha512')
                stored = hashlib.sha512(client_key).digest()
                signature = hmac.digest(stored, auth, 'sha512')
                proof = bytes(a ^ b for a, b in zip(client_key, signature))
                valid_proof = hmac.compare_digest(base64.b64decode(proof64), proof)
                if self.mode in ('reject', 'corr', 'other', 'trailing', 'wrong_password'):
                    if self.mode == 'wrong_password':
                        assert not valid_proof
                    self.auth(conn, corr + (1 if self.mode == 'corr' else 0), error=29 if self.mode == 'other' else 58,
                              suffix=b'junk' if self.mode == 'trailing' else b'')
                    return
                assert valid_proof
                server_key = hmac.digest(salted, b'Server Key', 'sha512')
                server_sig = hmac.digest(server_key, auth, 'sha512')
                if self.mode == 'bad_signature':
                    server_sig = bytes(64)
                token = b'' if self.mode == 'empty_final' else b'v=' + base64.b64encode(server_sig)
                self.auth(conn, corr, token=token)
                if self.mode in ('bad_signature', 'empty_final'):
                    return
                corr, body = self.request(conn, (3, 4))
                assert body == I(1) + S('kaas-sbx-a-events') + b'\x00'
                topic = 'wrong-topic' if self.mode == 'wrong_topic' else 'kaas-sbx-a-events'
                error = 29 if self.mode == 'denied' else 0
                partition = H(0) + I(0) + I(0) + I(1) + I(0) + I(1) + I(0)
                topic_data = H(error) + S(topic) + b'\x00' + I(1) + partition
                metadata = I(0) + I(1) + I(0) + S('127.0.0.1') + I(self.port) + H(-1) + S('offline-cluster') + I(0) + I(1) + topic_data
                self.send(conn, corr, metadata)
        except (ssl.SSLError, ConnectionResetError, BrokenPipeError, EOFError):
            pass  # Client is required to terminate malformed/untrusted streams.
        except Exception as error:
            self.errors.append(type(error).__name__)  # Never record tokens/credentials.
        finally:
            self.sock.close()

class ProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='kaas-auth-behavior-')
        cls.work = Path(cls.temp.name)
        cls.password = secrets.token_urlsafe(24).encode()
        cls.canary = 'OFFLINE-CANARY-' + secrets.token_hex(16)
        assert hashlib.sha256((SDK / 'kafka-clients-4.2.1.redhat-00003.jar').read_bytes()).hexdigest() == '5f13fa84c366c1b20388aadfea9b0539654563bc90bcacd2515c849e8d37e669'
        for name, host in [('server', HOST), ('other', 'untrusted.invalid')]:
            subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '1',
                '-subj', '/CN=' + host, '-addext', 'subjectAltName=DNS:' + host,
                '-keyout', str(cls.work / (name + '.key')), '-out', str(cls.work / (name + '.crt'))],
                check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
        cls.context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        cls.context.load_cert_chain(cls.work / 'server.crt', cls.work / 'server.key')
        subprocess.run([str(JDK / 'bin/javac'), '-proc:none', '--release', '17', '-Xlint:all', '-classpath', str(SDK / '*'),
                        '-d', str(cls.work), str(PACKAGE / 'source/AuthMetadataProbe.java'), str(Path(__file__).with_name('LoopbackAuth.java'))],
                       check=True, capture_output=True, timeout=30)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def case(self, mode, expected, host=HOST, trust='server', wrong_password=False):
        broker = Broker(self.context, mode, self.password, self.canary)
        supplied = secrets.token_urlsafe(20).encode() if wrong_password else self.password
        result = subprocess.run([str(JDK / 'bin/java'), '-cp', str(self.work) + os.pathsep + str(SDK / '*'),
              'LoopbackAuth', str(broker.port), str(self.work / (trust + '.crt')), host],
              input=supplied, capture_output=True, timeout=15)
        broker.thread.join(timeout=7)
        self.assertFalse(broker.thread.is_alive())
        self.assertEqual(broker.errors, [])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.decode().strip(), expected)
        for secret in (self.password, supplied, self.canary.encode(), hashlib.sha256(supplied).hexdigest().encode(), base64.b64encode(supplied)):
            self.assertNotIn(secret, result.stdout + result.stderr)
        self.assertLessEqual(len(broker.headers), 4)
        return broker.headers

    def test_valid_scram_and_own_metadata(self): self.assertEqual(len(self.case('valid', 'OWN_METADATA_OK')), 4)
    def test_actual_wrong_password_rejected(self): self.assertEqual(len(self.case('wrong_password', 'BROKER_SASL_REJECTED', wrong_password=True)), 3)
    def test_received58_not_error_text(self): self.case('reject', 'BROKER_SASL_REJECTED')
    def test_wrong_correlation_cannot_pass(self): self.case('corr', 'UNCLASSIFIED_FAILURE')
    def test_other_error_cannot_pass(self): self.case('other', 'OTHER_AUTHENTICATION_FAILURE')
    def test_early58_cannot_pass(self): self.assertEqual(len(self.case('early58', 'LOCAL_OR_UNPROVEN_SASL_FAILURE')), 2)
    def test_trailing_bytes_cannot_pass(self): self.case('trailing', 'UNCLASSIFIED_FAILURE')
    def test_bad_server_signature_cannot_pass(self): self.case('bad_signature', 'LOCAL_OR_UNPROVEN_SASL_FAILURE')
    def test_empty_server_final_cannot_pass(self): self.case('empty_final', 'UNCLASSIFIED_FAILURE')
    def test_wrong_topic_cannot_pass(self): self.case('wrong_topic', 'METADATA_MISMATCH')
    def test_authorization_is_distinct(self): self.case('denied', 'AUTHORIZATION_FAILURE')
    def test_oversized_frame_cannot_pass(self): self.case('oversize', 'UNCLASSIFIED_FAILURE')
    def test_truncated_frame_cannot_pass(self): self.case('truncated', 'UNCLASSIFIED_FAILURE')
    def test_excessive_iteration_work_rejected(self): self.case('iterations', 'UNCLASSIFIED_FAILURE')
    def test_wrong_nonce_cannot_pass(self): self.case('bad_nonce', 'LOCAL_OR_UNPROVEN_SASL_FAILURE')
    def test_tls_hostname_mismatch_cannot_pass(self): self.assertEqual(self.case('valid', 'TLS_FAILURE', host='wrong.invalid'), [])
    def test_untrusted_ca_cannot_pass(self): self.assertEqual(self.case('valid', 'TLS_FAILURE', trust='other'), [])
    def test_read_timeout_cannot_pass(self): self.case('timeout', 'TIMEOUT')

if __name__ == '__main__':
    unittest.main(verbosity=2)
