"""Arithmetic/unknown handling checks; no Kafka or collector dependency."""
import unittest
from budget_check import calculate


def fixture():
    return dict(daily_value_bytes=2_000_000_000_000, replication_factor=2,
                history_s=21600, oldest_unread_age_s=3600, outage_s=10800,
                catchup_s=1800, safety_s=1800, backlog_bytes=None,
                ingress_Bps=None, consume_Bps=None)


class BudgetChecks(unittest.TestCase):
    def test_decimal_replica_accounting(self):
        p = fixture()
        for daily, retained in [(2_000_000_000_000, 1_000_000_000_000),
                                (20_000_000_000_000, 10_000_000_000_000)]:
            p['daily_value_bytes'] = daily
            self.assertAlmostEqual(calculate(p)['retained_replica_payload_bytes'], retained, delta=0.01)

    def test_equality_is_unsafe(self):
        p = fixture()
        p['oldest_unread_age_s'] = 7200
        self.assertEqual(calculate(p)['replay_screen'], 'UNSAFE')

    def test_positive_margin_is_not_release(self):
        result = calculate(fixture())
        self.assertEqual(result['replay_slack_s'], 3600)
        self.assertFalse(result['release_qualified'])

    def test_unknown_not_zero(self):
        p = fixture()
        p['oldest_unread_age_s'] = None
        self.assertEqual(calculate(p)['replay_screen'], 'OPEN')

    def test_catchup_insufficient_service(self):
        p = fixture()
        p.update(backlog_bytes=100, ingress_Bps=10, consume_Bps=10)
        self.assertEqual(calculate(p)['catchup_model'], 'NO_POSITIVE_NET_DRAIN')
        p['consume_Bps'] = 9
        self.assertEqual(calculate(p)['catchup_model'], 'NO_POSITIVE_NET_DRAIN')

    def test_backlog_growth_and_allowance(self):
        p = fixture()
        p.update(backlog_bytes=100, ingress_Bps=10, consume_Bps=30, outage_s=10, catchup_s=9)
        result = calculate(p)
        self.assertEqual(result['catchup_estimate_s'], 10)
        self.assertFalse(result['catchup_allowance_covers_estimate'])

    def test_invalid_numeric_inputs(self):
        for value in [-1, float('nan'), float('inf'), True, '3600']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                p = fixture()
                p['outage_s'] = value
                calculate(p)

    def test_exact_contract(self):
        p = fixture()
        p['ingress_MBps'] = 10
        with self.assertRaises(ValueError):
            calculate(p)

    def test_replication_integer(self):
        p = fixture()
        p['replication_factor'] = 1.5
        with self.assertRaises(ValueError):
            calculate(p)

    def test_finite_overflow_rejected(self):
        p = fixture()
        p.update(daily_value_bytes=1e308, history_s=1e308)
        with self.assertRaises(ValueError):
            calculate(p)


if __name__ == '__main__':
    unittest.main()
