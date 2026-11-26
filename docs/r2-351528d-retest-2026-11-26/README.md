# R2 runner 351528d: verified image and bounded retest

**Result: INCOMPLETE R2 acceptance; all 16 positive messages reconciled.** The user authorized one build and one bounded retest. One fixture ran; there was no automatic retry or second live attempt. The user authorized publication of these pins and results as an incomplete R2 checkpoint. The owning Git commit identifies the published snapshot; original execution receipts retain their historical publication status. All three client Jobs are now suspended, and their processes have terminated.

## Exact build and runtime

Native source: `351528d83b1b95c5697f9322c7dcf5491a302625`; all 41 native source fingerprints match the published offline receipt. Build recipes and manifest pins were adapted locally for this authorized build; native source and the frozen logical plan were not changed. The verified archive had 17 runner entries, reopened and checked byte for byte. The sink image was unchanged and was not rebuilt.

| Item | Verified result |
| --- | --- |
| Build | `kaas-demo/kaas-r2-runner-351528d-1`, Complete |
| Build interval | 2026-11-26 14:27:01–14:29:11 UTC |
| Image | `image-registry.openshift-image-registry.svc:5000/kaas-demo/kaas-r2-runner-351528d@sha256:7773f3ed708cbf8ab07703ed978afd478f05d9afcb13f888a27ef4159124b1af` |
| Binary SHA256 | `e0294b2a2916408eb61805fbbeffcf785066c75105f665b61c325e7401ee3be3` |
| Public runtime-source manifest SHA256 | `a8ff40449e28da9f46aded0bca19b669c4d5dc8c2fa53fc5fc3d9e396270877e`, unchanged |

The actual build passed binary checksum and public native identity/import checks, reporting SDK/librdkafka 2.14.0. Build output, push log and registry metadata agree on the image digest; the retest Pod imageID matches it. Updated `packaging/r2-native/inputs.json`, Dockerfile checksum and suspended baseline Job/runtime pins. Sixteen packaging regressions and the disabled contract validator passed before launch. The validator initially caught an old embedded runtime digest; it was aligned with the new image before the successful checks and before execution. A first health-list command had invalid CLI syntax and failed before any mutation; its corrected read-only query passed. Neither was an extra fixture attempt.

## Fresh checks and single execution

API authentication used trusted TLS and credentials only in memory-backed sessions; no default kubeconfig or token file was written. Fresh metadata-only client checks passed TLS/SCRAM, native identity, sink TLS and four topic leaders/RF2/ISR2. Kafka, tenant CRs and brokers were Ready. All four logs were empty and all groups had zero members/null commits. An absent group after previous empty attempts is a current observation, not a deletion performed here.

Verified both prior sealed database exports against their saved hashes, read-only. Kept the previous Jobs suspended. A new immutable sink configuration selected `/var/lib/r2/evidence-351528d-retest.sqlite` on the existing 1Gi PVC, using the existing single sink replica and image. No new PVC or topic was allocated. Physical attempt `351528d-retest-20261126` and Job `kaas-r2-native-client-351528d-r2` separate this attempt from the old exports; the exact frozen logical plan ID remains `r2-native-20261125`. Do not merge event streams between attempts.

The single Job started **14:31:53 UTC**; its container finished **14:32:16 UTC**. Native reported duration was **23,083 ms**; conservative external observation was **27,503 ms**, within the 300-second maximum. The fixture is one bounded iteration, not five minutes of sustained transfer. Process guard, Job deadline, zero retries and external stop plan were retained; forced stop was not needed. Incomplete result propagated as **exit 108 / Job Failed**.

## Message and offset reconciliation

| Topic | Positive acknowledged / received / committed | Receipt offsets | Final log end / committed offset / members |
| --- | --- | --- | --- |
| `kaas-sbx-a-events` | 4 / 4 / 4 | 0–3 | 4 / 4 / 0 |
| `kaas-sbx-a-audit` | 4 / 4 / 4 | 0–3 | 4 / 4 / 0 |
| `kaas-sbx-b-events` | 4 / 4 / 4 | 0–3 | 4 / 4 / 0 |
| `kaas-sbx-b-audit` | 4 / 4 / 4 | 0–3 | 4 / 4 / 0 |

All 16 positive identities/checksums match their receipts and durable-receipt-before-commit events. No missing positive messages, duplicate receipts or uncertain commits were found. The separate post-run Admin check confirms all four committed offsets/log ends are 4 and no group members remain. Positive value bytes: **16,000**.

The first negative case, tenant-A cross-topic write, passed with a typed broker topic-authorization denial. Its 1,000-byte attempt was definitively rejected and did not increase the foreign log. Total attempted original value bytes: **17,000**; acknowledged 16,000; definitively rejected 1,000; unresolved zero; remaining planned/unattempted 3,000. These are value bytes, excluding protocol/replication/evidence traffic.

## Remaining finding R2-LIVE-03

**Only one of eight required negative cases passed.** The second case, tenant-A cross-topic read, emitted case-start and then stopped with `client_or_evidence_failure`, before a baseline group-state event, consumer-open or denial-result. Six later cases were not started. No forbidden read success is evidenced.

Source inspection locates the next boundary: `engine.mjs` obtains `state(group, topic)` before constructing the negative consumer; the binder invokes native `snapshot(topic, group)`. Native snapshot asks the group-owner consumer principal for offsets of that supplied topic. This case combines tenant-A group with tenant-B topic, so the baseline Admin request can itself meet the intended topic ACL denial. The underlying native error was not retained; that exact cause remains a source-supported hypothesis, not a confirmed error code.

Targeted next work is to separate authorized group-baseline observation from forbidden target-topic observation, preserve typed-denial and offset evidence, and add regression coverage without widening tenant ACLs or inventing offsets. No source fix, policy change or further live attempt was made during this request.

**R2-LIVE-01 is now live-confirmed fixed:** empty-topic positioning succeeded and all four positive cases passed. R2-LIVE-02 remains live-confirmed fixed: an incomplete run fails its Job. R2 acceptance remains incomplete because the negative-case matrix and final full-fixture phase did not finish.

## Evidence, stop and custody

After independently observing termination, re-suspended the new Job. The original two Jobs remained suspended. Native reports all handles closed; final Pod/controller evidence shows no client process running. The separate semantic auditor reports a complete-fixture cleanup dimension of INCOMPLETE along with missing-case/phase issues; that does not establish a leaked running process.

Owner stop, seal and export produced **140 events**, with terminal present. Export SHA256: `1b9125375cf3bd06c58f16b146edc77425f4d275a855b0473201ba64df528016`. Python byte/hash/chain verification passed. The separate JavaScript semantic audit correctly returned `NATIVE_INCOMPLETE` (exit 2), matching four positive cases and one negative case. Its offline-only provenance fields do not attest execution; external Pod/image/group metadata supplies actual runtime provenance.

The workspace export matches the sandbox seal. Retain the sandbox PVC and shared-workspace copy at least through **2026-12-03 14:32:16 UTC**, under the accepted seven-day policy; sandbox lifetime is externally controlled and no cleanup automation was created. Both old sealed databases remain preserved. Sink is 1/1 Available on its Bound PVC, now stopped/sealed for this attempt. Temporary metadata Pods/ConfigMap were removed; no topic/group/message/offset deletion or reset occurred. Full orchestration, API snapshots and custody evidence are in shared `docs/testing/runs/r2-native-351528d-retest-20261126/`. Sanitized portable receipts accompany this guide; credentials/private keys/token values are excluded.

This request's build, single test attempt, reconciliation and evidence export are complete. This is not full R2, capacity, 2 MiB, recovery or production qualification. Automatic sync, baseline fixture authorization and deployment remain disabled; actual completed attempt authority is consumed. This publication authorizes no further live execution.
