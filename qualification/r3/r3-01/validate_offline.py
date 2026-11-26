#!/usr/bin/env python3
"""R3-01 source/contract and negative probes. Local files/Git only; no API or clients."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
spec = importlib.util.spec_from_file_location('tenant_only', ROOT/'policies/tenant-only/tenant_only.py')
tool = importlib.util.module_from_spec(spec); spec.loader.exec_module(tool)
RESOURCE = '3211df93ae40d7d6f47c6334966ae6d1f658fee7'
REGISTRATION = 'ac2f57b1faedae88028486073abf597256a172af'

def load():
    registrations = {}; resources = {}
    for tenant in 'ab':
        resources[f'environments/sandbox-tenants/{tenant}'] = list(yaml.safe_load_all((ROOT/f'environments/sandbox-tenants/{tenant}/resources.yaml').read_text()))
        registrations[f'registration-preview/{tenant}.yaml.template'] = list(yaml.safe_load_all((ROOT/f'gitops/registration-candidates/sandbox-tenants/{tenant}.yaml.template').read_text()))
    package = list(yaml.safe_load_all((ROOT/'packaging/r2-native/deploy/resources.yaml').read_text()))
    return {'config': json.loads((ROOT/'gitops/registration-candidates/sandbox-tenants/inputs.json').read_text()),
            'resources': resources, 'registrations': registrations,
            'job': next(d for d in package if d['kind']=='Job'),
            'contract': json.loads((HERE/'service-contract.json').read_text())}

def validate(s):
    c = s['contract']; cfg = s['config']
    for flag in ['execution_enabled','deployment_enabled','registration_enabled','workloads_enabled']:
        assert c[flag] is False, 'arming not allowed'
    assert c['owner']==c['approver']=='user' and c['delegated_tenant_sync'] is False
    assert c['resource_commit']==cfg['resource_revision']==RESOURCE
    assert c['registration_package_commit']==REGISTRATION
    assert c['manual_sync_only'] is True
    for flag in ['prune_allowed','force_replace_allowed','existing_fixture_mutation_allowed']: assert c[flag] is False
    assert type(c['new_live_attempts_authorized']) is int and c['new_live_attempts_authorized']==0
    assert c['lifecycle']['change_window'] is None and c['lifecycle']['authorized_diff'] is None
    assert c['authority_assurance']['local_validation_is_admission_control'] is False
    assert c['authority_assurance']['effective_rights_status']=='HISTORICAL_OBSERVATIONS_ONLY_NOT_REFRESHED'
    tool.validate_documents(cfg,s['resources'],s['registrations'])
    job=s['job']; pod=job['spec']['template']['spec']; client=pod['containers'][0]
    assert job['spec']['suspend'] is True and job['spec']['activeDeadlineSeconds']==300
    assert pod['serviceAccountName']=='kaas-r2-harness' and pod['automountServiceAccountToken'] is False
    assert client['image'].endswith('@'+c['historical_R2_runner_digest'])
    assert c['historical_R2_runner_digest']=='sha256:41f328c85ee3d3e9d8834ce12e516b5ef52506067117b1c4f1145511b493998a'
    assert c['historical_R2_runtime_source_commit']=='05a3f2dcb551c7aa7ed12b4108c7ef488113aed9'
    env={e['name']:e.get('value') for e in client['env']}
    assert len(env)==len(client['env']), 'duplicate environment name'
    overlay=c['mount_contract_overlay']
    assert overlay['resource_kind']=='Job' and overlay['suspend'] is True and overlay['trusted_harness_only'] is True
    assert overlay['kafka_ca_file']=='/credentials/cluster-ca/ca.crt'
    assert overlay['sink_http_ca_env']=='SSL_CERT_FILE' and env['SSL_CERT_FILE']==overlay['sink_http_ca_file']=='/evidence-trust/service-ca.crt'
    mounts={v['name']:v for v in client['volumeMounts']};volumes={v['name']:v for v in pod['volumes']}
    for name in ['cluster-ca','credential-0','credential-1','credential-2','credential-3','execution','writer','sink-trust']:
        assert mounts[name]['readOnly'] is True, 'sensitive/reference mount must be read-only'
    assert mounts['sink-trust']['mountPath']=='/evidence-trust'
    assert volumes['sink-trust']['configMap']['name']=='kaas-r2-sink-trust'
    assert volumes['sink-trust']['configMap']['items']==[{'key':'service-ca.crt','path':'service-ca.crt'}]
    assert mounts['cluster-ca']['mountPath']=='/credentials/cluster-ca'
    assert volumes['cluster-ca']['configMap']['name']=='kaas-r2-cluster-ca'
    assert mounts['execution']['mountPath']=='/r2/runtime.json' and mounts['execution']['subPath']=='runtime.json'
    assert volumes['execution']['configMap']['name']=='kaas-r2-execution-disabled'
    assert volumes['arming']['configMap']['name']=='kaas-r2-arming-disabled'
    assert mounts['writer']['mountPath']=='/evidence-auth'
    assert all('owner' not in v.get('secret',{}).get('secretName','') for v in pod['volumes'])
    return {'KafkaTopic':4,'KafkaUser':4,'AppProject':2,'Application':2,'job_suspended':True}

def mutate_case(s,kind,action):
    doc=next(d for docs in s['resources'].values() for d in docs if d['kind']==kind);action(doc)

def probes(state):
    cases=[]
    def add(label,fn):cases.append((label,fn))
    for flag in ['execution_enabled','deployment_enabled','registration_enabled','workloads_enabled']:
        add('contract arms '+flag,lambda s,f=flag:s['contract'].__setitem__(f,True))
    add('delegated sync',lambda s:s['contract'].__setitem__('delegated_tenant_sync',True))
    add('other owner',lambda s:s['contract'].__setitem__('owner','tenant'))
    add('resource branch',lambda s:s['config'].__setitem__('resource_revision','main'))
    add('other full resource SHA',lambda s:s['config'].__setitem__('resource_revision','a'*40))
    add('boolean live-attempt count',lambda s:s['contract'].__setitem__('new_live_attempts_authorized',False))
    add('pretend fresh rights',lambda s:s['contract']['authority_assurance'].__setitem__('effective_rights_status','VERIFIED_NOW'))
    add('local checker is admission',lambda s:s['contract']['authority_assurance'].__setitem__('local_validation_is_admission_control',True))
    for flag in ['prune_allowed','force_replace_allowed','existing_fixture_mutation_allowed']:
        add(flag,lambda s,f=flag:s['contract'].__setitem__(f,True))
    add('foreign topic alias',lambda s:mutate_case(s,'KafkaTopic',lambda d:d['spec'].__setitem__('topicName','kaas-sbx-b-events')))
    add('foreign CR namespace',lambda s:mutate_case(s,'KafkaTopic',lambda d:d['metadata'].__setitem__('namespace','default')))
    add('unapproved retention',lambda s:mutate_case(s,'KafkaTopic',lambda d:d['spec']['config'].__setitem__('retention.ms',86400000)))
    add('missing quotas',lambda s:mutate_case(s,'KafkaUser',lambda d:d['spec'].pop('quotas')))
    add('quota broadened',lambda s:mutate_case(s,'KafkaUser',lambda d:d['spec']['quotas'].__setitem__('producerByteRate',65537)))
    add('wildcard ACL',lambda s:mutate_case(s,'KafkaUser',lambda d:d['spec']['authorization']['acls'][0]['resource'].__setitem__('name','*')))
    add('cross-tenant ACL',lambda s:mutate_case(s,'KafkaUser',lambda d:d['spec']['authorization']['acls'][0]['resource'].__setitem__('name','kaas-sbx-b-events')))
    add('unsuspended client',lambda s:s['job']['spec'].__setitem__('suspend',False))
    add('mutable image',lambda s:s['job']['spec']['template']['spec']['containers'][0].__setitem__('image','runner:latest'))
    add('old combined CA env',lambda s:next(e for e in s['job']['spec']['template']['spec']['containers'][0]['env'] if e['name']=='SSL_CERT_FILE').update(value='/evidence-trust/combined-ca.pem'))
    add('token automount',lambda s:s['job']['spec']['template']['spec'].__setitem__('automountServiceAccountToken',True))
    for label,mutate in cases:
        candidate=copy.deepcopy(state);mutate(candidate)
        try:validate(candidate)
        except (AssertionError,tool.Invalid):pass
        else:raise AssertionError('mutation accepted: '+label)
    return [label for label,_ in cases]

def main():
    state=load();counts=validate(state);rejected=probes(state)
    lock=json.loads((ROOT/'gitops/registration-candidates/sandbox-tenants/package-lock.json').read_text())
    paths=[]
    for p,expected in lock['source_files_at_resource_commit'].items():
        raw=(ROOT/p).read_bytes();assert hashlib.sha256(raw).hexdigest()==expected['sha256']
        assert raw==subprocess.check_output(['git','show',RESOURCE+':'+p],cwd=ROOT)
        assert subprocess.check_output(['git','rev-parse',RESOURCE+':'+p],cwd=ROOT,text=True).strip()==expected['git_blob'];paths.append(p)
    for name in ['a.yaml.template','b.yaml.template']:
        p='gitops/registration-candidates/sandbox-tenants/'+name
        assert (ROOT/p).read_bytes()==subprocess.check_output(['git','show',REGISTRATION+':'+p],cwd=ROOT);paths.append(p)
    for p in [RESOURCE,REGISTRATION]:subprocess.run(['git','merge-base','--is-ancestor',p,'HEAD'],cwd=ROOT,check=True)
    assert '"ssl.ca.location": "/credentials/cluster-ca/ca.crt"' in (ROOT/'tests/tenant-r2-native/native/module.go').read_text()
    docker=(ROOT/'packaging/r2-native/build/runner.Dockerfile').read_text();assert 'COPY r2 /r2' in docker
    print(json.dumps({'status':'OFFLINE_R3_01_CONTRACT_PASS','counts':counts,'negative_probes_rejected':len(rejected),'probe_labels':rejected,'pinned_git_paths_verified':paths,'cluster_accessed':False,'effective_rights_refreshed':False,'workloads_run':False},indent=2))

if __name__=='__main__':main()
