#!/usr/bin/env python3
"""Run local scaffold checks and Kustomize renders, saving evidence outside the repo."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import shutil
import subprocess
import sys

import yaml
import profile_tool as tool


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(output, label, command):
    result = subprocess.run(command, text=True, capture_output=True)
    (output / (label + '.stdout.txt')).write_text(result.stdout)
    (output / (label + '.stderr.txt')).write_text(result.stderr)
    tool.require(result.returncode == 0, f'{label} failed; see evidence logs')
    return {'label': label, 'command': command, 'returncode': result.returncode}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--preserved-baseline', type=Path,
                        help='Optional JSON mapping of existing repo-relative paths to SHA-256')
    args = parser.parse_args()
    output = args.output.resolve()
    tool.require(not output.exists() and not output.is_relative_to(tool.ROOT),
                 'use a fresh output outside the implementation repository')
    client = shutil.which('kubectl')
    tool.require(client is not None, 'local kubectl kustomize required; no download attempted')
    output.mkdir(parents=True)
    commands = [run(output, 'unit-checks', [sys.executable, '-m', 'unittest', 'discover',
        '-s', str(tool.HERE), '-p', 'test_*.py', '-v'])]
    commands.append(run(output, 'client-version', [client, 'version', '--client', '-o', 'json']))
    modes = {}
    for mode in ['dedicated', 'shared']:
        profile = tool.read_json(tool.HERE / 'fixtures' / (mode + '.json'))
        bundle = output / mode
        report = tool.write_bundle(profile, bundle)
        tool.read_bundle(profile, bundle)
        rendered = {}
        for i, component in enumerate(tool.build(profile)):
            label = mode + '-kustomize-' + str(i)
            command = [client, 'kustomize', str(bundle / component)]
            commands.append(run(output, label, command))
            rendered[component] = list(yaml.safe_load_all((output / (label + '.stdout.txt')).read_text()))
        counts = tool.validate_bundle(profile, rendered)
        modes[mode] = {'report': report, 'kustomize_exact_policy_and_cached_schema_counts': counts}
    candidates = {}
    for mode in ['dedicated', 'shared']:
        path = tool.ROOT / 'environments/candidates' / mode / 'profile.json'
        p = tool.read_json(path)
        tool.check_shape(p)
        missing = tool.unresolved(p)
        tool.require(bool(missing), 'candidate unexpectedly has no unresolved inputs')
        try:
            tool.build(p)
        except tool.Invalid as error:
            tool.require('unresolved inputs' in str(error), 'candidate rejected for unexpected reason')
        else:
            raise tool.Invalid('unresolved candidate unexpectedly rendered')
        candidates[mode] = {'render_rejected': True, 'unresolved_count': len(missing), 'unresolved': missing}
    provenance = tool.read_json(tool.HERE / 'schemas/provenance.json')
    for record in provenance['sources']:
        schema_path = tool.ROOT / record['schema_path']
        tool.require(digest(schema_path) == record['schema_sha256'], 'cached schema hash mismatch')
        original = tool.ROOT.parent / record['source_path']
        if original.exists():
            tool.require(digest(original) == record['source_sha256'], 'cached source hash mismatch')
            versions = tool.read_json(original)['spec']['versions']
            expected = next(v['schema']['openAPIV3Schema'] for v in versions if v['name'] == 'v1')
            tool.require(expected == tool.read_json(schema_path), 'schema differs from original v1 extraction')
    preserved = None
    if args.preserved_baseline:
        baseline = tool.read_json(args.preserved_baseline)
        changed = [p for p, sha in baseline.items() if not (tool.ROOT / p).is_file()
                   or digest(tool.ROOT / p) != sha]
        tool.require(not changed, 'existing files changed: ' + ', '.join(changed))
        preserved = {'count': len(baseline), 'all_unchanged': True, 'sha256': baseline}
    roots = ['platform/profiles', 'tenants/profiles', 'gitops/profiles',
             'policies/tenants', 'environments/candidates']
    sources = {str(p.relative_to(tool.ROOT)): digest(p)
               for prefix in roots for p in sorted((tool.ROOT / prefix).rglob('*'))
               if p.is_file() and '__pycache__' not in p.parts}
    result = {'date': '2026-11-25', 'timezone': 'Asia/Jerusalem',
              'status': 'OFFLINE_SCAFFOLDS_VALIDATED', 'execution_ready': False,
              'deployment_enabled': False, 'schema_source_date': '2026-11-23',
              'environment': {'python': sys.version.split()[0],
                  'PyYAML': importlib.metadata.version('PyYAML'),
                  'jsonschema': importlib.metadata.version('jsonschema')},
              'commands': commands, 'fixtures': modes, 'unresolved_candidates': candidates,
              'preserved_existing_demo_files': preserved, 'new_source_sha256': sources,
              'limitations': ['Kafka checks use cached v1 JSON schemas, not live server validation',
                  'ArgoCD objects policy-checked; no cached ArgoCD schema available',
                  'Kustomize commands only local files; no API/network or client traffic',
                  'No CI/admission/ArgoCD enforcement installation, bootstrap or Secret delivery',
                  'No deployment, sync, upgrade, restart, publication or continuity-test interaction',
                  'No runtime tenant isolation, capacity, recovery or independent reviewer claim']}
    (output / 'validation-result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'evidence': str(output),
                      'execution_ready': False, 'preserved_files': len(preserved['sha256']) if preserved else None}, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (tool.Invalid, OSError, ValueError, KeyError) as error:
        print('REJECTED: ' + str(error), file=sys.stderr)
        raise SystemExit(2)
