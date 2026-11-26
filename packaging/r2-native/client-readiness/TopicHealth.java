import java.util.*;
import java.nio.file.*;
import java.time.*;
import java.util.concurrent.*;
import org.apache.kafka.clients.admin.*;

class TopicHealth {
  static String q(String s) { return "\"" + s.replace("\\", "\\\\").replace("\"", "\\\"") + "\""; }
  public static void main(String[] args) {
    try {
      for (String tenant : List.of("a", "b")) {
        String user = "kaas-sbx-" + tenant + "-producer";
        String password = Files.readString(Path.of("/credentials/" + user + "/password"));
        if (password.indexOf('\n') >= 0 || password.indexOf('\r') >= 0 || password.indexOf(0) >= 0) throw new IllegalStateException();
        Properties p = new Properties();
        p.put("bootstrap.servers", "kaas-dev-kafka-bootstrap.kaas-kafka.svc:9093");
        p.put("security.protocol", "SASL_SSL"); p.put("sasl.mechanism", "SCRAM-SHA-512");
        p.put("sasl.jaas.config", "org.apache.kafka.common.security.scram.ScramLoginModule required username=" + q(user) + " password=" + q(password) + ";");
        p.put("ssl.truststore.type", "PEM"); p.put("ssl.truststore.certificates", Files.readString(Path.of("/credentials/cluster-ca/ca.crt")));
        p.put("ssl.endpoint.identification.algorithm", "https");
        p.put("default.api.timeout.ms", "10000"); p.put("request.timeout.ms", "5000"); p.put("retries", "0");
        try (Admin admin = Admin.create(p)) {
          var topics = admin.describeTopics(List.of("kaas-sbx-" + tenant + "-events", "kaas-sbx-" + tenant + "-audit")).allTopicNames().get(12, TimeUnit.SECONDS);
          for (var entry : topics.entrySet()) for (var part : entry.getValue().partitions()) {
            var leader = part.leader();
            System.out.println("R2_HEALTH {\"topic\":" + q(entry.getKey()) + ",\"partition\":" + part.partition() + ",\"leader\":" + (leader == null ? -1 : leader.id()) + ",\"leader_host\":" + (leader == null ? "null" : q(leader.host())) + ",\"replicas\":" + part.replicas().stream().map(n -> n.id()).toList() + ",\"ISR\":" + part.isr().stream().map(n -> n.id()).toList() + ",\"observed_UTC\":" + q(Instant.now().toString()) + "}");
          }
        }
      }
    } catch (Throwable error) {
      System.out.println("R2_HEALTH {\"status\":\"METADATA_CHECK_FAILED\"}");
      System.exit(2);
    }
  }
}
