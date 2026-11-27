// Metadata-only AUTH candidate. Compilation does not authorize execution.
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.InputStream;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.net.SocketTimeoutException;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.KeyStore;
import java.security.cert.CertificateFactory;
import java.util.Arrays;
import java.util.List;
import javax.net.ssl.SSLContext;
import javax.net.ssl.SSLException;
import javax.net.ssl.SSLParameters;
import javax.net.ssl.SSLSocket;
import javax.net.ssl.TrustManagerFactory;
import javax.security.auth.callback.NameCallback;
import javax.security.auth.callback.PasswordCallback;
import javax.security.auth.callback.UnsupportedCallbackException;
import javax.security.sasl.SaslException;
import org.apache.kafka.common.message.MetadataRequestData;
import org.apache.kafka.common.message.SaslAuthenticateRequestData;
import org.apache.kafka.common.message.SaslHandshakeRequestData;
import org.apache.kafka.common.protocol.Errors;
import org.apache.kafka.common.requests.AbstractRequest;
import org.apache.kafka.common.requests.AbstractResponse;
import org.apache.kafka.common.requests.MetadataRequest;
import org.apache.kafka.common.requests.MetadataResponse;
import org.apache.kafka.common.requests.RequestHeader;
import org.apache.kafka.common.requests.SaslAuthenticateRequest;
import org.apache.kafka.common.requests.SaslAuthenticateResponse;
import org.apache.kafka.common.requests.SaslHandshakeRequest;
import org.apache.kafka.common.requests.SaslHandshakeResponse;
import org.apache.kafka.common.security.scram.internals.ScramMechanism;
import org.apache.kafka.common.security.scram.internals.ScramMessages.ServerFirstMessage;
import org.apache.kafka.common.security.scram.internals.ScramSaslClient;
import org.apache.kafka.common.utils.AppInfoParser;

class AuthMetadataProbe {
  static final String HOST = "kaas-dev-kafka-bootstrap.kaas-kafka.svc";
  static final String PRINCIPAL = "kaas-sbx-a-producer";
  static final String TOPIC = "kaas-sbx-a-events";
  static final String MECHANISM = "SCRAM-SHA-512";
  static final Path CA = Path.of("/credentials/cluster-ca/ca.crt");
  static final int MAX_FRAME = 1048576;

  static final class InvalidProtocol extends Exception {
    private static final long serialVersionUID = 1L;
  }
  static String quote(String s) {
    return "\"" + s.replace("\\", "\\\\").replace("\"", "\\\"") + "\"";
  }
  static SSLContext trustContext() throws Exception { return trustContext(CA); }
  static SSLContext trustContext(Path ca) throws Exception {
    KeyStore trust = KeyStore.getInstance(KeyStore.getDefaultType());
    trust.load(null, null);
    int count = 0;
    try (InputStream input = Files.newInputStream(ca)) {
      for (java.security.cert.Certificate certificate : CertificateFactory.getInstance("X.509").generateCertificates(input))
        trust.setCertificateEntry("ca-" + count++, certificate);
    }
    if (count == 0) throw new InvalidProtocol();
    TrustManagerFactory managers = TrustManagerFactory.getInstance(TrustManagerFactory.getDefaultAlgorithm());
    managers.init(trust);
    SSLContext context = SSLContext.getInstance("TLS");
    context.init(null, managers.getTrustManagers(), null);
    return context;
  }
  static final class Wire {
    final DataInputStream input;
    final DataOutputStream output;
    int correlation = 0;
    Wire(SSLSocket socket) throws Exception {
      input = new DataInputStream(socket.getInputStream());
      output = new DataOutputStream(socket.getOutputStream());
    }
    AbstractResponse exchange(AbstractRequest request) throws Exception {
      if (++correlation > 4) throw new InvalidProtocol();
      RequestHeader header = new RequestHeader(request.apiKey(), request.version(), "kaas-r3-auth-metadata", correlation);
      ByteBuffer encoded = request.serializeWithHeader(header);
      if (encoded.remaining() <= 0 || encoded.remaining() > MAX_FRAME) throw new InvalidProtocol();
      byte[] body = new byte[encoded.remaining()];
      encoded.get(body);
      try {
        output.writeInt(body.length);
        output.write(body);
        output.flush();
      } finally { Arrays.fill(body, (byte) 0); }
      int size = input.readInt();
      if (size < 4 || size > MAX_FRAME) throw new InvalidProtocol();
      byte[] response = input.readNBytes(size);
      if (response.length != size) throw new InvalidProtocol();
      try {
        ByteBuffer buffer = ByteBuffer.wrap(response);
        // Pinned SDK verifies response correlation against this exact request.
        AbstractResponse parsed = AbstractResponse.parseResponse(buffer, header);
        if (buffer.hasRemaining()) throw new InvalidProtocol();
        return parsed;
      } finally { Arrays.fill(response, (byte) 0); }
    }
    SaslAuthenticateResponse authenticate(byte[] token) throws Exception {
      if (token == null || token.length > 16384) throw new InvalidProtocol();
      try {
        return (SaslAuthenticateResponse) exchange(new SaslAuthenticateRequest(
            new SaslAuthenticateRequestData().setAuthBytes(token), (short) 1));
      } finally { Arrays.fill(token, (byte) 0); }
    }
  }
  static String observe(char[] password) throws Exception {
    SSLContext context = trustContext();
    try (Socket raw = new Socket()) {
      raw.connect(new InetSocketAddress(HOST, 9093), 5000);
      try (SSLSocket socket = (SSLSocket) context.getSocketFactory().createSocket(raw, HOST, 9093, true)) {
        return observeSocket(socket, password);
      }
    }
  }
  // Package-private transport boundary permits loopback fixtures without making
  // the deployed main endpoint, trust path or profile configurable.
  static String observeSocket(SSLSocket socket, char[] password) throws Exception {
    ScramSaslClient scram = new ScramSaslClient(ScramMechanism.SCRAM_SHA_512, callbacks -> {
      for (javax.security.auth.callback.Callback callback : callbacks) {
        if (callback instanceof NameCallback) ((NameCallback) callback).setName(PRINCIPAL);
        else if (callback instanceof PasswordCallback) ((PasswordCallback) callback).setPassword(password);
        else throw new UnsupportedCallbackException(callback);
      }
    });
    try {
        socket.setSoTimeout(5000);
        SSLParameters parameters = socket.getSSLParameters();
        parameters.setEndpointIdentificationAlgorithm("HTTPS");
        socket.setSSLParameters(parameters);
        socket.startHandshake();
        Wire wire = new Wire(socket);
        SaslHandshakeResponse handshake = (SaslHandshakeResponse) wire.exchange(new SaslHandshakeRequest(
            new SaslHandshakeRequestData().setMechanism(MECHANISM), (short) 1));
        if (handshake.error() != Errors.NONE || !handshake.enabledMechanisms().contains(MECHANISM))
          return "OTHER_AUTHENTICATION_FAILURE";
        SaslAuthenticateResponse first = wire.authenticate(scram.evaluateChallenge(new byte[0]));
        if (first.error() != Errors.NONE) return "LOCAL_OR_UNPROVEN_SASL_FAILURE";
        byte[] challenge = first.saslAuthBytes();
        if (challenge == null || challenge.length == 0 || challenge.length > 16384) throw new InvalidProtocol();
        int iterations = new ServerFirstMessage(challenge).iterations();
        // Bound broker-controlled proof work before evaluating the challenge.
        if (iterations < 4096 || iterations > 65536) throw new InvalidProtocol();
        byte[] proof = scram.evaluateChallenge(challenge);
        SaslAuthenticateResponse last = wire.authenticate(proof);
        // Only a parsed, correlated response on verified TLS after client-final
        // may establish broker rejection. Never inspect error text or stacks.
        if (last.error() == Errors.SASL_AUTHENTICATION_FAILED) return "BROKER_SASL_REJECTED";
        if (last.error() != Errors.NONE) return "OTHER_AUTHENTICATION_FAILURE";
        byte[] serverFinal = last.saslAuthBytes();
        if (serverFinal == null || serverFinal.length == 0 || serverFinal.length > 16384) throw new InvalidProtocol();
        scram.evaluateChallenge(serverFinal); // Verify server signature for positives.
        if (!scram.isComplete()) throw new InvalidProtocol();
        MetadataResponse metadata = (MetadataResponse) wire.exchange(new MetadataRequest(
            new MetadataRequestData().setTopics(MetadataRequest.convertToMetadataRequestTopic(List.of(TOPIC)))
                .setAllowAutoTopicCreation(false), (short) 4));
        if (metadata.data().topics().size() != 1) return "METADATA_MISMATCH";
        var topic = metadata.data().topics().iterator().next();
        if (topic.errorCode() == Errors.TOPIC_AUTHORIZATION_FAILED.code()) return "AUTHORIZATION_FAILURE";
        if (!TOPIC.equals(topic.name()) || topic.errorCode() != 0 || topic.partitions().isEmpty())
          return "METADATA_MISMATCH";
        for (var partition : topic.partitions())
          if (partition.errorCode() != 0 || partition.leaderId() < 0) return "METADATA_MISMATCH";
        return "OWN_METADATA_OK";
    } finally { scram.dispose(); }
  }
  static String safeOutcome(Throwable error) {
    if (error instanceof IllegalArgumentException) return "INPUT_INVALID";
    if (error instanceof SSLException) return "TLS_FAILURE";
    if (error instanceof SocketTimeoutException) return "TIMEOUT";
    if (error instanceof SaslException) return "LOCAL_OR_UNPROVEN_SASL_FAILURE";
    return "UNCLASSIFIED_FAILURE";
  }
  public static void main(String[] args) {
    String phase = "invalid", outcome = "INPUT_INVALID";
    int code = 21;
    char[] password = null;
    try {
      if (args.length != 2 || !List.of("positive_before", "negative", "positive_after").contains(args[0]))
        throw new IllegalArgumentException();
      phase = args[0];
      if (!"4.2.1.redhat-00003".equals(args[1]) || !args[1].equals(AppInfoParser.getVersion()))
        throw new IllegalArgumentException();
      byte[] supplied;
      try (InputStream input = System.in) { supplied = input.readNBytes(4097); }
      try {
        if (supplied.length == 0 || supplied.length > 4096) throw new IllegalArgumentException();
        for (byte value : supplied) if (value == 0 || value == 10 || value == 13) throw new IllegalArgumentException();
        password = StandardCharsets.UTF_8.newDecoder().decode(ByteBuffer.wrap(supplied)).toString().toCharArray();
      } finally { Arrays.fill(supplied, (byte) 0); }
      outcome = observe(password);
      code = outcome.equals("OWN_METADATA_OK") ? 0 : (outcome.equals("BROKER_SASL_REJECTED") ? 20 : 21);
    } catch (Throwable error) { outcome = safeOutcome(error);
    } finally { if (password != null) Arrays.fill(password, '\0'); }
    System.out.println("{\"schema\":\"kaas-r3-auth-phase/v1\",\"phase\":" + quote(phase)
        + ",\"outcome\":" + quote(outcome) + "}");
    System.exit(code);
  }
}
