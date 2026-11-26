// Rehashed synthetic control only. Never reads credentials or invokes clients.
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
import {auditNativeEvidence as corrected} from '../../../tests/tenant-r2-native/audit.mjs';
const [planPath,fixtureDir,publishedAuditor,output]=process.argv.slice(2);
if(!output)throw Error('usage: PLAN SYNTHETIC_FIXTURE_DIR PUBLISHED_AUDITOR OUTPUT');
const {auditNativeEvidence:published}=await import(pathToFileURL(publishedAuditor));
const sha=x=>createHash('sha256').update(x).digest('hex');
const plan=JSON.parse(fs.readFileSync(planPath)),raw=fs.readFileSync(fixtureDir+'/export.ndjson','utf8');
const base=raw.trimEnd().split('\n').map(x=>JSON.parse(JSON.parse(x).event_json));
const seal=JSON.parse(fs.readFileSync(fixtureDir+'/seal.json')),observation=JSON.parse(fs.readFileSync(fixtureDir+'/observation.json'));
function run(auditor,events){
 let previous=null;
 const envelopes=events.map(e=>{const event_json=JSON.stringify({...e,previous_event_sha256:previous}),event_sha256=sha(event_json);previous=event_sha256;return {event_json,event_sha256};});
 const bytes=envelopes.map(e=>JSON.stringify(e)+'\n').join('');
 return auditor(plan,bytes,{...seal,export_sha256:sha(bytes),event_count:envelopes.length},observation,sha);
}
const control={published:run(published,structuredClone(base)).status,corrected:run(corrected,structuredClone(base)).status};
if(Object.values(control).some(x=>x!=='NATIVE_EVIDENCE_MATCHED'))throw Error('control_rejected');
const mutations={
 missing_case_kind:events=>{delete events.find(e=>e.type==='case_start'&&e.case_kind==='negative').case_kind;},
 missing_durable_case_id:events=>{delete events.find(e=>e.type==='durable_receipt_ack').case_id;},
 negative_positive_offsets:events=>{for(const e of events)if(e.case_id===plan.positive[0].id){if(e.type==='group_state'){e.log_end_offset-=4;e.committed_offset=e.stage==='before'?-4:e.committed_offset-4;}if(['receipt','commit_intent','commit'].includes(e.type))e.offset-=4;}},
};
for(const [name,value]of [['negative_fabricated_null',null],['negative_fabricated_zero',0],['negative_stale_position',3]])mutations[name]=events=>{const n=plan.negative.find(n=>n.operation==='consume');for(const e of events)if(e.type==='group_state'&&e.case_id===n.id)e.committed_offset=value;};
mutations.negative_log_growth=events=>{const n=plan.negative.find(n=>n.operation==='consume');events.find(e=>e.type==='group_state'&&e.case_id===n.id&&e.stage==='after').log_end_offset++;};
const results=[];
for(const [name,mutate]of Object.entries(mutations)){
 const events=structuredClone(base);mutate(events);
 const old=run(published,events),now=run(corrected,events);
 if(old.status!=='NATIVE_EVIDENCE_MATCHED'||now.status!=='NATIVE_INCOMPLETE')throw Error('probe_not_reproduced');
 results.push({name,published_status:old.status,corrected_status:now.status,corrected_issues:now.issues});
}
fs.writeFileSync(output,JSON.stringify({status:'C3_AND_GROUP_CONTINUITY_PROBES_REPRODUCED_AND_REJECTED',synthetic_fixture_sha256:sha(raw),published_auditor_sha256:sha(fs.readFileSync(publishedAuditor)),corrected_auditor_sha256:sha(fs.readFileSync(new URL('../../../tests/tenant-r2-native/audit.mjs',import.meta.url))),control,results,scope:'Synthetic rehashed controls only; historical owner probe/evidence files untouched'},null,2)+'\n');
console.log(JSON.stringify({control,results:results.map(x=>({name:x.name,published:x.published_status,corrected:x.corrected_status}))}));
