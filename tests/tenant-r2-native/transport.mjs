import {require} from './native-policy.mjs';
// At most two HTTP attempts for the SAME exact envelope, inside one 2s reserve.
// A recovered lost ACK never reopens mutation admission or retries Kafka calls.
export function evidenceTransport(post,origin,token,now){
 let stopped=false,broken=false;
 const settlement=new Set(['fixture_stop','client_close','close_skipped','fixture_terminal','send_outcome','commit_uncertain','durable_receipt_ack','not_sent','group_state','group_state_unavailable','negative_state_violation']);
 return {
  shouldStop:()=>stopped||broken,
  persist(envelope){
   let event;try{event=JSON.parse(envelope.event_json);}catch(_){throw new Error('evidence_envelope_invalid');}
   require(!broken&&(!stopped||settlement.has(event.type)),'evidence_stopped');
   const body=JSON.stringify(envelope),start=now();
   for(let attempt=0;attempt<2;attempt++){
    if(now()-start>1200)break;
    try{
     const r=post(origin+'/v1/events',body,{headers:{'Content-Type':'application/json',Authorization:'Bearer '+token},timeout:'700ms',redirects:0,tags:{name:'tenant-evidence'}});
     const obj=JSON.parse(r.body),ack=obj?.ack;
     if(now()-start<=2000&&[200,201].includes(r.status)&&ack?.durable===true&&ack.event_id===event.event_id&&ack.event_sha256===envelope.event_sha256)return {status:r.status,ack:{durable:true,event_id:ack.event_id,event_sha256:ack.event_sha256}};
    }catch(_){/* All raw transport/parse errors remain private. */}
    stopped=true;
   }
   stopped=true;broken=true;throw new Error('durable_ack_missing');
  }
 };
}
