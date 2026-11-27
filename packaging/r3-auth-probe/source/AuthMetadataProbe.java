// Metadata-only AUTH candidate. Compilation does not authorize execution.
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.List;
import java.util.Map;
import java.util.Properties;
import java.util.concurrent.TimeUnit;
import javax.net.ssl.SSLException;
import org.apache.kafka.clients.admin.Admin;
import org.apache.kafka.clients.admin.DescribeTopicsOptions;
import org.apache.kafka.clients.admin.TopicDescription;
import org.apache.kafka.common.errors.AuthenticationException;
import org.apache.kafka.common.errors.AuthorizationException;
import org.apache.kafka.common.errors.SaslAuthenticationException;
import org.apache.kafka.common.utils.AppInfoParser;

class AuthMetadataProbe {
  static final String ENDPOINT = "kaas-dev-kafka-bootstrap.kaas-kafka.svc:9093";
  static final String PRINCIPAL = "kaas-sbx-a-producer";
  static final String TOPIC = "kaas-sbx-a-events";
  static final Path CA = Path.of("/credentials/cluster-ca/ca.crt");

  static String quote(String s) {
    return "\"" + s.replace("\\", "\\\\").replace("\"", "\\\"") + "\"";
  }
  static String safeOutcome(Throwable error) {
    // Never emit an exception message, class dump, stack trace or configuration.
    // Exact downstream ApiException.fillInStackTrace() is a no-op. The
    // exception type alone cannot distinguish local errors from broker replies.
    // Keep this candidate nonpassing until a reviewed origin channel exists.
    boolean sasl = false;
    int depth = 0;
    for (Throwable t = error; t != null && depth++ < 16; t = t.getCause()) {
      if (t instanceof SSLException) return "TLS_FAILURE";
      if (t instanceof SaslAuthenticationException) {
        sasl = true;

      }
      if (t instanceof AuthorizationException) return "AUTHORIZATION_FAILURE";
      if (t instanceof java.util.concurrent.TimeoutException || t instanceof org.apache.kafka.common.errors.TimeoutException)
        return "TIMEOUT";
      if (t instanceof AuthenticationException && !(t instanceof SaslAuthenticationException))
        return "OTHER_AUTHENTICATION_FAILURE";
      if (t.getCause() == t) break;
    }
    return sasl ? "LOCAL_OR_UNPROVEN_SASL_FAILURE" : "UNCLASSIFIED_FAILURE";
  }
  public static void main(String[] args) {
    String phase = "invalid";
    String outcome = "INPUT_INVALID";
    Admin admin = null;
    int code = 21;
    try {
      if (args.length != 2 || !List.of("positive_before", "negative", "positive_after").contains(args[0]))
        throw new IllegalArgumentException();
      phase = args[0];
      // Version equality is an independent future arming input; no family-only
      // fallback or automatic allowance for an unreviewed downstream build.
      if (!"4.2.1.redhat-00003".equals(args[1]) || !args[1].equals(AppInfoParser.getVersion()))
        throw new IllegalArgumentException();
      byte[] supplied;
      try (InputStream input = System.in) { supplied = input.readNBytes(4097); }
      if (supplied.length == 0 || supplied.length > 4096) throw new IllegalArgumentException();
      String password = new String(supplied, StandardCharsets.UTF_8);
      java.util.Arrays.fill(supplied, (byte) 0);
      if (password.indexOf('\n') >= 0 || password.indexOf('\r') >= 0 || password.indexOf(0) >= 0)
        throw new IllegalArgumentException();
      Properties config = new Properties();
      config.put("bootstrap.servers", ENDPOINT);
      config.put("security.protocol", "SASL_SSL");
      config.put("sasl.mechanism", "SCRAM-SHA-512");
      config.put("sasl.jaas.config", "org.apache.kafka.common.security.scram.ScramLoginModule required username="
          + quote(PRINCIPAL) + " password=" + quote(password) + ";");
      config.put("ssl.truststore.type", "PEM");
      config.put("ssl.truststore.certificates", Files.readString(CA));
      config.put("ssl.endpoint.identification.algorithm", "https");
      config.put("client.id", "kaas-r3-auth-metadata"); // Identical for all phases.
      config.put("enable.metrics.push", "false");
      config.put("default.api.timeout.ms", "8000");
      config.put("request.timeout.ms", "5000");
      config.put("socket.connection.setup.timeout.ms", "5000");
      config.put("socket.connection.setup.timeout.max.ms", "5000");
      config.put("retries", "0");
      config.put("reconnect.backoff.ms", "60000");
      config.put("reconnect.backoff.max.ms", "60000");
      admin = Admin.create(config);
      // One exact-topic read-only operation. No listing, produce, consume,
      // group join, offset mutation or topic/configuration creation API exists.
      Map<String, TopicDescription> topics = admin.describeTopics(List.of(TOPIC),
          new DescribeTopicsOptions().timeoutMs(8000)).allTopicNames().get(10, TimeUnit.SECONDS);
      if (topics.size() != 1 || !topics.containsKey(TOPIC) || topics.get(TOPIC).partitions().isEmpty())
        outcome = "METADATA_MISMATCH";
      else { outcome = "OWN_METADATA_OK"; code = 0; }
    } catch (IllegalArgumentException error) {
      outcome = "INPUT_INVALID";
    } catch (Throwable error) {
      outcome = safeOutcome(error);
      if (outcome.equals("BROKER_SASL_REJECTED")) code = 20;
    } finally {
      if (admin != null) {
        try { admin.close(Duration.ofSeconds(2)); }
        catch (Throwable ignored) { outcome = "CLOSE_FAILED"; code = 21; }
      }
    }
    // Fixed schema and whitelist only; SDK stdout/stderr is bounded and discarded
    // by the parent unless stdout is exactly this one reviewed structured row.
    System.out.println("{\"schema\":\"kaas-r3-auth-phase/v1\",\"phase\":" + quote(phase)
        + ",\"outcome\":" + quote(outcome) + "}");
    System.exit(code);
  }
}
