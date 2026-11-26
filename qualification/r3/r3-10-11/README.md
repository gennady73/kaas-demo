# R3-10 and R3-11: offline failure coverage

**PASS for the requested offline review and regressions.** Based on published source `94674205d6619e8c7060f5463338e00582f7ed4a`, C0 mapped existing coverage, added 22 missing regressions and validated the result locally. No cluster access, Kafka client construction, k6 iterations, workload, image deployment or change to any of the four client Jobs occurred. They are untouched and last observed suspended; this is not a fresh live-state observation. The user authorized publication of these tests, coverage and receipts. The owning Git commit identifies the published snapshot; original validation receipts retain their historical pre-publication status.

[Result](result.json), [source fingerprints and full helper receipt](evidence/validation.json), [packaging source hashes](evidence/packaging-source-hashes.json), and [artifact manifest](artifact-manifest.json) identify this snapshot. No independent C1–C7 signature is implied. The original qualification plan is unchanged; its [progress overlay](../progress.json) distinguishes offline completion from target failure-path acceptance.

## R3-10: sink boundaries

| Requirement and failure assumption | Existing evidence reused | Added coverage / disposition |
| --- | --- | --- |
| Before SQLite commit: no durable ACK or preserved new event | `sink/test_store.py::test_three_process_crash_boundaries`; `test_disk_full_readonly_and_budget_do_not_ack` | `test_failure_boundaries.py::test_commit_failure_rolls_back_and_never_returns_ack` injects failure at actual COMMIT call, verifies rollback and reopen/new retry201. This is a connection double, not physical disk exhaustion. |
| Commit succeeds, response lost | Existing crash at `after_commit_before_response`, reopen and duplicate200 | `test_committed_event_survives_lost_handler_response_and_exact_retry`: in-memory Handler response raises BrokenPipe after commit; error is fixed503, reopening preserves exactly one envelope and retry200. No socket/TLS delivery is claimed. |
| After durable ACK construction/Store return | Existing child exits after `Store.event` returns; reopening retains event | Reuse existing check. The label `after_response` in that historical test is a local return boundary, not proof a remote writer observed the ACK. Actual network ACK delivery remains unqualified here. |
| Exact retry/conflict, hash/chain/schema binding | Existing commit/reopen/retry, conflict/unknown-schema and protocol tests | Existing bytes and validation rules reused; no new protocol implementation. |
| Stop/seal must persist and freeze evidence after restart | Existing stop/seal and partial-seal tests | `test_stop_and_seal_survive_reopen_without_changing_export` checks stop before seal, seal after reopen, exact terminal duplicate, rejection of new append and identical export/hash. |
| Disk full, read-only and capacity boundary: no new false ACK | Existing injected OperationalError tests | `test_concrete_capacity_boundaries_prevent_new_ack_but_allow_exact_retry` exercises real headroom comparisons, database cap, free bytes below/equal threshold and existing duplicate recovery. Physical read-only remount and full-volume behavior are not executed. |
| Partial/truncated export never becomes acceptance | Existing `test_export.py` partial export, hash/count/identity checks; `test_partial_seal_is_never_acceptance` | Reused unchanged. A seal attests bytes, not successful fixture acceptance. |
| Version/identity mismatch must not rebind evidence | Existing run mismatch, boolean version, hash/schema tests | `test_same_run_cannot_rebind_plan_and_unknown_version_cannot_append` verifies same run/different plan and version2 rejection with unchanged export. |
| No Kafka commit without durable evidence | Existing recovered receipt ACK closes admission | New JS failed receipt persistence and over-budget commit-intent tests confirm zero native commits. |

The sink protocol remains `kaas-tenant-evidence-v1`, WAL with SQLite synchronous FULL. The 18 existing sink tests were reused and five added, yielding 23. These checks establish local implementation behavior only. They do not qualify the storage service, PVC recovery or inherited DEP-PERSIST-01. No power-loss or infrastructure survival guarantee is inferred.

## R3-11: deadlines and late outcomes

| Boundary / acceptance criterion | Reused or added proof | Limit |
| --- | --- | --- |
| Stalled send/late ACK: no application retry; preserve late acknowledged bytes | New `test-containment.mjs` late producer ACK records1000 late bytes, zero unresolved bytes, one send, zero commits | Injected clock and producer double; actual SDK producer stall is not executed. |
| Sink latency consumes admission budget | New persisted attempt-intent and commit-intent tests: unsent event/native send0 or commit0 after budget exhaustion | Bounds admission after return, not cancellation of blocked HTTP. |
| Stalled sink/invalid or late ACK closes mutation admission | Existing exact retry/wrong ACK/recovered ACK tests; new1201/2001ms failure and >2s valid ACK tests; receipt failure prevents every commit | HTTP double; advertised700ms timeout and two-attempt/2s envelope remain source behavior, not a target network measurement. |
| Poll silence stops loop; no subsequent sends/commit | New delayed empty consume test, four initial sends, one poll, zero commits | Engine double. Native blocking-Poll regression explicitly shows an SDK call ignoring its timeout cannot be preempted by this facade. External termination is required. |
| Commit timeout or late success never becomes a confirmed commit | Existing ambiguous-commit engine and generic quarantine tests; new selected `Module.Commit` blocking consumerAPI path | Caller returns timeout, retains last record, latches quarantine/fault and refuses more work; fake worker later returns next offset8 without clearing uncertainty. No actual broker offset is observed or inferred. |
| Close timeout and late return preserve incomplete cleanup | Existing generic close/late-success tests; new engine overrun and selected `Module.Close` test | Late close does not remove quarantined handle; no claim that SDK work was cancelled. |
| Deadline includes startup; expired calls cannot start native mutations | New45,001ms initial age engine test; selected native270001ms commit/consume and300001ms close admission tests | Local clocks; actual startup timestamp delivery/Job timing remains target qualification. |
| Process termination contains stalled calls | Existing guard refusal test; two new `test_guard_containment.py` tests exercise real GNU timeout with inert Python stubs | Only a disposable copy:285s→0.8s, kill-after5s→0.2s; cooperative exit124 and raw Python return `-SIGKILL` for TERM-ignoring stub. Nonzero never equals fixture pass. No k6 run or shipped guard modification. |
| Job/external watchdog and final offset disposition | Existing source/package guards: native mutation270s, process TERM285s/KILL290s, Job300s; historical R2 process exits are normal-path evidence only | Actual Job-controller failure termination/process-tree evidence and post-failure offsets remain OPEN for a later explicitly authorized selected fixture. |

Selected native tests instantiate only the `consumerAPI` test double; no librdkafka Producer/Consumer/AdminClient is constructed. The race detector passed. A wait timeout is not SDK cancellation. A real uncertain commit must be reconciled against final group offsets after process termination; these tests do not supply a substitute offset receipt. No durable event or offset is silently promoted to confirmed success.

## Executed validation

| Suite | PASS count |
| --- | ---: |
| Native binding / existing review | 8 /37 |
| Standalone auditor schema/domain | 445 |
| New JS containment | 11 |
| Sink Store/protocol/export | 23 |
| Go race, top-level tests (subtests not double counted) | 26 |
| Full native helper total | **550** |
| Packaging including two local process-guard regressions | **18** |
| Combined regression total | **568** |

Host Go1.26.4 build and public `k6 inspect` passed with GOPROXY/GOSUMDB off. The helper never runs `k6 run`. Binary SHA remains `0174513d51947fb65aa17ae70f85fea19f7ed5a605aae0ca6d016d8e1cd94cc0`; candidate JS manifest remains `9af2ea57aaf851bb4855696ea0f9072ab7f4643a1b64441c9ea47f6bdf6627ff`. No runtime source fix or new image/pin was necessary. Actual image41f328c8/runtime manifest07f7bd42 remains the historical deployed identity, distinct from the offline auditor candidate.

Reproduce from the `kaas-demo` repository root, with the sibling `kafka-load-test` fake fixture source available:

```sh
python tests/tenant-r2-native/check_offline.py --go /path/to/go1.26.4/bin/go --output /tmp/new-r3-offline-output
python -m unittest discover -s packaging/r2-native -p 'test_*.py' -v
python packaging/r2-native/validate.py
python qualification/r3/validate_plan.py
```

The helper receipt fingerprints all46native-package files. The sibling fake/policy source and repository HEAD are fingerprinted in `evidence/sibling-source-hashes.json`; packaging guard/manifests/harness have additional hashes. Logs preserve the actual commands and results. The original plan validator still emits historical NW-01/02 OPEN labels by design; it is a planning checker, while the progress overlay and R3-00 result supply the current offline correction disposition. The artifact manifest covers this portable package except itself. Published buildinfo removes trailing whitespace only; the original raw output and raw/display hashes are retained in the shared review folder. The77MB locally built binary is intentionally outside the repository; its hash/buildinfo/inspect receipt are retained.

## What remains

Requested offline work is complete. Target image/SDK/network failure behavior, infrastructure persistence and actual Job/external-watchdog termination remain explicitly unexecuted; they are not a reason to automatically repeat successful R2. No deployment or live approval is sought now. Next offline preparation can address R3-01 configuration/authority/GitOps contracts using these evidence boundaries. The broader R3 service acceptance criteria and owner joins remain in the original plan.
