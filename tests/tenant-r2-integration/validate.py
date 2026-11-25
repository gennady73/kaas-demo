#!/usr/bin/env python3
"""Offline static checks only. No Kubernetes client, credential read or execution flag."""
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent

def validate(package,job,cm,bindings):
    for key in ('execution_enabled','deployment_enabled','workloads_enabled','execution_ready','automatic_sync_enabled'):
        assert package[key] is False,key
    assert package['live_entrypoint'] is None and package['native_image_qualified'] is False
    custody=package['evidence_custody_decision']
    assert custody['status']=='ACCEPTED_BY_USER' and type(custody['sandbox_retention_days']) is int and custody['sandbox_retention_days']==7
    assert custody['export_destination']=='/home/gunger/Projects/kaas-solution/docs/testing/runs/<run-id>/'
    assert custody['verified_second_copy'] is False
    assert package['resource_revision']=='3211df93ae40d7d6f47c6334966ae6d1f658fee7'
    f=package['fixture'];assert f['positive_records']==16 and f['value_bytes_each']==1000
    assert f['positive_original_value_bytes']==16000 and f['maximum_original_attempt_value_bytes']==20000
    assert f['negative_write_attempts_max']==4 and f['negative_read_operations']==4 and f['negative_operations']==8
    assert f['application_attempts_per_id']==1 and f['whole_client_job_seconds']==300
    assert f['phase_seconds']=={'startup_and_controls':45,'positive_delivery':90,'negative_cases':90,'final_reconciliation_drain':45,'shutdown':30}
    assert job['kind']=='Job' and job['metadata']['namespace']=='kaas-demo'
    s=job['spec'];assert s['suspend'] is True
    for key,value in {'backoffLimit':0,'activeDeadlineSeconds':300,'parallelism':1,'completions':1}.items():
        assert type(s[key]) is int and s[key]==value
    p=s['template']['spec'];assert p['automountServiceAccountToken'] is False and p['restartPolicy']=='Never' and p['terminationGracePeriodSeconds']==0
    assert p['serviceAccountName']=='kaas-r2-harness' and p['hostNetwork'] is False
    c=p['containers'][0];assert len(p['containers'])==1 and not p.get('initContainers')
    assert c['command']==['k6','run','/r2/disabled.js'] and '@sha256:' in c['image']
    assert c['securityContext']=={'runAsNonRoot':True,'allowPrivilegeEscalation':False,'capabilities':{'drop':['ALL']},'seccompProfile':{'type':'RuntimeDefault'},'readOnlyRootFilesystem':True}
    assert not c.get('env') and not c.get('envFrom')
    assert c['resources']=={'requests':{'cpu':'100m','memory':'128Mi'},'limits':{'cpu':'500m','memory':'512Mi'}}
    assert len(p['volumes'])==7 and all('hostPath' not in v for v in p['volumes'])
    assert cm['data']['disabled.js'].startswith("throw new Error('R2_OFFLINE_PACKAGE_ONLY_NATIVE_RUNTIME_NOT_IMPLEMENTED');")
    mounts={m['name']:m for m in c['volumeMounts']}
    secrets=[v for v in p['volumes'] if 'secret' in v];assert len(secrets)==4
    actual={}
    for v in secrets:
        sec=v['secret'];m=mounts[v['name']];assert m['readOnly'] is True
        assert sec['items']==[{'key':'password','path':'password'}]
        assert sec['defaultMode']==288
        actual[sec['secretName']]=m['mountPath']+'/password'
    expected={x['principal']:x['mount_path'] for x in bindings['credential_bindings']}
    assert actual==expected
    ca=[v for v in p['volumes'] if v.get('configMap',{}).get('name')=='kaas-r2-cluster-ca'];assert len(ca)==1
    assert mounts[ca[0]['name']]['mountPath']=='/credentials/cluster-ca'
    assert not list(HERE.glob('kustomization.y*ml'))
    return {'static_package':'PASS','execution_ready':False,'native_runtime':'NOT_IMPLEMENTED','cluster_validation':'NOT_RUN'}

def main():
    load=lambda name:json.loads((HERE/name).read_text())
    print(json.dumps(validate(load('package.json'),load('job.json.disabled'),load('disabled-entrypoint.json'),json.loads((HERE.parent/'tenant-r2-preparation/bindings.json').read_text()))))

if __name__=='__main__':main()
