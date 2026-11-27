# AUTH offline behavioral regression tests

These tests use only synthetic credentials and local fixtures. They do not run `oc`, contact Kafka/OpenShift/GitHub, modify a runtime profile, start a container, or deploy anything. The TLS broker binds only127.0.0.1; the Java harness connects only127.0.0.1, with the expected service hostname used for TLS identity validation. Restricted environments may need local socket access.

Prerequisites: Python3 with unittest, OpenSSL, JDK17+ and the exact extracted `kafka-clients-4.2.1.redhat-00003.jar` plus SLF4J API. SDK SHA256 is checked before protocol tests; the suites do not download dependencies. Default local paths match the coordinator's prepared artifacts; override explicitly when needed:

```sh
AUTH_TEST_JDK=/path/to/jdk \
AUTH_TEST_SDK_DIR=/path/to/extracted/libs \
python3 tests/r3-auth/run_offline.py --output /tmp/auth-offline-results
```

The runner writes sanitized case outcomes, source fingerprints and unittest logs. Generated self-signed fixture keys/certificates and compiled classes are temporary and removed after the suite. Tests never use real sandbox credentials or CA files. The source entry point remains fixed to its original service/CA; the fixture invokes a package-private socket boundary, with no new CLI/env/profile endpoint override.

The protocol suite independently implements enough broker framing and SCRAM-SHA-512 verification in Python to validate the Java SDK path: valid proof/server signature/own-topic metadata; wrong-password rejection; wrong correlation, early58/other codes, malformed/trailing/oversized/truncated frames, invalid signature/nonce, excessive iterations, wrong topic/authorization, TLS trust/hostname and read timeout. Each case also checks that synthetic credentials, common encodings/hashes and secret-like broker error text do not leak to Java stdout/stderr.

The supervisor suite runs actual local subprocesses through the unchanged child supervisor, using a stand-in `java` executable. It tests phase/password ordering, disabled/hash/source/protocol/window gates, negative success and positive failure, strict stdout/exit handling, secret-like stderr discard, output caps, JVM environment filtering, credential drift, evidence-write failure, real SIGTERM dispatch and phase-deadline killing of parents/descendants (including a descendant holding a pipe after its parent exits). An OS-dead/zombie process is not counted as a running descendant; direct children are reaped. Temporary fixture-only paths/profile approval are patched in Python memory; deployed files remain disabled.

Limits: this is offline behavior evidence, not a real Kafka broker, an actual target-image/source-launcher/SCC/Secret/network test, a hostile-code sandbox, full90-second scheduling test, or service/recovery qualification. Short local deadline fixtures exercise the same kill path. No new independent reviewer is implied. The production supervisor fix found here reports external cancellation during the first phase as INCONCLUSIVE rather than NOT_RUN; it remains nonpassing.
