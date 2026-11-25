import copy,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from validate import HERE,validate
class PackageTests(unittest.TestCase):
 def setUp(self):
  self.p=json.loads((HERE/'package.json').read_text());self.j=json.loads((HERE/'job.json.disabled').read_text());self.c=json.loads((HERE/'disabled-entrypoint.json').read_text());self.b=json.loads((HERE.parent/'tenant-r2-preparation/bindings.json').read_text())
 def check(self):return validate(self.p,self.j,self.c,self.b)
 def test_valid_disabled_package(self):self.assertFalse(self.check()['execution_ready'])
 def test_enabled_package_rejected(self):
  for k in ['execution_enabled','deployment_enabled','workloads_enabled','execution_ready','automatic_sync_enabled']:
   with self.subTest(k=k):
    self.p[k]=True
    with self.assertRaises(AssertionError):self.check()
    self.p[k]=False
 def test_unsuspend_rejected(self):
  self.j['spec']['suspend']=False
  with self.assertRaises(AssertionError):self.check()
 def test_larger_budget_rejected(self):
  self.p['fixture']['maximum_original_attempt_value_bytes']=20001
  with self.assertRaises(AssertionError):self.check()
 def test_credential_swap_rejected(self):
  self.j['spec']['template']['spec']['volumes'][1]['secret']['secretName']='kaas-smoke-client'
  with self.assertRaises(AssertionError):self.check()
 def test_credential_env_rejected(self):
  self.j['spec']['template']['spec']['containers'][0]['env']=[{'name':'PASSWORD','value':'CANARY'}]
  with self.assertRaises(AssertionError):self.check()
 def test_retry_rejected(self):
  self.j['spec']['backoffLimit']=1
  with self.assertRaises(AssertionError):self.check()
 def test_boolean_or_negative_job_counters_rejected(self):
  for key in ['backoffLimit','activeDeadlineSeconds','parallelism','completions']:
   original=self.j['spec'][key]
   for value in [True,False,-1]:
    with self.subTest(key=key,value=value):
     self.j['spec'][key]=value
     with self.assertRaises(AssertionError):self.check()
   self.j['spec'][key]=original
 def test_unaccepted_retention_rejected(self):
  self.p['evidence_custody_decision']['sandbox_retention_days']=-7
  with self.assertRaises(AssertionError):self.check()
 def test_changed_entrypoint_rejected(self):
  self.c['data']['disabled.js']='export default function(){}'
  with self.assertRaises(AssertionError):self.check()
if __name__=='__main__':unittest.main()
