// Bounded functional fallback using the deployed Kafka image's own Java client.
// No topic, user, schema or broker administration. Java 21 source-file launcher.
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Duration;
import java.util.*;
import java.util.concurrent.TimeUnit;
import org.apache.kafka.clients.producer.*;
import org.apache.kafka.clients.consumer.*;
import org.apache.kafka.common.serialization.*;

class Smoke {
 static final long boot=System.nanoTime();
 static String run,password; static int errors=0,duplicates=0,foreign=0;
 static final Map<String,Case> expected=new LinkedHashMap<>();
 static final Map<String,RecordMetadata> acked=new LinkedHashMap<>();
 static final Set<String> seen=new HashSet<>();
 record Case(String topic,int seq,String id,String group,int size,String hash){}
 static long elapsed(){return (System.nanoTime()-boot)/1_000_000;}
 static String quote(String s){return "\""+s.replace("\\","\\\\").replace("\"","\\\"").replace("\n","\\n").replace("\r","\\r")+"\"";}
 static void event(String type,String fields){System.out.println("SMOKE_EVENT {\"type\":"+quote(type)+",\"run_id\":"+quote(run)+",\"at_ms\":"+System.currentTimeMillis()+(fields.isEmpty()?"":","+fields)+"}");System.out.flush();}
 static String hash(byte[] value)throws Exception{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(value));}
 static byte[] payload(Case c,int seed)throws Exception{
  byte[] out=new byte[c.size];for(int pos=0,block=0;pos<out.length;block++){
   byte[] chunk=hash((seed+":"+c.topic+":"+c.seq+":"+block).getBytes(StandardCharsets.US_ASCII)).getBytes(StandardCharsets.US_ASCII);
   int n=Math.min(chunk.length,out.length-pos);System.arraycopy(chunk,0,out,pos,n);pos+=n;
  }return out;
 }
 static void read(String topic,KafkaConsumer<String,byte[]> consumer)throws Exception{
  for(ConsumerRecord<String,byte[]> r:consumer.poll(Duration.ofMillis(250))){
   Case c=expected.get(r.key());if(c==null){foreign++;continue;}
   String h=hash(r.value());RecordMetadata ack=acked.get(c.id);
   boolean valid=c.topic.equals(r.topic())&&c.size==r.value().length&&c.hash.equals(h);
   // During the initial poll there are no records from this unique run.
   if(ack!=null)valid=valid&&ack.partition()==r.partition()&&ack.offset()==r.offset();
   event("received","\"id\":"+quote(c.id)+",\"topic\":"+quote(r.topic())+",\"group\":"+quote(c.group)+",\"partition\":"+r.partition()+",\"offset\":"+r.offset()+",\"value_bytes\":"+r.value().length+",\"sha256\":"+quote(h)+",\"valid\":"+valid);
   if(!valid)errors++;else if(!seen.add(c.id))duplicates++;
  }
 }
 public static void main(String[] args)throws Exception{
  run=args[0];int seed=Integer.parseInt(args[1]);
  for(String line:Files.readAllLines(Path.of("/script/cases.tsv"))){String[] f=line.split("\t");Case c=new Case(f[0],Integer.parseInt(f[1]),f[2],f[3],Integer.parseInt(f[4]),f[5]);expected.put(c.id,c);}
  if(expected.size()!=16)throw new IllegalArgumentException("exactly 16 cases required");
  password=Files.readString(Path.of("/credentials/password")).strip();
  Properties common=new Properties();common.put("bootstrap.servers","kaas-dev-kafka-bootstrap.kaas-kafka.svc:9093");common.put("security.protocol","SASL_SSL");common.put("sasl.mechanism","SCRAM-SHA-512");
  common.put("sasl.jaas.config","org.apache.kafka.common.security.scram.ScramLoginModule required username=\"kaas-smoke-client\" password="+quote(password)+";");
  common.put("ssl.truststore.type","PEM");common.put("ssl.truststore.certificates",Files.readString(Path.of("/credentials/ca.crt")));common.put("ssl.endpoint.identification.algorithm","https");
  Map<String,KafkaProducer<String,byte[]>> producers=new LinkedHashMap<>();Map<String,KafkaConsumer<String,byte[]>> consumers=new LinkedHashMap<>();
  event("start","\"record_count\":16,\"original_value_bytes\":12849152,\"acks\":\"all\",\"application_retries\":0,\"native_retries\":1,\"hard_job_deadline_seconds\":300,\"producer_stop_seconds\":180,\"consumer_stop_seconds\":265");
  try{
   for(Case c:expected.values())if(!consumers.containsKey(c.topic)){
    Properties p=new Properties();p.putAll(common);p.put("client.id",run+"-producer-"+c.topic);p.put("key.serializer",StringSerializer.class.getName());p.put("value.serializer",ByteArraySerializer.class.getName());p.put("acks","all");p.put("enable.idempotence","true");p.put("retries","1");p.put("max.in.flight.requests.per.connection","1");p.put("max.request.size","3145728");p.put("batch.size","3145728");p.put("compression.type","none");p.put("linger.ms","0");p.put("request.timeout.ms","5000");p.put("delivery.timeout.ms","10000");p.put("max.block.ms","10000");producers.put(c.topic,new KafkaProducer<>(p));
    p=new Properties();p.putAll(common);p.put("client.id",run+"-consumer-"+c.topic);p.put("key.deserializer",StringDeserializer.class.getName());p.put("value.deserializer",ByteArrayDeserializer.class.getName());p.put("group.id",c.group);p.put("auto.offset.reset","earliest");p.put("enable.auto.commit","false");p.put("fetch.max.bytes","4194304");p.put("max.partition.fetch.bytes","4194304");p.put("default.api.timeout.ms","10000");p.put("request.timeout.ms","10000");p.put("session.timeout.ms","10000");p.put("heartbeat.interval.ms","3000");
    KafkaConsumer<String,byte[]> consumer=new KafkaConsumer<>(p);consumer.subscribe(List.of(c.topic));consumers.put(c.topic,consumer);
   }
   // Poll all consumers until assignments exist, before any send.
   boolean assigned=false;while(!assigned&&elapsed()<30000){assigned=true;for(var e:consumers.entrySet()){read(e.getKey(),e.getValue());assigned&=!e.getValue().assignment().isEmpty();}}
   if(!assigned)throw new IllegalStateException("consumer assignment deadline");
   for(Case c:expected.values()){
    if(elapsed()>=180000)throw new IllegalStateException("producer deadline");byte[] value=payload(c,seed);if(!hash(value).equals(c.hash))throw new IllegalStateException("generated checksum mismatch");
    event("attempt","\"id\":"+quote(c.id)+",\"topic\":"+quote(c.topic)+",\"value_bytes\":"+c.size+",\"sha256\":"+quote(c.hash)+",\"attempt\":1");
    RecordMetadata m=producers.get(c.topic).send(new ProducerRecord<>(c.topic,c.id,value)).get(15,TimeUnit.SECONDS);acked.put(c.id,m);
    event("acknowledged","\"id\":"+quote(c.id)+",\"topic\":"+quote(m.topic())+",\"partition\":"+m.partition()+",\"offset\":"+m.offset()+",\"value_bytes\":"+c.size+",\"sha256\":"+quote(c.hash));
   }
   while(elapsed()<265000){for(var e:consumers.entrySet()){if(elapsed()>=265000)break;read(e.getKey(),e.getValue());}}
   if(seen.size()==16&&errors==0)for(var e:consumers.entrySet()){e.getValue().commitSync(Duration.ofSeconds(3));event("offsets_committed","\"topic\":"+quote(e.getKey()));}
  }catch(Exception e){errors++;event("error","\"detail\":"+quote(e.toString().replace(password,"[REDACTED]")));}
  finally{
   for(var p:producers.values())try{p.close(Duration.ofSeconds(1));}catch(Exception e){errors++;}
   for(var c:consumers.values())try{c.close(Duration.ofSeconds(1));}catch(Exception e){errors++;}
  }
  boolean pass=errors==0&&acked.size()==16&&seen.size()==16&&elapsed()<285000;
  event("end","\"status\":"+quote(pass?"PASS":"FAIL")+",\"acknowledged\":"+acked.size()+",\"unique_deliveries\":"+seen.size()+",\"duplicates\":"+duplicates+",\"foreign_records\":"+foreign+",\"errors\":"+errors+",\"elapsed_ms\":"+elapsed()+",\"clean_shutdown\":true");
  if(!pass)System.exit(1);
 }
}
