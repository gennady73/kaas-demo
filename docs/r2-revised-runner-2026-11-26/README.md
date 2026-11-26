# Revised R2 runner build and bounded retest — 2026-11-26

**IMAGE_BUILT_AND_VERIFIED; RETEST_INCOMPLETE. R2-LIVE-02 is confirmed fixed live; R2-LIVE-01 remains open.** The user authorized building the revised runner from `02e2e2fed7db0c0e42072ef245e104fb6167b193`, updating its pins and attempting a live retest. One additional bounded fixture was executed, with no automatic retry.

## Revised image and pins

| Item | Verified value |
| --- | --- |
| Native/runtime source | `02e2e2fed7db0c0e42072ef245e104fb6167b193`; all 41 frozen native source fingerprints match |
| Build | `kaas-demo/kaas-r2-runner-02e2e2f-1`, Complete |
| Build time | 13:44:03–13:46:13 UTC, 130 seconds |
| Registry image | `image-registry.openshift-image-registry.svc:5000/kaas-demo/kaas-r2-runner-02e2e2f` |
| Immutable image digest | `sha256:d82a1444de832a824a135d66eef9c7486d8587299b54b5c490bccc194c42dabe` |
| Executable SHA256 | `71430df6e0a407e241c570a63759f7ebd915cb36c81f5ac5e1d82c31d2057f9f` |
| Runtime-source manifest SHA256 | `a8ff40449e28da9f46aded0bca19b669c4d5dc8c2fa53fc5fc3d9e396270877e` |

The checksum/import checks ran in the actual image build and reported the exact executable, native version 2.14.0 and expected mapping. Build output, registry push log and ImageStreamTag agree on the digest; metadata confirms amd64, user `1001:0` and the guarded entrypoint. The actual retest Pod imageID matches this digest. The sink image was not rebuilt because its source was unchanged.

Updated `packaging/r2-native/inputs.json`, runner Dockerfile checksum, disabled client image/runtime pins, and selected validation receipt in `prepare_contexts.py`. The generator still verifies every source/binary fingerprint, requires a successful offline receipt and rejects a receipt outside the repository. It now selects the published revised receipt rather than the historical pre-fix receipt. Packaging changes are local recipe/pin adaptations; the native source itself remains exactly the published 02e revision. Seventeen runner archive entries were reopened and byte-checked before upload. The generated sink archive was not submitted as a build.

`build/runner-02e2e2f.yaml.disabled` retains the exact two manual build resources used. Sixteen offline packaging regressions and the disabled contract validation passed after pin updates. No automatic build or ArgoCD synchronization was enabled. The old image/digests and historical receipts remain preserved.

An initial automatic approval review rejected the old broad session helper as stale/unclear. It did not execute. Preparation continued offline; an inspected, source-pinned build-only helper with an exact command allowlist was then approved. Separate inspected prepare/finish and one-shot retest helpers were pinned to 02e and limited to this authorized attempt. API credentials stayed in memory-backed sessions, with trusted TLS, no redirects and no default kubeconfig changes.

## Fresh physical attempt and preservation

Verified the old database's eight-event seal SHA256 `91cf8d49ca2091a3d0900cc6a8cec9b3b9fca0c9b0b60b49f23e003d5369c3e6` before rotating the sink configuration. It remains at `/var/lib/r2/evidence.sqlite`; no reset, deletion or writable access to that database was performed.

The new physical attempt is `02e2e2f-retest-20261126`, with Job `kaas-r2-native-client-02e2e2f-r2`, unique arming/runtime ConfigMaps and new database `/var/lib/r2/evidence-02e2e2f-retest.sqlite`. This reuses the existing 1Gi PVC, Service/TLS and capabilities, adding no second PVC or persistent sink replica. The sink's Recreate rollout selected a new immutable configuration with the new database filename; its actual overlay now includes that configuration.

The logical fixture ID `r2-native-20261125` and plan hash are frozen into the reviewed source. They were retained to build exactly the requested source, while physical Job/UID, database and custody directories distinguish attempts. The prior attempt sent zero records, and the refreshed metadata confirmed all topic logs empty and all committed offsets null. Event IDs must never be merged across these two separate attempt exports.

The original Job remained suspended. A metadata-only Pod using the revised image refreshed TLS/SCRAM, RF2/ISR2, zero group members, null commits and zero log start/end immediately before the fixture. The first group already existed empty from the prior attempt. No offsets or groups were reset to prepare the retest.

## Retest outcome

| Result | Observed |
| --- | --- |
| Job start / container finish | 13:49:04 / 13:49:12 UTC |
| Native / conservative external elapsed | 7,889 / 12,544 ms; below 300-second ceiling |
| Fixture status | `NATIVE_INCOMPLETE` |
| Container exit / Kubernetes status | **108 / Failed** — correct failure propagation |
| Stop reason | **`initial_position_unverified`** |
| Positive originals planned / attempted | 16 / **0** |
| Negative cases completed | **0 of 8** |
| Topic log start/end, all four | **0 / 0**, unchanged |
| Committed offsets / final group members | **null / 0**, all four |

The first consumer opened and closed; the run stopped before producer-open or send intent. Eight durable events include the specific stop reason and incomplete terminal. No producer send, receipt or commit event exists. Native cleanup was reported complete, and the process was independently observed terminated. This does not establish positive delivery or isolation acceptance; the separate semantic auditor correctly returns INCOMPLETE because the required matrix was not executed.

R2-LIVE-02 is **live-confirmed fixed**: unlike the first attempt, an incomplete fixture now exits 108 and fails its Job. R2-LIVE-01 is **not resolved live**.

## Remaining targeted defect

Source inspection identified a concrete EOF representation gap in 02e: it rejects every non-nil `PartitionEOF.Error`. The pinned SDK constructs EOF from a C partition-level error event and copies its error field, so its normal typed `ErrPartitionEOF` sentinel must be handled as EOF evidence rather than a generic failure. The original offline fakes used nil error and missed this representation.

An additional **offline-only control in a temporary source copy** supplies a valid topic/partition/offset-zero EOF with typed `ErrPartitionEOF`; 02e rejects it. `eof-shape-control.txt` retains this reproduced source gap. The live stream does not expose the exact underlying event, so attributing this particular live stop specifically to that sentinel remains source-supported inference. The newly specific stop reason does conclusively locate the failed boundary in initial positioning.

Next correction should narrowly normalize typed `ErrPartitionEOF` only inside an actual EOF event, preserve rejection of all other errors and retain assignment/offset guards, with an SDK-shaped regression. **No further source modification, image build or live attempt was performed here.**

## Stop, reconciliation and custody

After process termination, re-suspended the new Job. Both original and retest Jobs are suspended; no client process remains. Owner stop/seal/export froze the new database. Separate Python hash/chain verification passed; the independent semantic audit returned `NATIVE_INCOMPLETE`, as required by the incomplete coverage.

New export SHA256: `32496208a625aa6115dc5442e511ffc7072af6fc7267432726b4fe898ad754d3`. The shared-workspace copy matches the sink seal. Both old and new databases are preserved on the Bound PVC; the sink remains 1/1 Available with the new database stopped/sealed. Temporary pre/post metadata Pods and their ConfigMap were removed. No topic, message, group, offset or old evidence was deleted.

Build and selected sanitized retest evidence are alongside this guide. Full retest record is in shared `docs/testing/runs/r2-native-02e2e2f-retest-20261126/`, including public orchestration scripts, actual runtime/Job requests, controller observations, exact logs and pre/post Admin metadata. Retain sandbox evidence and its verified workspace copy at least until **2026-12-03 13:49:12 UTC**. The original attempt retains its separate earlier custody record. No credentials, private keys or token values were exported.

The user authorized Git publication as an explicitly incomplete R2 checkpoint. The owning commit identifies the published snapshot; original build/run receipts retain their historical publication status. The disabled baseline Job remains suspended; its new image/runtime pins do not authorize another execution. **The requested build and retest attempt are complete; R2 acceptance has not passed.**

Published log display copies trim trailing whitespace only; original raw logs remain in shared evidence, with raw/display hashes in publication-checks.json. The sealed event stream is unchanged.
