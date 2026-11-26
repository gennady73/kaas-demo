#!/usr/bin/env python3
"""One bounded, projected read-only R3 refresh. No Secret API, exec or resource write."""
import base64,datetime,hashlib,json,ssl,subprocess,time,urllib.error,urllib.parse,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent/'evidence'
BASE='https://api.ocp.rddgh.sandbox3088.opentlc.com:6443'
JOBS=['kaas-r2-native-client','kaas-r2-native-client-02e2e2f-r2','kaas-r2-native-client-351528d-r2','kaas-r2-native-client-05a3f2d-r2']
class Stop(Exception):pass
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs):return None

def main():
 if OUT.exists():raise SystemExit('Fresh evidence directory required; no automatic repeat')
 OUT.mkdir();begin=time.monotonic();queries=[];total=0;results={};token='';started=datetime.datetime.now(datetime.timezone.utc).isoformat()
 ca=ROOT/'config/environments/certificates/ocp-rddgh-api-ca.crt'
 ctx=ssl.create_default_context(cafile=str(ca));ctx.check_hostname=True;ctx.verify_mode=ssl.CERT_REQUIRED
 opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),urllib.request.HTTPSHandler(context=ctx),NoRedirect())
 def save(name,obj):
  raw=json.dumps(obj,indent=2)+'\n'
  if token and token in raw:raise Stop('credential_redaction_guard')
  if any(x in raw for x in ['-----BEGIN PRIVATE KEY-----','sha256~']):raise Stop('sensitive_content_guard')
  (OUT/(name+'.json')).write_text(raw)
 def request(label,path,projection,body=None,host=BASE,optional=False):
  nonlocal total
  if len(queries)>=40 or time.monotonic()-begin>=600:raise Stop('total_budget_exhausted')
  assert '/secrets' not in path and '/exec' not in path and '/log' not in path
  assert host==BASE or host=='https://thanos-querier-openshift-monitoring.apps.ocp.rddgh.sandbox3088.opentlc.com'
  assert body is None or path=='/apis/authorization.k8s.io/v1/selfsubjectaccessreviews'
  entry={'name':label,'path':path,'host':host,'method':'POST_NONPERSISTENT_SSAR' if body else 'GET','at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};queries.append(entry)
  req=urllib.request.Request(host+path,data=json.dumps(body).encode() if body else None,headers={'Authorization':'Bearer '+token,'Accept':'application/json','Content-Type':'application/json'})
  try:
   with opener.open(req,timeout=min(15,max(.1,600-(time.monotonic()-begin)))) as response:
    raw=response.read(1048577);entry['http_status']=response.status;entry['response_bytes']=len(raw);total+=len(raw)
   if len(raw)>1048576 or total>8388608:raise Stop('response_byte_cap')
   obj=json.loads(raw)
   if len(obj.get('items',[]))>100 or obj.get('metadata',{}).get('continue'):raise Stop('list_cap_or_pagination')
   projected=projection(obj);save(label,projected);results[label]=projected
   entry['result']='PROJECTED_SAVED';return obj
  except urllib.error.HTTPError as e:
   entry['http_status']=e.code;entry['result']='OPEN_HTTP_'+str(e.code)
   save(label,{'status':'OPEN','http_status':e.code})
   if optional and e.code==404:return None
   raise Stop(label+'_http_'+str(e.code)) from None
  except (urllib.error.URLError,TimeoutError,ssl.SSLError) as e:
   entry['result']='OPEN_'+type(e).__name__;save(label,{'status':'OPEN','error_type':type(e).__name__})
   raise Stop(label+'_connection_or_TLS_unavailable') from None
  except (ValueError,KeyError,TypeError):
   entry['result']='OPEN_RESPONSE_SHAPE';raise Stop(label+'_response_shape') from None
 def meta(o):return {k:o.get('metadata',{}).get(k) for k in ['name','namespace','uid','generation','resourceVersion']}
 def conditions(o):return [{k:c.get(k) for k in ['type','status','reason','lastTransitionTime']} for c in o.get('status',{}).get('conditions',[])]
 def job(o):return {'metadata':meta(o),'suspend':o['spec'].get('suspend',False),'active':o.get('status',{}).get('active',0),'succeeded':o.get('status',{}).get('succeeded',0),'failed':o.get('status',{}).get('failed',0),'conditions':conditions(o)}
 def items(project):return lambda o:{'items':[project(x) for x in o.get('items',[])]}
 def pvc(o):return {'metadata':meta(o),'phase':o.get('status',{}).get('phase'),'storageClass':o.get('spec',{}).get('storageClassName'),'requested':o.get('spec',{}).get('resources',{}).get('requests',{}),'capacity':o.get('status',{}).get('capacity',{})}
 stop=None
 try:
  config=json.loads(subprocess.check_output(['oc','config','view','--raw','--minify','-o','json'],text=True,stderr=subprocess.DEVNULL,timeout=5));cluster=config['clusters'][0]['cluster'];user=config['users'][0]['user']
  if cluster.get('server','').rstrip('/')!=BASE:raise Stop('local_target_mismatch')
  if user.get('exec') or user.get('auth-provider'):raise Stop('external_auth_provider_not_invoked')
  token=user.get('token','').strip()
  if not token:raise Stop('no_existing_local_memory_credential')
  save('local-session-policy',{'target_matches':True,'credential_present':True,'credential_saved':False,'local_insecure_flag_ignored':bool(cluster.get('insecure-skip-tls-verify')),'TLS':'CERT_REQUIRED_HOSTNAME_CHECKED','trusted_CA_sha256':hashlib.sha256(ca.read_bytes()).hexdigest()})
  identity=request('identity','/apis/user.openshift.io/v1/users/~',lambda o:{'name':o.get('metadata',{}).get('name')})
  if identity.get('metadata',{}).get('name')!='admin':raise Stop('identity_not_existing_sandbox_admin')
  # Observe all four Jobs before any other remote inspection; never repair them.
  for name in JOBS:
   request('job-'+name,'/apis/batch/v1/namespaces/kaas-demo/jobs/'+name,job)
   j=results['job-'+name]
   if j['suspend'] is not True or j['active']!=0:raise Stop('unexpected_unsuspended_or_active_client_Job')
  for t in 'ab':
   name='kaas-sbx-tenants-'+t
   obj=request('application-'+t,'/apis/argoproj.io/v1alpha1/namespaces/openshift-gitops/applications/'+name,lambda o:{'metadata':meta(o),'spec':{k:o.get('spec',{}).get(k) for k in ['project','source','destination','syncPolicy']},'sync':o.get('status',{}).get('sync'),'health':o.get('status',{}).get('health'),'operationPhase':o.get('status',{}).get('operationState',{}).get('phase'),'pending_operation':bool(o.get('operation'))})
   expected=list(__import__('yaml').safe_load_all((ROOT/f'kaas-demo/gitops/registration-candidates/sandbox-tenants/{t}.yaml.template').read_text()))
   if obj['spec']!=expected[1]['spec'] or obj.get('operation'):raise Stop('Application_source_or_policy_drift')
   obj=request('appproject-'+t,'/apis/argoproj.io/v1alpha1/namespaces/openshift-gitops/appprojects/'+name,lambda o:{'metadata':meta(o),'spec':o.get('spec')})
   if obj['spec']!=expected[0]['spec']:raise Stop('AppProject_scope_drift')
  request('kafka','/apis/kafka.strimzi.io/v1/namespaces/kaas-kafka/kafkas/kaas-dev',lambda o:{'metadata':meta(o),'version':o.get('spec',{}).get('kafka',{}).get('version'),'config':o.get('spec',{}).get('kafka',{}).get('config'),'listener_modes':[{k:l.get(k) for k in ['name','port','type','tls','authentication','networkPolicyPeers']} for l in o.get('spec',{}).get('kafka',{}).get('listeners',[])],'conditions':conditions(o),'observedGeneration':o.get('status',{}).get('observedGeneration')})
  request('kafka-pods','/api/v1/namespaces/kaas-kafka/pods?limit=100&labelSelector=strimzi.io%2Fcluster%3Dkaas-dev',items(lambda o:{'metadata':meta(o),'phase':o.get('status',{}).get('phase'),'conditions':conditions(o),'containers':[{k:c.get(k) for k in ['name','ready','restartCount']} for c in o.get('status',{}).get('containerStatuses',[])]}))
  request('kafka-pvcs','/api/v1/namespaces/kaas-kafka/persistentvolumeclaims?limit=100&labelSelector=strimzi.io%2Fcluster%3Dkaas-dev',items(pvc))
  request('sink-deployment','/apis/apps/v1/namespaces/kaas-demo/deployments/kaas-r2-evidence',lambda o:{'metadata':meta(o),'replicas':o.get('spec',{}).get('replicas'),'readyReplicas':o.get('status',{}).get('readyReplicas',0),'conditions':conditions(o)},optional=True)
  request('sink-pvc','/api/v1/namespaces/kaas-demo/persistentvolumeclaims/kaas-r2-native-evidence',pvc)
  for name,keys in [('argocd-cm',['admin.enabled','exec.enabled','application.resourceTrackingMethod','application.instanceLabelKey']),('argocd-rbac-cm',['policy.csv','policy.default','scopes'])]:
   request(name,'/api/v1/namespaces/openshift-gitops/configmaps/'+name,lambda o,keys=keys:{'metadata':meta(o),'selected_data':{k:o.get('data',{}).get(k) for k in keys}})
  role='openshift-gitops-openshift-gitops-argocd-application-controller'
  request('controller-role','/apis/rbac.authorization.k8s.io/v1/clusterroles/'+role,lambda o:{'metadata':meta(o),'rules':o.get('rules',[])})
  request('controller-binding','/apis/rbac.authorization.k8s.io/v1/clusterrolebindings/'+role,lambda o:{'metadata':meta(o),'roleRef':o.get('roleRef'),'subjects':o.get('subjects')})
  for ns in ['kaas-kafka','kaas-demo']:
   request('networkpolicies-'+ns,'/apis/networking.k8s.io/v1/namespaces/'+ns+'/networkpolicies?limit=100',items(lambda o:{'metadata':meta(o),'spec':o.get('spec')}))
  for name in ['kaas-r2-cluster-ca','kaas-r2-sink-trust']:
   request(name,'/api/v1/namespaces/kaas-demo/configmaps/'+name,lambda o:{'metadata':meta(o),'public_data_keys':sorted(o.get('data',{})),'data_sha256':{k:hashlib.sha256(v.encode()).hexdigest() for k,v in o.get('data',{}).items()}})
  for ns in ['kaas-kafka','kaas-demo']:
   request('prometheusrules-'+ns,'/apis/monitoring.coreos.com/v1/namespaces/'+ns+'/prometheusrules?limit=100',items(lambda o:{'metadata':meta(o),'groups':[{'name':g.get('name'),'rules':[{k:r.get(k) for k in ['alert','record','expr','for','labels']} for r in g.get('rules',[])]} for g in o.get('spec',{}).get('groups',[])]}),optional=True)
   request('servicemonitors-'+ns,'/apis/monitoring.coreos.com/v1/namespaces/'+ns+'/servicemonitors?limit=100',items(lambda o:{'metadata':meta(o),'selector':o.get('spec',{}).get('selector'),'namespaceSelector':o.get('spec',{}).get('namespaceSelector'),'endpoints':[{k:e.get(k) for k in ['port','path','interval','scheme']} for e in o.get('spec',{}).get('endpoints',[])]}),optional=True)
  request('prometheus-k8s','/apis/monitoring.coreos.com/v1/namespaces/openshift-monitoring/prometheuses/k8s',lambda o:{'metadata':meta(o),'selected_spec':{k:o.get('spec',{}).get(k) for k in ['retention','retentionSize','ruleSelector','ruleNamespaceSelector','serviceMonitorSelector','serviceMonitorNamespaceSelector','storage']},'conditions':conditions(o)},optional=True)
  request('alertmanager-main','/apis/monitoring.coreos.com/v1/namespaces/openshift-monitoring/alertmanagers/main',lambda o:{'metadata':meta(o),'selected_spec':{k:o.get('spec',{}).get(k) for k in ['configSecret','alertmanagerConfigSelector','alertmanagerConfigNamespaceSelector','replicas']},'conditions':conditions(o)},optional=True)
  request('cluster-monitoring-config','/api/v1/namespaces/openshift-monitoring/configmaps/cluster-monitoring-config',lambda o:{'metadata':meta(o),'selected_config':{k:__import__('yaml').safe_load(o.get('data',{}).get('config.yaml','') or '{}').get(k) for k in ['enableUserWorkload']}},optional=True)
  attributes=[('applications','argoproj.io','openshift-gitops','patch','kaas-sbx-tenants-a'),('kafkatopics','kafka.strimzi.io','kaas-kafka','list',None),('kafkausers','kafka.strimzi.io','kaas-kafka','list',None),('jobs','batch','kaas-demo','get',JOBS[0]),('prometheusrules','monitoring.coreos.com','kaas-kafka','list',None),('configmaps','','openshift-gitops','get','argocd-rbac-cm')]
  for i,(resource,group,ns,verb,name) in enumerate(attributes):
   a={'resource':resource,'group':group,'namespace':ns,'verb':verb}
   if name:a['name']=name
   request('self-access-'+str(i),'/apis/authorization.k8s.io/v1/selfsubjectaccessreviews',lambda o,a=a:{'attributes':a,'allowed':o.get('status',{}).get('allowed'),'denied':o.get('status',{}).get('denied'),'evaluationError':bool(o.get('status',{}).get('evaluationError'))},body={'apiVersion':'authorization.k8s.io/v1','kind':'SelfSubjectAccessReview','spec':{'resourceAttributes':a}})
  # Query existing monitoring only after public ingress trust and exact route binding.
  caobj=request('ingress-public-ca','/api/v1/namespaces/openshift-config-managed/configmaps/default-ingress-cert',lambda o:{'metadata':meta(o),'public_data_keys':sorted(o.get('data',{}))},optional=True)
  if caobj:
   for value in caobj.get('data',{}).values():
    if '-----BEGIN CERTIFICATE-----' in value:ctx.load_verify_locations(cadata=value)
   route=request('thanos-route','/apis/route.openshift.io/v1/namespaces/openshift-monitoring/routes/thanos-querier',lambda o:{'metadata':meta(o),'host':o.get('spec',{}).get('host')})
   host=route.get('spec',{}).get('host')
   if host!='thanos-querier-openshift-monitoring.apps.ocp.rddgh.sandbox3088.opentlc.com':raise Stop('monitoring_route_mismatch')
   q='{__name__=~"kubelet_volume_stats_(available|capacity)_bytes",namespace="kaas-demo",persistentvolumeclaim="kaas-r2-native-evidence"}'
   request('sink-pvc-headroom','/api/v1/query?'+urllib.parse.urlencode({'query':q}),lambda o:{'status':o.get('status'),'resultType':o.get('data',{}).get('resultType'),'results':[{'metric':{k:x.get('metric',{}).get(k) for k in ['__name__','namespace','persistentvolumeclaim']},'value':x.get('value')} for x in o.get('data',{}).get('result',[])]},host='https://'+host)
 except Stop as e:stop=str(e)
 except Exception as e:stop='LOCAL_OR_RESPONSE_FAILURE_'+type(e).__name__
 finally:
  summary={'status':'PARTIAL_STOPPED' if stop else 'BOUNDED_READ_ONLY_REFRESH_COMPLETE','started_at_utc':started,'finished_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'elapsed_seconds':round(time.monotonic()-begin,3),'stop_reason':stop,'request_count':len(queries),'response_bytes':total,'requests':queries,'authenticated_identity':results.get('identity'),'four_jobs_observed_suspended':len([x for k,x in results.items() if k.startswith('job-') and x['suspend'] is True and x['active']==0])==4,'jobs_changed':False,'resources_changed':False,'workloads_run':False,'Secret_API_reads':0,'notifications_sent':0,'credentials_saved':False,'GitHub_effective_controls':'NOT_REFRESHED_OPTIONAL_BRANCH_NOT_SELECTED','receiver_delivery':'NOT_ASSESSED_NO_SECRET_OR_NOTIFICATION_ACCESS','custody':'Local saved references reviewed separately; live DB contents not read'}
  save('result',summary);print(json.dumps({k:v for k,v in summary.items() if k!='requests'},indent=2));token=''
if __name__=='__main__':main()
