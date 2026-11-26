# R2 single bounded run — incomplete, 2026-11-26

**One authorized attempt executed; R2 acceptance did not pass.** Source pinned to `a85b42854753fbb42eb55aaadbe9fcf7aec21b56`; reviewed native source and image digests were unchanged. The fixture stopped before the first send. It was not automatically retried.

| Result | Observation |
| --- | --- |
| Job start | 2026-11-26 13:08:54 UTC |
| Container end | 13:09:03 UTC (API timestamp has second precision) |
| Native elapsed | 9,430 ms; terminal event at 9,422 ms |
| Conservative external completion observation | 14,173 ms, below 300-second ceiling |
| Fixture status | `NATIVE_INCOMPLETE` |
| Kubernetes / process status | Job Complete / exit 0 — **not accepted as a passing test** |
| Planned positives / attempted | 16 / **0**; all 16 remain unattempted |
| Planned negatives / completed | 8 / **0** |
| Original value bytes attempted | **0**, within the 20,000-byte ceiling |
| Durable evidence | Eight events, valid hash chain, terminal present; owner stopped and sealed sink |
| Independent semantic audit | `NATIVE_INCOMPLETE`, zero matched positive/negative cases |
| Final state | Client Job re-suspended, no running client process; sink 1/1 Available, PVC Bound and preserved |

Five minutes was the maximum bound, not a requirement to pad the run. The reviewed single-iteration fixture ended early on failure. There was one fixture attempt and no retry. Read-only metadata refreshes before and after are separate from the fixture.

## Execution and stop record

`execution-stop-evidence-record.json` records the user's explicit authority, pinned source/image/binary/plan evidence, owner/executor, exclusive four-group window, startup-inclusive timing, stop controls and seven-day/shared-workspace custody plan. Per-run execution gates referenced existing coordinator C3/C6 contract/source checks, actual image/credential/network/storage checks and the final containment/export procedure. They are preconditions and controls, not proof of successful future behavior or independent specialist signatures.

Before launch, current Kafka/topics were Ready; fresh actual Admin metadata confirmed RF2/ISR2, empty topics and absent groups. The sink had zero events and flags. Created a distinct client arming ConfigMap and a one-shot runtime ConfigMap, preserving the original disabled controls. The client Job was first created suspended, then resumed. Its controller start time supplied the immutable runtime start clock before the Pod could mount that runtime. This charged startup to the same 300-second budget.

Controls were: one iteration, backoffLimit 0, Job deadline 300s, process TERM at 285s with KILL after five more seconds, and an external two-second observer with conservative stop at 295s or explicit stop request. The timeout path was armed but **not exercised**; the process ended earlier. Actual termination and final offsets were observed. No cancellation or failure-recovery guarantee is inferred from this short run.

After termination, re-suspended the Job, then used the separate owner capability to stop, seal and export the sink over verified TLS. Removed the two metadata-only refresh Pods and their script ConfigMap. Preserved the Job/completed client Pod, per-run immutable records, sink/PVC, credentials, records/groups and all evidence. No offsets were reset and no messages/topics/groups were deleted. The run authority is consumed; its old start clock cannot be reused for another attempt.

## Message and offset reconciliation

The sealed stream contains: fixture start, positive phase start, first case start, initial group state, first consumer open, its close, stop and incomplete terminal. It contains **no producer-open, send intent, send outcome, receipt or commit**. Every evidence HTTP operation reported success; this does not prove native client setup succeeded.

| Topic and literal `<topic>-group` | Pre / post log start | Pre / post log end | Pre / post committed | Final members |
| --- | --- | --- | --- | --- |
| `kaas-sbx-a-events` | 0 / 0 | 0 / 0 | null / null | 0 |
| `kaas-sbx-a-audit` | 0 / 0 | 0 / 0 | null / null | 0 |
| `kaas-sbx-b-events` | 0 / 0 | 0 / 0 | null / null | 0 |
| `kaas-sbx-b-audit` | 0 / 0 | 0 / 0 | null / null | 0 |

The first group now exists empty; the other three remain absent. This is a group lifecycle change, not an offset commit. `null` means no committed offset. All four partitions retained RF2/ISR2 after the run. No acknowledged/sent records are missing because none were attempted; successful delivery, isolation and no-loss behavior remain **unestablished**. Four planned negative-write originals were also not attempted, making 20,000 planned original bytes unattempted in the semantic accounting.

The fixture reported its opened consumer closed, and the process physically terminated. The semantic auditor's cleanup dimension remains INCOMPLETE because the full expected handle/case denominator was never reached; its generic `missing_terminal_or_open_clients` issue does not establish a leaked process here. The terminal event is present and byte-verified.

## Findings requiring correction

**R2-LIVE-01 — initial consumer setup/position boundary.** Verified: the first consumer opened, then the run stopped before any producer-open or send intent, reporting `client_or_evidence_failure`. The operation-level native error is not retained. The approximately six-second gap matches the native `Position` deadline on an initially empty partition, making initial-position establishment the likely cause. That is an inference; the source boundary could also include the following producer construction. Preserve sanitized operation/error detail and correct the actual behavior before a new run. Do not seed messages or reset offsets to bypass the check.

**R2-LIVE-02 — false-positive process/controller completion.** Verified: the fixture logged `NATIVE_INCOMPLETE` and threw `tenant_fixture_incomplete`, yet k6 exited 0 and Kubernetes marked Complete. Process status must reflect incomplete fixture outcome. This record uses sealed events, semantic audit and external offsets as acceptance evidence, so the Job status was not treated as a pass.

No code/image fix or second fixture run was performed in this request. A subsequent attempt needs corrected/reviewed runtime behavior and a fresh, explicitly authorized execution/sink identity; the preserved stopped/sealed sink must not be cleared or silently reused.

## Evidence custody

The sandbox's isolated `kaas-r2-native-evidence` PVC retains the stopped/sealed database and eight events. A byte-identical export and seal were copied to shared workspace `docs/testing/runs/r2-native-20261125-bounded-20261126/`, with control-plane snapshots, public execution scripts, observation log and file manifest. No API bearer, password, token value or private key is exported.

Export SHA256: `91cf8d49ca2091a3d0900cc6a8cec9b3b9fca0c9b0b60b49f23e003d5369c3e6`. Local bytes match the sandbox seal; the separate Python byte/chain verifier passed. The separate JavaScript semantic auditor returned INCOMPLETE and exit 2 as expected for this run. Its file-only report does not independently attest broker execution; actual Job/Pod/image/log and pre/post Admin snapshots supply external provenance.

Selected sanitized results, stream/seal, auditors, reconciliation, findings and custody record are alongside this guide. Trailing whitespace was trimmed only from the published log display; its raw/display hashes are in the publication receipt, and the original raw log remains in shared evidence. Sealed event bytes were not changed. Full external evidence is in the shared directory above. Retain through at least **2026-12-03 13:09:03 UTC**, with no automatic deletion. Hash-verified workspace export satisfies the selected second-copy procedure; it is not an infrastructure disaster-recovery test. Sandbox lifetime remains externally controlled.

The user authorized Git publication of the documentation and sanitized result artifacts. Their owning commit identifies the published snapshot; original run receipts retain their execution-time publication status. **This execution request is completed; R2 acceptance remains incomplete pending the two findings.** No throughput, production isolation, recovery or 24-hour qualification follows from this attempt.
