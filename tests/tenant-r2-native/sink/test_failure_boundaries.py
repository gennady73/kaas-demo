"""R3-10: local SQLite and in-memory handler faults; no sockets or Kafka."""
import io
import sqlite3
from types import SimpleNamespace
from unittest.mock import patch
from store import Store, Rejected, encode, digest, parse, MIN_FREE_BYTES
from server import handler
import test_store as fixtures
from test_store import envelope, RUN, PLAN

# Inherit only fixture setup/teardown, not the historical test suite.
import unittest
class FailureBoundaries(unittest.TestCase):
    setUp = fixtures.Checks.setUp
    tearDown = fixtures.Checks.tearDown

    def test_commit_failure_rolls_back_and_never_returns_ack(self):
        real = self.s.db
        class FailCommit:
            @property
            def in_transaction(self): return real.in_transaction
            def execute(self, sql, *args):
                if sql == 'COMMIT': raise sqlite3.OperationalError('synthetic commit failure')
                return real.execute(sql, *args)
            def __getattr__(self, name): return getattr(real, name)
        self.s.db = FailCommit()
        with self.assertRaises(sqlite3.OperationalError): self.s.event(envelope())
        self.assertFalse(real.in_transaction)
        self.assertEqual(self.s.export(), b'')
        self.s.close(); self.s = Store(self.path, RUN, PLAN)
        self.assertEqual(self.s.event(envelope())[0], 201)

    def test_committed_event_survives_lost_handler_response_and_exact_retry(self):
        H = handler(self.s, 'writer-synthetic', 'owner-synthetic')
        h = object.__new__(H); h.path = '/v1/events'
        raw = encode(envelope())
        h.headers = {'Authorization':'Bearer writer-synthetic','Content-Length':str(len(raw))}
        h.rfile = io.BytesIO(raw)
        h.connection = SimpleNamespace(settimeout=lambda _: None)
        responses = []
        def respond(*args):
            responses.append(args)
            if len(responses) == 1: raise BrokenPipeError('synthetic-private-canary')
        h.respond = respond
        h.dispatch('POST')
        self.assertEqual(responses[0][0], 201)  # construction after commit, delivery lost
        self.assertEqual(responses[1], (503, {'error':'unavailable'}))
        self.s.close(); self.s = Store(self.path, RUN, PLAN)
        status, reply = self.s.event(envelope())
        self.assertEqual(status, 200); self.assertTrue(reply['ack']['durable'])
        self.assertEqual(self.s.export(), encode(envelope()) + b'\n')

    def test_stop_and_seal_survive_reopen_without_changing_export(self):
        e = envelope(); self.s.event(e); self.s.stop()
        self.s.close(); self.s = Store(self.path, RUN, PLAN)
        with self.assertRaisesRegex(Rejected, 'stopped'):
            self.s.event(envelope(1, e['event_sha256'], 'attempt_intent'))
        terminal = envelope(1, e['event_sha256'], 'fixture_terminal')
        self.s.event(terminal); seal = self.s.seal(); raw = self.s.export()
        self.s.close(); self.s = Store(self.path, RUN, PLAN)
        self.assertEqual(self.s.seal(), seal)
        self.assertEqual(self.s.event(terminal)[0], 200)
        with self.assertRaises(Rejected): self.s.event(envelope(2, terminal['event_sha256']))
        self.assertEqual(self.s.export(), raw)
        self.assertEqual(digest(raw), seal['export_sha256'])

    def test_same_run_cannot_rebind_plan_and_unknown_version_cannot_append(self):
        self.s.event(envelope()); raw = self.s.export()
        with self.assertRaisesRegex(Rejected, 'identity_conflict'): Store(self.path, RUN, 'b'*64)
        e = envelope(); event = parse(e['event_json']); event['version'] = 2
        e = {'event_json':encode(event).decode(), 'event_sha256':digest(encode(event))}
        with self.assertRaisesRegex(Rejected, 'binding'): self.s.event(e)
        self.assertEqual(self.s.export(), raw)

    def test_concrete_capacity_boundaries_prevent_new_ack_but_allow_exact_retry(self):
        # Execute actual headroom comparisons, not a replacement headroom function.
        with patch('store.MAX_DATABASE_BYTES', 0):
            with self.assertRaisesRegex(Rejected, 'storage_budget'): self.s.event(envelope())
        with patch('store.shutil.disk_usage', return_value=SimpleNamespace(free=MIN_FREE_BYTES-1)):
            with self.assertRaisesRegex(Rejected, 'storage_budget'): self.s.event(envelope())
        self.assertEqual(self.s.export(), b'')
        with patch('store.shutil.disk_usage', return_value=SimpleNamespace(free=MIN_FREE_BYTES)):
            self.assertEqual(self.s.event(envelope())[0], 201)
        with patch('store.MAX_DATABASE_BYTES', 0):
            self.assertEqual(self.s.event(envelope())[0], 200)
        self.assertEqual(len(self.s.export().splitlines()), 1)
