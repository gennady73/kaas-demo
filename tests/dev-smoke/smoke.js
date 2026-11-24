// One bounded functional run. No topic, schema, user, or offset administration.
import {sleep} from 'k6';
import crypto from 'k6/crypto';
import {Counter} from 'k6/metrics';
import {Producer, Consumer, SASL_SCRAM_SHA512, START_OFFSETS_FIRST_OFFSET} from 'k6/x/kafka';
const bootMs=Date.now();
const plan=JSON.parse(open('/script/expected.json'));
const password=open('/credentials/password').trim();
const ca=open('/credentials/ca.crt');
const errors=new Counter('smoke_errors'), acknowledgements=new Counter('smoke_acknowledgements'), deliveries=new Counter('smoke_unique_deliveries');
export const options={scenarios:{smoke:{executor:'shared-iterations',vus:1,iterations:1,maxDuration:'285s',gracefulStop:'0s'}},thresholds:{smoke_errors:['count==0'],smoke_acknowledgements:['count==16'],smoke_unique_deliveries:['count==16']}};
function emit(type,fields={}){console.log('SMOKE_EVENT '+JSON.stringify({type,run_id:plan.run_id,at_ms:Date.now(),...fields}));}
function ascii(value){
 if(typeof value==='string')return value;
 if(value instanceof ArrayBuffer)value=new Uint8Array(value);
 if(!value || typeof value.length!=='number')throw Error('unsupported byte representation');
 const chunks=[];for(let i=0;i<value.length;i+=4096){let s='';for(let j=i;j<Math.min(i+4096,value.length);j++){if(value[j]>127)throw Error('non-ASCII value');s+=String.fromCharCode(value[j]);}chunks.push(s);}return chunks.join('');
}
function payload(r){const chunks=[];for(let n=0;n*64<r.value_bytes;n++)chunks.push(crypto.sha256(`${plan.seed}:${r.topic}:${r.sequence}:${n}`,'hex'));return chunks.join('').slice(0,r.value_bytes);}
export default function(){
 errors.add(0);acknowledgements.add(0);deliveries.add(0);
 const producers={},consumers={},seen={},expected={};let failures=0,acked=0,duplicates=0,foreign=0;
 const security={sasl:{username:'kaas-smoke-client',password,algorithm:SASL_SCRAM_SHA512},tls:{enableTls:true,insecureSkipTlsVerify:false,serverCaPem:ca}};
 const topics=[...new Set(plan.records.map(r=>r.topic))];plan.records.forEach(r=>expected[r.id]=r);
 function bad(phase,detail){failures++;errors.add(1);emit('error',{phase,detail});}
 function read(topic){
  const messages=consumers[topic].consume({limit:1,expectTimeout:true});
  for(const m of messages){
   const id=ascii(m.key),r=expected[id];
   if(!r){foreign++;continue;}
   const value=ascii(m.value),checksum=crypto.sha256(value,'hex');
   const valid=m.topic===r.topic && value.length===r.value_bytes && checksum===r.sha256;
   emit('received',{id,topic:m.topic,group:r.consumer_group,partition:m.partition,offset:m.offset,value_bytes:value.length,sha256:checksum,valid});
   if(!valid)bad('verification','record mismatch');
   else if(seen[id])duplicates++;
   else {seen[id]=true;deliveries.add(1);}
  }
 }
 emit('start',{boot_ms:bootMs,record_count:plan.records.length,original_value_bytes:plan.total_original_value_bytes,acks:-1,application_retries:0,client_stop_seconds:270,hard_job_deadline_seconds:300});
 try{
  for(const topic of topics){
   const r=plan.records.find(r=>r.topic===topic);
   consumers[topic]=new Consumer({...security,brokers:['kaas-dev-kafka-bootstrap.kaas-kafka.svc:9093'],topic,groupId:r.consumer_group,startOffset:START_OFFSETS_FIRST_OFFSET,maxBytes:4194304,maxWait:'250ms',readTimeout:5000000000,sessionTimeout:10000000000,heartbeatInterval:3000000000});
   producers[topic]=new Producer({...security,brokers:['kaas-dev-kafka-bootstrap.kaas-kafka.svc:9093'],topic,requiredAcks:-1,batchSize:1,batchBytes:3145728,batchTimeout:1000000,writeTimeout:10000000000,readTimeout:10000000000,compression:'',autoCreateTopic:false});
  }
  // Activate each fresh group before sending this run's records.
  for(const topic of topics)read(topic);
  for(const r of plan.records){
   if(Date.now()-bootMs>=180000)throw Error('producer phase deadline');
   const value=payload(r);if(value.length!==r.value_bytes || crypto.sha256(value,'hex')!==r.sha256)throw Error('generated value mismatch');
   emit('attempt',{id:r.id,topic:r.topic,value_bytes:r.value_bytes,sha256:r.sha256,attempt:1});
   producers[r.topic].produce({messages:[{topic:r.topic,key:r.id,value}]});
   acked++;acknowledgements.add(1);emit('acknowledged',{id:r.id,topic:r.topic,value_bytes:r.value_bytes,sha256:r.sha256});
  }
  while(Date.now()-bootMs<265000){for(const topic of topics){if(Date.now()-bootMs>=265000)break;read(topic);}sleep(0.05);}
 }catch(e){bad('client',String(e).split('\n')[0].replace(password,'[REDACTED]'));}
 finally{
  for(const topic of topics){try{if(producers[topic])producers[topic].close();}catch(e){bad('producer_close','close failed');}try{if(consumers[topic])consumers[topic].close();}catch(e){bad('consumer_close','close failed');}}
 }
 const unique=Object.keys(seen).length,missing=plan.records.filter(r=>!seen[r.id]).map(r=>r.id);
 const passed=failures===0&&acked===16&&unique===16&&missing.length===0&&Date.now()-bootMs<285000;
 if(!passed)errors.add(1);
 emit('end',{status:passed?'PASS':'FAIL',acknowledged:acked,unique_deliveries:unique,duplicates,foreign_records:foreign,missing,failures,elapsed_ms:Date.now()-bootMs,clean_shutdown:true});
 if(!passed)throw Error('smoke acceptance failed');
}
