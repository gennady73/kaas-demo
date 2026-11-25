#!/usr/bin/env python3
"""Replay the accepted fake engine through the isolated SQLite protocol, then audit it.

All paths are supplied explicitly. No broker, Secret, API or network access.
"""
import argparse,json,subprocess,tempfile
from pathlib import Path
from offline_sink import Sink


def replay(utility,contract,c3,c6,output):
    output.mkdir(parents=True,exist_ok=False)
    subprocess.run(['node',str(utility/'preflight/tenant/offline.mjs'),'--contract',str(contract),'--c3-review',str(c3),'--c6-review',str(c6),'--output',str(output/'fake-engine'),'--run-id','offline-native-integration','--seed','2511'],check=True,capture_output=True,text=True,timeout=30)
    plan=json.loads((output/'fake-engine/plan.json').read_text())
    lines=(output/'fake-engine/events.ndjson').read_text().splitlines()
    with tempfile.TemporaryDirectory() as temp:
        sink=Sink(Path(temp)/'candidate.db',plan)
        for line in lines:
            ack=sink.persist(line)
            assert ack['ack']['durable'] is True
        # Verify successful receipt survives a process-equivalent close/reopen and retry.
        sink.close();sink=Sink(Path(temp)/'candidate.db',plan)
        assert sink.persist(lines[-1])['status']==200
        raw,seal=sink.seal(json.loads((output/'fake-engine/seal.json').read_text())['observed_job_elapsed_ms'])
        (output/'sink-export.ndjson').write_text(raw);(output/'sink-seal.json').write_text(json.dumps(seal,indent=2)+'\n')
        sink.close()
    script='''import fs from 'node:fs';import {createHash} from 'node:crypto';
const [utility,directory]=process.argv.slice(1);const {auditFixture}=await import(utility+'/preflight/tenant/audit.mjs');
const {compileIntegration}=await import(utility+'/preflight/tenant-native-candidate/native-contract.mjs');
const p=JSON.parse(fs.readFileSync(directory+'/fake-engine/plan.json','utf8'));
const e=fs.readFileSync(directory+'/sink-export.ndjson','utf8').trim().split('\\n').map(s=>JSON.parse(s));
const seal=JSON.parse(fs.readFileSync(directory+'/sink-seal.json','utf8'));
const audit=auditFixture(p,e,seal,s=>createHash('sha256').update(s).digest('hex'));
fs.writeFileSync(directory+'/native-options.json',JSON.stringify(compileIntegration(p),null,2)+'\\n');
fs.writeFileSync(directory+'/sink-audit.json',JSON.stringify(audit,null,2)+'\\n');
if(audit.status!=='OFFLINE_COMPLETE')process.exit(2);
'''
    subprocess.run(['node','--input-type=module','-e',script,str(utility),str(output)],check=True,capture_output=True,text=True,timeout=30)
    result={'offline_replay':'PASS','events_committed':len(lines),'audit':'OFFLINE_COMPLETE','real_native_calls':0,'workloads_started':0,'live_ready':False}
    (output/'replay-result.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['utility','contract','c3-review','c6-review','output']:p.add_argument('--'+name,required=True,type=Path)
    a=p.parse_args();print(json.dumps(replay(a.utility.resolve(),a.contract.resolve(),a.c3_review.resolve(),a.c6_review.resolve(),a.output.resolve())))
