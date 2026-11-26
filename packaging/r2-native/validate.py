#!/usr/bin/env python3
"""Offline typed contract checks. No API, native SDK, credentials or apply calls."""
import json,yaml
from pathlib import Path
HERE=Path(__file__).resolve().parent

def load():
 return (list(yaml.safe_load_all((HERE/'deploy/resources.yaml').read_text())),list(yaml.safe_load_all((HERE/'build/buildconfigs.yaml.disabled').read_text())),yaml.safe_load((HERE/'optional-storage/pvc.yaml.disabled').read_text()),json.loads((HERE/'inputs.json').read_text()),{r:(HERE/'build'/(r+'.Dockerfile')).read_text() for r in ['runner','sink']})
def validate(objects,builds,pvc,inputs,docker):
 assert len(objects)==11 and len(builds)==4
 assert all(inputs[k] is False for k in ['execution_enabled','deployment_enabled','workloads_enabled','build_enabled'])
 assert inputs['runner_image_digest'] is None and inputs['sink_image_digest'] is None
 index={(o['kind'],o['metadata']['name']):o for o in objects}
 assert len(index)==11 and all(o['metadata']['namespace']=='kaas-demo' for o in objects)
 assert {o['kind'] for o in objects}=={'ConfigMap','ServiceAccount','Service','Job','Deployment','NetworkPolicy'}
 get=lambda kind,name:index[(kind,name)]
 assert get('ConfigMap','kaas-r2-arming-disabled')['data']=={'enabled':'false'}
 runtime=json.loads(get('ConfigMap','kaas-r2-execution-disabled')['data']['runtime.json'])
 assert runtime['execution_authorized'] is False and runtime['tests_enabled'] is False and all(x=='OPEN' for x in runtime['gates'].values())
 assert runtime['image_digest'] is None and runtime['job_start_unix_ms'] is None and runtime['authority_reference'] is None
 assert runtime['binary_sha256']==inputs['binary_sha256'] and runtime['package_sha256']==inputs['runtime_manifest_sha256'] and runtime['plan_sha256']==inputs['plan_sha256']
 assert runtime['sink_origin']=='https://kaas-r2-evidence.kaas-demo.svc:8443'
 job=get('Job','kaas-r2-native-client')['spec'];assert job['suspend'] is True
 for key,value in {'backoffLimit':0,'activeDeadlineSeconds':300,'parallelism':1,'completions':1}.items():assert type(job[key]) is int and job[key]==value
 dep=get('Deployment','kaas-r2-evidence')['spec'];assert type(dep['replicas']) is int and dep['replicas']==0 and dep['paused'] is True and dep['strategy']=={'type':'Recreate'}
 cp=job['template']['spec'];sp=dep['template']['spec'];assert cp['restartPolicy']=='Never' and cp['terminationGracePeriodSeconds']==0
 for pod in [cp,sp]:
  assert pod['nodeSelector']=={'kubernetes.io/os':'linux','kubernetes.io/arch':'amd64'}
  assert pod['automountServiceAccountToken'] is False and pod['hostNetwork'] is False and not pod.get('initContainers') and len(pod['containers'])==1
  assert not any('hostPath' in x for x in pod['volumes'])
  for c in pod['containers']:
   assert c['image'].startswith('invalid.invalid/') and c['image'].endswith('@sha256:'+'0'*64)
   assert not c.get('envFrom') and c['command'][0].endswith('-guard.sh')
   assert c['securityContext']=={'runAsNonRoot':True,'allowPrivilegeEscalation':False,'capabilities':{'drop':['ALL']},'seccompProfile':{'type':'RuntimeDefault'},'readOnlyRootFilesystem':True}
   assert not any(x['name'] in ['K6_HTTP_DEBUG','K6_VERBOSE','PASSWORD','TOKEN'] for x in c.get('env',[]))
 csecrets={x['secret']['secretName']:x['secret'] for x in cp['volumes'] if 'secret' in x}
 expected={'kaas-sbx-'+t+'-'+r for t in ['a','b'] for r in ['producer','consumer']}
 assert set(csecrets)==expected|{'kaas-r2-evidence-writer'}
 for name in expected:assert csecrets[name]['items']==[{'key':'password','path':'password'}] and csecrets[name]['defaultMode']==288
 mount={x['name']:x for x in cp['containers'][0]['volumeMounts']}
 for v in cp['volumes']:
  if 'secret' in v and v['secret']['secretName'] in expected:assert mount[v['name']]['mountPath']=='/credentials/'+v['secret']['secretName'] and mount[v['name']]['readOnly'] is True
 assert 'kaas-r2-evidence-owner' not in csecrets
 assert next(x for x in sp['volumes'] if x['name']=='data')['persistentVolumeClaim']['claimName']=='kaas-r2-native-evidence'
 svc=get('Service','kaas-r2-evidence');assert svc['spec']['type']=='ClusterIP' and svc['spec']['ports']==[{'name':'https','port':8443,'targetPort':'https','protocol':'TCP'}]
 assert svc['spec']['selector']==dep['selector']['matchLabels']==dep['template']['metadata']['labels']
 assert svc['metadata']['annotations']['service.beta.openshift.io/serving-cert-secret-name']=='kaas-r2-sink-tls'
 trust=get('ConfigMap','kaas-r2-sink-trust');assert trust['metadata']['annotations']=={'service.beta.openshift.io/inject-cabundle':'true'} and trust['data']=={}
 np=get('NetworkPolicy','kaas-r2-native-client')['spec'];assert np['policyTypes']==['Ingress','Egress'] and np['ingress']==[] and len(np['egress'])==3
 assert np['egress'][1]['ports']==[{'protocol':'TCP','port':9093}] and np['egress'][2]['ports']==[{'protocol':'TCP','port':8443}]
 for rule in np['egress']:
  for peer in rule['to']:assert 'namespaceSelector' in peer and 'podSelector' in peer and peer['namespaceSelector'].get('matchLabels') and peer['podSelector'].get('matchLabels')
 snp=get('NetworkPolicy','kaas-r2-evidence')['spec'];assert snp['egress']==[] and snp['ingress'][0]['ports']==[{'protocol':'TCP','port':8443}]
 assert len([x for x in builds if x['kind']=='ImageStream'])==2
 for stream in [x for x in builds if x['kind']=='ImageStream']:assert stream['spec']=={} and stream['metadata']['namespace']=='kaas-demo'
 for build in [x for x in builds if x['kind']=='BuildConfig']:
  b=build['spec'];assert build['kind']=='BuildConfig' and b['triggers']==[] and b['source']=={'type':'Binary','binary':{}} and b['completionDeadlineSeconds']==600
  assert b['nodeSelector']=={'kubernetes.io/os':'linux','kubernetes.io/arch':'amd64'}
  assert b['output']['to']=={'kind':'ImageStreamTag','name':build['metadata']['name']+':candidate-20261126'}
  assert b['strategy']['type']=='Docker' and b['strategy']['dockerStrategy']['dockerfilePath']=='Dockerfile'
 for role,text in docker.items():
  assert text.splitlines()[0]=='FROM '+inputs['base_image'] and '@sha256:' in text.splitlines()[0]
  assert not any(x in text for x in ['@latest',':latest','curl ','wget ','dnf ','pip install','go get','k6 run'])
  assert 'USER 1001:0' in text
 assert inputs['binary_sha256'] in docker['runner'] and 'k6 inspect /r2/inspect.js' in docker['runner']
 assert pvc['kind']=='PersistentVolumeClaim' and pvc['metadata']['name']=='kaas-r2-native-evidence' and pvc['spec']['storageClassName']=='gp3-csi' and pvc['spec']['resources']['requests']['storage']=='1Gi'
 assert (HERE/'deploy/kustomization.yaml').read_text().count('resources.yaml')==1
 return {'status':'OFFLINE_CONTRACT_PASS','manifest_objects':11,'manual_binary_build_definitions':2,'PVC_included':False,'deployment_enabled':False,'workloads_enabled':False,'actual_image_build':'NOT_RUN','API_schema_validation':'SEPARATE_VALIDATOR','server_admission':'NOT_RUN'}
if __name__=='__main__':print(json.dumps(validate(*load())))
