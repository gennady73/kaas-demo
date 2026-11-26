"""Bounded activation prerequisite inspection; only GET, access reviews, dryRun=All.
Alertmanager configuration is decoded in memory; only a credential-free projection is saved.
"""
import base64,datetime,getpass,gzip,json,re,ssl,time,urllib.error,urllib.parse,urllib.request
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[6]
HERE=Path(__file__).resolve().parent
BASE='https://api.ocp.rddgh.sandbox3088.opentlc.com:6443'
JOBS=['kaas-r2-native-client','kaas-r2-native-client-02e2e2f-r2','kaas-r2-native-client-351528d-r2','kaas-r2-native-client-05a3f2d-r2']
IMAGE='sha256:4aae77bd4739acfa0dfa1689a24cd86b44a36787772c3495df82a6c44b30ad4f'
class Stop(Exception):pass
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*a,**k):return None
def main():
 out=HERE/'evidence'
 if out.exists():raise SystemExit('Fresh output required')
 out.mkdir();token=getpass.getpass('Sandbox token (memory only): ').strip();start=time.monotonic();queries=[];total=0;secrets=0
 ctx=ssl.create_default_context(cafile=str(ROOT/'config/environments/certificates/ocp-rddgh-api-ca.crt'))
 op=urllib.request.build_opener(urllib.request.ProxyHandler({}),urllib.request.HTTPSHandler(context=ctx),NoRedirect())
 def save(n,d):
  b=json.dumps(d,indent=2)+'\n'
  if token and token in b:raise Stop('redaction_guard')
  (out/(n+'.json')).write_text(b)
 def request(n,p,project,method='GET',payload=None,optional=False,host=BASE):
  nonlocal total
  if len(queries)>=45 or time.monotonic()-start>300:raise Stop('budget')
  if '/secrets/' in p and not re.fullmatch('/api/v1/namespaces/openshift-monitoring/secrets/alertmanager-main(-generated)?',p):raise Stop('Secret_allowlist')
  if method!='GET' and p not in ['/apis/authorization.k8s.io/v1/subjectaccessreviews','/apis/authorization.k8s.io/v1/selfsubjectaccessreviews'] and 'dryRun=All' not in p:raise Stop('write_guard')
  q={'name':n,'method':method,'path':p,'at_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat()};queries.append(q)
  try:
   h={'Authorization':'Bearer '+token,'Accept':'application/json'}
   if payload is not None:h['Content-Type']='application/json'
   req=urllib.request.Request(host+p,headers=h,method=method,data=json.dumps(payload).encode() if payload is not None else None)
   with op.open(req,timeout=15) as r:b=r.read(4194305);q['http']=r.status
   total+=len(b)
   if len(b)>4194304 or total>16777216:raise Stop('size_budget')
   d=json.loads(b)
   if d.get('metadata',{}).get('continue'):raise Stop('pagination')
   save(n,project(d));return d
  except urllib.error.HTTPError as e:
   q['http']=e.code;save(n,{'http_status':e.code,'status':'NOT_FOUND_OR_NOT_ALLOWED' if optional else 'STOPPED'})
   if optional and e.code in [403,404]:return None
   raise Stop(n+'_http_'+str(e.code)) from None
  except (urllib.error.URLError,TimeoutError):raise Stop(n+'_connection_or_TLS') from None
 def meta(d):return {k:d.get('metadata',{}).get(k) for k in ['name','namespace','uid','resourceVersion']}
 def safe_host(s):return s if isinstance(s,str) and re.fullmatch(r'[A-Za-z0-9_.:\[\]-]+',s) else ('PRESENT_REDACTED' if s else None)
 def project_config(d):
  data=d.get('data',{});key=next((k for k in ['alertmanager.yaml','alertmanager.yaml.gz'] if k in data),None)
  if key is None:return {'metadata':meta(d),'config_key_found':False}
  b=base64.b64decode(data[key]);b=gzip.decompress(b) if key.endswith('.gz') else b
  c=yaml.safe_load(b);g=c.get('global',{}) or {};receivers=[]
  for r in c.get('receivers',[]):
   emails=[]
   for e in r.get('email_configs',[]):
    emails.append({'to_is_approved_recipient':e.get('to')=='gunger@redhat.com','from':e.get('from',g.get('smtp_from')),'smarthost':safe_host(e.get('smarthost',g.get('smtp_smarthost'))),'require_tls':e.get('require_tls',g.get('smtp_require_tls',True)),'auth_configured':any(e.get(k) or g.get('smtp_'+k) for k in ['auth_username','auth_password','auth_password_file','auth_secret']),'TLS_config_keys':list((e.get('tls_config',g.get('smtp_tls_config',{})) or {}).keys())})
   receivers.append({'name':r['name'],'integration_types':[k for k in r if k!='name'],'email_settings':emails})
  def routes(r):return {'receiver':r.get('receiver'),'matchers':r.get('matchers',[]),'match':r.get('match',{}),'match_re':r.get('match_re',{}),'continue':r.get('continue',False),'routes':[routes(x) for x in r.get('routes',[])]}
  return {'metadata':meta(d),'config_key_found':True,'SMTP_global':{'smarthost':safe_host(g.get('smtp_smarthost')),'from':g.get('smtp_from'),'require_tls':g.get('smtp_require_tls',True),'auth_configured':any(g.get(k) for k in ['smtp_auth_username','smtp_auth_password','smtp_auth_password_file','smtp_auth_secret'])},'receivers':receivers,'route':routes(c.get('route',{})),'inhibit_rule_count':len(c.get('inhibit_rules',[])),'config_raw_saved':False,'credential_values_saved':False}
 try:
  d=request('identity','/apis/user.openshift.io/v1/users/~',lambda d:{'name':d['metadata']['name']})
  if d['metadata']['name']!='admin':raise Stop('identity')
  for n in JOBS:
   d=request('job-'+n,'/apis/batch/v1/namespaces/kaas-demo/jobs/'+n,lambda d:{'metadata':meta(d),'suspend':d['spec'].get('suspend'),'active':d.get('status',{}).get('active',0)})
   if d['spec'].get('suspend') is not True or d.get('status',{}).get('active',0):raise Stop('Job_state')
  am=request('alertmanager','/apis/monitoring.coreos.com/v1/namespaces/openshift-monitoring/alertmanagers/main',lambda d:{'metadata':meta(d),'spec':{k:d['spec'].get(k) for k in ['configSecret','replicas','alertmanagerConfigSelector','alertmanagerConfigNamespaceSelector']},'status':d.get('status')})
  config=am['spec'].get('configSecret') or 'alertmanager-main'
  if config!='alertmanager-main':raise Stop('unexpected_AM_configSecret')
  request('alertmanager-base-configuration','/api/v1/namespaces/openshift-monitoring/secrets/'+config,project_config);secrets+=1
  request('alertmanager-effective-configuration','/api/v1/namespaces/openshift-monitoring/secrets/alertmanager-main-generated',project_config,optional=True);secrets+=1
  request('CMO-image-metadata','/apis/image.openshift.io/v1/images/'+IMAGE,lambda d:{'metadata':meta(d),'image':d.get('dockerImageReference'),'source_labels':{k:v for k,v in d.get('dockerImageMetadata',{}).get('Config',{}).get('Labels',{}).items() if any(x in k.lower() for x in ['source','commit','version','revision'])}},optional=True)
  request('monitoring-operator','/apis/apps/v1/namespaces/openshift-monitoring/deployments/cluster-monitoring-operator',lambda d:{'metadata':meta(d),'template':d['spec']['template'],'status':d.get('status')})
  request('prometheus-operator','/apis/apps/v1/namespaces/openshift-monitoring/deployments/prometheus-operator',lambda d:{'metadata':meta(d),'template':d['spec']['template'],'status':d.get('status')})
  request('core-prometheus','/apis/monitoring.coreos.com/v1/namespaces/openshift-monitoring/prometheuses/k8s',lambda d:{'metadata':meta(d),'spec':{k:d['spec'].get(k) for k in ['version','image','resources','containers','thanos']},'status':d.get('status')})
  ca=request('ingress-CA','/api/v1/namespaces/openshift-config-managed/configmaps/default-ingress-cert',lambda d:{'metadata':meta(d),'public_data_keys':list(d.get('data',{}))})
  for v in ca.get('data',{}).values():
   if '-----BEGIN CERTIFICATE-----' in v:ctx.load_verify_locations(cadata=v)
  host='https://thanos-querier-openshift-monitoring.apps.ocp.rddgh.sandbox3088.opentlc.com'
  for name,query in [('CMO-build','{namespace="openshift-monitoring",pod=~"cluster-monitoring-operator-.*",__name__=~".*build_info"}'),('operator-build','{namespace="openshift-monitoring",pod=~"prometheus-operator-.*",__name__=~".*build_info"}')]:
   request(name,'/api/v1/query?'+urllib.parse.urlencode({'query':query}),lambda d:{'status':d.get('status'),'data':d.get('data')},host=host)
  request('controller-role','/apis/rbac.authorization.k8s.io/v1/clusterroles/openshift-gitops-openshift-gitops-argocd-application-controller',lambda d:{'metadata':meta(d),'rules':d['rules']})
  sa='system:serviceaccount:openshift-gitops:openshift-gitops-argocd-application-controller'
  for ns,group,resource in [('kaas-kafka','monitoring.coreos.com','podmonitors'),('kaas-kafka','','configmaps'),('openshift-monitoring','','configmaps'),('openshift-user-workload-monitoring','','configmaps')]:
   for verb in ['create','patch']:
    payload={'apiVersion':'authorization.k8s.io/v1','kind':'SubjectAccessReview','spec':{'user':sa,'groups':['system:authenticated','system:serviceaccounts','system:serviceaccounts:openshift-gitops'],'resourceAttributes':{'namespace':ns,'group':group,'resource':resource,'verb':verb}}}
    request('controller-'+ns+'-'+resource+'-'+verb,'/apis/authorization.k8s.io/v1/subjectaccessreviews',lambda d:{'spec':d['spec'],'status':d['status']},method='POST',payload=payload)
  execution=HERE.parent
  for target in ['platform','broker-scrape']:
   docs=list(yaml.safe_load_all((execution/'evidence'/('rendered-'+target+'.yaml')).read_text()))
   for d in docs:
    ns=d['metadata']['namespace'];n=d['metadata']['name'];kind=d['kind']
    path='/api/v1/namespaces/'+ns+'/configmaps' if kind=='ConfigMap' else '/apis/monitoring.coreos.com/v1/namespaces/'+ns+'/podmonitors'
    request('dryrun-'+n,path+'?dryRun=All&fieldManager=kaas-r3-prerequisite',lambda o:{'metadata':meta(o),'kind':o['kind'],'admission_dryRun_only':True},method='POST',payload=d)
  status='COMPLETE';reason=None
 except Stop as e:status='STOPPED';reason=str(e)
 except Exception as e:status='STOPPED';reason=type(e).__name__
 finally:
  token='';result={'status':status,'stop_reason':reason,'elapsed_seconds':round(time.monotonic()-start,3),'requests':len(queries),'response_bytes':total,'queries':queries,'Alertmanager_configuration_Secret_reads':secrets,'credential_values_saved':False,'raw_Secret_data_saved':False,'resource_changes':False,'workloads_run':False,'emails_sent':False};save('result',result);print(json.dumps({'status':status,'stop_reason':reason,'requests':len(queries),'elapsed_seconds':result['elapsed_seconds']}))
if __name__=='__main__':main()
