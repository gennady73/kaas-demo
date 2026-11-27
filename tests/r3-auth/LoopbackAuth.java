// Fixture only. Never included in the runtime ConfigMap or source lock.
import java.net.Socket;
import java.nio.file.Path;
import java.nio.charset.StandardCharsets;
import javax.net.ssl.SSLSocket;
class LoopbackAuth {
  public static void main(String[] args) throws Exception {
    String outcome;
    byte[] bytes = System.in.readNBytes(4097);
    char[] password = new String(bytes, StandardCharsets.UTF_8).toCharArray();
    java.util.Arrays.fill(bytes, (byte) 0);
    try (Socket raw = new Socket("127.0.0.1", Integer.parseInt(args[0]));
         SSLSocket tls = (SSLSocket) AuthMetadataProbe.trustContext(Path.of(args[1])).getSocketFactory()
             .createSocket(raw, args[2], Integer.parseInt(args[0]), true)) {
      outcome = AuthMetadataProbe.observeSocket(tls, password);
    } catch (Throwable error) { outcome = AuthMetadataProbe.safeOutcome(error); }
    finally { java.util.Arrays.fill(password, '\0'); }
    System.out.println(outcome);
  }
}
