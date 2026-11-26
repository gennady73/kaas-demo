#!/usr/bin/env python3
"""Build/import/unit/fake checks only; deliberately has no k6 run or live action."""
import argparse,datetime,hashlib,json,os,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent

def check(output,go):
 assert output!=HERE and HERE not in output.parents,'evidence_output_must_be_outside_source'
 output.mkdir(parents=True,exist_ok=False);commands=[]
 fingerprint=lambda:{str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
 before=fingerprint()
 env={**os.environ,'GOTOOLCHAIN':'local','GOPROXY':'off','GOSUMDB':'off','CGO_ENABLED':'1','GOEXPERIMENT':'','GOCACHE':'/tmp/kaas-r2-go-cache','K6_NO_USAGE_REPORT':'true'}
 def run(name,args,cwd=HERE):
  r=subprocess.run([str(x) for x in args],cwd=cwd,env=env,capture_output=True,text=True,timeout=240)
  (output/(name+'.txt')).write_text(r.stdout+r.stderr);commands.append({'name':name,'argv':[str(x) for x in args],'exit_code':r.returncode})
  if r.returncode:raise RuntimeError('offline check failed: '+name)
  return r.stdout
 if 'go1.26.4 ' not in run('go-version',[go,'version']):raise RuntimeError('pinned Go1.26.4 required')
 gate=json.loads((HERE/'runtime.example.json').read_text());assert gate['execution_authorized'] is False and gate['tests_enabled'] is False and not (HERE/'runtime.json').exists()
 run('projection',['node',HERE/'compile-projection.mjs'])
 run('binding',['node',HERE/'test-binding.mjs']);run('review',['node',HERE/'test-review.mjs'])
 run('auditor-schema',['node',HERE/'test-audit-schema.mjs'])
 run('sink',[sys.executable,'-m','unittest','discover','-s',HERE/'sink','-p','test_*.py','-v'])
 run('go-race',[go,'test','-mod=readonly','-race','-count=1','-v','./...'],HERE/'native')
 binary=output/'k6'
 run('build',[go,'build','-mod=readonly','-buildvcs=false','-trimpath','-o',binary,'./cmd/k6'],HERE/'native')
 run('buildinfo',[go,'version','-m',binary])
 config=output/'empty-k6.json';config.write_text('{}\n')
 inspect=run('inspect',[binary,'--config',config,'inspect',HERE/'inspect.js'])
 binary_hash=hashlib.sha256(binary.read_bytes()).hexdigest();assert binary_hash in (output/'inspect.txt').read_text()
 run('replay',[sys.executable,HERE/'replay_native_offline.py','--output',output/'replay'])
 source=fingerprint();assert source==before,'source_changed_during_validation'
 result={'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'OFFLINE_BUILD_AND_REVIEW_CHECKS_PASS','binary_sha256':binary_hash,'runtime_manifest_sha256':hashlib.sha256((HERE/'runtime-source-manifest.json').read_bytes()).hexdigest(),'commands':commands,'source_sha256':source,'deployment_enabled':False,'workloads_enabled':False,'Kafka_clients_constructed':False,'k6_run_invoked':False,'runtime_acceptance':'NOT_ASSESSED','limitations':['Bounded facade waiting does not cancel an SDK operation; late completion stays uncertain and quarantined','Actual broker TLS/auth/ACL/group/commit behavior and complete-case timing are NOT_RUN','Target image, mount/network/storage/admission and execution authority remain open']}
 (output/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['source_sha256','commands']}))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--go',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args();check(a.output.resolve(),a.go.resolve())
