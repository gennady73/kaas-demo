// R3-11 injected-clock/transport regressions: no k6, sockets or SDK clients.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {canonical} from './native-policy.mjs';
import {runNativeTenantFixture} from './engine.mjs';
import {evidenceTransport} from './transport.mjs';
import {fakeWorld} from '../../../kafka-load-test/preflight/tenant/offline-fakes.mjs';
const plan=JSON.parse(fs.readFileSync(new URL('./plan.json',import.meta.url)));
const sha=x=>createHash('sha256').update(x).digest('hex');
function world(opts={}) {
 const w=fakeWorld(plan,sha,opts),norm=w.deps.normalizeNativeError;
 Object.assign(w.deps,{mode:'NATIVE_KAFKA_V1',execution_context:'SYNTHETIC',runtimeAuthorized:true,reviewedPlanHash:sha(canonical(plan)),normalizeNativeError:e=>({...norm(e),mapping_id:'KAAS_R2_CONFLUENT_2_14_V1'})});
 return w;
}
function incomplete(r){assert.equal(r.status,'NATIVE_INCOMPLETE');assert.equal(r.live_execution,false);}
test('late producer ACK is recorded as late, never retried or committed',()=>{
 const w=world({produceDelayMs:150000}),r=runNativeTenantFixture(plan,w.deps);incomplete(r);
 assert.equal(w.calls.filter(c=>c.type==='produce').length,1);assert.equal(w.commits.length,0);
 assert.equal(r.stats.late_acknowledged_value_bytes,1000);assert.equal(r.stats.unresolved_value_bytes,0);
 assert.equal(r.first_failure.reason,'late_positive_ack');
});
for(const [type,produced] of [['attempt_intent',0],['commit_intent',4]])test('persisted '+type+' exhausting phase prevents the next native mutation',()=>{
 const w=world({sinkLatencyByType:{[type]:150000}}),r=runNativeTenantFixture(plan,w.deps);incomplete(r);
 assert.equal(w.calls.filter(c=>c.type==='produce').length,produced);assert.equal(w.commits.length,0);
 assert.equal(r.events.filter(e=>e.type==='commit').length,0);
 if(type==='attempt_intent')assert.equal(r.events.filter(e=>e.type==='not_sent').length,1);
});
test('stalled poll returning no records exhausts budget without another send or commit',()=>{
 const w=world({consumeDelayMs:150000,emptyPositive:true}),r=runNativeTenantFixture(plan,w.deps);incomplete(r);
 assert.equal(w.calls.filter(c=>c.type==='consume').length,1);assert.equal(w.calls.filter(c=>c.type==='produce').length,4);
 assert.equal(w.commits.length,0);assert.equal(r.first_failure.reason,'budget_exhausted');
});
test('commit timeout preserves uncertainty even when the fake broker offset advanced',()=>{
 const w=world({commitTimeout:true}),r=runNativeTenantFixture(plan,w.deps);incomplete(r);
 assert.equal(w.commits.length,1);assert.equal(r.events.filter(e=>e.type==='commit_uncertain').length,1);
 assert.equal(r.events.filter(e=>e.type==='commit').length,0);assert.equal(r.records.filter(x=>x.commit_uncertain).length,1);
 assert.equal(w.calls.filter(c=>c.type==='produce').length,4);
});
test('close returning after reserve is incomplete and never starts the next case',()=>{
 const w=world({closeDelayMs:plan.close_reserve_ms+1}),r=runNativeTenantFixture(plan,w.deps);incomplete(r);
 assert.equal(r.cleanup_complete,false);assert.ok(r.events.some(e=>e.type==='client_close'&&!e.within_reserve));
 assert.equal(r.events.filter(e=>e.type==='case_start').length,1);
});
test('startup delay is charged to the same total clock, before client construction',()=>{
 const w=world({initialTimeMs:45001}),r=runNativeTenantFixture(plan,w.deps);incomplete(r);
 assert.equal(w.calls.length,0);assert.equal(r.first_failure.reason,'budget_exhausted');assert.ok(r.duration_ms>=45001);
});
for(const elapsed of [1201,2001])test('sink response failure after '+elapsed+'ms cannot extend retry admission',()=>{
 let clock=0,calls=0;
 const t=evidenceTransport(()=>{calls++;clock+=elapsed;throw Error('PRIVATE_CANARY');},'https://offline.invalid','SYNTHETIC',()=>clock);
 const e={event_json:JSON.stringify({event_id:'r/0',type:'receipt'}),event_sha256:'a'.repeat(64)};
 assert.throws(()=>t.persist(e),/durable_ack_missing/);assert.equal(calls,1);assert.equal(t.shouldStop(),true);
 assert.throws(()=>t.persist({...e,event_json:JSON.stringify({event_id:'r/1',type:'commit_intent'})}),/evidence_stopped/);
 assert.equal(calls,1);
});
test('durable ACK arriving beyond 2s is rejected even with matching identity',()=>{
 let clock=0,calls=0;const e={event_json:JSON.stringify({event_id:'r/0',type:'receipt'}),event_sha256:'a'.repeat(64)};
 const t=evidenceTransport(()=>{calls++;clock=2001;return {status:201,body:JSON.stringify({ack:{durable:true,event_id:'r/0',event_sha256:e.event_sha256}})};},'https://offline.invalid','SYNTHETIC',()=>clock);
 assert.throws(()=>t.persist(e),/durable_ack_missing/);assert.equal(calls,1);assert.equal(t.shouldStop(),true);
});
test('failed receipt persistence prevents every Kafka commit and remains incomplete',()=>{
 const w=world({sinkThrowType:'receipt'}),r=runNativeTenantFixture(plan,w.deps);incomplete(r);
 assert.equal(w.commits.length,0);assert.ok(r.unpersisted.some(e=>e.type==='receipt'));
 assert.equal(r.events.filter(e=>e.type==='commit').length,0);
});
