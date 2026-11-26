// Synthetic Go-result/HTTP envelopes only: no k6 import or native clients.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {canonical,validateExecution,valueFor} from './native-policy.mjs';
import {evidenceTransport} from './transport.mjs';
import {bindNative} from './binder.mjs';
import {runNativeTenantFixture} from './engine.mjs';
import {fakeWorld} from '../../../kafka-load-test/preflight/tenant/offline-fakes.mjs';
const plan=JSON.parse(fs.readFileSync(new URL('./plan.json',import.meta.url)));
const disabled=JSON.parse(fs.readFileSync(new URL('./runtime.example.json',import.meta.url)));
const sha=x=>createHash('sha256').update(x).digest('hex');
test('shipped execution record refuses before native or HTTP',()=>{
 assert.throws(()=>validateExecution(plan,disabled,sha),/execution_not_authorized/);
 const gate={...disabled,execution_authorized:true,tests_enabled:true,authority_reference:'synthetic'};
 assert.throws(()=>validateExecution(plan,gate,sha),/execution_gates_open/);
});
test('transport exact durable ack wrapping, no redirect and bounded request',()=>{
 let input;
 const t=evidenceTransport((url,body,opts)=>{input={url,body,opts};return {status:201,body:JSON.stringify({ack:{durable:true,event_id:'r/0',event_sha256:'a'.repeat(64)}})};},'https://sink:8443','synthetic-auth-canary',()=>0);
 const envelope={event_json:JSON.stringify({event_id:'r/0',type:'fixture_start'}),event_sha256:'a'.repeat(64)};
 assert.equal(t.persist(envelope).ack.durable,true);assert.equal(input.body,JSON.stringify(envelope));assert.equal(input.opts.redirects,0);assert.equal(input.opts.timeout,'700ms');
});
test('lost or mismatching acknowledgement stops further evidence and admission',()=>{
 for(const response of [{status:503,body:'{}'},{status:201,body:'bad'},{status:201,body:JSON.stringify({ack:{durable:true,event_sha256:'wrong'}})}]){
  let calls=0;const t=evidenceTransport(()=>{calls++;return response;},'https://sink:8443','canary',()=>0);
  assert.throws(()=>t.persist({event_json:JSON.stringify({event_id:'r/0',type:'fixture_start'}),event_sha256:'a'.repeat(64)}));assert.equal(t.shouldStop(),true);assert.throws(()=>t.persist({}));assert.equal(calls,2);
 }
});
test('only private typed native results classify; arbitrary error text stays unknown',()=>{
 const canary='synthetic-password-canary';let captures=[];
 const native={identity:()=>({ok:true,binary_sha256:'b'.repeat(64),mapping_id:'KAAS_R2_CONFLUENT_2_14_V1'}),start:()=>({ok:true,binary_sha256:'b'.repeat(64),mapping_id:'KAAS_R2_CONFLUENT_2_14_V1'}),openProducer:()=>({ok:true,handle:1}),produce:()=>({ok:false,mapping_id:'KAAS_R2_CONFLUENT_2_14_V1',native_code:29,category:'topic_authorization_denied',stage:'produce',raw:canary}),close:()=>({ok:true}),now:()=>0};
 const d=bindNative(native,{persist:x=>captures.push(x),shouldStop:()=>false},plan,{plan_sha256:sha(canonical(plan)),job_start_unix_ms:1,binary_sha256:'b'.repeat(64)},sha,()=>{});
 const b=plan.bindings[0],p=d.makeProducer({binding_id:b.id,principal:b.principal,password_path:b.password_path,topic:plan.positive[0].topic});
 let err;try{const r=plan.records[0];p.produce({messages:[{topic:r.topic,key:r.id,value:valueFor(plan.seed,r,sha)}]});}catch(e){err=e;}
 assert.equal(d.normalizeNativeError(err).category,'topic_authorization_denied');assert.equal(d.normalizeNativeError(new Error(canary)),undefined);assert.equal(String(err).includes(canary),false);assert.equal(JSON.stringify(captures).includes(canary),false);
});
test('positive native return and explicit offset commit map to undefined only on ok',()=>{
 const called=[];const native={identity:()=>({ok:true,binary_sha256:'b'.repeat(64),mapping_id:'KAAS_R2_CONFLUENT_2_14_V1'}),start:()=>({ok:true,binary_sha256:'b'.repeat(64),mapping_id:'KAAS_R2_CONFLUENT_2_14_V1'}),openConsumer:(...x)=>{called.push(x);return {ok:true,handle:3};},position:()=>({ok:true,position:0}),consume:()=>({ok:true,messages:[]}),commit:()=>{called.push('commit');return {ok:true};},close:()=>({ok:true}),now:()=>0};
 const d=bindNative(native,{shouldStop:()=>false},plan,{plan_sha256:sha(canonical(plan)),job_start_unix_ms:1,binary_sha256:'b'.repeat(64)},sha,()=>{});
 const b=plan.bindings.find(b=>b.role==='consumer'),p=plan.positive[0];
 const c=d.makeConsumer({binding_id:b.id,principal:b.principal,password_path:b.password_path,topic:p.topic,group:p.group});
 assert.equal(c.position(),0);assert.deepEqual(c.consume({limit:1}),[]);assert.equal(c.commitOffsets(),undefined);assert.equal(c.close(),undefined);assert.ok(called.includes('commit'));assert.ok(!JSON.stringify(called).includes('password-canary'));
});
function syntheticWorld(){
 const world=fakeWorld(plan,sha),original=world.deps.normalizeNativeError;
 Object.assign(world.deps,{mode:'NATIVE_KAFKA_V1',execution_context:'SYNTHETIC',runtimeAuthorized:true,reviewedPlanHash:sha(canonical(plan)),normalizeNativeError:e=>({...original(e),mapping_id:'KAAS_R2_CONFLUENT_2_14_V1'})});
 return world;
}
test('synthetic engine preserves full fixture ledger and receipt ordering',()=>{
 const world=syntheticWorld(),result=runNativeTenantFixture(plan,world.deps);
 assert.equal(result.status,'NATIVE_COMPLETE');assert.equal(world.commits.length,16);assert.equal(result.stats.attempted_unique_value_bytes,20000);
 for(const commit of result.events.filter(e=>e.type==='commit')){
  const receipt=result.events.findIndex(e=>e.event_id===commit.receipt_event_id),durable=result.events.findIndex(e=>e.event_id===commit.durable_event_id),committed=result.events.indexOf(commit);
  assert.ok(receipt>=0&&receipt<durable&&durable<committed);
 }
 if(process.env.R2_SYNTHETIC_ENVELOPES)fs.writeFileSync(process.env.R2_SYNTHETIC_ENVELOPES,JSON.stringify({run:plan.run_id,hash:sha(canonical(plan)),events:world.sink}),{flag:'wx'});
 assert.equal(JSON.stringify(world.sink).includes(world.canary),false);
});
test('synthetic post-poll unauthorized membership stops without negative commits',()=>{
 const world=syntheticWorld(),make=world.deps.makeConsumer;
 world.deps.makeConsumer=o=>{
  const c=make(o);let polled=false;
  if(o.principal==='kaas-sbx-a-consumer'&&o.topic==='kaas-sbx-b-events')return {...c,consume(){polled=true;return [];},probeState:()=>({broker_confirmed:polled,group_joined:polled,forbidden_assignment:polled})};
  return c;
 };
 const result=runNativeTenantFixture(plan,world.deps);
 assert.equal(result.status,'NATIVE_INCOMPLETE');assert.equal(result.first_failure.reason,'unexpected_negative_join');assert.equal(result.first_failure.severity,'FAIL');assert.equal(world.commits.length,16);
});

test('binder rejects mixed observation topic/group before native snapshot and preserves canonical offset',()=>{
 const calls=[];const native={identity:()=>({ok:true,binary_sha256:'b'.repeat(64),mapping_id:'KAAS_R2_CONFLUENT_2_14_V1'}),start:()=>({ok:true}),snapshot:(topic,group)=>{calls.push([topic,group]);return {ok:true,committed_offset:4,log_start_offset:0,log_end_offset:4,members:0,membership_observed:true};}};
 const group=plan.positive[0].group,topic=plan.positive[0].topic;
 const d=bindNative(native,null,plan,{plan_sha256:sha(canonical(plan)),job_start_unix_ms:1,binary_sha256:'b'.repeat(64),exclusive_fixture_groups:[group]},sha,()=>{});
 assert.throws(()=>d.groupState(group,'kaas-sbx-b-events'),/observation_topic_binding/);assert.equal(calls.length,0);
 assert.equal(d.groupState(group,topic).committed_offset,4);assert.deepEqual(calls,[[topic,group]]);
});
