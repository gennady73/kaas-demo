"""Offline scope, privilege, collision and file-tampering regressions."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import tenant_only as tool


class TenantOnlyChecks(unittest.TestCase):
    def setUp(self):
        self.config = tool.read_json(tool.DEFAULT_INPUT)

    def documents(self):
        return tool.resource_documents(self.config), tool.registration_documents(self.config)

    def reject_input(self, mutate):
        mutate(self.config)
        with self.assertRaises(tool.Invalid):
            tool.resource_documents(self.config)

    def reject_resource(self, kind, mutate):
        resources, registration = self.documents()
        doc = next(d for docs in resources.values() for d in docs if d['kind'] == kind)
        mutate(doc)
        with self.assertRaises(tool.Invalid):
            tool.validate_documents(self.config, resources, registration)

    def reject_registration(self, kind, mutate):
        resources, registration = self.documents()
        doc = next(d for docs in registration.values() for d in docs if d['kind'] == kind)
        mutate(doc)
        with self.assertRaises(tool.Invalid):
            tool.validate_documents(self.config, resources, registration)

    def test_positive_exact_eight_tenant_resources_and_four_previews(self):
        resources, registration = self.documents()
        self.assertEqual(tool.validate_documents(self.config, resources, registration), {
            'KafkaTopic': 4, 'KafkaUser': 4, 'AppProject_preview': 2, 'Application_preview': 2})
        summary = tool.report(self.config, resources, registration)
        for flag in ['deployment_enabled', 'registration_enabled', 'tests_enabled', 'execution_ready']:
            self.assertIs(summary[flag], False)
        self.assertIsNone(summary['resource_revision'])

    def test_no_platform_client_or_credential_resources(self):
        resources, _ = self.documents()
        self.assertEqual({d['kind'] for docs in resources.values() for d in docs}, {'KafkaTopic', 'KafkaUser'})

    def test_kustomize_document_order_allowed_but_duplicate_or_component_move_rejected(self):
        resources, registration = self.documents()
        for docs in resources.values():
            docs.reverse()
        tool.validate_documents(self.config, resources, registration)
        paths = list(resources)
        resources[paths[0]].append(copy.deepcopy(resources[paths[0]][0]))
        with self.assertRaises(tool.Invalid):
            tool.validate_documents(self.config, resources, registration)
        resources, registration = self.documents()
        resources[paths[1]].append(resources[paths[0]].pop())
        with self.assertRaises(tool.Invalid):
            tool.validate_documents(self.config, resources, registration)

    def test_arming_or_adding_an_unknown_input_is_rejected(self):
        for flag in ['deployment_enabled', 'registration_enabled', 'tests_enabled', 'execution_ready']:
            config = copy.deepcopy(self.config)
            config[flag] = True
            with self.subTest(flag=flag), self.assertRaises(tool.Invalid):
                tool.check_input(config)
        self.reject_input(lambda d: d.update(extra='ignored?'))

    def test_numeric_boolean_confusion_is_rejected(self):
        self.reject_input(lambda d: d['topic_policy'].update(partitions=True))

    def test_fixed_scope_and_owner_cannot_be_redirected(self):
        for field, value in [('kafka_namespace', 'other'), ('kafka_name', 'other'),
                             ('gitops_namespace', 'default')]:
            config = copy.deepcopy(self.config)
            config['target'][field] = value
            with self.subTest(field=field), self.assertRaises(tool.Invalid):
                tool.check_input(config)
        self.reject_input(lambda d: d.update(owner='unapproved-delegate'))

    def test_duplicate_or_other_tenant_rejected(self):
        self.reject_input(lambda d: d.update(tenants=['kaas-sbx-a', 'kaas-sbx-a']))

    def test_no_other_repository_or_branch_pin(self):
        for value in ['main', '${REVISION}', 'https://example.invalid']:
            config = copy.deepcopy(self.config)
            config['resource_revision'] = value
            with self.subTest(value=value), self.assertRaises(tool.Invalid):
                tool.check_input(config)
        self.reject_input(lambda d: d.update(repo_url='https://example.invalid/other.git'))

    def test_explicit_revision_is_only_a_preview_not_execution(self):
        self.config['resource_revision'] = '1' * 40
        resources, registration = self.documents()
        summary = tool.report(self.config, resources, registration)
        self.assertFalse(summary['execution_ready'])
        self.assertTrue(all(p.endswith('.yaml.template') for p in registration))
        self.assertTrue(all(d['spec']['source']['targetRevision'] == '1' * 40
                            for docs in registration.values() for d in docs if d['kind'] == 'Application'))

    def test_protected_saved_resource_collision_rejected(self):
        resources, registration = self.documents()
        protected = {tool.identity(next(iter(resources.values()))[0])}
        with patch.object(tool, 'saved_identities', return_value=protected), self.assertRaises(tool.Invalid):
            tool.validate_documents(self.config, resources, registration)

    def test_smoke_name_alias_or_wrong_cluster_label_rejected(self):
        self.reject_resource('KafkaTopic', lambda d: d['spec'].update(topicName='kaas-dev-smoke-01'))
        self.reject_resource('KafkaUser', lambda d: d['metadata']['labels'].update({'strimzi.io/cluster': 'other'}))

    def test_extra_platform_resource_rejected(self):
        resources, registration = self.documents()
        next(iter(resources.values())).append({'apiVersion': 'kafka.strimzi.io/v1', 'kind': 'Kafka'})
        with self.assertRaises(tool.Invalid):
            tool.validate_documents(self.config, resources, registration)

    def test_retention_replication_or_partition_change_rejected(self):
        self.reject_resource('KafkaTopic', lambda d: d['spec']['config'].update({'retention.ms': 1000}))
        self.reject_resource('KafkaTopic', lambda d: d['spec'].update(replicas=1))
        self.reject_resource('KafkaTopic', lambda d: d['spec'].update(partitions=2))

    def test_cross_tenant_or_wildcard_acl_rejected(self):
        self.reject_resource('KafkaUser', lambda d: d['spec']['authorization']['acls'][0]['resource'].update(name='kaas-sbx-b-events'))
        self.reject_resource('KafkaUser', lambda d: d['spec']['authorization']['acls'][0]['resource'].update(patternType='prefix'))

    def test_admin_privilege_and_missing_quota_rejected(self):
        self.reject_resource('KafkaUser', lambda d: d['spec']['authorization']['acls'][0]['operations'].append('All'))
        self.reject_resource('KafkaUser', lambda d: d['spec'].pop('quotas'))

    def test_hooks_tracking_override_or_finalizer_rejected(self):
        for annotation in ['argocd.argoproj.io/hook', 'argocd.argoproj.io/tracking-id']:
            with self.subTest(annotation=annotation):
                self.reject_resource('KafkaTopic', lambda d: d['metadata'].update(annotations={annotation: 'unexpected'}))
        self.reject_resource('KafkaTopic', lambda d: d['metadata'].update(finalizers=['unexpected']))

    def test_registration_permissions_and_source_cannot_be_broadened(self):
        self.reject_registration('AppProject', lambda d: d['spec'].update(namespaceResourceWhitelist=[{'group': '*', 'kind': '*'}]))
        self.reject_registration('AppProject', lambda d: d['spec'].update(roles=[{'name': 'admin'}]))
        self.reject_registration('Application', lambda d: d['spec']['source'].update(path='environments/dev/kafka'))
        self.reject_registration('Application', lambda d: d['spec']['destination'].update(namespace='other'))

    def test_automated_sync_namespace_creation_prune_or_delete_rejected(self):
        self.reject_registration('Application', lambda d: d['spec']['syncPolicy'].update(automated={'prune': True}))
        self.reject_registration('Application', lambda d: d['spec']['syncPolicy']['syncOptions'].append('CreateNamespace=true'))
        self.reject_registration('Application', lambda d: d['metadata'].update(finalizers=['resources-finalizer.argocd.argoproj.io']))

    def test_fresh_bundle_round_trip_and_deterministic_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp)/'a', Path(tmp)/'b'
            summary = tool.write_bundle(self.config, a)
            self.assertEqual(summary, tool.validate_bundle(self.config, a))
            tool.write_bundle(self.config, b)
            self.assertEqual({p.relative_to(a): p.read_bytes() for p in a.rglob('*') if p.is_file()},
                             {p.relative_to(b): p.read_bytes() for p in b.rglob('*') if p.is_file()})

    def test_extra_hook_or_tampered_bundle_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)/'bundle'
            tool.write_bundle(self.config, out)
            (out/'hook.yaml').write_text('kind: Job\n')
            with self.assertRaises(tool.Invalid):
                tool.validate_bundle(self.config, out)
            (out/'hook.yaml').unlink()
            (out/'environments/sandbox-tenants/a/kustomization.yaml').write_text('resources: [https://example.invalid]\n')
            with self.assertRaises(tool.Invalid):
                tool.validate_bundle(self.config, out)

    def test_no_overwrite_source_write_or_symlink_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(tool.Invalid):
                tool.write_bundle(self.config, Path(tmp))
            link = Path(tmp)/'link'
            link.symlink_to(Path(tmp), target_is_directory=True)
            with self.assertRaises(tool.Invalid):
                tool.write_bundle(self.config, link/'child')
        with self.assertRaises(tool.Invalid):
            tool.write_bundle(self.config, tool.ROOT/'forbidden-generated-bundle')

    def test_symlink_in_bundle_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)/'bundle'
            tool.write_bundle(self.config, out)
            path = out/'environments/sandbox-tenants/a/resources.yaml'
            other = Path(tmp)/'copied.yaml'
            other.write_bytes(path.read_bytes())
            path.unlink()
            path.symlink_to(other)
            with self.assertRaises(tool.Invalid):
                tool.validate_bundle(self.config, out)

    def test_cli_inspects_and_rejects_invalid_contract_without_building(self):
        result = subprocess.run([sys.executable, str(tool.HERE/'tenant_only.py'), 'inspect'],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(json.loads(result.stdout)['deployment_enabled'])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'bad.json'
            self.config['deployment_enabled'] = True
            path.write_text(json.dumps(self.config))
            result = subprocess.run([sys.executable, str(tool.HERE/'tenant_only.py'),
                                     'build', '--input', str(path), '--output', str(Path(tmp)/'out')],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertFalse((Path(tmp)/'out').exists())


if __name__ == '__main__':
    unittest.main()
