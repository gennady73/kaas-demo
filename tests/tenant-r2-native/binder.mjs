// Injectable binding: local checks supply synthetic result envelopes, never clients.
import {require} from './native-policy.mjs';
export function bindNative(native,transport,plan,gate,sha,sleep){
 const errors=new WeakMap();
 function call(result){
  if(!result||result.ok!==true){
   const e=new Error('native_operation_failed');
   if(result?.mapping_id==='KAAS_R2_CONFLUENT_2_14_V1'&&Number.isInteger(result.native_code))errors.set(e,{typed:result.native_code!==0,mapping_id:result.mapping_id,category:result.category,stage:result.stage});
   throw e;
  }
  return result;
 }
 const paths=new Set(plan.bindings.map(b=>b.password_path));
 const safe=call(native.start(gate.job_start_unix_ms));
 require(safe.mapping_id==='KAAS_R2_CONFLUENT_2_14_V1','native_mapping');
 function client(o,producer){
  const b=plan.bindings.find(b=>b.id===o.binding_id);
  require(b&&b.principal===o.principal&&b.password_path===o.password_path,'binding');
  const id=call(producer?native.openProducer(b.principal,o.topic):native.openConsumer(b.principal,o.topic,o.group)).handle;
  const probe=()=>{const r=call(native.probeState(id));return {broker_confirmed:r.broker_confirmed,group_joined:r.group_joined,forbidden_assignment:r.forbidden_assignment};};
  return producer?{
   produce({messages}){require(messages.length===1,'one_send');const m=messages[0];require(m.topic===o.topic,'topic_binding');call(native.produce(id,m.key,m.value));},
   close(){call(native.close(id));}
  }:{
   position(){return call(native.position(id)).position;},
   consume({limit}){require(limit===1,'one_poll');const r=call(native.consume(id));return r.messages;},
   probeState:probe,
   commitOffsets(){call(native.commit(id));},
   close(){call(native.close(id));}
  };
 }
 return {
  mode:'NATIVE_KAFKA_V1',runtimeAuthorized:true,reviewedPlanHash:gate.plan_sha256,sha256:sha,
  jobStartMs:0,now:()=>native.now(),sleep,
  debugConfigurationSafe:()=>true,capabilities:{manual_commit_only:true,no_commit_on_close:true},
  readCredential(path){require(paths.has(path),'credential_binding');return 'NATIVE_FILE_BINDING_ONLY';},
  readPublicCA(path){require(path==='/credentials/cluster-ca/ca.crt','CA_binding');return 'NATIVE_PUBLIC_CA_FILE_ONLY';},
  makeProducer:o=>client(o,true),makeConsumer:o=>client(o,false),
  normalizeNativeError:e=>errors.get(e),
  persist:envelope=>transport.persist(envelope),shouldStop:()=>transport.shouldStop(),
  groupState(group,topic){
   require(gate.exclusive_fixture_groups.includes(group),'fixture_ownership');
   const r=call(native.snapshot(topic,group));
   require(r.log_start_offset<=r.log_end_offset&&(r.committed_offset===null?r.log_start_offset===0:r.committed_offset>=r.log_start_offset&&r.committed_offset<=r.log_end_offset),'retained_baseline');
   return {fixture_only:true,exclusive:true,members:r.members,membership_observed:r.membership_observed,committed_offset:r.committed_offset,log_end_offset:r.log_end_offset};
  }
 };
}
