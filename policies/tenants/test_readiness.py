"""Readiness/namespace/bootstrap regression checks; no live state or network."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import yaml
import bootstrap_tool as bootstrap
import profile_tool as tool
import readiness


class StagedChecks(unittest.TestCase):
    def profile(self, mode='shared'):
        return tool.read_json(tool.HERE / 'fixtures' / (mode + '.json'))

    def plan(self, mode='shared'):
        return tool.read_json(tool.HERE / 'fixtures' / ('bootstrap-' + mode + '.json'))

    def defer_later(self, p):
        for k in ['secret_delivery', 'governance', 'observability', 'recovery_and_persistence']:
            p['policy_references'][k] = None
        for t in p['tenants']:
            for identity in t['identities'].values():
                identity['delivery_reference'] = None

    def test_existing_control_namespace_allowed_only_for_gitops_metadata(self):
        p = self.profile()
        p['gitops']['namespace'] = 'openshift-gitops'
        docs = tool.build(p)
        tool.validate_bundle(p, docs)
        for group in docs.values():
            for doc in group:
                self.assertEqual(doc['metadata']['namespace'],
                    'openshift-gitops' if doc['kind'] in ('AppProject', 'Application') else p['cluster']['namespace'])
        plan = self.plan()
        plan['argocd_instance_namespace'] = 'openshift-gitops'
        proposal = bootstrap.expected_resources(plan, p)
        self.assertNotIn('openshift-gitops', [x['metadata']['name'] for x in proposal if x['kind']=='Namespace'])
        binding = next(x for x in proposal if x['kind']=='RoleBinding')
        self.assertEqual(binding['subjects'][0]['namespace'], 'openshift-gitops')

    def test_existing_gitops_projects_and_applications_cannot_be_reused(self):
        for profile_id, tenant_id in [('kaas','demo'),('kaas-demo','kafka'),('kaas-demo','operator')]:
            p = self.profile()
            p.update(profile_id=profile_id, synthetic_fixture=False)
            p['gitops']['namespace'] = 'openshift-gitops'
            p['tenants'][0]['id'] = tenant_id
            with self.assertRaisesRegex(tool.Invalid, 'protected existing project/application'):
                tool.build(p)
            p['cluster']['image'] = None
            r = readiness.assess(p)
            self.assertEqual(r['stages']['R0']['local_status'], 'BLOCKED')
            self.assertIn('protected existing project/application', ' '.join(r['stages']['R0']['local_errors']))

    def test_protected_namespace_guards_survive(self):
        for key in ['namespace', 'name']:
            for value in (['openshift-gitops','kaas-kafka','kaas-demo','kafka-operator'] if key=='namespace' else ['kaas-dev']):
                p = self.profile();p['cluster'][key] = value
                with self.subTest(key=key, value=value), self.assertRaises(tool.Invalid):
                    tool.build(p)
        p = self.profile();p['tenants'][0]['app_namespaces'] = ['openshift-gitops']
        with self.assertRaisesRegex(tool.Invalid, 'platform/live'):
            tool.build(p)

    def test_distinct_control_workload_namespaces(self):
        p = self.profile();p['gitops']['namespace'] = p['cluster']['namespace']
        with self.assertRaisesRegex(tool.Invalid, 'must differ'):
            tool.build(p)

    def test_later_nulls_do_not_block_resource_render_or_erase_unknowns(self):
        p = self.profile();self.defer_later(p)
        docs = tool.build(p)
        report = tool.summary(p, docs)
        self.assertEqual(report['unresolved_inputs_by_stage']['R1'], [])
        self.assertTrue(report['unresolved_inputs_by_stage']['R2'])
        self.assertTrue(report['unresolved_inputs_by_stage']['R3'])
        self.assertIsNone(p['policy_references']['governance'])
        self.assertFalse(report['deployment_enabled'])
        self.assertFalse(report['execution_ready'])
        r = readiness.assess(p, self.plan())
        self.assertEqual(r['stages']['R1']['local_status'], 'SYNTHETIC_ONLY')
        self.assertEqual(r['stages']['R2']['local_status'], 'BLOCKED')
        self.assertEqual(r['stages']['R3']['local_status'], 'BLOCKED')

    def test_core_nulls_still_block_before_output(self):
        p = self.profile();p['cluster']['pools'][0]['resources'] = None
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)/'out'
            with self.assertRaisesRegex(tool.Invalid, 'unresolved inputs'):
                tool.write_bundle(p, out)
            self.assertFalse(out.exists())
        r = readiness.assess(p, self.plan())
        self.assertEqual(r['stages']['R0']['local_status'], 'SYNTHETIC_ONLY')
        self.assertEqual(r['stages']['R1']['local_status'], 'BLOCKED')

    def test_r0_policy_errors_reported_even_when_r1_inputs_missing(self):
        p = self.profile();p['cluster']['image'] = None
        p['tenants'][0]['sync_groups'] = p['gitops']['platform_sync_groups']
        r = readiness.assess(p)
        self.assertEqual(r['stages']['R0']['local_status'], 'BLOCKED')
        self.assertIn('sync groups overlap', ' '.join(r['stages']['R0']['local_errors']))

    def test_r1_mapping_errors_are_not_hidden_by_later_stages(self):
        p = self.profile();self.defer_later(p);p['cluster']['follower_fetch_bytes'] = 1
        r = readiness.assess(p, self.plan())
        self.assertEqual(r['stages']['R0']['local_status'], 'SYNTHETIC_ONLY')
        self.assertIn('follower fetch', ' '.join(r['stages']['R1']['local_errors']))

    def test_all_filled_inputs_never_become_execution_approval(self):
        p, plan = self.profile(), self.plan()
        plan['credential_ca_delivery_and_rotation_evidence'] = 'fixture-only:delivery-check'
        r = readiness.assess(p, plan)
        self.assertFalse(r['deployment_enabled']);self.assertFalse(r['execution_ready'])
        for stage in r['stages'].values():
            self.assertEqual(stage['local_status'], 'SYNTHETIC_ONLY')
            self.assertFalse(stage['execution_ready'])
            self.assertTrue(stage['external_gates_not_verified'])

    def test_real_candidates_remain_unresolved_and_disabled(self):
        plan = tool.read_json(tool.ROOT/'gitops/profiles/bootstrap-inputs.json')
        for mode, n in [('dedicated',43),('shared',56)]:
            p = tool.read_json(tool.ROOT/'environments/candidates'/mode/'profile.json')
            r = readiness.assess(p, plan)
            self.assertEqual(len(r['unresolved']),n)
            self.assertTrue(all(x['local_status']=='BLOCKED' for x in r['stages'].values()))
            self.assertFalse(p['deployment_enabled'])

    def test_unprovided_bootstrap_blocks_r1_not_r0(self):
        r = readiness.assess(self.profile())
        self.assertEqual(r['stages']['R0']['local_status'], 'SYNTHETIC_ONLY')
        self.assertIn('bootstrap:$.bootstrap', r['stages']['R1']['cumulative_missing_inputs'])

    def test_bootstrap_positive_local_plan_and_resources_both_modes(self):
        for mode in ['dedicated','shared']:
            p,plan = self.profile(mode),self.plan(mode)
            report = bootstrap.assess(plan,p)
            self.assertEqual(report['local_status'],'SYNTHETIC_ONLY')
            self.assertTrue(report['later_unresolved'])
            docs = bootstrap.expected_resources(plan,p)
            self.assertEqual(bootstrap.validate_resources(plan,p,docs)['local_resource_policy'],'PASS')
            self.assertTrue(report['external_checks_not_executed'])

    def test_bootstrap_does_not_drop_existing_watch_namespace(self):
        p,plan = self.profile(),self.plan()
        plan['selected_operator_target_namespaces'] = [p['cluster']['namespace']]
        self.assertIn('drops an existing namespace',' '.join(bootstrap.assess(plan,p)['errors']))

    def test_bootstrap_rejects_uncoordinated_additional_watch_scope(self):
        p,plan = self.profile(),self.plan()
        plan['selected_operator_target_namespaces'].append('other-unreviewed-kafka')
        self.assertIn('coordinated multi-profile',' '.join(bootstrap.assess(plan,p)['errors']))

    def test_bootstrap_rejects_foreign_controller_scope_and_identity(self):
        p,plan = self.profile(),self.plan()
        plan['proposed_controller_permissions']['namespace_scope'] = ['kaas-kafka']
        self.assertIn('Role scope',' '.join(bootstrap.assess(plan,p)['errors']))
        plan = self.plan();plan['argocd_instance_namespace'] = 'other-control'
        self.assertIn('namespace mismatch',' '.join(bootstrap.assess(plan,p)['errors']))
        plan = self.plan();plan['synthetic_fixture'] = False
        self.assertIn('provenance differs',' '.join(bootstrap.assess(plan,p)['errors']))

    def test_bootstrap_schema_forbids_delete_secret_wildcard_upgrade_and_arming(self):
        changes = [lambda x:x.update(deployment_enabled=True),
            lambda x:x.update(selected_operator_csv='amqstreams.v3.2.2-9'),
            lambda x:x['proposed_controller_permissions'].update(delete_permissions_proposed=True),
            lambda x:x['proposed_controller_permissions'].update(secret_permissions_proposed=True),
            lambda x:x['proposed_controller_permissions'].update(wildcard_permissions_proposed=True),
            lambda x:x['proposed_controller_permissions']['non_delete_verbs'].append('delete'),
            lambda x:x['proposed_controller_permissions'].update(api_group='*')]
        for change in changes:
            p = self.plan();change(p)
            with self.assertRaisesRegex(tool.Invalid,'bootstrap schema'):
                bootstrap.assess(p,self.profile())

    def test_bootstrap_watch_review_missing_or_placeholder_stays_blocked(self):
        for value in [None,'TBD']:
            plan = self.plan();plan['watch_scope_versioned_evidence'] = value
            r = bootstrap.assess(plan,self.profile())
            self.assertEqual(r['local_status'],'BLOCKED')
            self.assertIn('$.watch_scope_versioned_evidence',r['missing'])

    def test_bootstrap_resource_privilege_and_namespace_injection(self):
        p,plan = self.profile(),self.plan()
        clean = bootstrap.expected_resources(plan,p)
        changes = [lambda docs:next(d for d in docs if d['kind']=='Role')['rules'][0]['verbs'].append('delete'),
            lambda docs:next(d for d in docs if d['kind']=='RoleBinding')['roleRef'].update(kind='ClusterRole',name='cluster-admin'),
            lambda docs:next(d for d in docs if d['kind']=='RoleBinding')['subjects'][0].update(name='unapproved-controller'),
            lambda docs:next(d for d in docs if d['kind']=='Namespace')['metadata'].update(name='openshift-gitops'),
            lambda docs:docs.append({'apiVersion':'operators.coreos.com/v1','kind':'OperatorGroup','metadata':{'name':'unreviewed'}}),
            lambda docs:docs.append({'apiVersion':'v1','kind':'Secret','metadata':{'name':'forbidden'}})]
        for change in changes:
            docs = copy.deepcopy(clean);change(docs)
            with self.assertRaisesRegex(tool.Invalid,'differs'):
                bootstrap.validate_resources(plan,p,docs)
        docs = copy.deepcopy(clean);docs.append(copy.deepcopy(clean[0]))
        with self.assertRaisesRegex(tool.Invalid,'duplicate bootstrap'):
            bootstrap.validate_resources(plan,p,docs)

    def test_readiness_cli_is_read_only_and_reports_blocked_candidates(self):
        p = tool.ROOT/'environments/candidates/shared/profile.json'
        before = p.read_bytes()
        result = subprocess.run([sys.executable,str(tool.HERE/'profile_tool.py'),'readiness',
            '--profile',str(p),'--bootstrap',str(tool.ROOT/'gitops/profiles/bootstrap-inputs.json')],
            capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout)['stages']['R1']['local_status'],'BLOCKED')
        self.assertEqual(p.read_bytes(),before)

    def test_bootstrap_cli_checks_local_proposal_and_rejects_incomplete_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp)/'proposal.yaml'
            docs.write_text(yaml.safe_dump_all(bootstrap.expected_resources(self.plan(),self.profile())))
            command = [sys.executable,str(tool.HERE/'bootstrap_tool.py'),'--input',str(tool.HERE/'fixtures/bootstrap-shared.json'),
                '--profile',str(tool.HERE/'fixtures/shared.json'),'--resources',str(docs)]
            result = subprocess.run(command,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertFalse(json.loads(result.stdout)['execution_ready'])
        result = subprocess.run([sys.executable,str(tool.HERE/'bootstrap_tool.py'),'--input',
            str(tool.ROOT/'gitops/profiles/bootstrap-inputs.json'),'--profile',
            str(tool.ROOT/'environments/candidates/shared/profile.json')],capture_output=True,text=True)
        self.assertEqual(result.returncode,2)
        self.assertEqual(json.loads(result.stdout)['local_status'],'BLOCKED')


if __name__ == '__main__':
    unittest.main(verbosity=2)
