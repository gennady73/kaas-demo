#!/usr/bin/env python3
"""Validate an offline bootstrap plan and optional local proposal documents. No apply."""
import argparse
import json
from pathlib import Path
import sys

import jsonschema
import yaml
import profile_tool as tool

LATER_FIELDS = {'$.credential_ca_delivery_and_rotation_evidence'}
VERBS = ['get', 'list', 'watch', 'create', 'update', 'patch']
RESOURCES = ['kafkas', 'kafkanodepools', 'kafkatopics', 'kafkausers']
EXTERNAL_CHECKS = [
    'Verify actual namespace ownership, operator/OLM watch configuration and no competing reconciler',
    'Check selected-version documentation/source supports the proposed watch-scope mechanism',
    'Validate real installed schemas and actual controller/global/project authorization',
    'Coordinate combined watch scopes/change window with other candidate and run owners',
    'Inspect actual namespace budgets/health before separately authorized execution',
]


def check_shape(plan):
    errors = list(jsonschema.Draft202012Validator(tool.read_json(tool.HERE / 'bootstrap.schema.json'))
                  .iter_errors(plan))
    tool.require(not errors, 'bootstrap schema: ' + '; '.join(e.message for e in errors[:4]))


def assess(plan, profile):
    tool.check_shape(profile)
    if plan is None:
        return {'local_status': 'UNPROVIDED', 'missing': ['$.bootstrap'], 'errors': [],
                'deployment_enabled': False, 'execution_ready': False,
                'external_checks_not_executed': EXTERNAL_CHECKS}
    check_shape(plan)
    unknown = tool.unresolved(plan)
    missing = [p for p in unknown if p not in LATER_FIELDS]
    errors = []
    c, g = profile['cluster'], profile['gitops']
    for field, value in [('cluster.namespace', c['namespace']), ('gitops.namespace', g['namespace'])]:
        if value is None:
            missing.append('$.profile.' + field)
    for i, tenant in enumerate(profile['tenants']):
        if tenant['app_namespaces'] is None:
            missing.append(f'$.profile.tenants[{i}].app_namespaces')
    def valid(condition, message):
        if not condition:
            errors.append(message)
    try:
        tool.check_placement(profile)
    except tool.Invalid as error:
        errors.append(str(error))
    valid(plan['synthetic_fixture'] == profile['synthetic_fixture'], 'bootstrap/profile fixture provenance differs')
    control = plan['argocd_instance_namespace']
    if control is not None:
        valid(control not in tool.LIVE_NAMESPACES - tool.CONTROL_PLANE_NAMESPACES,
              'bootstrap controller namespace is protected for workloads/operators')
        if g['namespace'] is not None:
            valid(control == g['namespace'], 'bootstrap/profile ArgoCD namespace mismatch')
    operator = plan['kafka_operator_namespace']
    if operator is not None and c['namespace'] is not None:
        valid(operator != c['namespace'] and operator != control,
              'operator, Kafka and ArgoCD namespaces must remain separate')
    if plan['selected_operator_csv'] is not None:
        valid(plan['selected_operator_csv'] == c['operator_csv'], 'operator CSV/profile mismatch')
    scope = plan['proposed_controller_permissions']['namespace_scope']
    if scope is not None and c['namespace'] is not None:
        valid(scope == [c['namespace']], 'controller Role scope must be only the candidate Kafka namespace')
    before = plan['existing_operator_target_namespaces']
    after = plan['selected_operator_target_namespaces']
    if before is not None and after is not None:
        valid(set(before) <= set(after), 'proposed watch scope drops an existing namespace')
        if c['namespace'] is not None:
            valid(c['namespace'] in after, 'candidate Kafka namespace is not in proposed watch scope')
            valid(set(after) - set(before) <= {c['namespace']},
                  'additional watch targets need a coordinated multi-profile scope review')
        valid(not (set(after) & (tool.LIVE_NAMESPACES - {'kaas-kafka'})),
              'operator watch proposal includes protected non-Kafka namespaces')
    app_namespaces = [n for t in profile['tenants'] for n in (t['app_namespaces'] or [])]
    valid(len(app_namespaces) == len(set(app_namespaces)), 'tenant application namespaces overlap')
    valid(not (set(app_namespaces) & (tool.LIVE_NAMESPACES | {control, operator, c['namespace']})),
          'tenant application namespaces overlap platform/protected namespaces')
    status = 'BLOCKED' if missing or errors else ('SYNTHETIC_ONLY' if plan['synthetic_fixture'] else 'OFFLINE_INPUTS_COMPLETE')
    return {'local_status': status, 'missing': sorted(set(missing)), 'errors': errors,
            'later_unresolved': [p for p in unknown if p in LATER_FIELDS],
            'deployment_enabled': False, 'execution_ready': False,
            'external_checks_not_executed': EXTERNAL_CHECKS}


def expected_resources(plan, profile):
    """Pure proposal for exact validation only. Never writes or applies resources."""
    result = assess(plan, profile)
    tool.require(not result['missing'] and not result['errors'], 'bootstrap plan has unresolved/invalid R1 inputs')
    namespace = profile['cluster']['namespace']
    allowed = sorted({namespace} | {n for t in profile['tenants'] for n in t['app_namespaces']})
    docs = [{'apiVersion': 'v1', 'kind': 'Namespace', 'metadata': {'name': ns}}
            for ns in allowed]
    tool.require(profile['profile_id'] is not None, 'unresolved bootstrap profile ID')
    role_name = profile['profile_id'] + '-gitops'
    tool.require(len(role_name) <= 63, 'invalid bootstrap Role name')
    docs += [
        {'apiVersion': 'rbac.authorization.k8s.io/v1', 'kind': 'Role',
         'metadata': {'name': role_name, 'namespace': namespace},
         'rules': [{'apiGroups': ['kafka.strimzi.io'], 'resources': RESOURCES, 'verbs': VERBS}]},
        {'apiVersion': 'rbac.authorization.k8s.io/v1', 'kind': 'RoleBinding',
         'metadata': {'name': role_name, 'namespace': namespace},
         'roleRef': {'apiGroup': 'rbac.authorization.k8s.io', 'kind': 'Role', 'name': role_name},
         'subjects': [{'kind': 'ServiceAccount', 'name': plan['argocd_controller_service_account'],
                       'namespace': plan['argocd_instance_namespace']}]},
    ]
    return docs


def validate_resources(plan, profile, docs):
    expected = expected_resources(plan, profile)
    def key(d):
        m = d['metadata']
        return (d['apiVersion'], d['kind'], m.get('namespace', ''), m['name'])
    keys = [key(d) for d in docs]
    tool.require(len(set(keys)) == len(keys), 'duplicate bootstrap resource')
    tool.require({key(d): d for d in expected} == {key(d): d for d in docs},
                 'bootstrap proposal differs from exact namespace/non-delete Role/RoleBinding policy')
    return {'local_resource_policy': 'PASS', 'resource_count': len(docs),
            'execution_ready': False, 'deployment_enabled': False,
            'limitation': 'Exact local content checks only; no Kubernetes schema/server or effective authorization test'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--profile', type=Path, required=True)
    parser.add_argument('--resources', type=Path, help='Optional local multi-document proposal; never applied')
    args = parser.parse_args()
    try:
        plan, profile = tool.read_json(args.input), tool.read_json(args.profile)
        result = assess(plan, profile)
        if args.resources:
            docs = list(yaml.safe_load_all(args.resources.read_text()))
            result['resources'] = validate_resources(plan, profile, docs)
        print(json.dumps(result, indent=2))
        return 2 if result['missing'] or result['errors'] else 0
    except (tool.Invalid, OSError, ValueError, KeyError, TypeError, yaml.YAMLError) as error:
        print('REJECTED: ' + str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
