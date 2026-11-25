#!/usr/bin/env python3
"""Local tests and Kustomize checks; never downloads, authenticates, applies or syncs."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

import yaml
import tenant_only as tool


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='Fresh evidence directory outside repository')
    parser.add_argument('--kubectl', default=shutil.which('kubectl'))
    args = parser.parse_args()
    config = tool.read_json(tool.DEFAULT_INPUT)
    out = args.output.absolute()
    tool.require(args.kubectl is not None, 'local kubectl required for kustomize; nothing downloaded')
    tool.require(not out.exists(), 'evidence output must be a fresh directory')
    bundle = out/'bundle'
    tool.write_bundle(config, bundle)
    commands = []
    def run(label, command):
        result = subprocess.run(command, cwd=tool.ROOT, capture_output=True, text=True)
        (out/(label+'.stdout')).write_text(result.stdout)
        (out/(label+'.stderr')).write_text(result.stderr)
        commands.append({'label': label, 'command': command, 'returncode': result.returncode})
        tool.require(result.returncode == 0, label+' failed; inspect retained output')
        return result.stdout
    run('tenant-only-tests', [sys.executable, '-m', 'unittest', 'discover',
                             '-s', 'policies/tenant-only', '-p', 'test_*.py', '-v'])
    run('existing-c4-tests', [sys.executable, '-m', 'unittest', 'discover',
                             '-s', 'policies/tenants', '-p', 'test_*.py', '-v'])
    run('kubectl-client-version', [args.kubectl, 'version', '--client', '-o', 'json'])
    expected = tool.resource_documents(config)
    actual = {}
    for i, component in enumerate(expected):
        text = run('kustomize-'+str(i), [args.kubectl, 'kustomize', str(bundle/component)])
        actual[component] = list(yaml.safe_load_all(text))
    tool.validate_documents(config, actual, tool.registration_documents(config))
    summary = tool.validate_bundle(config, bundle)
    # Confirm the existing new-cluster workflow still excludes active platform identities.
    sys.path.insert(0, str(tool.ROOT/'policies/tenants'))
    import profile_tool
    fixture = profile_tool.read_json(profile_tool.HERE/'fixtures/shared.json')
    fixture['cluster'].update(namespace='kaas-kafka', name='kaas-dev')
    try:
        profile_tool.check_profile(fixture)
    except profile_tool.Invalid as error:
        existing_guard = str(error)
    else:
        raise tool.Invalid('existing new-cluster placement guard no longer protects live cluster')
    hashes = {str(p.relative_to(tool.ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
              for folder in [tool.HERE, tool.DEFAULT_INPUT.parent]
              for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    summary.update(commands=commands, input_source_sha256=hashes,
                   kustomize_exact_resources='PASS', existing_new_cluster_guard=existing_guard,
                   tests='tenant-only plus existing C4 suite PASS',
                   schema_scope='Cached Kafka v1 and exact local ArgoCD content; no installed ArgoCD/server admission')
    (out/'validation-result.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (tool.Invalid, OSError, ValueError, KeyError, TypeError) as error:
        raise SystemExit(str(error))
