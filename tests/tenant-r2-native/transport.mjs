import {require} from './native-policy.mjs';
// Exact same bytes on a transport retry; no automatic retry in this candidate.
export function evidenceTransport(post,origin,token,now){
 let stopped=false;
 return {
  shouldStop:()=>stopped,
  persist(envelope){
   require(!stopped,'evidence_stopped');
   const start=now();
   let response;
   try{response=post(origin+'/v1/events',JSON.stringify(envelope),{headers:{'Content-Type':'application/json',Authorization:'Bearer '+token},timeout:'1500ms',redirects:0,tags:{name:'tenant-evidence'}});}
   catch(_){stopped=true;throw new Error('evidence_transport_failed');}
   let obj;try{obj=JSON.parse(response.body);}catch(_){stopped=true;throw new Error('evidence_response_invalid');}
   if(now()-start>2000||![200,201].includes(response.status)||obj?.ack?.durable!==true||obj.ack.event_sha256!==envelope.event_sha256){stopped=true;throw new Error('durable_ack_missing');}
   return {status:response.status,ack:obj.ack};
  }
 };
}
