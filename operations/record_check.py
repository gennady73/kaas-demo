"""Check local C7 documentation records; never fetch evidence or qualify a release."""
import argparse
from datetime import datetime, timedelta
import json
import math
from pathlib import Path

TYPES = {'deployment-support', 'incident', 'recovery-result', 'evidence-custody', 'monitoring-evidence'}


def finite_number(value):
    try:
        return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)
    except OverflowError:
        return False


def read_json(path):
    def reject_constant(value):
        raise ValueError(f'nonfinite JSON number: {value}')

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f'duplicate JSON field: {key}')
            result[key] = value
        return result
    return json.loads(Path(path).read_text(), object_pairs_hook=pairs, parse_constant=reject_constant)


def assess(record, template):
    errors, unresolved = [], []

    def shape(value, example, path='$'):
        if example is None:
            return
        if isinstance(example, dict):
            if not isinstance(value, dict):
                errors.append(f'{path}: expected object')
                return
            if set(value) != set(example):
                errors.append(f'{path}: fields differ from template')
            for key in set(value) & set(example):
                shape(value[key], example[key], f'{path}.{key}')
        elif isinstance(example, list):
            if not isinstance(value, list):
                errors.append(f'{path}: expected array')
            elif example:
                for index, item in enumerate(value):
                    shape(item, example[0], f'{path}[{index}]')
        elif type(value) is not type(example):
            errors.append(f'{path}: expected {type(example).__name__}')

    def report():
        return {'scope': 'LOCAL_DOCUMENT_CONSISTENCY_ONLY', 'release_qualified': False,
                'execution_ready': False, 'status': 'INVALID' if errors else 'OPEN' if unresolved else 'NO_LOCAL_CONTRADICTION',
                'reported_conclusion': record.get('conclusion') if isinstance(record, dict) else None,
                'errors': sorted(set(errors)), 'unresolved_fields': sorted(set(unresolved)),
                'limitations': ['Evidence references are not opened, authenticated or verified.',
                                'No completeness, approval, no-loss, recovery or release acceptance is granted.']}

    shape(record, template)
    if errors:
        return report()

    def walk(value, path='$'):
        if isinstance(value, dict):
            for key, item in value.items():
                yield from walk(item, f'{path}.{key}')
        elif isinstance(value, list):
            if not value:
                unresolved.append(path + ': empty collection; meaning requires review')
            for index, item in enumerate(value):
                yield from walk(item, f'{path}[{index}]')
        else:
            yield path, value

    for path, value in walk(record):
        key = path.rsplit('.', 1)[-1]
        if value is None or value == 'OPEN' or value == '':
            unresolved.append(path)
            continue
        if isinstance(value, float) and not math.isfinite(value):
            errors.append(f'{path}: finite value required')
        if key.endswith(('_seconds', '_bytes', '_count')):
            if not finite_number(value) or value < 0:
                errors.append(f'{path}: nonnegative finite number required')
            elif key.endswith(('_bytes', '_count')) and not float(value).is_integer():
                errors.append(f'{path}: integer required')
        if key.endswith('_utc'):
            try:
                stamp = datetime.fromisoformat(value.replace('Z', '+00:00'))
                if 'T' not in value or stamp.utcoffset() != timedelta(0):
                    raise ValueError()
            except (AttributeError, TypeError, ValueError):
                errors.append(f'{path}: UTC ISO 8601 timestamp required')

    if record['record_type'] not in TYPES or record['record_type'] != template['record_type']:
        errors.append('record_type: unknown or mismatched template')
    if record['template_revision'] != template['template_revision']:
        errors.append('template_revision: mismatched template')
    if record['execution_enabled'] is not False:
        errors.append('execution_enabled: must remain false for documentation records')
    if record['record_status'] not in {'TEMPLATE', 'DRAFT', 'REVIEWED'}:
        errors.append('record_status: unsupported value')
    if record['conclusion'] not in {'OPEN', 'PASS', 'FAIL', 'INCONCLUSIVE', 'NOT_APPLICABLE'}:
        errors.append('conclusion: unsupported value')
    if record['record_status'] == 'REVIEWED' and not all(record[k] for k in ('reviewer', 'reviewed_at_utc')):
        errors.append('REVIEWED requires reviewer and review timestamp')
    if record['conclusion'] == 'PASS' and record['record_status'] != 'REVIEWED':
        errors.append('PASS claim requires reviewed record; this checker does not verify acceptance')

    if record['record_type'] == 'recovery-result':
        a, t, counts = record['acceptance'], record['timeline'], record['accounting']
        # These counters do not use the generic *_count naming convention.
        # Check supplied values even on FAIL/OPEN records; bool is not a count.
        for key in ('missing_required_records', 'integrity_mismatches'):
            value = counts[key]
            if value is not None and (type(value) is not int or value < 0):
                errors.append(f'$.accounting.{key}: nonnegative integer required (not boolean)')
        if a['no_loss_required'] is not True or a['recovery_target_seconds'] != 10800:
            errors.append('recovery requirements must preserve no loss and 10800-second target')
        if record['restart_category'] not in (None, 'RST-01', 'RST-02', 'RST-03', 'RST-04'):
            errors.append('restart_category: unsupported value')
        if record['variant'] not in (None, 'controlled', 'abrupt'):
            errors.append('variant: controlled or abrupt required; split mixed scenarios')
        try:
            start = datetime.fromisoformat(t['t0_utc'].replace('Z', '+00:00')) if t['t0_utc'] else None
            end = datetime.fromisoformat(t['t1_utc'].replace('Z', '+00:00')) if t['t1_utc'] else None
            if start and end:
                duration = (end - start).total_seconds()
                if duration < 0 or t['total_recovery_seconds'] != duration:
                    errors.append('recovery clock: reversed or inconsistent total')
        except (TypeError, ValueError, AttributeError):
            errors.append('recovery clock: invalid timestamps')
        if record['conclusion'] == 'PASS':
            required = [record['record_id'], record['environment_id'], record['tenancy_mode'],
                        record['restart_category'], record['variant'], a['preservation_contract_reference'],
                        a['approved_clock_definition_reference'], t['t0_utc'], t['t1_utc'],
                        counts['reconciliation_result_reference'], record['assessment']['c3_result_reference']]
            if not all(required):
                errors.append('recovery PASS claim missing core identity/contract/clock/result references')
            if counts['missing_required_records'] != 0 or counts['integrity_mismatches'] != 0:
                errors.append('recovery PASS conflicts with missing/unknown record or integrity counts')
            duration = t['total_recovery_seconds']
            if isinstance(duration, bool) or not isinstance(duration, (int, float)) or not 0 <= duration <= 10800:
                errors.append('recovery PASS conflicts with missing/invalid/over-target duration')
            if any(record['assessment'][key] != 'PASS' for key in ('no_loss_status', 'recovery_time_status', 'evidence_completeness_status')):
                errors.append('recovery PASS conflicts with OPEN/nonpassing assessment')
    return report()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('record', type=Path)
    parser.add_argument('--templates', type=Path, required=True, help='Explicit local directory of C7 templates')
    args = parser.parse_args()
    try:
        record = read_json(args.record)
        kind = record.get('record_type') if isinstance(record, dict) else None
        if not isinstance(kind, str) or kind not in TYPES:
            raise ValueError('unknown record_type')
        result = assess(record, read_json(args.templates / f'{kind}.json'))
    except (OSError, ValueError) as error:
        parser.exit(2, f'Invalid local record: {error}\n')
    print(json.dumps(result, indent=2, allow_nan=False))
    return 2 if result['errors'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
