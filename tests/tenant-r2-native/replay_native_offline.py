#!/usr/bin/env python3
"""Fake native engine -> actual local SQLite protocol -> independent semantic audit.
No native Go object, Kafka connection, API, Secret or HTTPS endpoint is used.
"""
import argparse,json,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'sink'))
from store import Store
from verify_export import verify

def replay(output,utility):
 output.mkdir(parents=True,exist_ok=False)
 script='''import fs from 'node:fs';import {createHash} from 'node:crypto';
const [root,utility,dest]=process.argv.slice(1),sha=s=>createHash('sha256').update(s).digest('hex');
const {runNativeTenantFixture}=await import(root+'/engine.mjs');const {canonical}=await import(root+'/native-policy.mjs');const {fakeWorld}=await import(utility+'/preflight/tenant/offline-fakes.mjs');
const p=JSON.parse(fs.readFileSync(new URL(root+'/plan.json'))),w=fakeWorld(p,sha),norm=w.deps.normalizeNativeError;
Object.assign(w.deps,{mode:'NATIVE_KAFKA_V1',execution_context:'SYNTHETIC',runtimeAuthorized:true,reviewedPlanHash:sha(canonical(p)),normalizeNativeError:e=>({...norm(e),mapping_id:'KAAS_R2_CONFLUENT_2_14_V1'})});
const r=runNativeTenantFixture(p,w.deps);if(r.status!=='NATIVE_COMPLETE')throw Error('fake_fixture_failed');
fs.writeFileSync(dest+'/model.json',JSON.stringify({run_id:p.run_id,plan_sha256:sha(canonical(p)),envelopes:r.envelopes,observation:{kind:'SYNTHETIC',elapsed_ms:Math.ceil(r.duration_ms)}},null,2)+'\\n');
'''
 subprocess.run(['node','--input-type=module','-e',script,HERE.as_uri(),utility.as_uri(),str(output)],check=True,capture_output=True,text=True,timeout=30)
 model=json.loads((output/'model.json').read_text());store=Store(output/'temporary.sqlite',model['run_id'],model['plan_sha256'])
 try:
  for e in model['envelopes']:assert store.event(e)[1]['ack']['durable'] is True
  store.stop();seal=store.seal();raw=store.export();byte_result=verify(raw,seal)
 finally:store.close()
 (output/'export.ndjson').write_bytes(raw);(output/'seal.json').write_text(json.dumps(seal,indent=2)+'\n');(output/'observation.json').write_text(json.dumps(model['observation'])+'\n')
 r=subprocess.run(['node',str(HERE/'audit-export.mjs'),str(HERE/'plan.json'),str(output/'export.ndjson'),str(output/'seal.json'),str(output/'observation.json')],check=True,capture_output=True,text=True,timeout=30)
 audit=json.loads(r.stdout);(output/'audit.json').write_text(json.dumps(audit,indent=2)+'\n')
 result={'mode':'SYNTHETIC_ONLY','events':len(model['envelopes']),'byte_verification':byte_result['byte_integrity'],'semantic_status':audit['status'],'reported_commit_records':audit['stats']['confirmed_commit_records'],'Kafka_clients_constructed':False,'runtime_acceptance':'NOT_ASSESSED'}
 (output/'result.json').write_text(json.dumps(result,indent=2)+'\n');return result
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);p.add_argument('--utility',type=Path,default=HERE.parents[2]/'kafka-load-test');a=p.parse_args();print(json.dumps(replay(a.output.resolve(),a.utility.resolve())))
