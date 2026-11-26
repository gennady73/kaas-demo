// Injectable binding: local checks supply synthetic result envelopes, never clients.
import {require,validatePlan} from './native-policy.mjs';
export function bindNative(native,transport,plan,gate,sha,sleep){
 validatePlan(plan,{runtimeAuthorized:true,sha256:sha,reviewedPlanHash:gate.plan_sha256});
 const errors=new WeakMap();
 function call(result){
  if(!result||result.ok!==true){
   const e=new Error('native_operation_failed');
   const categories={29:'topic_authorization_denied',30:'group_authorization_denied',31:'cluster_authorization_denied'};
   if(result?.mapping_id==='KAAS_R2_CONFLUENT_2_14_V1'&&Number.isInteger(result.native_code)&&categories[result.native_code]&&['produce','consume','group_join'].includes(result.stage))errors.set(e,{typed:true,mapping_id:'KAAS_R2_CONFLUENT_2_14_V1',category:categories[result.native_code],stage:result.stage});
   throw e;
  }
  return result;
 }
 function invoke(method,...args){try{return call(native[method](...args));}catch(e){if(e&&typeof e==='object'&&errors.has(e))throw e;throw new Error('native_operation_failed');}}
 const paths=new Set(plan.bindings.map(b=>b.password_path));
 const safe=invoke('identity');
 require(safe.mapping_id==='KAAS_R2_CONFLUENT_2_14_V1'&&safe.binary_sha256===gate.binary_sha256&&/^[a-f0-9]{64}$/.test(gate.binary_sha256||''),'native_mapping');
 invoke('start',gate.job_start_unix_ms);
 function client(o,producer){
  const b=plan.bindings.find(b=>b.id===o.binding_id);
  require(b&&b.principal===o.principal&&b.password_path===o.password_path,'binding');
  const permitted=plan.positive.some(p=>p.topic===o.topic&&(producer?p.producer===b.id:p.consumer===b.id&&p.group===o.group))||plan.negative.some(n=>n.binding===b.id&&n.topic===o.topic&&n.operation===(producer?'produce':'consume')&&(producer||n.group===o.group));
  require(permitted,'resource_binding');
  const id=(producer?invoke('openProducer',b.principal,o.topic):invoke('openConsumer',b.principal,o.topic,o.group)).handle;
  const probe=()=>{const r=invoke('probeState',id);return {broker_confirmed:r.broker_confirmed,group_joined:r.group_joined,forbidden_assignment:r.forbidden_assignment};};
  return producer?{
   produce({messages}){require(messages.length===1,'one_send');const m=messages[0];require(m.topic===o.topic,'topic_binding');const r=[...plan.records,...plan.negative.filter(n=>n.record).map(n=>n.record)].find(r=>r.id===m.key&&r.topic===o.topic);require(r&&typeof m.value==='string'&&m.value.length===1000&&sha(m.value)===r.checksum,'record_binding');invoke('produce',id,m.key,m.value);},
   close(){invoke('close',id);}
  }:{
   position(){return invoke('position',id).position;},
   consume({limit}){require(limit===1,'one_poll');const r=invoke('consume',id);return r.messages;},
   probeState:probe,
   commitOffsets(){invoke('commit',id);},
   close(){invoke('close',id);}
  };
 }
 return {
  mode:'NATIVE_KAFKA_V1',execution_context:'NATIVE_BOUNDARY',runtimeAuthorized:true,reviewedPlanHash:gate.plan_sha256,sha256:sha,
  jobStartMs:0,now:()=>native.now(),sleep,
  debugConfigurationSafe:()=>true,capabilities:{manual_commit_only:true,no_commit_on_close:true},
  readCredential(path){require(paths.has(path),'credential_binding');return 'NATIVE_FILE_BINDING_ONLY';},
  readPublicCA(path){require(path==='/credentials/cluster-ca/ca.crt','CA_binding');return 'NATIVE_PUBLIC_CA_FILE_ONLY';},
  makeProducer:o=>client(o,true),makeConsumer:o=>client(o,false),
  normalizeNativeError:e=>errors.get(e),
  persist:envelope=>transport.persist(envelope),shouldStop:()=>transport.shouldStop(),
  groupState(group,topic){
   require(gate.exclusive_fixture_groups.includes(group),'fixture_ownership');
   require(topic===group.replace(/-group$/,''),'observation_topic_binding');
   const r=invoke('snapshot',topic,group);
   require(Number.isSafeInteger(r.log_start_offset)&&r.log_start_offset>=0&&Number.isSafeInteger(r.log_end_offset)&&Number.isSafeInteger(r.members)&&r.members>=0&&(r.committed_offset===null||Number.isSafeInteger(r.committed_offset))&&r.membership_observed===true,'group_state_shape');
   require(r.log_start_offset<=r.log_end_offset&&(r.committed_offset===null?r.log_start_offset===0:r.committed_offset>=r.log_start_offset&&r.committed_offset<=r.log_end_offset),'retained_baseline');
   return {fixture_only:true,exclusive:true,members:r.members,membership_observed:r.membership_observed,committed_offset:r.committed_offset,log_end_offset:r.log_end_offset};
  }
 };
}
