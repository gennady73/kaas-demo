# Four-topic functional smoke test — 2026-11-23

**PASS for functional Kafka delivery using the native Java client.** The selected xk6 image failed its initial attempt and is not qualified by this result. The user authorized a test in `kaas-demo`, four topics, values up to **2,097,152 bytes**, and at most five minutes of runtime. No Kafka broker, topic, user specification, GitOps source pin or operator upgrade was changed for the test.

## Verified execution

Successful run `smoke20261123b`, Job `kaas-demo/kaas-smoke-20261123-b`, UID `5e2edc1a-2407-4f13-ae06-5dfe4b9c9db1`; Pod `kaas-smoke-20261123-b-qt9qv`. Kafka service: `kaas-dev-kafka-bootstrap.kaas-kafka.svc:9093`, cluster `kaas-kafka/kaas-dev`, deployed Kafka 4.2.0. Input baseline: SRS 0.9, dev smoke profile 0.1, deployed workload revision `ea80ef82c6586ca1d6deaa56e37a19e888553dc0`. Source and expected cases are retained with the evidence; the offline JSON case generator itself is not an executable load-runner configuration.

| Topic | Acknowledged | Unique verified deliveries | Values per topic | Partition / offsets |
| --- | ---: | ---: | --- | --- |
| kaas-dev-smoke-01 | 4 | 4 | 1 KiB, 64 KiB, 1 MiB, 2 MiB | 0 / 2–5 |
| kaas-dev-smoke-02 | 4 | 4 | 1 KiB, 64 KiB, 1 MiB, 2 MiB | 0 / 0–3 |
| kaas-dev-smoke-03 | 4 | 4 | 1 KiB, 64 KiB, 1 MiB, 2 MiB | 0 / 0–3 |
| kaas-dev-smoke-04 | 4 | 4 | 1 KiB, 64 KiB, 1 MiB, 2 MiB | 0 / 0–3 |

Total: **16 originals, 12,849,152 original value bytes**. No missing records, duplicate deliveries, checksum mismatches or client errors in the successful run. Two records from the failed attempt were encountered and excluded by run-specific identity; their presence explains the first topic's starting offset. Four fresh consumer groups, one per topic, confirmed successful synchronous offset commits after verification.

Job start `14:07:16Z`; container `14:07:17Z`–`14:11:44Z`; Job Complete `14:11:46Z`. Client reported **265.501 seconds**, Job start to container finish **268 seconds**, Job start to Complete **270 seconds**. This is a test within a five-minute maximum, not five minutes of sustained ingestion. The small fixed record set was sent near the start; consumers continued polling until approximately 265 seconds to check delivery/duplicates and allow clean shutdown.

Each producer awaited its send future and captured acknowledged partition/offset. Each consumer independently hashed the received bytes and recorded ID, group, topic, partition and offset. A separate Python reconciliation recomputed expected hashes, checked exact ID/size/checksum sets and matched acknowledged locations to received locations. It also checked Job completion, exit code 0, the final clean-shutdown marker and the deadline. This is independent implementation/calculation checking, not a second human reviewer.

## Client and runtime controls

Runner: `kaas-demo/tests/dev-smoke/Smoke.java`, Java 21 source launcher with the Kafka libraries in the already deployed Red Hat image. Requested image is pinned to `registry.redhat.io/amq-streams/kafka-42-rhel9@sha256:ce7dc91b664600c6f06e1df3d6b56a4684bb779865d9c28b4df648addd89189d`; runtime image ID is `sha256:ccca1fa9be261fac850b918c27cecdd31bc2bbe85baf9c8a268db96ee332aa05`. No claim of matching this binary to an independently rebuilt Kafka distribution is made.

TLS verifies the cluster CA and hostnames; SCRAM-SHA-512 uses the existing scoped smoke user. Password/CA are mounted from a temporary namespace-local Secret; bearer token stayed in the API helper's memory. Producer: `acks=all`, idempotence enabled, one native retry, one in-flight request, `max.request.size=3145728`, no compression, 10-second delivery/max-block limits. Four logical producers and four consumers run in one process. Consumer fetch limits: 4 MiB globally and per partition, earliest on fresh groups, automatic commits disabled. No application-level resend was performed. The Java client settings were checked against [Kafka 4.2 producer configuration](https://kafka.apache.org/42/configuration/producer-configs/) and [consumer configuration](https://kafka.apache.org/42/configuration/consumer-configs/), accessed 2026-11-23; the actual successful delivery is the size-feasibility evidence.

Job: `activeDeadlineSeconds=300`, `backoffLimit=0`, `restartPolicy=Never`; process timeout 285 seconds with a three-second kill fallback, producers stop by 180 seconds, polling ends at 265 seconds and client completion must precede 285 seconds. The watchdog was configured and normal bounded completion was witnessed; forced termination under a deliberately hung client was not tested. OpenShift assigned a non-root UID under restricted security, with capabilities dropped and service-account token automount disabled. Worker request 500m CPU/512Mi, limit 2 CPU/1Gi, temporary functional-test allocations only.

The compiler emitted a deprecation warning for KafkaConsumer `close(Duration)`; closure completed successfully. Preserve the executed source for provenance; an API modernization can be a later reviewed edit.

## Failed attempt and credential containment

Image-only probe initially failed because its default working directory was unreadable by the OpenShift-assigned UID. A second image-only probe succeeded with `/tmp`; neither connected Kafka clients.

First actual attempt `smoke20261123a` used pinned `docker.io/gennady73/k6v2ubi9@sha256:9d924b0bff1afd5a42ddad8f2b10cc31a9c0c15af09be1c9699778eef36a1421`, reporting k6 1.8.1 and an xk6-kafka/v2 development build. It acknowledged 1 KiB and 64 KiB values on topic 01, then rejected 1 MiB with `Message size too large`; it exited 99 after approximately 6.854 seconds, before the delivery phase. This does not establish record loss or a broker size-limit defect. Its printed producer configuration omitted the larger native message limit despite the supplied size input. The intended producer setting was therefore not demonstrated as effective. The Java retry succeeded without a Kafka configuration change, localizing the practical blocker to the selected client path; an exact binary/source root-cause analysis remains open.

The image printed its SCRAM password in debug configuration output. The first API helper redacted the saved file but initially printed the unredacted log tail to the tool output; that was a handling defect and was corrected before later log collection. The exposed **test-user** credential was replaced by removing its operator-generated Secret, leaving the declarative KafkaUser unchanged. The User Operator regeneration behavior was checked in [Strimzi 0.51.0 KafkaUserModel, maybeGeneratePassword](https://github.com/strimzi/strimzi-kafka-operator/blob/0.51.0/user-operator/src/main/java/io/strimzi/operator/user/model/KafkaUserModel.java); this upstream source explains the mechanism, not exact Red Hat build provenance. Regeneration plus successful authentication with the replacement credential was observed; postflight records old/new Secret UIDs. The failed Pod was removed to remove its API log endpoint. Temporary Secret copies in `kaas-demo` were removed after use. Saved logs contain redactions. External log collector retention and copies in already emitted tool history cannot be established as erased; no such claim is made.

Do not reuse that xk6 digest with live credentials until debug configuration printing and message-size mapping are corrected. This native-client smoke PASS is not an xk6 PASS.

## User-supplied OpenShift dashboard baseline

Six supplied screenshots are preserved under `runs/smoke-20261123/dashboard-baseline/`. They show project `kaas-kafka`, namespace/pod compute dashboard, last 30 minutes, 30-second refresh; visible clocks approximately 15:25–15:55, without an explicit date/timezone. Exact alignment with UTC test timestamps is unverified. They are user-supplied visual evidence, not API metric exports or successful-run measurements.

- CPU table: brokers approximately 0.012–0.013 cores each (12–13 millicores); entity operator approximately 0.002 cores. This is light observed activity, not measured peak capacity or validated CPU sizing. The 15.90% summary card differs from instantaneous row ratios; inspect panel PromQL and aggregation/time selection before comparing them.
- Memory table: brokers 563.7, 640 and 730.8 MiB; entity operator 437.7 MiB. Entity operator is 85.50% of its 512Mi request and 42.75% of its 1Gi limit; this alone is not evidence of imminent exhaustion. The panel excludes cache and does not establish JVM heap, page-cache coverage, throttling or OOM history.
- Storage: roughly 12 combined IOPS and 49–50 KB/s combined read/write throughput near the table snapshot, not per-broker totals. Network: approximately 9–12 KB/s aggregate receive, approximately 10–17 KB/s transmit, and visible dropped-packet series at zero. These are pod/OS counters, including replication/control traffic; they do not count original producer value bytes or establish storage/network capacity.
- Kafka brokers are in `kaas-kafka`, while the test worker runs in `kaas-demo`; the supplied dashboard omits the worker's resources. For later load tests capture both namespaces on the same UTC time window, plus Kafka ingress/egress, consumer lag, ISR/under-replication, request latency/errors and client counters. These Kafka metrics were not exported in this smoke run.

## Evidence and remaining acceptance

Primary evidence directory: `docs/testing/runs/smoke-20261123/` in the coordinating workspace. Successful input/configuration: `expected-b.json`, `configmap-b.json`, `job-b.json`; runtime: `kaas-smoke-20261123-b.log` and corresponding `-observation.json`; independent result and evidence hashes: `reconciliation.json`; cleanup/readiness: `postflight.json`; replacement request: `credential-regeneration-request.json`. Initial failure and image-only probes are retained separately with redacted saved logs. Full snapshots include environment identifiers; they were not published externally in this turn.

Functional delivery is closed for this run/configuration. OPEN: xk6 image correction/requalification, sustained/24-hour volume and overload testing, negative ACL/network tests, restart/recovery/no-loss qualification, retention expiry behavior, production topology/resources/storage and cross-namespace performance correlation. RF2/minISR2 plus `acks=all` does not turn this no-fault smoke into a no-loss guarantee. No fault injection, operator upgrade, cluster restart, retention change, Git commit/push or publication occurred.
