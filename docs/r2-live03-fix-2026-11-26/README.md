# R2-LIVE-03: baseline correction validated offline

**FIXED OFFLINE; R2 ACCEPTANCE STILL INCOMPLETE.** Source base is published checkpoint `c6a74b41e06ebf06d050aad322a844daeda619e1`. The user authorized publication of this correction, regression tests and receipts. The owning Git commit identifies the published snapshot; original offline validation receipts retain their historical publication status. No cluster access, image build, deployment or live test occurred. All three client Jobs were untouched; their last saved API states are suspended.

## Finding and evidence

The actual 351528d retest delivered and committed all 16 positive records, then passed the first cross-topic-write denial. Its next cross-topic-read case stopped before baseline group-state/consumer-open. Its specific native error was not retained. The source nevertheless demonstrates a conflicting request: the harness asked the tenant-A group owner for OffsetFetch on tenant-B's forbidden topic. [Kafka 4.2 authorization documentation](https://kafka.apache.org/42/security/authorization-and-acls/) requires Describe permission on both the group and topic. The supplied tenant ACLs intentionally do not permit that foreign topic.

An offline fake reproduces this conflict by rejecting every mixed topic/group observation. The original routing fails this regression; the corrected routing completes the synthetic matrix. This verifies the source-level defect and correction, not the historical live error code or a new live acceptance pass.

## Correction and evidence semantics

The harness observes the group's established fixture partition under its owner: for `kaas-sbx-a-events-group`, the offset topic is `kaas-sbx-a-events`. The negative client's forbidden target remains `kaas-sbx-b-events`. Group-state events name the actual observed offset topic. Case-start and client-open events continue to name the attempted target. The auditor independently derives the expected group-state topic from the frozen fixture group, rejects relabelling, and still requires unchanged negative offsets and zero members.

This name pairing selects a fixture observation, not a new Kafka ACL rule. It does not restrict the existing Consumer constructor or imply tenants cannot use another authorized topic with their group. Binder and native snapshot now reject mixed observation inputs before SDK construction; no tenant ACL, principal, Secret, workload plan or record budget changes. Native baseline failures receive a fixed safe diagnostic rather than raw error text or fabricated offset values.

The baseline retains the measured positive offset **4**; it never replaces an unavailable/denied result with zero or null. These snapshots measure the group's established fixture partition and membership. They do **not** claim direct measurement of committed offsets for a forbidden group/topic pair, or all possible group partitions. Forbidden access still needs its typed native denial, successful controls and no-negative-commit path; these remain required. A future complete broker run must verify those claims and the scoped baseline/final accounting. If direct observation of every forbidden pair is required, it needs a separately reviewed observation authority; this correction does not pretend existing tenant permissions provide it.

The event field allowlist and sink code are unchanged; only the meaningfully corrected topic value and auditor expectation change. The JavaScript runtime-source manifest is regenerated, and the native snapshot guard is rebuilt offline. Historical exports/audits remain pinned to their original source and are preserved without modification.

## Executed offline checks

- Eight binding checks, including rejection before invoking a mixed native snapshot.
- Thirty-seven review checks, including all eight ACL-shaped synthetic negative cases, retention of offset4, changed-offset failure, safe failure reporting and rehashed topic-spoof rejection.
- Eighteen sink/export checks and 22 top-level Go race tests, including the complete observation-binding matrix and mixed snapshot rejection.
- Go1.26.4/CGO build and public `k6 inspect`, with k6 1.7.1 and SDK/librdkafka 2.14.0; module lookup disabled.
- Synthetic SQLite/export/auditor replay: 182 events, 16 reported commits, hash/chain and semantic match. This is not Kafka delivery evidence.
- Four separate local synthetic k6 exit tests passed. The full helper itself runs no k6 iterations; the exit tests stub external dependencies and construct no Kafka client or HTTP request.
- Temporary negative control reverting only baseline routing fails the new ACL-shaped regression as expected. The production source suite passes.

Commands:

```sh
python tests/tenant-r2-native/check_offline.py \
  --go /home/gunger/go/pkg/mod/golang.org/toolchain@v0.0.1-go1.26.4.linux-amd64/bin/go \
  --output /tmp/kaas-r2-live03-offline-20261126
python tests/tenant-r2-native/test_exit_offline.py \
  --binary /tmp/kaas-r2-live03-offline-20261126/k6
```

All **42 source fingerprints** match `offline-build-validation.json`. Candidate binary SHA256: `0174513d51947fb65aa17ae70f85fea19f7ed5a605aae0ca6d016d8e1cd94cc0`. New runtime-source manifest SHA256: `07f7bd428716626f2d0ca3a229fd4d4d346c5a5a5ff8dff92fa119827ee27b59`. Binary remains outside Git under `/tmp`; receipts and source are retained here. No new image digest exists.

## Remaining R2 work and estimate

R2-LIVE-01 and R2-LIVE-02 remain live-confirmed fixed. R2-LIVE-03 is corrected offline and awaits exact-image broker confirmation. Actual image/runtime pins remain `7773f3ed...` / `e0294b2a...` / `a8ff4044...`; that image does not contain this correction. `packaging/r2-native/inputs.json` records a separate candidate, while `next-build-inputs.json` is disabled. The old source-bound context generator will reject changed source until deliberately rebound to the new receipt for an authorized build.

The remaining path is publication/freeze, build and verify the revised runner image and runtime pins, then one explicitly authorized bounded run and evidence review. Planning estimate: **30–60 minutes of active work once that continuation is authorized, if no new defect appears**. The fixture itself remains at most five minutes. Closure requires all16positive records and all8negative cases, complete reconciliation, termination and verified evidence custody; the seven previously unpassed negative cases are not considered accepted because the offline suite passes. Further work depends on actual findings, not repeated generic readiness cycles.

No permission decision is pending for this completed offline task. Publication authorizes no automatic retry, image submission, ArgoCD sync or workload activation. Existing three sealed attempt exports and retention records remain unchanged.
