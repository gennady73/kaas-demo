# R3-02 AUTH probe — offline preparation

**PREPARED CANDIDATE; NOT COMPILED, TESTED, DEPLOYED OR RUN.** User scope is wrong Kafka password with a valid-credential positive control, offline only. No existing Job, source/image pin, credentials, Kafka configuration, rule, route or collector changes. All four existing client Jobs remain protected/suspended. Email and all other external notifications remain disabled.

## Exact operation and reuse

The source reuses the existing [Java Admin readiness pattern](../r2-native/client-readiness/TopicHealth.java) with the existing TLS/SCRAM endpoint/principal/CA conventions. It is separate from the frozen R2 xk6/librdkafka module, runner, fixtures and evidence schema. This probe assesses the selected Java Admin path; it makes no cross-SDK claim about all clients or the existing xk6 error boundary.

Fixed endpoint is `kaas-dev-kafka-bootstrap.kaas-kafka.svc:9093`, principal `kaas-sbx-a-producer`, and own topic `kaas-sbx-a-events`. Use only an exact-topic read-only DescribeTopics call. There are no producer, consumer, group, offset, topic/config/ACL mutation or list-all APIs. Kafka4.2 named-topic describe is noncreating; the saved broker auto-create setting is also false. Metadata/handshake protocol traffic is nonzero; application-value bytes are zero.

Sequence uses three fresh JVMs, all with the same principal, endpoint, client settings, verified CA/hostname and SDK:

1. Valid credential describes the known own topic. Failure stops before the negative.
2. An ephemeral random nonmatching password is supplied only to this JVM through anonymous stdin. No mounted Secret is modified, no bad password file/env/argument/hash is created. Exactly one negative phase/API call is proposed; SDK negotiation or connection traffic is not promised to be a single wire attempt.
3. Only after the expected rejection, repeat the valid control in another cold JVM. Failure makes the pair inconclusive. No post-control runs after an unexpected negative success or wrong-layer failure.

The parent snapshots the valid password in RAM, checks credential/CA stability around phases and never records credential values or hashes. Java reads the selected password from stdin. No plaintext JAAS/config file is created. This is a trusted owner-operated diagnostic, not hostile tenant/Secret isolation.

## Strict failure classification

[SASL source inspection](evidence/source-references.json) matters: Kafka's `SaslAuthenticationException` can be raised locally as well as from a broker response. Candidate code accepts only that typed exception with an in-memory `SaslClientAuthenticator.receiveToken` origin frame, which upstream4.2.0 uses for a received SASL error. It records a fixed enum, never the stack/message. Missing/unreviewed origin, TLS/network/timeout/local-input/authorization errors are not a successful wrong-password result. Negative metadata success stops as failure.

TLS completion for that negative is inferred from the received SASL response over enforced SASL_SSL, paired with valid controls; no separate packet trace is claimed. Exact installed downstream Kafka client version/jar/hash and this origin mapping remain future verification inputs. A version/origin mismatch must be inconclusive, never bypassed through error-text matching or generic connection failure. This source is not asserted to be operational without compilation and the specifically deferred checks.

`source/run_probe.py` supervises fresh JVM process groups with bounded in-memory stdout/stderr capture; SDK logs are suppressed/discarded. It accepts only a one-row whitelist schema, expected exit codes and phase order. No automatic case retry. Timeout/forced exit cannot pass; process/Job termination must also be observed externally for a later accepted run. These untested safeguards are not a new R3-11 runtime cancellation proof.

## Disabled configuration and resource proposal

[profile.disabled.json](profile.disabled.json) fixes the scope with execution/deployment false. Run ID, authority, window, actual image reference and exact Java client version/jar/hash are null. Approved profile SHA environment is empty. Both immutable source hashes and an explicitly approved future profile must match before Java can start. Filling or flipping one flag does not arm this package.

[disabled/resources.yaml.disabled](disabled/resources.yaml.disabled) contains four inactive objects, outside every active GitOps/Kustomize root: separate tokenless ServiceAccount, immutable source/profile ConfigMap, probe-only NetworkPolicy and a **suspended new** `kaas-r3-auth-proposed` Job. No RBAC, Secret manifests, sink, storage claim or Build. It mounts only the A producer password and existing public Kafka CA; none of the other tenant credentials or sink owner/writer tokens. The candidate image is the existing pinned05a3f2d R2 image, selected for its Kafka Java/Python toolchain lineage; this preparation did not pull/inspect it or verify the exact Java jar. Final image/toolchain/mount/admission/permission readiness remains unverified.

Proposed bounds, not a selected live budget: client90s including startup/close/evidence, phase20s, Job120s including Pod startup, max3phase processes/3explicit metadata calls/one negative phase, no case retry. GNU timeout provides an outer90s limit; a kill makes the observation nonpassing. Request100mCPU/256Mi, limit500mCPU/512Mi; bounded memory emptyDirs64Mi temporary/1Mi sanitized evidence, no new persistent resources. No allocation/scheduling or measured runtime fit is claimed.

The candidate policy permits DNS to the saved OpenShift DNS selector and Kafka9093 to the existing broker selector; it adds no sink or external destination. Unique probe labels do not reuse trusted R2 client/owner labels. Actual additive policies, DNS/advertised broker endpoints, SCC arbitrary UID/fsGroup and read-only Secret permissions must be checked before any later authorized execution. This NetworkPolicy is not an already verified isolation boundary.

## Evidence, stop and custody contract

Only the three safe phase outcomes and sanitized summary are retained. Raw SDK stdout that fails schema and all stderr are discarded; output overflow stops. A candidate observation is `AUTH_PAIR_OBSERVED`, not a self-sufficient release PASS. Local sanitized result/termination files are each capped3000bytes and accompanied by matching stdout. The regular result file is atomically replaced/fsynced; the Kubernetes termination file is written in place/fsynced because it can be a bind mount. A write/final deadline failure exits nonzero. A saved file alone never passes: the custodian must verify child/Job exit0, normal termination within the selected bound, three expected outcomes, correct source/profile/image/jar bindings and preserved export. Killed/late/incomplete or conflicting evidence is nonpassing even if an earlier file contains an observed pair.

The candidate uses a distinct in-memory emptyDir and Kubernetes termination message, not the frozen R2 sink/database. This is not durable replay storage: promptly acquire sanitized result/Pod status/stdout into the shared workspace, hash the copies, and retain the completed Job/Pod plus export under the accepted seven-day custody policy until disposition. No automatic TTL/cleanup. Node/Pod loss before export makes evidence unavailable/nonpassing; no durability claim or new PVC requirement is inferred from this metadata-only scope. No HTTP sink call or external notification occurs.

Common stops: invalid/missing authority/profile/source/SDK pins, credential/trust drift, missing positive control, unexpected authenticated access, wrong-layer or unclassified result, timeout/deadline, output/evidence limit, termination uncertainty or evidence failure. Do not retry, relax TLS, rotate a Secret, modify ACL/policy or unsuspend an existing Job to repair the case.

## Current completion boundary

Prepared Java/Python source, source lock, disabled profile/manifest, proposed budgets/evidence contract and primary/local source mapping. Static source/document/AST/YAML/hash inspection only; **no probe launch, Java compilation, unit/regression tests, fake-broker tests, native build, image pull/build, Kubernetes/Secret/API access or deployment.** A local JRE was inventoried, but javac was unavailable; it supplies no compile or behavior proof.

Before a later operation: review/compile the candidate and source-specific classification/redaction/containment behavior when authorized; verify the exact candidate image/Java jar/version and source locks; freeze an immutable per-run ConfigMap/Job/profile with concrete authority/window and hash; refresh only applicable live trust/permissions/health and mount/network readiness; select custody/export/stop execution. Current owner/seven-day policy and known endpoint/principal are proposals reused from saved evidence, not questions that block this offline preparation. No new user input is needed now. No runtime security PASS is claimed.

`prepare_disabled.py` can reproduce only inert local files; it has no arming/network/execution mode. Source archives, disabled flags and this README do not authorize running the probe. No tests or live work follow automatically.

## Publication disposition

The owning commit publishes this uncompiled/untested candidate and disabled package only. It does not arm or deploy the Job, fill SDK/runtime/window inputs, run tests, enable notifications or change any existing client Job. Original preparation receipts retain their dated scope.
