"""Synthetic record checks; requires the shared C7 templates, never a live service."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from record_check import assess, read_json

TEMPLATES = Path(__file__).resolve().parents[1] / 'docs/operations/templates'


class RecordChecks(unittest.TestCase):
    def setUp(self):
        self.template = read_json(TEMPLATES / 'recovery-result.json')
        self.record = copy.deepcopy(self.template)

    def result(self):
        return assess(self.record, self.template)

    def reviewed_recovery(self):
        """Synthetic locally consistent core, not actual recovery evidence."""
        record = copy.deepcopy(self.template)
        record.update(record_status='REVIEWED', conclusion='PASS',
                      reviewer='SYNTHETIC-REVIEW-FIXTURE',
                      reviewed_at_utc='2026-11-25T10:00:00Z',
                      record_id='SYNTHETIC-NOT-RECOVERY-EVIDENCE',
                      environment_id='offline-fixture', tenancy_mode='dedicated',
                      restart_category='RST-01', variant='controlled')
        record['acceptance'].update(preservation_contract_reference='offline/contract',
                                    approved_clock_definition_reference='offline/clock')
        record['timeline'].update(t0_utc='2026-11-25T09:00:00Z',
                                  t1_utc='2026-11-25T10:00:00Z', total_recovery_seconds=3600)
        record['accounting'].update(missing_required_records=0, integrity_mismatches=0,
                                    reconciliation_result_reference='offline/reconcile')
        record['assessment'].update(c3_result_reference='offline/result',
                                    no_loss_status='PASS', recovery_time_status='PASS',
                                    evidence_completeness_status='PASS')
        return record

    def test_recovery_false_counters_are_invalid_for_pass(self):
        for field in ('missing_required_records', 'integrity_mismatches'):
            with self.subTest(field=field):
                record = self.reviewed_recovery()
                record['accounting'][field] = False
                result = assess(record, self.template)
                self.assertEqual(result['status'], 'INVALID')
                self.assertTrue(any(field in error for error in result['errors']))

    def test_recovery_counter_types_checked_regardless_of_conclusion(self):
        for field in ('missing_required_records', 'integrity_mismatches'):
            for conclusion in ('OPEN', 'PASS', 'FAIL', 'INCONCLUSIVE', 'NOT_APPLICABLE'):
                for value in (True, False, -1, 0.5, 0.0, float('nan'), float('inf'),
                              '0', [], {}):
                    with self.subTest(field=field, conclusion=conclusion, value=value):
                        record = self.reviewed_recovery()
                        record['conclusion'] = conclusion
                        record['accounting'][field] = value
                        result = assess(record, self.template)
                        self.assertEqual(result['status'], 'INVALID')
                        self.assertTrue(any(field in error for error in result['errors']))

    def test_recovery_zero_counters_do_not_grant_qualification(self):
        result = assess(self.reviewed_recovery(), self.template)
        self.assertEqual(result['errors'], [])
        self.assertEqual(result['status'], 'OPEN')  # Other evidence is intentionally missing.
        self.assertFalse(result['release_qualified'])
        self.assertFalse(result['execution_ready'])

    def test_recovery_null_counters_stay_unresolved(self):
        self.record['accounting'].update(missing_required_records=None, integrity_mismatches=None)
        result = self.result()
        self.assertEqual(result['errors'], [])
        self.assertEqual(result['status'], 'OPEN')
        for field in ('missing_required_records', 'integrity_mismatches'):
            self.assertIn('$.accounting.' + field, result['unresolved_fields'])

    def test_recovery_positive_failure_counts_are_valid_observations(self):
        record = self.reviewed_recovery()
        record['conclusion'] = 'FAIL'
        record['accounting'].update(missing_required_records=2, integrity_mismatches=1)
        result = assess(record, self.template)
        self.assertEqual(result['errors'], [])
        self.assertEqual(result['reported_conclusion'], 'FAIL')
        self.assertFalse(result['release_qualified'])

    def test_cli_recovery_counter_validation_and_controls(self):
        cases = []
        for field in ('missing_required_records', 'integrity_mismatches'):
            for conclusion in ('PASS', 'FAIL'):
                for value in (False, True, -1, 0.5):
                    record = self.reviewed_recovery()
                    record['conclusion'] = conclusion
                    record['accounting'][field] = value
                    cases.append((field, conclusion, value, record, 2))
        cases.append(('zero-control', 'PASS', 0, self.reviewed_recovery(), 0))
        failure = self.reviewed_recovery()
        failure['conclusion'] = 'FAIL'
        failure['accounting'].update(missing_required_records=1, integrity_mismatches=0)
        cases.append(('positive-failure-control', 'FAIL', 1, failure, 0))
        cases.append(('null-control', 'OPEN', None, copy.deepcopy(self.template), 0))
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'SYNTHETIC-counter-check.json'
            for field, conclusion, value, record, expected_code in cases:
                with self.subTest(field=field, conclusion=conclusion, value=value):
                    path.write_text(json.dumps(record, allow_nan=False))
                    run = subprocess.run([sys.executable, '-B',
                                          str(Path(__file__).with_name('record_check.py')),
                                          str(path), '--templates', str(TEMPLATES)],
                                         capture_output=True, text=True)
                    self.assertEqual(run.returncode, expected_code, run.stderr)
                    result = json.loads(run.stdout)
                    if expected_code == 2:
                        self.assertEqual(result['status'], 'INVALID')
                        self.assertTrue(any(field in error for error in result['errors']))
                    else:
                        self.assertEqual(result['errors'], [])
                        self.assertEqual(result['status'], 'OPEN')
                    self.assertFalse(result['release_qualified'])
                    self.assertFalse(result['execution_ready'])

    def test_all_five_templates_remain_open(self):
        for path in TEMPLATES.glob('*.json'):
            with self.subTest(path=path.name):
                template = read_json(path)
                result = assess(copy.deepcopy(template), template)
                self.assertEqual(result['status'], 'OPEN')
                self.assertFalse(result['release_qualified'])
                self.assertFalse(result['execution_ready'])

    def test_missing_field_is_invalid_not_defaulted(self):
        del self.record['timeline']['t0_utc']
        self.assertEqual(self.result()['status'], 'INVALID')

    def test_unexpected_field_rejected(self):
        self.record['approved'] = True
        self.assertTrue(self.result()['errors'])

    def test_wrong_section_type_has_diagnostic(self):
        self.record['timeline'] = 'bad'
        self.assertTrue(self.result()['errors'])

    def test_execution_flag_cannot_arm_record(self):
        self.record['execution_enabled'] = True
        self.assertTrue(self.result()['errors'])

    def test_reviewed_requires_person_and_time(self):
        self.record['record_status'] = 'REVIEWED'
        self.assertTrue(self.result()['errors'])

    def test_pass_needs_review_and_core_recovery_evidence(self):
        self.record['conclusion'] = 'PASS'
        errors = self.result()['errors']
        self.assertGreaterEqual(len(errors), 4)

    def test_over_target_and_missing_data_cannot_support_pass(self):
        self.record['conclusion'] = 'PASS'
        self.record['timeline']['total_recovery_seconds'] = 10801
        self.record['accounting']['missing_required_records'] = 1
        errors = '\n'.join(self.result()['errors'])
        self.assertIn('over-target duration', errors)
        self.assertIn('missing/unknown record', errors)

    def test_failure_with_missing_evidence_stays_open_not_pass(self):
        self.record['conclusion'] = 'FAIL'
        result = self.result()
        self.assertEqual(result['status'], 'OPEN')
        self.assertFalse(result['release_qualified'])

    def test_no_loss_and_target_cannot_be_weakened(self):
        self.record['acceptance']['no_loss_required'] = False
        self.record['acceptance']['recovery_target_seconds'] = 20000
        self.assertTrue(self.result()['errors'])

    def test_utc_required(self):
        for value in ['2026-11-25', '2026-11-25T10:00:00', '2026-11-25T10:00:00+02:00']:
            with self.subTest(value=value):
                self.record['timeline']['t0_utc'] = value
                self.assertTrue(self.result()['errors'])

    def test_clock_reversal_and_inconsistent_total(self):
        t = self.record['timeline']
        t.update(t0_utc='2026-11-25T10:00:00Z', t1_utc='2026-11-25T09:00:00Z', total_recovery_seconds=3600)
        self.assertTrue(self.result()['errors'])
        t['t1_utc'] = '2026-11-25T11:00:00Z'
        t['total_recovery_seconds'] = 3599
        self.assertTrue(self.result()['errors'])

    def test_correct_clock_does_not_fill_other_evidence(self):
        self.record['timeline'].update(t0_utc='2026-11-25T10:00:00Z', t1_utc='2026-11-25T11:00:00+00:00', total_recovery_seconds=3600)
        self.assertEqual(self.result()['status'], 'OPEN')

    def test_counters_reject_boolean_negative_fraction_nonfinite(self):
        for value in [True, -1, 0.5, float('nan')]:
            with self.subTest(value=value):
                self.record['accounting']['unsent_count'] = value
                self.assertTrue(self.result()['errors'])

    def test_invalid_variant_and_restart(self):
        self.record.update(variant='mixed', restart_category='collector-only')
        self.assertTrue(self.result()['errors'])

    def test_malformed_nullable_values_report_without_crash(self):
        self.record.update(variant=[], restart_category={})
        self.record['accounting']['unsent_count'] = 10 ** 400
        self.assertTrue(self.result()['errors'])

    def test_references_not_opened_and_input_not_mutated(self):
        self.record['evidence'][0]['source_reference'] = 'https://example.invalid/evidence'
        before = copy.deepcopy(self.record)
        with patch.object(Path, 'read_text', side_effect=AssertionError('must not read evidence')):
            self.assertEqual(self.result()['status'], 'OPEN')
        self.assertEqual(before, self.record)

    def test_duplicate_json_fields_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'duplicate.json'
            path.write_text('{"conclusion":"FAIL","conclusion":"PASS"}')
            with self.assertRaises(ValueError):
                read_json(path)

    def test_cli_unknown_type_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'bad.json'
            path.write_text(json.dumps({'record_type': '../arbitrary'}))
            run = subprocess.run([sys.executable, '-B', str(Path(__file__).with_name('record_check.py')),
                                  str(path), '--templates', str(TEMPLATES)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 2)
            self.assertIn('unknown record_type', run.stderr)


if __name__ == '__main__':
    unittest.main()
