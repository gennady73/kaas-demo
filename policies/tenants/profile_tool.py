#!/usr/bin/env python3
"""Offline tenant scaffold renderer/checker. No network or cluster operations."""
from __future__ import annotations
import argparse
import copy
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sys

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
LIVE_NAMESPACES = {'kaas-kafka', 'kaas-demo', 'kafka-operator', 'openshift-gitops',
                   'openshift-gitops-operator'}
CONTROL_PLANE_NAMESPACES = {'openshift-gitops'}
PROTECTED_GITOPS_NAMES = {'kaas-demo', 'kaas-demo-kafka', 'kaas-demo-operator'}
STAGES = ('R0', 'R1', 'R2', 'R3')
ANNOTATION = 'kaas.example.com/offline-scaffold'


class Invalid(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise Invalid(message)


def read_json(path):
    return json.loads(Path(path).read_text())


def unresolved(value, path='$'):
    if value is None:
        return [path]
    if isinstance(value, str) and (not value.strip() or value.upper() in {'TODO', 'TBD', 'OPEN', 'UNRESOLVED'} or '${' in value):
        return [path]
    if isinstance(value, dict):
        return [p for k, v in value.items() for p in unresolved(v, path + '.' + k)]
    if isinstance(value, list):
        return [p for i, v in enumerate(value) for p in unresolved(v, f'{path}[{i}]')]
    return []


def input_stage(path):
    """Earliest milestone needing this input; input completeness is not approval."""
    if path.endswith('.delivery_reference') or path == '$.policy_references.secret_delivery':
        return 'R2'
    if path in {'$.policy_references.recovery_and_persistence',
                '$.policy_references.observability', '$.policy_references.governance'}:
        return 'R3'
    if (path in {'$.profile_id', '$.environment', '$.cluster.name', '$.cluster.namespace',
                 '$.policy_references.git_authorization'} or path.startswith('$.gitops.')
            or re.fullmatch(r'\$\.tenants\[\d+\]\.(id|owner|sync_groups)', path)):
        return 'R0'
    return 'R1'


def required_unresolved(profile, stage='R1'):
    require(stage in STAGES, 'unknown readiness stage')
    return [p for p in unresolved(profile) if STAGES.index(input_stage(p)) <= STAGES.index(stage)]


def check_placement(profile):
    """ArgoCD metadata may use the existing control plane; workloads may not."""
    c, g = profile['cluster'], profile['gitops']
    require(c['namespace'] not in LIVE_NAMESPACES and c['name'] != 'kaas-dev',
            'current live dev identities are excluded from scaffolds')
    require(g['namespace'] not in LIVE_NAMESPACES - CONTROL_PLANE_NAMESPACES,
            'protected namespace cannot host candidate GitOps metadata')
    if c['namespace'] is not None and g['namespace'] is not None:
        require(c['namespace'] != g['namespace'], 'Kafka and GitOps namespaces must differ')


def check_shape(profile):
    errors = sorted(jsonschema.Draft202012Validator(read_json(HERE / 'profile.schema.json'))
                    .iter_errors(profile), key=lambda e: str(list(e.path)))
    require(not errors, 'profile schema: ' + '; '.join(e.message for e in errors[:5]))


def quantity(value, cpu=False):
    pattern = r'([0-9]+(?:\.[0-9]+)?)(m?)' if cpu else r'([0-9]+(?:\.[0-9]+)?)(Ki|Mi|Gi|Ti)'
    match = re.fullmatch(pattern, value)
    require(match is not None, f'invalid {"CPU" if cpu else "memory/storage"} quantity: {value}')
    factors = {'': 1, 'm': Decimal('.001')} if cpu else {s: 1024 ** i for i, s in enumerate(['Ki', 'Mi', 'Gi', 'Ti'], 1)}
    result = Decimal(match[1]) * factors[match[2]]
    require(result > 0, 'resource quantity must be positive')
    return result


def check_resources(resources):
    for field in ['cpu', 'memory']:
        request = quantity(resources['requests'][field], field == 'cpu')
        limit = quantity(resources['limits'][field], field == 'cpu')
        require(request <= limit, f'{field} request exceeds limit')


def check_registration(profile):
    check_placement(profile)
    cluster, tenants = profile['cluster'], profile['tenants']
    descriptor = read_json(ROOT / 'platform/profiles' / profile['mode'] / 'composition.json')
    require(len(tenants) >= descriptor['minimum_tenants'], 'wrong tenant count for mode')
    require(descriptor['maximum_tenants'] is None or len(tenants) <= descriptor['maximum_tenants'],
            'dedicated mode requires exactly one tenant')
    require(profile['profile_id'].startswith('fixture-') == profile['synthetic_fixture'],
            'fixture profiles must use fixture- IDs; candidates must not')
    if profile['synthetic_fixture']:
        require(profile['gitops']['repo_url'].startswith('https://git.invalid/'),
                'fixture repository must be the reserved git.invalid host')
    require(not any(c in profile['gitops']['repo_url'] for c in ['*', '?', '#']),
            'repository URL must be exact and contain no wildcard/query/fragment')
    if profile['gitops']['namespace'] in CONTROL_PLANE_NAMESPACES:
        names = {profile['profile_id'] + '-platform'} | {
            profile['profile_id'] + '-' + t['id'] for t in tenants}
        require(not (names & PROTECTED_GITOPS_NAMES),
                'candidate GitOps metadata collides with a protected existing project/application')
    ids = [t['id'] for t in tenants]
    require(len(set(ids)) == len(ids), 'duplicate tenant IDs')
    groups = [set(profile['gitops']['platform_sync_groups'])] + [set(t['sync_groups']) for t in tenants]
    require(all(not (a & b) for i, a in enumerate(groups) for b in groups[i+1:]),
            'platform/tenant sync groups overlap')
    require(all(re.fullmatch(r'[a-zA-Z0-9_.:@/-]+', group) and '*' not in group
                for values in groups for group in values), 'invalid sync group')
    require(all(len(profile['profile_id'] + '-' + t['id']) <= 63 for t in tenants)
            and len(profile['profile_id'] + '-platform') <= 63,
            'generated GitOps name exceeds 63 characters')


def check_profile(profile):
    check_shape(profile)
    missing = required_unresolved(profile)
    require(not missing, 'unresolved inputs: ' + ', '.join(missing))
    cluster = profile['cluster']
    tenants = profile['tenants']
    check_registration(profile)
    require(cluster['follower_fetch_bytes'] >= cluster['record_ceiling_bytes'],
            'follower fetch must cover declared record ceiling')
    require(re.fullmatch(r'[a-zA-Z0-9./_-]+', cluster['rack_topology_key']) is not None,
            'invalid rack topology key')
    ids = [t['id'] for t in tenants]
    require(len(set(ids)) == len(ids), 'duplicate tenant IDs')
    app_namespaces = [ns for t in tenants for ns in t['app_namespaces']]
    require(len(set(app_namespaces)) == len(app_namespaces), 'tenant app namespaces overlap')
    require(not (set(app_namespaces) & (LIVE_NAMESPACES | {cluster['namespace'], profile['gitops']['namespace']})),
            'tenant namespaces overlap platform/live namespaces')
    group_sets = [set(profile['gitops']['platform_sync_groups'])] + [set(t['sync_groups']) for t in tenants]
    require(all(not (a & b) for i, a in enumerate(group_sets) for b in group_sets[i+1:]),
            'platform/tenant sync groups overlap')
    require(all(re.fullmatch(r'[a-zA-Z0-9_.:@/-]+', group) and '*' not in group
                for groups in group_sets for group in groups), 'invalid sync group')
    pool_names = [p['name'] for p in cluster['pools']]
    require(len(set(pool_names)) == len(pool_names), 'duplicate node pool name')
    broker_count = sum(p['replicas'] for p in cluster['pools'] if 'broker' in p['roles'])
    controllers = sum(p['replicas'] for p in cluster['pools'] if 'controller' in p['roles'])
    require(broker_count >= 2, 'RF2 requires at least two broker replicas')
    require(controllers in (3, 5), 'scaffold supports explicitly selected 3 or 5 controllers')
    for pool in cluster['pools']:
        quantity(pool['storage_size'])
        check_resources(pool['resources'])
        heaps = {}
        for key, heap in pool['heap'].items():
            require(re.fullmatch(r'[1-9][0-9]*[mMgG]', heap) is not None, 'invalid JVM heap quantity')
            heaps[key] = int(heap[:-1]) * (1024 ** (2 if heap[-1].lower() == 'm' else 3))
        require(heaps['-Xms'] <= heaps['-Xmx'] <= quantity(pool['resources']['limits']['memory']),
                'JVM heap ordering or memory limit invalid')
    check_resources(cluster['entity_operator_resources'])
    all_names = []
    for tenant in tenants:
        require(len(tenant['topics']) <= tenant['max_topics'], 'tenant topic admission budget exceeded')
        require(sum(t['partitions'] for t in tenant['topics']) <= tenant['max_partitions'],
                'tenant partition admission budget exceeded')
        suffixes = [t['suffix'] for t in tenant['topics']]
        require(len(set(suffixes)) == len(suffixes), 'duplicate topic suffix')
        for topic in tenant['topics']:
            require(topic['max_record_bytes'] <= cluster['record_ceiling_bytes'],
                    'topic record limit exceeds broker ceiling')
            all_names.extend([tenant['id'] + '-' + topic['suffix'],
                              tenant['id'] + '-' + topic['suffix'] + '-group'])
        all_names.extend(tenant['id'] + '-' + role for role in ['producer', 'consumer'])
        require(len(profile['profile_id'] + '-' + tenant['id']) <= 63,
                'generated GitOps name exceeds 63 characters')
    # Literal names remain unambiguous even for fixture-a and fixture-ab.
    require(len(set(all_names)) == len(all_names), 'generated tenant resource/group names collide')
    require(all(len(n) <= 63 for n in all_names + [profile['profile_id'] + '-platform']),
            'generated resource name exceeds 63 characters')


def template(path, values):
    def replace(value):
        if isinstance(value, dict):
            return {k: replace(v) for k, v in value.items()}
        if isinstance(value, list):
            return [replace(v) for v in value]
        if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
            return copy.deepcopy(values[value[2:-1]])
        return value
    return [replace(d) for d in yaml.safe_load_all((ROOT / path).read_text())]


def mark(document, profile):
    document['metadata'].setdefault('annotations', {}).update({ANNOTATION: 'true',
        'kaas.example.com/profile': profile['profile_id'],
        'kaas.example.com/deployment-enabled': 'false'})
    return document


def build(profile):
    check_profile(profile)
    c, g = profile['cluster'], profile['gitops']
    prefix = 'environments/candidates/' + profile['profile_id']
    values = dict(c, cluster_name=c['name'], namespace=c['namespace'])
    allowed_namespaces = sorted({c['namespace']} | {n for t in profile['tenants'] for n in t['app_namespaces']})
    values['network_peers'] = [{'namespaceSelector': {'matchLabels':
        {'kubernetes.io/metadata.name': ns}}} for ns in allowed_namespaces]
    platform = template('platform/profiles/common/kafka.yaml.template', values)
    for pool in c['pools']:
        platform += template('platform/profiles/common/nodepool.yaml.template',
                             dict(values, **pool, pool_name=pool['name']))
    documents = {prefix + '/platform': platform}
    scopes = [(profile['profile_id'] + '-platform', prefix + '/platform',
               ['Kafka', 'KafkaNodePool'], g['platform_sync_groups'])]
    for tenant in profile['tenants']:
        tid = tenant['id']
        tv = dict(values, tenant_id=tid)
        resources = []
        for topic in tenant['topics']:
            resources += template('tenants/profiles/topic.yaml.template',
                                  dict(tv, **topic, topic_name=tid + '-' + topic['suffix']))
        for role, identity in tenant['identities'].items():
            acls = [{'resource': {'type': 'topic', 'name': tid + '-' + t['suffix'],
                                  'patternType': 'literal'},
                     'operations': ['Write', 'Describe'] if role == 'producer' else ['Read', 'Describe']}
                    for t in tenant['topics']]
            if role == 'producer':
                acls.append({'resource': {'type': 'cluster'}, 'operations': ['IdempotentWrite']})
            else:
                acls += [{'resource': {'type': 'group', 'name': tid + '-' + t['suffix'] + '-group',
                                       'patternType': 'literal'}, 'operations': ['Read', 'Describe']}
                         for t in tenant['topics']]
            resources += template('tenants/profiles/user.yaml.template',
                                  dict(tv, user_name=tid + '-' + role, acls=acls, quotas=identity['quotas']))
        path = prefix + '/tenants/' + tid
        documents[path] = resources
        scopes.append((profile['profile_id'] + '-' + tid, path, ['KafkaTopic', 'KafkaUser'], tenant['sync_groups']))
    gitops = []
    for name, path, kinds, groups in scopes:
        gv = dict(values, **g, project_name=name, gitops_namespace=g['namespace'],
                  source_path=path, kind_allowlist=[{'group': 'kafka.strimzi.io', 'kind': k} for k in kinds],
                  sync_groups=groups,
                  sync_policies=[f'p, proj:{name}:sync, applications, {action}, {name}/*, allow'
                                 for action in ['get', 'sync']])
        gitops += template('gitops/profiles/application-set.yaml.template', gv)
    documents[prefix + '/gitops'] = gitops
    for docs in documents.values():
        for document in docs:
            mark(document, profile)
    return documents


def validate_schemas(documents):
    results = {}
    for docs in documents.values():
        for doc in docs:
            kind = doc['kind']
            if doc['apiVersion'] == 'kafka.strimzi.io/v1':
                schema = read_json(HERE / 'schemas' / (kind + '-v1.json'))
                errors = list(jsonschema.Draft4Validator(schema).iter_errors(doc))
                require(not errors, kind + ' cached schema: ' + '; '.join(e.message for e in errors[:3]))
                results[kind] = results.get(kind, 0) + 1
            else:
                require(kind in ['AppProject', 'Application'], 'forbidden kind: ' + kind)
    return results


def identity(document):
    m = document['metadata']
    return (document['apiVersion'], document['kind'], m.get('namespace', ''), m['name'])


def validate_bundle(profile, actual):
    expected = build(profile)
    require(set(actual) == set(expected), 'bundle component paths differ from approved profile')
    identities = set()
    for path, docs in actual.items():
        require(all(isinstance(d, dict) for d in docs), 'invalid resource document')
        ids = [identity(d) for d in docs]
        require(len(set(ids)) == len(ids), 'duplicate resource identity')
        require(not identities.intersection(ids), 'resource owned by multiple components')
        identities.update(ids)
        want = {identity(d): d for d in expected[path]}
        got = {identity(d): d for d in docs}
        require(want == got, 'resource content/ownership differs from approved profile: ' + path)
    return validate_schemas(actual)


def summary(profile, documents):
    c = profile['cluster']
    totals = {}
    for scope in ['requests', 'limits']:
        for resource in ['cpu', 'memory']:
            amount = sum(p['replicas'] * quantity(p['resources'][scope][resource], resource == 'cpu')
                         for p in c['pools'])
            amount += 2 * quantity(c['entity_operator_resources'][scope][resource], resource == 'cpu')
            totals[scope + '_' + ('cpu_cores' if resource == 'cpu' else 'memory_bytes')] = str(amount)
    return {'contract_version': '0.1', 'status': 'OFFLINE_SCAFFOLD_ONLY', 'deployment_enabled': False,
            'execution_ready': False, 'synthetic_fixture': profile['synthetic_fixture'],
            'report_version': '0.2',
            'unresolved_inputs_by_stage': {stage: [p for p in unresolved(profile)
                if input_stage(p) == stage] for stage in STAGES},
            'mode': profile['mode'], 'profile_id': profile['profile_id'],
            'components': {p: len(d) for p, d in documents.items()},
            'cached_schema_validated': validate_bundle(profile, documents),
            'derived_allocations_exclude_cluster_operator_and_platform': totals,
            'limitations': ['No deployment, runtime readiness or capacity qualification',
                'ArgoCD schemas not available locally; generated ArgoCD objects checked by exact policy only',
                'Git/ArgoCD/Kubernetes policy enforcement not installed',
                'No bootstrap/watch-scope/RBAC/Secret-delivery implementation or runtime isolation tests']}


def write_bundle(profile, output):
    documents = build(profile)
    report = summary(profile, documents)
    output = Path(output).resolve()
    # Never write a generated bundle inside source/workload trees.
    require(not output.is_relative_to(ROOT), 'output must be outside the implementation repository')
    require(not output.exists(), 'output directory already exists; use a fresh destination')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.mkdir()
    for component, docs in documents.items():
        dest = output / component
        dest.mkdir(parents=True)
        (dest / 'resources.yaml').write_text(yaml.safe_dump_all(docs, sort_keys=False))
        (dest / 'kustomization.yaml').write_text(yaml.safe_dump({
            'apiVersion': 'kustomize.config.k8s.io/v1beta1', 'kind': 'Kustomization',
            'resources': ['resources.yaml']}, sort_keys=False))
    report['profile_sha256'] = hashlib.sha256(json.dumps(profile, sort_keys=True).encode()).hexdigest()
    (output / 'review-report.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def read_bundle(profile, output):
    output = Path(output)
    expected = build(profile)
    expected_files = {Path('review-report.json')}
    actual = {}
    for component in expected:
        expected_files.update([Path(component) / 'resources.yaml', Path(component) / 'kustomization.yaml'])
        k = yaml.safe_load((output / component / 'kustomization.yaml').read_text())
        require(k == {'apiVersion': 'kustomize.config.k8s.io/v1beta1', 'kind': 'Kustomization',
                      'resources': ['resources.yaml']}, 'unexpected Kustomize components/patches/hooks')
        actual[component] = list(yaml.safe_load_all((output / component / 'resources.yaml').read_text()))
    require({p.relative_to(output) for p in output.rglob('*') if p.is_file()} == expected_files,
            'extra/missing files in generated bundle')
    report = read_json(output / 'review-report.json')
    want = summary(profile, actual)
    want['profile_sha256'] = hashlib.sha256(json.dumps(profile, sort_keys=True).encode()).hexdigest()
    require(report == want, 'review report differs from validated profile/bundle')
    return validate_bundle(profile, actual)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['inspect', 'readiness', 'render', 'validate'])
    parser.add_argument('--profile', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--bootstrap', type=Path,
                        help='Optional offline bootstrap plan for readiness; no resources applied')
    args = parser.parse_args()
    try:
        profile = read_json(args.profile)
        if args.command == 'inspect':
            check_shape(profile)
            print(json.dumps({'status': 'UNRESOLVED' if unresolved(profile) else 'INPUTS_FILLED_NOT_READY',
                              'deployment_enabled': False, 'execution_ready': False,
                              'unresolved': unresolved(profile)}, indent=2))
        elif args.command == 'readiness':
            import readiness
            bootstrap = read_json(args.bootstrap) if args.bootstrap else None
            print(json.dumps(readiness.assess(profile, bootstrap), indent=2))
        else:
            require(args.output is not None, '--output is required')
            result = write_bundle(profile, args.output) if args.command == 'render' else read_bundle(profile, args.output)
            print(json.dumps(result, indent=2))
    except (Invalid, OSError, ValueError, KeyError, TypeError, yaml.YAMLError) as error:
        print('REJECTED: ' + str(error), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
