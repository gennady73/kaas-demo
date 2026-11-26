#!/usr/bin/env python3
"""Re-audit preserved R2 files locally; never invokes clients, builds or services."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

REPO = Path(__file__).resolve().parents[3]
SOURCE = REPO / 'tests/tenant-r2-native'
EVIDENCE = REPO / 'docs/r2-05a3f2d-retest-2026-11-26'
EXPECTED_EXPORT = '18ba064608624da60e80101aaea81af9f0e8bfe9f4edbed126cc5903dd66c96e'

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def run(output):
    output.mkdir(parents=True, exist_ok=False)
    inputs = {p.name: sha(p.read_bytes()) for p in EVIDENCE.iterdir() if p.is_file()}
    public = json.loads((SOURCE / 'runtime-source-manifest.json').read_text())
    for name, digest in public['files'].items():
        if sha((SOURCE / name).read_bytes()) != digest:
            raise ValueError('auditor_source_manifest_drift')
    source_hashes = {name: sha((SOURCE / name).read_bytes()) for name in
                     ['audit.mjs', 'strict-json.mjs', 'native-policy.mjs', 'projection-lock.mjs', 'runtime-source-manifest.json']}
    raw = (EVIDENCE / 'events.ndjson').read_bytes()
    seal = json.loads((EVIDENCE / 'seal.json').read_text())
    if sha(raw) != EXPECTED_EXPORT or seal['export_sha256'] != EXPECTED_EXPORT:
        raise ValueError('historical_export_changed')
    commands = []
    for name, argv in [
        ('byte-integrity.json', [sys.executable, str(SOURCE / 'sink/verify_export.py'), '--export', str(EVIDENCE / 'events.ndjson'), '--seal', str(EVIDENCE / 'seal.json')]),
        ('semantic-reaudit.json', ['node', str(SOURCE / 'audit-export.mjs'), str(SOURCE / 'plan.json'), str(EVIDENCE / 'events.ndjson'), str(EVIDENCE / 'seal.json'), str(EVIDENCE / 'external-observation.json')]),
    ]:
        result = subprocess.run(argv, capture_output=True, text=True, timeout=30)
        commands.append({'argv': argv, 'exit_code': result.returncode, 'stderr': result.stderr})
        (output / name).write_text(result.stdout)
        if result.returncode:
            raise ValueError('offline_reaudit_failed:' + name)
    audit = json.loads((output / 'semantic-reaudit.json').read_text())
    if audit['status'] != 'NATIVE_EVIDENCE_MATCHED' or audit['matched_positive_cases'] != 4 or audit['matched_negative_cases'] != 8 or audit['issues']:
        raise ValueError('reaudit_scope_or_result')
    for name, digest in inputs.items():
        if sha((EVIDENCE / name).read_bytes()) != digest:
            raise ValueError('historical_file_changed:' + name)
    for name, digest in source_hashes.items():
        if sha((SOURCE / name).read_bytes()) != digest:
            raise ValueError('auditor_changed_during_review')
    report = {'status': 'SEALED_R2_OFFLINE_REAUDIT_PASS', 'historical_evidence_commit': '072eb185b32ca39b6ecaebf5b6c78e9569145d2e',
              'export_sha256': EXPECTED_EXPORT, 'event_count': seal['event_count'], 'input_files_sha256': inputs,
              'tool_source_sha256': source_hashes, 'commands': commands, 'historical_files_unchanged': True,
              'positive_cases_matched': 4, 'negative_cases_matched': 8, 'cluster_access': False,
              'producer_consumer_workloads_run': False, 'runtime_execution_repeated': False,
              'provenance': 'Re-audit of saved real-run evidence with versioned offline tool; saved external observations are not fresh cluster state'}
    (output / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ['input_files_sha256', 'tool_source_sha256', 'commands']}, indent=2))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.output.resolve())
