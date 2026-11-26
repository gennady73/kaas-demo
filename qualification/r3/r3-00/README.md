# R3-00 — auditor corrections and sealed R2 re-audit

**PASS: offline technical completion.** C0 reviewed and completed the existing candidate for C3-NW-01/02, ran regressions and re-audited the original sealed successful R2export. No cluster access, Kafka client construction, k6iterations, image build/deployment or live workload occurred. All four client Jobs were untouched and remain last observed suspended. The user authorized publication of these fixes and receipts. The owning Git commit identifies the published snapshot; original validation/re-audit receipts retain their historical publication status.

## Scope and correction

Source base: `0f9df49fc0dfb3632c9c7f4eb32fb7e6d3aec1e6`, with the pre-existing auditor/schema-test candidate preserved from the preceding planning/publication work. That candidate's412schema checks passed at intake. C0 completed offset correspondence/continuity guards and added33checks, yielding445standalone schema/domain controls. This is a C0technical disposition, not an invented independent C3/C6signature or an edit to their handoffs.

The selected remedy validates schemas independently inside the standalone auditor, rather than trusting an earlier sink check. Correct hashes prove byte consistency but cannot supply a missing field or make a negative record offset valid. Rehashed controls show why sink-only validation is insufficient for a separately invoked auditor. The change keeps valid and incomplete transcripts distinguishable and adds no runtime permission or workload.

**C3-NW-01:** the standalone auditor now independently requires common and event-specific fields, conditional negative-case/send-result fields, allowed field shapes and scalar/array types. It validates case-kind, binding/control identity and record/case links before semantic completion. Missing `case_kind` and `durable_receipt_ack.case_id` cannot disappear behind valid envelope hashes. Structurally invalid evidence returns incomplete dimensions before partial semantic processing; no malformed input is allowed to produce matched accounting/cleanup dimensions.

**C3-NW-02:** positions/record offsets/partitions/counts must be safe nonnegative integers; only committed offsets retain their explicit null meaning. Boolean, fractional, object/array/string, unsafe, nonfinite and negative/sentinel values are rejected. Offset relationships and record/receipt/commit references remain checked. Valid empty committed-null/log-end-zero, established baseline4and safe-integer boundary controls still pass.

C0 also closed a related correspondence gap: every established canonical group baseline must agree with its prior observation, and a negative case cannot fabricate null/zero/stale positions, grow its observed log or regress its log end. These are controlled fixture observations, not direct measurement of every forbidden topic/group offset. The actual forbidden client target and typed-denial/control requirements remain unchanged.

The native Go code, engine/binder behavior, tenant ACLs, plan/record budget, sink schema/Store and actual runtime image pins were not changed. The public JavaScript source manifest was regenerated for the corrected auditor. No old sealed event stream, historical audit output or result was relabelled or overwritten.

## Executed checks

| Check | Result |
| --- | --- |
| Standalone auditor schema/domain mutations and valid controls | 445PASS |
| Binding / review / sink-export suites | 8/37/18PASS |
| Top-level Go race tests | 22PASS; subtests not counted twice |
| Total regression checks in the full helper | **530PASS** |
| Host build and public k6inspect | PASS; no k6run or native clients |
| Synthetic SQLite/export/semantic replay |182events,16reported commits, byte/semanticPASS; not Kafka delivery evidence |
| Original three C3probes | Old published auditor accepts; corrected auditor rejects all3after recomputed hashes/seal |
| Four extra baseline/log-growth controls | Old accepts; corrected rejects all4 |

The mutation suite independently enumerates mandatory fields for every event, including partial lifecycle types absent from a successful transcript. It retains conditional/type/link mutations, negative/Boolean/fraction/sentinel/null/nonfinite/unsafe offsets and valid upper boundaries. The two controls accept the unmodified complete synthetic fixture, so rejection is not achieved by refusing all input.

Full-helper command, from kaas-demo:

```sh
python tests/tenant-r2-native/check_offline.py \
  --go /home/gunger/go/pkg/mod/golang.org/toolchain@v0.0.1-go1.26.4.linux-amd64/bin/go \
  --output /tmp/kaas-r3-00-offline-20261126
```

The helper uses cached Go1.26.4/CGO/k6v1.7.1/librdkafka2.14.0 with module lookup disabled. It runs local Go/Node/Python fakes, temporary SQLite/process faults and in-memory handler requests; no service listener or Kafka client is started. It runs `k6 inspect`, never iterations. The separate exit-iteration suite was not repeated because entrypoint/exit behavior was unchanged.

All43source fingerprints match [offline validation](evidence/offline-build-validation.json). Native binary SHA256 remains `0174513d51947fb65aa17ae70f85fea19f7ed5a605aae0ca6d016d8e1cd94cc0`; candidate runtime-source manifest is `9af2ea57aaf851bb4855696ea0f9072ab7f4643a1b64441c9ea47f6bdf6627ff`. No binary is committed. Actual deployed image/source pins remain41f328c8.../07f7bd42...; that image does not contain the hardened offline auditor. An offline re-audit does not require rebuilding/redeploying it.

## Original sealed R2 evidence re-audit

[Receipt](evidence/reaudit/receipt.json), [semantic result](evidence/reaudit/semantic-reaudit.json), [byte/schema verifier](evidence/reaudit/byte-integrity.json). This is the same physical attempt `05a3f2d-retest-20261126`, result checkpoint072eb18, exact182-event export SHA256 `18ba064608624da60e80101aaea81af9f0e8bfe9f4edbed126cc5903dd66c96e`.

The corrected tool returns **NATIVE_EVIDENCE_MATCHED**, fourpositive/eightnegative cases,16confirmed commits and no issues. Byte/hash/chain validation returns VERIFIED. The original 16positive records, four typed-rejected negative writes and external committed/log-end offsets4→8remain reconciled. This is saved runtime evidence, not a fresh execution, health/offset query or test.

The re-audit tool hashes every historical portable result file before/after and validates the new auditor's public source manifest plus tool hashes. Historical event bytes, seal, original successful audit, previous run exports and custody records remain unchanged. The new results are additive. Saved external Pod/controller/Admin metadata remains the execution provenance; an offline auditor does not attest a new broker contact.

```sh
python qualification/r3/r3-00/reaudit.py \
  --output /tmp/kaas-r3-00-new-reaudit-directory
```

Use a new output directory; existing directories are refused. `reproduce-findings.mjs` replays the original synthetic field/offset probes and the added continuity probes against an extracted published072eb18auditor and current code. Its CLI requires explicit plan, synthetic export/seal/observation directory, absolute baseline-auditor module path and new result path. [Adversarial control receipt](evidence/adversarial-controls.json) records both source hashes; it does not modify the C3owner's original probe files.

## Disposition and next work

[Machine-readable result](result.json): C3-NW-01/02 **FIXED_OFFLINE_VALIDATED_C0_TECHNICAL_DISPOSITION**; R3-00 offline fix/regression/re-audit task complete. Original owner OPEN/P2snapshots remain historical until their owners record concurrence; no new owner signature is claimed. The accepted bounded R2run stays accepted and was not rerun. R3service/runtime/production qualification is still separate.

The published planning contract remains its original disabled proposal; [progress overlay](../progress.json) records this completed offline case. Historical planning checks that say findings are open describe the pre-correction snapshot and do not override this exact-source result. Publication freezes this offline correction. Later work may map R3-10sink-failure/R3-11deadline coverage or prepare the selected next case. Do not automatically rebuild an image, rearm the old Jobs, repeat R2or run another workload.

Seven-day sandbox+workspace custody for the accepted R2export remains through at least2026-12-03T15:12:05Z. No automatic cleanup, credential operation, storage allocation, source policy change or infrastructure fault was authorized/performed by this work.
