#!/usr/bin/env python3
"""Offline sandbox tenant-only GitOps builder. No API, Git, apply or sync capability."""
import argparse
import hashlib
import json
from pathlib import Path

import jsonschema
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DEFAULT_INPUT = ROOT / 'environments/candidates/sandbox-tenants/inputs.json'
SCHEMAS = ROOT / 'policies/tenants/schemas'
SAVED_RESOURCES = (ROOT / 'platform/kafka/smoke-topics.yaml',
                   ROOT / 'platform/kafka/smoke-user.yaml')
REVISION_TOKEN = '${RESOURCE_REVISION}'
EXTERNAL_GATES = [
    'Fresh target health, metadata/storage headroom, effective versions and unchanged watch scope',
    'Fresh names, topicName/backend user collisions, namespace and reconciliation ownership',
    'Existing ArgoCD tracking/prune boundary and no competing resource owner',
    'Installed Kafka/ArgoCD schema/admission and effective Git/global/controller authorization',
    'Actual reviewed published resource SHA/source paths and repository trust/access',
    'Concrete owner-approved change window, reviewed diff and non-destructive rollback',
]


class Invalid(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise Invalid(message)


def read_json(path):
    return json.loads(Path(path).read_text())


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def check_input(config):
    errors = list(jsonschema.Draft202012Validator(read_json(HERE / 'inputs.schema.json'))
                  .iter_errors(config))
    require(not errors, 'input contract: ' + '; '.join(e.message for e in errors[:3]))
    require(all(config[k] is False for k in (
        'deployment_enabled', 'registration_enabled', 'tests_enabled', 'execution_ready')),
        'all execution flags must be false')


def saved_identities():
    """Static smoke identity protection; never substitutes for a live collision check."""
    docs = [doc for p in SAVED_RESOURCES for doc in yaml.safe_load_all(p.read_text()) if doc]
    return {identity(doc) for doc in docs}


def identity(doc):
    return (doc['apiVersion'], doc['kind'], doc['metadata']['namespace'], doc['metadata']['name'])


def resource_documents(config):
    check_input(config)
    target, policy, quotas = config['target'], config['topic_policy'], config['user_policy']
    result = {}
    for tenant in config['tenants']:
        topic_names = [tenant + '-' + suffix for suffix in policy['suffixes']]
        def metadata(name):
            return {'name': name, 'namespace': target['kafka_namespace'], 'labels': {
                'strimzi.io/cluster': target['kafka_name'], 'kaas.example.com/tenant': tenant}}
        docs = []
        for name in topic_names:
            docs.append({'apiVersion': 'kafka.strimzi.io/v1', 'kind': 'KafkaTopic',
                         'metadata': metadata(name), 'spec': {
                             'topicName': name, 'partitions': policy['partitions'],
                             'replicas': policy['replicas'], 'config': {
                                 'retention.ms': policy['retention_ms'],
                                 'min.insync.replicas': policy['min_insync_replicas'],
                                 'max.message.bytes': policy['max_message_bytes'],
                                 'cleanup.policy': policy['cleanup_policy']}}})
        for role in ('producer', 'consumer'):
            acls = [{'resource': {'type': 'topic', 'name': name, 'patternType': 'literal'},
                     'operations': ['Write', 'Describe'] if role == 'producer'
                     else ['Read', 'Describe']} for name in topic_names]
            if role == 'producer':
                acls.append({'resource': {'type': 'cluster'}, 'operations': ['IdempotentWrite']})
            else:
                acls.extend({'resource': {'type': 'group', 'name': name + '-group',
                                         'patternType': 'literal'},
                             'operations': ['Read', 'Describe']} for name in topic_names)
            docs.append({'apiVersion': 'kafka.strimzi.io/v1', 'kind': 'KafkaUser',
                         'metadata': metadata(tenant + '-' + role), 'spec': {
                             'authentication': {'type': quotas['authentication']},
                             'authorization': {'type': quotas['authorization'], 'acls': acls},
                             'quotas': {k: quotas[k] for k in (
                                 'producerByteRate', 'consumerByteRate', 'requestPercentage')}}})
        result['environments/sandbox-tenants/' + tenant[-1]] = docs
    return result


def registration_documents(config):
    check_input(config)
    target = config['target']
    result = {}
    for tenant in config['tenants']:
        name = 'kaas-sbx-tenants-' + tenant[-1]
        metadata = {'name': name, 'namespace': target['gitops_namespace']}
        destination = {'namespace': target['kafka_namespace'], 'server': 'https://kubernetes.default.svc'}
        project = {'apiVersion': 'argoproj.io/v1alpha1', 'kind': 'AppProject',
                   'metadata': metadata.copy(), 'spec': {
                       'sourceRepos': [config['repo_url']], 'destinations': [destination.copy()],
                       'clusterResourceWhitelist': [], 'namespaceResourceWhitelist': [
                           {'group': 'kafka.strimzi.io', 'kind': kind}
                           for kind in ('KafkaTopic', 'KafkaUser')]}}
        app = {'apiVersion': 'argoproj.io/v1alpha1', 'kind': 'Application',
               'metadata': metadata.copy(), 'spec': {
                   'project': name, 'source': {'repoURL': config['repo_url'],
                       'targetRevision': config['resource_revision'] or REVISION_TOKEN,
                       'path': 'environments/sandbox-tenants/' + tenant[-1]},
                   'destination': destination.copy(),
                   'syncPolicy': {'syncOptions': ['FailOnSharedResource=true']}}}
        # Always a preview/template, even with a syntactically valid revision.
        result['registration-preview/' + tenant[-1] + '.yaml.template'] = [project, app]
    return result


def validate_documents(config, resources, registrations):
    expected = resource_documents(config)
    # Kustomize sorts whole documents; compare identities/content within each
    # component, retaining duplicate detection and exact nested policy contents.
    def ordered(components):
        try:
            return {path: sorted(docs, key=identity) for path, docs in components.items()}
        except (KeyError, TypeError) as error:
            raise Invalid('malformed resource identity') from error
    require(canonical(ordered(resources)) == canonical(ordered(expected)),
            'resource content/identity differs from exact tenant-only allowlist')
    require(canonical(registrations) == canonical(registration_documents(config)),
            'registration source/destination/privilege/manual-sync policy differs')
    seen = set()
    protected = saved_identities()
    for docs in resources.values():
        for doc in docs:
            key = identity(doc)
            require(key not in seen and key not in protected, 'duplicate/protected saved identity')
            seen.add(key)
            schema = read_json(SCHEMAS / (doc['kind'] + '-v1.json'))
            errors = list(jsonschema.Draft4Validator(schema).iter_errors(doc))
            require(not errors, 'cached Kafka schema: ' + '; '.join(e.message for e in errors[:3]))
    return {'KafkaTopic': 4, 'KafkaUser': 4, 'AppProject_preview': 2, 'Application_preview': 2}


def report(config, resources, registrations):
    counts = validate_documents(config, resources, registrations)
    return {'status': 'OFFLINE_VALIDATED_NOT_DEPLOYMENT_READY',
            'deployment_enabled': False, 'registration_enabled': False,
            'tests_enabled': False, 'execution_ready': False,
            'input_sha256': hashlib.sha256(canonical(config).encode()).hexdigest(),
            'counts': counts, 'new_brokers': 0, 'new_pvcs': 0,
            'logical_partitions_added': 4, 'partition_replicas_added': 8,
            'resource_revision': config['resource_revision'],
            'registration_revision_supplied': config['resource_revision'] is not None,
            'user_scope_owner_decisions': 'ACCEPTED; not deployment authorization',
            'external_gates_not_verified': EXTERNAL_GATES,
            'limitations': [
                'Exact local validation, not live collision/ownership, policy enforcement or server admission',
                'Resource manifests can be applied manually; false flags and preview suffixes are not admission controls',
                'No Kafka/NodePool, operator/watch/RBAC/Secret/network/bootstrap/client resources generated',
                'New app namespaces, effective network and credential delivery belong to later R2 preparation',
                'Owner identity is user instruction, not a fabricated ArgoCD role/group grant',
                'AppProject kinds/manual sync do not enforce content ownership or prohibit manual prune',
            ]}


def bundle_files(config):
    resources, registrations = resource_documents(config), registration_documents(config)
    summary = report(config, resources, registrations)
    files = {}
    for component, docs in resources.items():
        files[component + '/resources.yaml'] = yaml.safe_dump_all(docs, sort_keys=False)
        files[component + '/kustomization.yaml'] = yaml.safe_dump({
            'apiVersion': 'kustomize.config.k8s.io/v1beta1', 'kind': 'Kustomization',
            'resources': ['resources.yaml']}, sort_keys=False)
    for path, docs in registrations.items():
        files[path] = '# OFFLINE PREVIEW ONLY; registration and deployment disabled\n' + yaml.safe_dump_all(docs, sort_keys=False)
    files['review-report.json'] = json.dumps(summary, indent=2) + '\n'
    return files, summary


def write_bundle(config, output):
    files, summary = bundle_files(config)
    output = Path(output).absolute()
    require(not any(p.is_symlink() for p in (output, *output.parents)), 'symlink output/ancestor rejected')
    require(not output.resolve().is_relative_to(ROOT.resolve()), 'output must be outside implementation repository')
    require(not output.exists(), 'output must be a fresh directory')
    output.mkdir(parents=True)
    for relative, text in files.items():
        path = output / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    return summary


def validate_bundle(config, output):
    files, summary = bundle_files(config)
    output = Path(output)
    require(output.is_dir() and not output.is_symlink(), 'bundle directory required; symlinks rejected')
    entries = list(output.rglob('*'))
    require(not any(p.is_symlink() for p in entries), 'bundle symlink rejected')
    actual = {str(p.relative_to(output)) for p in entries if p.is_file()}
    require(actual == set(files), 'bundle contains extra/missing files or hooks')
    for relative, text in files.items():
        require((output / relative).read_text() == text, 'changed bundle file: ' + relative)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['inspect', 'build', 'validate'])
    parser.add_argument('--input', type=Path, default=DEFAULT_INPUT)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        config = read_json(args.input)
        if args.command == 'inspect':
            result = report(config, resource_documents(config), registration_documents(config))
        else:
            require(args.output is not None, '--output is required')
            result = (write_bundle if args.command == 'build' else validate_bundle)(config, args.output)
        print(json.dumps(result, indent=2))
        return 0
    except (Invalid, OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(2, str(error) + '\n')


if __name__ == '__main__':
    raise SystemExit(main())
