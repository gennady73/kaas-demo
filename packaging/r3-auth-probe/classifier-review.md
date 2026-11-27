# AUTH broker-rejection classifier, 2026-11-27

**R3-AUTH-SRC-02 resolved in source; compilation PASS. Runtime qualification remains NOT RUN.** No test, probe/class/container execution, deployment, sandbox API/Secret access, external notification, or change to an existing Job occurred. This is one C0 source review, not independent concurrence. The four existing Jobs must remain suspended.

## Reliable provenance without exception inspection

The previous AdminClient exception-stack design cannot work because the exact SDK suppresses exception stack traces. This revision removes that dependency rather than accepting local failures as broker rejection. It changes only the dedicated AUTH diagnostic, not the frozen R2 runner/xk6 adapter, fixtures or sink. Its claim is the service's TLS/SCRAM rejection through this direct SDK protocol path, not AdminClient/xk6 exception semantics or all-client compatibility.

Each phase opens one socket to fixed `kaas-dev-kafka-bootstrap.kaas-kafka.svc:9093`. Trust is built only from the mounted public Kafka CA. JSSE verifies the endpoint hostname with HTTPS identification; no default trust fallback, trust-all option, client certificate, relay, external route or advertised-broker connection is used. Both positive phases and the negative use this same implementation, SDK, principal, endpoint and trust settings; only the password differs.

After verified TLS, the probe sends SaslHandshake v1 for SCRAM-SHA-512. The pinned Kafka SDK's ScramSaslClient creates the client-first token. A successful SaslAuthenticate v1 server-first response is validated by that SDK; iteration work is checked to4096–65536 before proof calculation. Only after the client-final proof has been sent can a parsed SaslAuthenticate v1 response with numeric error58 establish BROKER_SASL_REJECTED. The SDK parser checks response correlation against the exact request; incomplete, oversized, extra-trailing-byte or unparseable frames are nonpassing. No exception message, stack, response error text, packet log or credential is used for classification or retained.

Successful authentication requires the SDK to verify the server-final SCRAM signature and mark the exchange complete. Then one Metadata v4 request names only `kaas-sbx-a-events`, with auto-creation explicitly false. Success requires exactly that topic and nonempty error-free partitions with assigned leaders. This replaces the Admin describe call with its narrowly scoped metadata protocol operation. There is no all-topic request or producer, consumer, group, offset, ACL, topic/configuration mutation API.

Local SASL exceptions, TLS failures, pre-client-final authentication errors, wrong correlation/API shape, truncated frames, other broker codes, parsing failures and timeouts remain nonpassing. An unexpected successful negative must also pass own-topic metadata before being classified OWN_METADATA_OK; either way an unexpected negative or incomplete evidence cannot qualify AUTH. Valid-before failure stops before the negative. Valid-after runs only after the expected negative. Three cold JVMs and the unchanged parent outcome/exit-code contract prevent cross-phase reuse.

## Exact SDK, framing and bounds

Kafka SDK remains4.2.1.redhat-00003, jar SHA256 `5f13fa84c366c1b20388aadfea9b0539654563bc90bcacd2515c849e8d37e669`; candidate runner remains digest41f328c85ee3d3e9d8834ce12e516b5ef52506067117b1c4f1145511b493998a. Reuse [prior image/SDK provenance](evidence/compile-review.json); no new image or fresh running-image attestation is claimed. The source uses pinned SDK internal SCRAM classes; a version/hash change requires review, not a family-version fallback.

Exact jar `javap -c -p` inspection confirms request serialization contains header/body without the length prefix (the probe writes one length prefix), response parsing verifies correlation, Errors.SASL_AUTHENTICATION_FAILED maps to58, and successful SCRAM server-final handling checks the signature before completion. Disassembly evidence is retained; no class was run. No new dependency, Java agent, SDK patch or image build is needed for this source-only candidate.

Each phase uses at most one TCP connection and four Kafka RPCs: handshake, two authentication exchanges, then own-topic metadata if authenticated. The negative normally ends at the third RPC. Across all three phases the hard maximum is12RPCs and at most3metadata requests; there are no SDK/network retries or ApiVersions negotiation/fallback. Explicit versions1/1/4 are intentional for the pinned sandbox family; unsupported versions remain nonpassing and must not trigger an automatic fallback. TCP/TLS packets and DNS lookups are not RPCs, and encrypted traffic is not zero bytes. Application-value bytes remain zero.

Frame limit1MiB, token limit16KiB, iteration cap65536, connect/read timeout5s. Existing parent phase20s/client90s/Job120s limits remain. Socket timeout alone does not bound DNS, partial reads or all CPU work; parent process-group/deadline/output limits and outer timeout remain essential and untested. Only sanitized output is retained. Password/proof buffers are not written to disk; some SDK/JDK immutable objects may remain in memory until process exit, so complete memory zeroization is not claimed.

## Compilation and completion boundary

Temurin javac25.0.5 compiled the final source with `-proc:none --release 17 -Xlint:all` against the extracted exact SDK and SLF4J jars: exit0, no warnings/errors. [Receipt](evidence/classifier-review.json) binds source/supervisor/class hashes, bounds and bytecode inspection. The compiler is not the target runtime launcher. No unit, fake-server, positive/negative, regression, redaction, containment or live test ran. Source review and compilation do not prove runtime behavior. Historical compile/publication receipts remain unchanged and are superseded only for this source revision.

The disabled profile now pins this protocol contract. The parent checks it exactly before starting Java, in addition to the SDK/source/profile hashes. Execution/deployment false, external notifications false, protected-Jobs-suspended true; authority/run/window and approved profile hash remain unset. Source lock and immutable embedded ConfigMap regenerated; proposed Job remains suspended and outside active GitOps roots. No active resources or R2 files changed.

## What remains before deployment or execution

Kafka, tenants and collection-only monitoring already exist for the evidenced sandbox scope. This AUTH diagnostic is the remaining selected increment; no fresh R2 payload run or24-hour soak is needed for its source change.

1. Publish this reviewed source, source lock, disabled profile/manifest and evidence at a pinned revision. This task saves local changes only.
2. With explicit authorization, validate the new correlation/error classification and failure/redaction/containment behavior. These checks remain unrun under the current no-tests instruction; do not call the source runtime-qualified.
3. Refresh only applicable image/toolchain identity, Kafka health, CA/credential mount permissions, DNS/network path and evidence custody. Freeze a unique run/authority/window, immutable per-run ConfigMap/Job and approved profile hash. Existing endpoint/principal and accepted seven-day custody/export policy need not be selected again.
4. Obtain explicit authority for the bounded metadata-only AUTH run. Deploy the separate probe resources, leave all four old client Jobs suspended, execute once under the agreed bounds and reconcile/export the outcomes. No external notification is needed. This task does not authorize those actions.

No new architecture, storage, resource-budget or notification decision is required from the user for this offline resolution. Full service qualification still requires the applicable remaining R3 security/other-scope cases and evidence closeout; AUTH success alone cannot declare the whole project production-ready.
