> Superseded for current source by [classifier-review.md](classifier-review.md): R3-AUTH-SRC-02 resolved offline through direct protocol classification; runtime remains untested. The following record is historical.

# R3-02 AUTH compilation and source review, 2026-11-27

**Compilation passed; execution remains blocked by R3-AUTH-SRC-02.** No tests, probe, container or workload ran. No sandbox API call or resource change occurred. The four client Jobs were untouched and must remain suspended; external notifications remain disabled. This is not a fresh observation of cluster state.

The local compiler is Temurin javac25.0.5, found outside PATH. Compilation used `-proc:none --release 17 -Xlint:all`, the exact extracted Kafka client and SLF4J API jars, and produced no warnings/errors. No compiled class or SDK application was executed. Python was parsed as3.9 AST only. The earlier “javac unavailable” entry described PATH discovery and is superseded by this inventory.

## Image and SDK evidence

Read-only registry download verified base index `ce7dc91b664600c6f06e1df3d6b56a4684bb779865d9c28b4df648addd89189d`, amd64 manifest `ccca1fa9be261fac850b918c27cecdd31bc2bbe85baf9c8a268db96ee332aa05` and compressed layer hashes. Selective extraction found `kafka-clients-4.2.1.redhat-00003.jar`, SHA256 `5f13fa84c366c1b20388aadfea9b0539654563bc90bcacd2515c849e8d37e669`; jar properties report version4.2.1.redhat-00003, commit6f44a337d1d1ec8a. The candidate's4.2.0 assumption was wrong. Exact Java/Python guards and disabled profile SDK pins now match this artifact (R3-AUTH-SRC-01).

The existing runner remains pinned to41f328c85ee3d3e9d8834ce12e516b5ef52506067117b1c4f1145511b493998a. Saved Nov26 build/image receipts match that digest and the two freshly checked base layers. Its unchanged Dockerfile adds the R2 files/binary without changing Kafka libraries. SDK inheritance is a derived lineage conclusion, not a fresh registry/runtime attestation of the41f image. Digest integrity does not independently establish signature trust. No sandbox credential/Secret or global pull-secret access was needed.

## Source findings

**R3-AUTH-SRC-02 OPEN:** `javap -c -p` on the exact SDK confirms receiveToken handles a received SASL error response. However, its ApiException overrides fillInStackTrace with a no-op, so SaslAuthenticationException cannot supply the proposed receiveToken stack frame. Its type alone is insufficient because local SASL paths also create it. The candidate's stack-based acceptance was removed. It now reports LOCAL_OR_UNPROVEN_SASL_FAILURE, making the negative phase inconclusive; no broker-rejection PASS can be emitted by the current Java code. A null-message response also uses a shared Errors exception, reinforcing why origin cannot be inferred from the exception object.

Do not arm this source. Next is a narrowly scoped offline design for a reliable, sanitized broker-response origin channel, or an explicit decision to accept a narrower claim that proves only a typed authentication failure. No such relaxation is assumed here. It requires no new sandbox resources or immediate user decision. SDK changes, bytecode instrumentation, raw error-text matching and generic-failure acceptance have not been introduced.

The source review also inspected exact own-topic DescribeTopics scope, TLS/SCRAM/hostname configuration, password-only anonymous stdin, output whitelisting/discarded SDK diagnostics, source/profile locks, three process groups, signal/deadline paths and evidence handling. No producer, consumer, group, offset or mutation API is selected. This is a C0 source review, not independent concurrence or behavioral proof. The original Java regex escaping was valid; an initially mistaken edit during this review caused an intermediate compile error and was replaced with exact version equality. The final compilation alone is PASS.

Containment/redaction, target source-launcher compatibility, runtime mounts/permissions, exact running-image binding and failure propagation remain untested. A final evidence/deadline failure can leave an earlier observation file; acceptance still requires matching stdout/files/export, normal timely exit0 and external termination verification. No file alone proves success.

## Disabled and preserved

Execution/deployment false; new proposed Job suspended; run ID, authority, window and approved profile SHA unset. Image and SDK identifiers are populated as provenance only. Inactive manifest remains outside active GitOps roots. Source lock and embedded ConfigMap were regenerated and checked; no R2 runtime, existing Job manifest, active GitOps resource, monitoring rule, route or notification configuration changed. Historical preparation/publication receipts are retained with their original scope.

Machine-readable compilation, source hashes, SDK/image lineage, findings and limits: [compile-review.json](evidence/compile-review.json). Compiler output, exact SDK bytecode disassembly and base manifests are retained alongside it. SDK jar/layer/class binaries remain temporary local artifacts, not repository payloads. No commit or push is part of this task.
