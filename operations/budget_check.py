"""Offline planning arithmetic only; never performs qualification or network I/O."""
import argparse
import json
import math
from pathlib import Path


def number(value, name, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name}: finite numeric value required")
    if not math.isfinite(value) or value < 0 or (positive and value == 0):
        raise ValueError(f"{name}: invalid range")
    return value


def calculate(plan):
    required = {
        'daily_value_bytes', 'replication_factor', 'history_s',
        'oldest_unread_age_s', 'outage_s', 'catchup_s', 'safety_s',
        'backlog_bytes', 'ingress_Bps', 'consume_Bps',
    }
    if not isinstance(plan, dict) or set(plan) != required:
        raise ValueError('exact planning input fields required')
    for key, value in plan.items():
        if value is not None:
            number(value, key, key in {'replication_factor', 'history_s'})
    rf = plan['replication_factor']
    if rf is not None and not float(rf).is_integer():
        raise ValueError('replication_factor: integer required')
    out = {'scope': 'DERIVED_PLANNING_ONLY', 'release_qualified': False}
    daily, history = plan['daily_value_bytes'], plan['history_s']
    if all(x is not None for x in (daily, history, rf)):
        avg = daily / 86400
        out.update(mean_ingress_Bps=avg, retained_original_bytes=avg * history,
                   retained_replica_payload_bytes=avg * history * rf)
    terms = [plan[k] for k in ('history_s', 'oldest_unread_age_s', 'outage_s', 'catchup_s', 'safety_s')]
    if any(v is None for v in terms):
        out['replay_screen'] = 'OPEN'
    else:
        slack = terms[0] - sum(terms[1:])
        out.update(replay_slack_s=slack, replay_screen='POSITIVE_MARGIN' if slack > 0 else 'UNSAFE')
    terms = [plan[k] for k in ('backlog_bytes', 'ingress_Bps', 'consume_Bps', 'outage_s')]
    if any(v is None for v in terms):
        out['catchup_model'] = 'OPEN'
    else:
        backlog, ingress, consume, outage = terms
        if consume <= ingress:
            out['catchup_model'] = 'NO_POSITIVE_NET_DRAIN'
        else:
            estimate = (backlog + ingress * outage) / (consume - ingress)
            out.update(catchup_model='CONSTANT_RATE_ESTIMATE', catchup_estimate_s=estimate)
            selected = plan['catchup_s']
            out['catchup_allowance_covers_estimate'] = None if selected is None else selected >= estimate
    # Avoid emitting infinity after otherwise finite but overflowing arithmetic.
    for key, value in out.items():
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError(f'{key}: arithmetic overflow')
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plan', type=Path)
    args = parser.parse_args()
    try:
        result = calculate(json.loads(args.plan.read_text()))
    except (ValueError, OSError) as error:
        parser.exit(2, f'Invalid planning input: {error}\n')
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
