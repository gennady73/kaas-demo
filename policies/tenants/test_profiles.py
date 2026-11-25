"""Offline-only positive, negative, and generated-resource policy checks."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import yaml
import profile_tool as tool


class ProfileChecks(unittest.TestCase):
    def fixture(self, mode='shared'):
        return tool.read_json(tool.HERE / 'fixtures' / (mode + '.json'))

    def reject_profile(self, change, message):
        p = self.fixture()
        change(p)
        with self.assertRaisesRegex(tool.Invalid, message):
            tool.build(p)

    def reject_resource(self, kind, change, message='differs'):
        p = self.fixture()
        docs = tool.build(p)
        doc = next(d for group in docs.values() for d in group if d['kind'] == kind)
        change(doc)
        with self.assertRaisesRegex(tool.Invalid, message):
            tool.validate_bundle(p, docs)

    def test_positive_dedicated_and_shared_schema_and_counts(self):
        for mode, tenants, total in [('dedicated', 1, 9), ('shared', 2, 14)]:
            with self.subTest(mode=mode):
                p = self.fixture(mode)
                docs = tool.build(p)
                counts = tool.validate_bundle(p, docs)
                self.assertEqual(counts, {'Kafka': 1, 'KafkaNodePool': 1,
                                         'KafkaTopic': tenants, 'KafkaUser': tenants * 2})
                self.assertEqual(sum(map(len, docs.values())), total)
                self.assertFalse(tool.summary(p, docs)['execution_ready'])

    def test_separate_controller_and_broker_pools(self):
        p = self.fixture('dedicated')
        controller = copy.deepcopy(p['cluster']['pools'][0])
        broker = copy.deepcopy(controller)
        controller.update(name='fixture-controllers', roles=['controller'])
        broker.update(name='fixture-brokers', roles=['broker'])
        p['cluster']['pools'] = [controller, broker]
        self.assertEqual(tool.validate_bundle(p, tool.build(p))['KafkaNodePool'], 2)

    def test_heap_ordering_and_memory_mapping(self):
        self.reject_profile(lambda p: p['cluster']['pools'][0].update(heap={'-Xms':'512m','-Xmx':'256m'}), 'heap ordering')
        self.reject_profile(lambda p: p['cluster']['pools'][0].update(heap={'-Xms':'128m','-Xmx':'2g'}), 'heap ordering')

    def test_deterministic(self):
        self.assertEqual(tool.build(self.fixture()), tool.build(self.fixture()))

    def test_unresolved_candidate_profiles_block_before_writes(self):
        for mode in ['dedicated', 'shared']:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                p = tool.read_json(tool.ROOT / 'environments/candidates' / mode / 'profile.json')
                tool.check_shape(p)
                self.assertGreater(len(tool.unresolved(p)), 20)
                out = Path(tmp) / 'out'
                with self.assertRaisesRegex(tool.Invalid, 'unresolved inputs'):
                    tool.write_bundle(p, out)
                self.assertFalse(out.exists())

    def test_unknown_input_rejected(self):
        self.reject_profile(lambda p: p.update(extra='ignored?'), 'profile schema')

    def test_deployment_flag_cannot_be_enabled(self):
        self.reject_profile(lambda p: p.update(deployment_enabled=True), 'profile schema')

    def test_placeholder_not_filled_input(self):
        self.reject_profile(lambda p: p['policy_references'].update(identity_network='TBD'), 'unresolved inputs')

    def test_dedicated_rejects_second_tenant(self):
        self.reject_profile(lambda p: p.update(mode='dedicated'), 'exactly one tenant')

    def test_shared_requires_two_tenants_for_scaffold(self):
        self.reject_profile(lambda p: p.update(tenants=p['tenants'][:1]), 'tenant count')

    def test_duplicate_tenant(self):
        self.reject_profile(lambda p: p['tenants'][1].update(id='fixture-a'), 'duplicate tenant')

    def test_namespace_collision(self):
        self.reject_profile(lambda p: p['tenants'][1].update(app_namespaces=p['tenants'][0]['app_namespaces']), 'namespaces overlap')

    def test_live_cluster_and_namespace_rejected(self):
        for key, value in [('name', 'kaas-dev'), ('namespace', 'kaas-kafka')]:
            self.reject_profile(lambda p: p['cluster'].update({key: value}), 'live dev identities')
        self.reject_profile(lambda p: p['gitops'].update(namespace='kaas-demo'), 'protected namespace')
        self.reject_profile(lambda p: p['tenants'][0].update(app_namespaces=['kaas-demo']), 'platform/live')

    def test_sync_actor_overlap(self):
        self.reject_profile(lambda p: p['tenants'][0].update(sync_groups=p['gitops']['platform_sync_groups']), 'sync groups overlap')

    def test_mutable_git_revision(self):
        self.reject_profile(lambda p: p['gitops'].update(revision='main'), 'profile schema')

    def test_mutable_image(self):
        self.reject_profile(lambda p: p['cluster'].update(image='registry.invalid/kafka:latest'), 'profile schema')

    def test_fixture_cannot_masquerade_as_real_candidate(self):
        self.reject_profile(lambda p: p.update(synthetic_fixture=False), 'fixture profiles')

    def test_quota_field_type_and_unknown_acl_inputs(self):
        self.reject_profile(lambda p: p['tenants'][0]['identities']['producer']['quotas'].update(producerByteRate='100'), 'profile schema')
        self.reject_profile(lambda p: p['tenants'][0]['identities']['producer'].update(acls=[{'resource':'*'}]), 'profile schema')

    def test_admission_and_duplicate_topics(self):
        self.reject_profile(lambda p: p['tenants'][0].update(max_partitions=1), 'partition admission')
        self.reject_profile(lambda p: p['tenants'][0]['topics'].append(copy.deepcopy(p['tenants'][0]['topics'][0])), 'duplicate topic suffix')
        self.reject_profile(lambda p: p['tenants'][0].update(max_topics=0), 'profile schema')

    def test_name_collision_within_tenant(self):
        # A topic named fixture-a-producer collides with the generated principal;
        # conservative admission rejects even across differing Kafka resource kinds.
        self.reject_profile(lambda p: p['tenants'][0]['topics'][0].update(suffix='producer'), 'names collide')

    def test_resource_limits_and_quantities(self):
        self.reject_profile(lambda p: p['cluster']['pools'][0]['resources']['requests'].update(cpu='1'), 'request exceeds')
        self.reject_profile(lambda p: p['cluster']['pools'][0]['resources']['requests'].update(cpu='1Gi'), 'invalid CPU')
        self.reject_profile(lambda p: p['cluster']['pools'][0].update(storage_size='20'), 'invalid memory/storage')

    def test_broker_controller_topology(self):
        self.reject_profile(lambda p: p['cluster']['pools'][0].update(replicas=1), 'at least two broker')
        self.reject_profile(lambda p: p['cluster']['pools'][0].update(roles=['broker']), '3 or 5 controllers')

    def test_protocol_size_mapping(self):
        self.reject_profile(lambda p: p['cluster'].update(follower_fetch_bytes=1), 'follower fetch')
        self.reject_profile(lambda p: p['tenants'][0]['topics'][0].update(max_record_bytes=10000000), 'broker ceiling')

    def test_literal_acl_no_cross_tenant_prefix_collision(self):
        p = self.fixture()
        for path, docs in tool.build(p).items():
            if '/tenants/' not in path:
                continue
            tid = path.rsplit('/', 1)[1]
            other = 'fixture-ab' if tid == 'fixture-a' else 'fixture-a'
            for doc in docs:
                if doc['kind'] != 'KafkaUser':
                    continue
                for acl in doc['spec']['authorization']['acls']:
                    r = acl['resource']
                    if r['type'] == 'cluster':
                        self.assertEqual(acl['operations'], ['IdempotentWrite'])
                    else:
                        self.assertEqual(r['patternType'], 'literal')
                        self.assertTrue(r['name'].startswith(tid + '-'))
                        self.assertNotIn(r['name'], [other + '-events', other + '-events-group'])

    def test_wildcard_acl_injection(self):
        self.reject_resource('KafkaUser', lambda d: d['spec']['authorization']['acls'][0]['resource'].update(name='*'))

    def test_cross_tenant_group_acl_injection(self):
        self.reject_resource('KafkaUser', lambda d: d['spec']['authorization']['acls'].append({'resource': {'type': 'group', 'name': 'fixture-ab-events-group', 'patternType':'literal'}, 'operations':['Read']}))

    def test_rf_retention_cleanup_and_owner_tampering(self):
        for config in [{'retention.ms': 1000}, {'cleanup.policy': 'compact'}]:
            self.reject_resource('KafkaTopic', lambda d: d['spec']['config'].update(config))
        self.reject_resource('KafkaTopic', lambda d: d['spec'].update(replicas=1))
        self.reject_resource('KafkaTopic', lambda d: d['metadata']['labels'].update({'strimzi.io/cluster': 'kaas-dev'}))

    def test_automatic_topic_creation_rejected(self):
        self.reject_resource('Kafka', lambda d: d['spec']['kafka']['config'].update({'auto.create.topics.enable':True}))

    def test_argocd_privilege_and_auto_sync_rejected(self):
        self.reject_resource('AppProject', lambda d: d['spec']['namespaceResourceWhitelist'].append({'group':'*','kind':'*'}))
        self.reject_resource('Application', lambda d: d['spec']['syncPolicy'].update(automated={'prune':True}))
        self.reject_resource('Application', lambda d: d['metadata'].update(finalizers=['resources-finalizer.argocd.argoproj.io']))

    def test_extra_and_duplicate_resource_rejected(self):
        p = self.fixture()
        docs = tool.build(p)
        path = next(iter(docs))
        docs[path].append(copy.deepcopy(docs[path][0]))
        with self.assertRaisesRegex(tool.Invalid, 'duplicate resource'):
            tool.validate_bundle(p, docs)
        docs = tool.build(p)
        docs[path].append({'apiVersion':'v1','kind':'Secret','metadata':{'name':'injected','namespace':p['cluster']['namespace']}})
        with self.assertRaisesRegex(tool.Invalid, 'differs'):
            tool.validate_bundle(p, docs)

    def test_components_cannot_share_resource(self):
        p = self.fixture()
        docs = tool.build(p)
        paths = list(docs)
        docs[paths[1]].append(copy.deepcopy(docs[paths[0]][0]))
        with self.assertRaisesRegex(tool.Invalid, 'multiple components'):
            tool.validate_bundle(p, docs)

    def test_structural_schema_detects_invalid_native_type(self):
        p = self.fixture()
        docs = tool.build(p)
        next(d for group in docs.values() for d in group if d['kind']=='KafkaNodePool')['spec']['replicas']='three'
        with self.assertRaisesRegex(tool.Invalid, 'cached schema'):
            tool.validate_schemas(docs)

    def test_file_roundtrip_and_fresh_output_guard(self):
        p = self.fixture()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'bundle'
            tool.write_bundle(p, out)
            self.assertEqual(tool.read_bundle(p, out)['KafkaUser'], 4)
            with self.assertRaisesRegex(tool.Invalid, 'already exists'):
                tool.write_bundle(p, out)
            (out/'extra.yaml').write_text('kind: Job\n')
            with self.assertRaisesRegex(tool.Invalid, 'extra/missing'):
                tool.read_bundle(p, out)

    def test_output_inside_implementation_repo_rejected(self):
        with self.assertRaisesRegex(tool.Invalid, 'outside the implementation'):
            tool.write_bundle(self.fixture(), tool.ROOT / 'environments/dev/forbidden-c4-output')

    def test_cli_rejects_unresolved_without_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)/'out'
            run = subprocess.run([sys.executable, str(tool.HERE/'profile_tool.py'), 'render',
                '--profile', str(tool.ROOT/'environments/candidates/shared/profile.json'), '--output', str(out)],
                capture_output=True, text=True)
            self.assertEqual(run.returncode, 2)
            self.assertIn('unresolved inputs', run.stderr)
            self.assertFalse(out.exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
