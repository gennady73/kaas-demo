import copy,unittest
from validate import load,validate
class Checks(unittest.TestCase):
 def setUp(self):self.data=copy.deepcopy(load())
 def check(self):return validate(*self.data)
 def get(self,kind):return next(o for o in self.data[0] if o['kind']==kind)
 def test_disabled_package(self):self.assertFalse(self.check()['workloads_enabled'])
 def test_flags(self):
  for k in ['execution_enabled','deployment_enabled','workloads_enabled','build_enabled']:
   with self.subTest(flag=k):
    self.data[3][k]=True
    with self.assertRaises(AssertionError):self.check()
    self.data[3][k]=False
 def test_unsuspend(self):
  self.get('Job')['spec']['suspend']=False
  with self.assertRaises(AssertionError):self.check()
 def test_replicas(self):
  self.get('Deployment')['spec']['replicas']=1
  with self.assertRaises(AssertionError):self.check()
 def test_boolean_counters(self):
  self.get('Job')['spec']['parallelism']=True
  with self.assertRaises(AssertionError):self.check()
 def test_trigger(self):
  self.data[1][0]['spec']['triggers']=[{'type':'ConfigChange'}]
  with self.assertRaises(AssertionError):self.check()
 def test_owner_secret_not_on_client(self):
  self.get('Job')['spec']['template']['spec']['volumes'].append({'name':'owner','secret':{'secretName':'kaas-r2-evidence-owner'}})
  with self.assertRaises(AssertionError):self.check()
 def test_wrong_password_mount(self):
  self.get('Job')['spec']['template']['spec']['containers'][0]['volumeMounts'][1]['mountPath']='/credentials/kaas-smoke-client'
  with self.assertRaises(AssertionError):self.check()
 def test_no_reused_continuity_storage(self):
  v=next(v for v in self.get('Deployment')['spec']['template']['spec']['volumes'] if v['name']=='data');v['persistentVolumeClaim']['claimName']='continuity-data'
  with self.assertRaises(AssertionError):self.check()
 def test_no_wildcard_egress(self):
  n=next(o for o in self.data[0] if o['kind']=='NetworkPolicy' and o['metadata']['name']=='kaas-r2-native-client');n['spec']['egress'][2]['to']=[{}]
  with self.assertRaises(AssertionError):self.check()
 def test_mutable_base(self):
  self.data[4]['runner']=self.data[4]['runner'].replace(self.data[3]['base_image'],'registry.example/image:latest')
  with self.assertRaises(AssertionError):self.check()
 def test_privilege(self):
  self.get('Job')['spec']['template']['spec']['containers'][0]['securityContext']['allowPrivilegeEscalation']=True
  with self.assertRaises(AssertionError):self.check()

class GuardAndBuildChecks(unittest.TestCase):
 def test_guards_refuse_without_invoking_process(self):
  import tempfile,os,subprocess
  from pathlib import Path
  from validate import HERE
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'cat').write_text('#!/bin/sh\nprintf false\n');(root/'cat').chmod(0o755)
   for name in ['timeout','python3']:
    f=root/name;f.write_text('#!/bin/sh\nexit 99\n');f.chmod(0o755)
   for role,marker in [('client','R2_CLIENT_DISABLED'),('sink','R2_SINK_DISABLED')]:
    r=subprocess.run(['/bin/sh',str(HERE/'build'/(role+'-guard.sh'))],env={**os.environ,'PATH':str(root)+os.pathsep+os.defpath},capture_output=True,text=True,timeout=5)
    self.assertEqual(r.returncode,78);self.assertEqual(r.stderr,marker+'\n')
 def test_runner_checksum_line_executes_correctly(self):
  import tempfile,hashlib,subprocess
  from pathlib import Path
  from validate import HERE
  text=(HERE/'build/runner.Dockerfile').read_text();line=next(x for x in text.splitlines() if 'printf ' in x);command=line[line.index('printf '):]
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'binary';p.write_bytes(b'offline checksum fixture')
   expected=hashlib.sha256(p.read_bytes()).hexdigest();command=command.replace(load()[3]['binary_sha256'],expected).replace('/usr/local/bin/k6',str(p))
   r=subprocess.run(['/bin/sh','-c',command],capture_output=True,text=True,timeout=5);self.assertEqual(r.returncode,0,r.stderr)
 def test_runtime_flags_cannot_be_armed(self):
  import json
  d=copy.deepcopy(load());cm=next(o for o in d[0] if o['kind']=='ConfigMap' and o['metadata']['name']=='kaas-r2-execution-disabled');v=json.loads(cm['data']['runtime.json']);v['execution_authorized']=True;cm['data']['runtime.json']=json.dumps(v)
  with self.assertRaises(AssertionError):validate(*d)
 def test_sink_cannot_unpause(self):
  d=copy.deepcopy(load());next(o for o in d[0] if o['kind']=='Deployment')['spec']['paused']=False
  with self.assertRaises(AssertionError):validate(*d)

if __name__=='__main__':unittest.main()
