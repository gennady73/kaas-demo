#!/usr/bin/env python3
"""Offline plan/data checks only. No subprocess, service clients or execution path."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]

def need(value, reason):
    if not value:
        raise ValueError(reason)

def validate():
    plan = json.loads((HERE / 'plan.json').read_text())
    flags = ['execution_enabled', 'deployment_enabled', 'registration_enabled',
             'workloads_enabled', 'fault_injection_enabled', 'automatic_sync_enabled', 'prune_enabled']
    need(all(plan[k] is False for k in flags), 'plan_enabled')
    need(plan['execution_window'] is None and plan['run_owner'] is None and plan['new_runner_image'] is None, 'runtime_authority_present')
    cases = {c['id']: c for c in plan['cases']}
    need(len(cases) == len(plan['cases']) == 12, 'case_ids')
    visited, active = set(), set()
    def walk(key):
        need(key in cases and key not in active, 'dependency_missing_or_cycle')
        if key in visited:
            return
        active.add(key)
        for dep in cases[key]['depends_on']:
            walk(dep)
        active.remove(key)
        visited.add(key)
    for key, case in cases.items():
        walk(key)
        need(case['execution_enabled'] is False and case['status'] == 'PLANNED_NOT_EXECUTED', 'case_enabled_or_tested')
        need(case['owners'] and case['acceptance'], 'case_contract')
        budget = case['future_budget_proposal']
        if budget:
            for field in ['maximum_client_seconds', 'maximum_original_value_bytes', 'maximum_payload_bytes']:
                need(type(budget[field]) is int and budget[field] > 0, 'invalid_budget')
            need(budget['maximum_client_seconds'] <= 300, 'functional_runtime_exceeds_proposal')
            if 'large_record_value_bytes' in budget:
                need(budget['proposed_large_records'] * budget['maximum_payload_bytes'] == budget['large_record_value_bytes'] <= budget['maximum_original_value_bytes'], 'payload_budget')
    for rel, digest in plan['baseline']['source_refs_sha256'].items():
        path = (REPO / rel).resolve()
        need(REPO in path.parents, 'source_path_outside_repository')
        need(hashlib.sha256(path.read_bytes()).hexdigest() == digest, 'source_changed:' + rel)
    base = REPO / 'docs/r2-05a3f2d-retest-2026-11-26'
    seal = json.loads((base / 'seal.json').read_text())
    raw = (base / 'events.ndjson').read_bytes()
    need(hashlib.sha256(raw).hexdigest() == seal['export_sha256'] == plan['baseline']['export_sha256'], 'seal_hash')
    events = [json.loads(json.loads(line)['event_json']) for line in raw.splitlines()]
    need(len(events) == seal['event_count'] == 182, 'evidence_count')
    by_id = {e['event_id']: e for e in events}
    for event in events:
        if event['type'] == 'case_start':
            need(event.get('case_kind') in ['positive', 'negative'], 'actual_case_kind_missing')
        if event['type'] == 'durable_receipt_ack':
            receipt = by_id.get(event.get('receipt_event_id'), {})
            need(event.get('case_id') is not None and event['case_id'] == receipt.get('case_id') and event['id'] == receipt.get('id'), 'actual_durable_case_link')
        for field in ['offset', 'log_start_offset', 'log_end_offset', 'partition']:
            if field in event:
                need(type(event[field]) is int and event[field] >= 0, 'actual_offset_domain')
        if 'committed_offset' in event:
            offset = event['committed_offset']
            need(offset is None or type(offset) is int and offset >= 0, 'actual_committed_domain')
    final = json.loads((base / 'final-resources.json').read_text())
    jobs = [x for x in final['items'] if x['kind'] == 'Job']
    need({j['metadata']['name'] for j in jobs} == set(plan['protected_client_Jobs']), 'saved_jobs_identity')
    need(all(j['spec']['suspend'] is True for j in jobs), 'saved_job_not_suspended')
    return {'status': 'OFFLINE_PLAN_VALIDATED', 'cases': len(cases),
            'R2_saved_event_count': len(events), 'R2_seal_hash_verified': True,
            'specific_C3_reported_field_and_offset_shapes_in_real_export': 'VALID',
            'C3_NW_01_02_general_auditor_findings': 'OPEN_NOT_FIXED_BY_THIS_VALIDATOR',
            'saved_jobs_suspended': len(jobs), 'live_state_refreshed': False,
            'execution_enabled': False, 'workloads_executed': False,
            'limitation': 'Plan and preserved-data inspection only; not an independent full auditor or R3 runtime qualification'}

if __name__ == '__main__':
    print(json.dumps(validate(), indent=2))
