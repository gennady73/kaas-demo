# R2-LIVE-01 and R2-LIVE-02 — fixes validated offline

**FIXED_OFFLINE; NEW_IMAGE_NOT_BUILT; LIVE_TEST_NOT_RERUN.** User authorized investigation, fixes, regression tests and offline validation, preserving the suspended client Job. No cluster/API, credential, deployment, sink or live Kafka action occurred. The user authorized publication of these fixes and offline evidence after baseline `79992572c793b8b2f2d6af735bf96d08c50f338a`; the owning commit identifies the published candidate. Original validation receipts retain their validation-time publication status. The published incomplete run and sealed evidence remain unchanged.

## R2-LIVE-01: empty-partition initial position

Primary source inspection confirms the failure condition: librdkafka 2.14.0 documents `Position` as the last application-consumed offset plus one, or INVALID when no previous message exists. The old adapter required a nonnegative SDK position before it would create a producer, while partition EOF reporting was disabled. An empty partition could therefore exhaust the six-second position wait despite successful group assignment.

The original live run did not retain the exact native error, so its precise root cause cannot be conclusively replayed offline. Its six-second boundary and empty topic agree with this source-supported condition. The fix covers that condition, and future failures now report the specific sanitized `initial_position_unverified` reason instead of losing that boundary in the generic error.

Changes in `tests/tenant-r2-native/native/module.go`:

- Enable `enable.partition.eof` for consumers. A broker EOF event supplies position evidence without a seed message.
- Retain only validated topic/partition/nonnegative EOF offsets; accept that evidence only for the current exact assigned partition after group assignment, when SDK Position is INVALID. Never infer zero from silence.
- Clear EOF evidence on assignment/revocation and actual message delivery. Preserve SDK errors, reject foreign assignment/EOF/backlog and retain the normal nonnegative SDK-position path.
- Treat EOF as an empty read, never as authorization denial. No seek, offset reset, commit or topic/message mutation was added; auto-commit and auto-offset-store remain false.

An unexported SDK interface permits fake polling without constructing native Kafka clients. Go regressions cover EOF position zero and nonzero, silence/timeouts, rebalance-stale evidence, wrong topic/partition/offset, partition SDK errors and redaction, no join, initial backlog, normal SDK position and EOF-not-denial. A temporary control copy with the EOF fallback disabled fails the new position regression, demonstrating the test detects the missing behavior.

## R2-LIVE-02: incomplete fixture must fail the process

The actual k6 1.7.1 local subprocess control reproduces the prior behavior: throwing an iteration exception alone exits 0. The revised entrypoint imports `k6/execution` and calls `exec.test.abort` for an incomplete result, after the engine has completed its cleanup and terminal-evidence path. Unexpected execution exceptions also abort with a fixed safe message; raw exceptions/credentials are not logged. Successful completion retains exit 0.

`test_exit_offline.py` extracts the exact production iteration body into a synthetic script with stubbed engine/transport/native objects. It imports only `k6/execution` and runs the actual rebuilt k6 executable locally. Results: legacy throw **0**, incomplete **108**, unexpected exception **108**, success **0**. The unexpected-exception canary is absent from output. This runs no fixture entrypoint, native extension import, Kafka constructor, HTTP request or cluster action. These subprocesses are offline regressions, not a live test rerun.

## Validation executed

Pinned Go **1.26.4**, CGO, k6 **1.7.1**, confluent/librdkafka **2.14.0**; Go proxy/checksum network lookups disabled. All checks passed:

| Check | Result |
| --- | --- |
| Binding regressions | 7 PASS |
| Review/engine/source-integrity regressions | 32 PASS |
| Sink/export tests | 18 PASS |
| Go race tests | 16 top-level tests PASS, including six new position regressions |
| Real local k6 process-exit regressions | 4 PASS |
| Missing-EOF control | Expected FAIL, retained as a negative control |
| Native build and public import inspection | PASS; no Kafka clients constructed |
| Synthetic SQLite/export/auditor replay | 182 synthetic events, 16 reported commits, byte and semantic checks PASS; no broker execution |

Reproduction from the repository, using a new temporary output directory:

```sh
python tests/tenant-r2-native/check_offline.py --go /home/gunger/go/pkg/mod/golang.org/toolchain@v0.0.1-go1.26.4.linux-amd64/bin/go --output /tmp/r2-new-offline-build
python tests/tenant-r2-native/test_exit_offline.py --binary /tmp/r2-new-offline-build/k6
```

The build helper itself does not run k6 iterations; the second command deliberately runs the synthetic exit harness described above. Source fingerprints are checked before/after the full helper and again when copying receipts. A first wrapper used an incorrect path for a proposed helper edit; that edit did not occur, and the existing helper completed successfully. No failed code check is hidden by that wrapper error.

Candidate binary SHA256: `71430df6e0a407e241c570a63759f7ebd915cb36c81f5ac5e1d82c31d2057f9f`.

Candidate runtime-source manifest SHA256: `a8ff40449e28da9f46aded0bca19b669c4d5dc8c2fa53fc5fc3d9e396270877e`.

Logical plan hash, fixture volumes, cases, ACLs and time budgets are unchanged. The runtime-source manifest was regenerated for the changed engine/entrypoint; the new executable independently binds changed Go code. Binary remains `/tmp/kaas-r2-live-fixes-offline-20261126/k6`, outside Git.

`offline-build-validation.json`, individual logs, `additional-regressions.json`, negative control and `validation-summary.json` retain exact commands/results/source hashes. Primary evidence was inspected in cached version-pinned [confluent consumer source](https://github.com/confluentinc/confluent-kafka-go/blob/v2.14.0/kafka/consumer.go), [EOF event source](https://github.com/confluentinc/confluent-kafka-go/blob/v2.14.0/kafka/event.go), vendored `rdkafka.h`, and [k6 execution source](https://github.com/grafana/k6/blob/v1.7.1/internal/js/modules/k6/execution/execution.go). `primary-source-inspection.json` records local paths/hashes; no online retrieval was required. The published build-info display trims trailing whitespace; raw/display hashes are recorded in publication-checks.json and raw logs remain in shared evidence. Validation is coordinator source review plus executed offline checks, not an independent human review or actual broker retest.

## Deployment and acceptance boundary

The client Job was untouched; its last observed live state and committed baseline remain suspended. No API credential was used. Existing image references, historical build receipts and sealed sink are preserved; **those images do not contain these fixes**. A disabled candidate-binding record identifies the new binary/manifest separately. Existing old-source context checks must continue failing closed until a future approved image build explicitly selects the new receipt, binary checksum and manifest pin; do not relabel an old digest as fixed.

Before a new live attempt: publish/freeze these changes when requested, build/verify the revised runner image and exact pins, and prepare a reviewed fresh run/sink identity preserving the prior sealed evidence. The new live attempt is not authorized by this offline task. Offline regressions close the code-fix increment; **R2 live acceptance remains INCOMPLETE until a separately authorized retest passes**.
