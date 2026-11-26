"""Read only /assets YAML from the existing CMO container; memory-only kubeconfig.
No shell inside container, no build, no Job, no producer/consumer or email execution.
"""
import datetime,getpass,json,os,ssl,subprocess,time,urllib.request
from pathlib import Path
import yaml
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[5]
BASE='https://api.ocp.rddgh.sandbox3088.opentlc.com:6443'
PATHS=['prometheus-operator-user-workload/deployment.yaml','prometheus-user-workload/prometheus.yaml','thanos-ruler/thanos-ruler.yaml']
EXPECTED='quay.io/openshift-release-dev/ocp-v4.0-art-dev@sha256:4aae77bd4739acfa0dfa1689a24cd86b44a36787772c3495df82a6c44b30ad4f'
def main():
 out=HERE/'installed-assets'
 if out.exists():raise SystemExit('Fresh output required')
 out.mkdir();token=getpass.getpass('Sandbox token (memory only): ').strip();ca=ROOT/'config/environments/certificates/ocp-rddgh-api-ca.crt';t=time.monotonic();receipts=[]
 ctx=ssl.create_default_context(cafile=str(ca));op=urllib.request.build_opener(urllib.request.ProxyHandler({}),urllib.request.HTTPSHandler(context=ctx))
 def get(path):
  with op.open(urllib.request.Request(BASE+path,headers={'Authorization':'Bearer '+token}),timeout=15) as r:return json.loads(r.read(2097152))
 fd=None;status='STOPPED';reason=None
 try:
  d=get('/api/v1/namespaces/openshift-monitoring/pods?labelSelector=app%3Dcluster-monitoring-operator&limit=10')
  if len(d['items'])!=1:raise RuntimeError('expected_one_CMO_Pod')
  pod=d['items'][0];c=next(c for c in pod['spec']['containers'] if c['name']=='cluster-monitoring-operator')
  if c['image']!=EXPECTED:raise RuntimeError('installed_image_changed')
  identity={'name':pod['metadata']['name'],'uid':pod['metadata']['uid'],'resourceVersion':pod['metadata']['resourceVersion'],'image':c['image'],'containerStatus':[{k:x.get(k) for k in ['name','image','imageID','containerID','ready','restartCount']} for x in pod.get('status',{}).get('containerStatuses',[]) if x['name']==c['name']]}
  config={'apiVersion':'v1','kind':'Config','clusters':[{'name':'sandbox','cluster':{'server':BASE,'certificate-authority':str(ca)}}],'users':[{'name':'memory','user':{'token':token}}],'contexts':[{'name':'memory','context':{'cluster':'sandbox','user':'memory'}}],'current-context':'memory'}
  fd=os.memfd_create('kaas-memory-kubeconfig',os.MFD_CLOEXEC);os.write(fd,json.dumps(config).encode());os.lseek(fd,0,0)
  for path in PATHS:
   os.lseek(fd,0,0)
   cmd=['oc','--kubeconfig=/proc/self/fd/'+str(fd),'--cache-dir=/tmp/kaas-r3-prerequisite-oc-cache','--request-timeout=15s','exec','-n','openshift-monitoring',pod['metadata']['name'],'-c',c['name'],'--','cat','/assets/'+path]
   proc=subprocess.run(cmd,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,pass_fds=(fd,),timeout=25)
   q={'path':'/assets/'+path,'exit_code':proc.returncode,'stdout_bytes':len(proc.stdout)};receipts.append(q)
   if proc.returncode:raise RuntimeError('asset_read_exit_'+str(proc.returncode))
   if len(proc.stdout)>1048576 or token.encode() in proc.stdout:raise RuntimeError('output_guard')
   parsed=yaml.safe_load(proc.stdout)
   if not isinstance(parsed,dict) or parsed.get('kind') not in ['Deployment','Prometheus','ThanosRuler']:raise RuntimeError('asset_kind')
   (out/path.replace('/','__')).write_bytes(proc.stdout)
  (out/'identity.json').write_text(json.dumps(identity,indent=2)+'\n');status='COMPLETE'
 except Exception as e:reason=str(e) if isinstance(e,RuntimeError) else type(e).__name__
 finally:
  token=''
  if fd is not None:os.close(fd)
  d={'status':status,'reason':reason,'at_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'elapsed_seconds':round(time.monotonic()-t,3),'asset_reads':receipts,'method':'GET Pod identity, then oc exec cat of three exact /assets YAML paths in existing CMO container','diagnostic_exec_processes':len(receipts),'client_workloads_run':False,'Jobs_changed':False,'emails_sent':False,'credentials_saved':False,'kubeconfig_storage':'anonymous RAM memfd only; closed on exit; no filesystem credential file'};(out/'result.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d))
if __name__=='__main__':main()
