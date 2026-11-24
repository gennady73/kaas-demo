// Read-only guard: refuse to start if any proposed consumer group already exists.
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.*;
import org.apache.kafka.clients.admin.*;
import org.apache.kafka.common.errors.GroupIdNotFoundException;
class InitialGroups {
 static String quote(String s){return "\""+s.replace("\\","\\\\").replace("\"","\\\"")+"\"";}
 public static void main(String[] groups)throws Exception{
  Properties p=new Properties();p.put("bootstrap.servers","kaas-dev-kafka-bootstrap.kaas-kafka.svc:9093");p.put("security.protocol","SASL_SSL");p.put("sasl.mechanism","SCRAM-SHA-512");
  p.put("sasl.jaas.config","org.apache.kafka.common.security.scram.ScramLoginModule required username=\"kaas-smoke-client\" password="+quote(Files.readString(Path.of("/credentials/password")).strip())+";");
  p.put("ssl.truststore.type","PEM");p.put("ssl.truststore.certificates",Files.readString(Path.of("/credentials/ca.crt")));p.put("ssl.endpoint.identification.algorithm","https");p.put("default.api.timeout.ms","5000");p.put("request.timeout.ms","3000");
  try(Admin admin=Admin.create(p)){
   for(String group:groups){
    try{admin.describeConsumerGroups(List.of(group)).describedGroups().get(group).get(6,TimeUnit.SECONDS);throw new IllegalStateException("Consumer group already exists; use a fresh run ID");}
    catch(ExecutionException e){if(!(e.getCause() instanceof GroupIdNotFoundException))throw new IllegalStateException("Initial group inspection failed: "+e.getCause().getClass().getSimpleName());}
    System.out.println("INITIAL_GROUP_ABSENT "+group);
   }
  }
 }
}
