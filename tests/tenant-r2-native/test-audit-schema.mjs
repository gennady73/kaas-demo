// Standalone-auditor mutations. Only synthetic clients/clock/evidence are used.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {auditNativeEvidence} from './audit.mjs';
import {canonical} from './native-policy.mjs';
import {runNativeTenantFixture} from './engine.mjs';
import {fakeWorld} from '../../../kafka-load-test/preflight/tenant/offline-fakes.mjs';
const sha=x=>createHash('sha256').update(x).digest('hex');
const plan=JSON.parse(fs.readFileSync(new URL('./plan.json',import.meta.url)));
const w=fakeWorld(plan,sha),normalize=w.deps.normalizeNativeError;
Object.assign(w.deps,{mode:'NATIVE_KAFKA_V1',execution_context:'SYNTHETIC',runtimeAuthorized:true,
 reviewedPlanHash:sha(canonical(plan)),normalizeNativeError:e=>({...normalize(e),mapping_id:'KAAS_R2_CONFLUENT_2_14_V1'})});
const fixture=runNativeTenantFixture(plan,w.deps);
assert.equal(fixture.status,'NATIVE_COMPLETE');
const copy=x=>structuredClone(x);
function audit(events,afterIdentity=()=>{}){
 let previous=null;
 const rows=events.map((event,i)=>{
  const e={...event,event_id:`${plan.run_id}/tenant_fixture/${i}`,previous_event_sha256:previous};
  afterIdentity(e,i);
  const event_json=JSON.stringify(e),event_sha256=sha(event_json);previous=event_sha256;
  return {event_json,event_sha256};
 });
 const raw=rows.map(x=>JSON.stringify(x)+'\n').join('');
 return auditNativeEvidence(plan,raw,{protocol:'kaas-tenant-evidence-v1',run_id:plan.run_id,
  plan_sha256:sha(canonical(plan)),export_sha256:sha(raw),event_count:rows.length,
  terminal_present:true,acceptance:'REQUIRES_INDEPENDENT_AUDIT'},
  {kind:'SYNTHETIC',elapsed_ms:Math.ceil(fixture.duration_ms)},sha);
}
const rejected=a=>assert.equal(a.status,'NATIVE_INCOMPLETE',JSON.stringify(a));
const schemaRejected=a=>{rejected(a);assert.ok(a.issues.some(x=>/^event_(required_field|shape_or_type|field_type_or_domain)/.test(x.code)),JSON.stringify(a));};
test('control: complete synthetic export still matches',()=>assert.equal(audit(copy(fixture.events)).status,'NATIVE_EVIDENCE_MATCHED'));

// Independently enumerated from the protocol/emitter contract, including partial
// lifecycle types absent from a complete fixture. Optional/conditional fields
// have their own tests below. Do not infer this roster from auditor source.
const roster={
 fixture_start:'job_start_ms deadline_ms mode',phase_start:'phase deadline_ms positive_cutoff_ms',
 case_start:'case_id case_kind topic group_id',group_state:'case_id group_id topic stage committed_offset log_end_offset members membership_observed',
 client_open:'case_id binding_id client_role topic group_id auto_commit commit_on_close write_settings_signature',
 client_close:'case_id binding_id client_role closed within_reserve',close_skipped:'case_id binding_id reason',
 attempt_intent:'case_id id topic value_bytes checksum negative',not_sent:'case_id id reason',
 send_outcome:'case_id id topic value_bytes checksum outcome negative intent_event_id',
 receipt:'case_id id topic group_id value_bytes checksum partition offset',durable_receipt_ack:'case_id id receipt_event_id',
 commit_intent:'case_id id receipt_event_id durable_event_id group_id partition offset',
 commit:'case_id id receipt_event_id durable_event_id group_id partition offset',commit_uncertain:'case_id id receipt_event_id',
 case_end:'case_id status',denial_result:'case_id status category failure_stage typed control_ids write_path_control_id consumer_write_confounded confound_resolution',
 unexpected_record:'case_id topic observed_key_sha256 checksum',unexpected_access:'case_id topic group_id kind',
 group_state_unavailable:'case_id topic group_id reason',negative_state_violation:'case_id reason',
 reconciliation_boundary:'positive_cutoff_ms',fixture_stop:'reason status',fixture_terminal:'status elapsed_ms closed positive_cutoff_ms',
};
const common='version run_id plan_sha256 client_id event_id type at_ms previous_event_sha256'.split(' ');
const sample={...fixture.events.find(e=>e.type==='client_open'),...fixture.events.find(e=>e.type==='receipt'),
 reason:'budget_exhausted',kind:'record',status:'PASS',elapsed_ms:1,closed:true,within_reserve:true,
 receipt_event_id:'receipt',durable_event_id:'durable',intent_event_id:'intent',case_kind:'positive',
 category:'topic_authorization_denied',failure_stage:'produce',typed:true,control_ids:[],write_path_control_id:null,
 consumer_write_confounded:false,confound_resolution:'not_applicable',observed_key_sha256:'a'.repeat(64),
 outcome:'acknowledged',negative:false,acknowledged_at_ms:1,ack_bucket:'on_time',job_start_ms:0,deadline_ms:300000,
 mode:'NATIVE_CANDIDATE',phase:'positive_delivery',positive_cutoff_ms:90000,stage:'before',committed_offset:null,
 log_end_offset:0,members:0,membership_observed:true};
for(const [type,keys] of Object.entries(roster)){
 for(const field of [...common,...keys.split(' ')])test(`NW01 required ${type}.${field}`,()=>{
  const events=copy(fixture.events),existing=events.findIndex(e=>e.type===type),i=existing<0?1:existing;
  if(existing<0){events[i]=Object.fromEntries([...common,...keys.split(' ')].map(k=>[k,sample[k]]));events[i].type=type;}
  schemaRejected(audit(events,(e,n)=>{if(n===i)delete e[field];}));
 });
}
for(const [type,key,select] of [
 ['case_start','binding_id',e=>e.case_kind==='negative'],['case_start','control_ids',e=>e.case_kind==='negative'],
 ['send_outcome','acknowledged_at_ms',e=>e.outcome==='acknowledged'],['send_outcome','ack_bucket',e=>e.outcome==='acknowledged'],
 ...['category','failure_stage','typed'].map(k=>['send_outcome',k,e=>e.outcome==='definitive_not_accepted']),
])test(`NW01 conditional ${type}.${key}`,()=>{
 const events=copy(fixture.events);delete events.find(e=>e.type===type&&select(e))[key];schemaRejected(audit(events));
});
for(const [type,key,bad] of [
 ['case_start','case_kind',true],['case_start','case_id',null],['case_start','control_ids','positive'],
 ['durable_receipt_ack','receipt_event_id',[]],['client_open','auto_commit',0],['client_close','closed','true'],
 ['send_outcome','typed',1],['denial_result','control_ids',[true]],['receipt','checksum',false],
 ['fixture_terminal','elapsed_ms','25'],['group_state','membership_observed',1],['group_state','members',false],
])test(`NW01 field type ${type}.${key}`,()=>{
 const events=copy(fixture.events),e=events.find(x=>x.type===type&&(key!=='control_ids'||x.case_kind==='negative'||type==='denial_result')&&(key!=='typed'||x.outcome==='definitive_not_accepted'));
 e[key]=bad;schemaRejected(audit(events));
});
for(const type of ['durable_receipt_ack','commit_intent','commit'])test(`NW01 ${type} cannot switch record to another valid case`,()=>{
 const events=copy(fixture.events);events.find(e=>e.type===type).case_id=plan.positive[1].id;
 const a=audit(events);rejected(a);assert.ok(a.issues.some(x=>x.code==='record_case_link'));
});
test('NW01 case kind cannot bypass negative controls',()=>{
 const events=copy(fixture.events),e=events.find(e=>e.type==='case_start'&&e.case_kind==='negative');e.case_kind='positive';
 const a=audit(events);rejected(a);assert.ok(a.issues.some(x=>x.code==='case_start_binding_or_kind'));
});
for(const [type,key] of [['receipt','offset'],['receipt','partition'],['commit_intent','offset'],['commit','offset'],['commit_intent','partition'],['commit','partition'],
 ['group_state','committed_offset'],['group_state','log_end_offset'],['group_state','members']]){
 for(const bad of [-4,-1,-2,-1001,true,false,0.5,Number.MAX_SAFE_INTEGER+1,'0',{},[]])test(`NW02 ${type}.${key} rejects ${JSON.stringify(bad)}`,()=>{
  const events=copy(fixture.events);events.find(e=>e.type===type)[key]=bad;schemaRejected(audit(events));
 });
}
test('NW02 internally consistent negative positive offsets are rejected',()=>{
 const events=copy(fixture.events);
 for(const e of events)if(e.case_id===plan.positive[0].id){
  if(e.type==='group_state'){e.log_end_offset-=4;e.committed_offset=e.stage==='before'?-4:e.committed_offset-4;}
  if(['receipt','commit_intent','commit'].includes(e.type))e.offset-=4;
 }
 schemaRejected(audit(events));
});
function shift(events,amount){
 for(const e of events){
  if(e.type==='group_state'){e.log_end_offset+=amount;e.committed_offset=e.committed_offset===null?amount:e.committed_offset+amount;}
  if(['receipt','commit_intent','commit'].includes(e.type))e.offset+=amount;
 }
 return events;
}
test('NW02 valid null empty baselines and zero receipt offsets retained',()=>{
 assert.ok(fixture.events.some(e=>e.type==='group_state'&&e.committed_offset===null&&e.log_end_offset===0));
 assert.ok(fixture.events.some(e=>e.type==='receipt'&&e.offset===0));
 assert.equal(audit(copy(fixture.events)).status,'NATIVE_EVIDENCE_MATCHED');
});
test('NW02 established nonzero baseline four retained',()=>assert.equal(audit(shift(copy(fixture.events),4)).status,'NATIVE_EVIDENCE_MATCHED'));
test('NW02 safe integer upper boundary retained without next-offset overflow',()=>assert.equal(audit(shift(copy(fixture.events),Number.MAX_SAFE_INTEGER-4)).status,'NATIVE_EVIDENCE_MATCHED'));
test('NW02 committed offset above log end is rejected',()=>{
 const events=copy(fixture.events),e=events.find(e=>e.type==='group_state');e.committed_offset=1;e.log_end_offset=0;schemaRejected(audit(events));
});
for(const bad of ['1e999','NaN','Infinity'])test('NW02 nonfinite JSON token rejected: '+bad,()=>{
 const events=copy(fixture.events);
 let previous=null;
 const rows=events.map((e,i)=>{
  let event_json=JSON.stringify({...e,event_id:`${plan.run_id}/tenant_fixture/${i}`,previous_event_sha256:previous});
  if(e.type==='receipt')event_json=event_json.replace(/"offset":\d+/,`"offset":${bad}`);
  const event_sha256=sha(event_json);previous=event_sha256;return {event_json,event_sha256};
 });
 const raw=rows.map(x=>JSON.stringify(x)+'\n').join('');
 rejected(auditNativeEvidence(plan,raw,{protocol:'kaas-tenant-evidence-v1',run_id:plan.run_id,plan_sha256:sha(canonical(plan)),export_sha256:sha(raw),event_count:rows.length,terminal_present:true,acceptance:'REQUIRES_INDEPENDENT_AUDIT'},{kind:'SYNTHETIC',elapsed_ms:Math.ceil(fixture.duration_ms)},sha));
});

for(const [type,key] of [['receipt','offset'],['receipt','partition'],['commit_intent','offset'],['commit_intent','partition'],['commit','offset'],['commit','partition'],['group_state','log_end_offset']])test(`NW02 ${type}.${key} cannot be null`,()=>{
 const events=copy(fixture.events);events.find(e=>e.type===type)[key]=null;schemaRejected(audit(events));
});
for(const [label,offset] of [['fabricated null',null],['fabricated zero',0],['stale offset',3]])test('NW02 negative baseline must retain established group position: '+label,()=>{
 const events=shift(copy(fixture.events),4),negative=plan.negative.find(n=>n.operation==='consume');
 for(const e of events)if(e.type==='group_state'&&e.case_id===negative.id)e.committed_offset=offset;
 const a=audit(events);rejected(a);assert.ok(a.issues.some(x=>x.code==='group_baseline_discontinuity'));
});
test('NW02 negative phase cannot grow its observed fixture log without a planned write',()=>{
 const events=copy(fixture.events),n=plan.negative.find(n=>n.operation==='consume');
 events.find(e=>e.type==='group_state'&&e.case_id===n.id&&e.stage==='after').log_end_offset++;
 const a=audit(events);rejected(a);assert.ok(a.issues.some(x=>x.code==='negative_offset_changed'));
});
