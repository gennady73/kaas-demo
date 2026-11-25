> Portable publication copy. Source revisions and coordinator-only references are listed in the C7 publication provenance; historical results remain scoped to their original review dates.

# Incident response and evidence custody

Revision 0.1; PROPOSED support contract. C7 coordinates procedure/evidence, C3 owns result classification, named run owner controls active Jobs/collector/observer, C4 owns Kafka/GitOps, C1 owns platform/storage interface, C5 governance and C6 access. Actual support/on-call names, escalation route and response SLA must be supplied at R1. No outbound notification or live command executed by this document.

## Triage

1. Record UTC detection time, incident/run IDs, affected deployment/tenants/topics/groups, last successful observation, operator/Kafka/metadata/client versions, source pins and what is unavailable. Preserve both first-impact and detection timestamps; do not shift the recovery clock to exclude detection delay.
2. Have the authorized run owner capture worker/observer/collector status, exit/deadline/stop reason, exact registered plan, immutable source ConfigMaps, image IDs, restart deltas and time-bounded logs. C4/C1 capture Kafka Ready/current generation, quorum/ISR/partition leaders, topic configs/offsets, PV/PVC identities and infrastructure events. Collect metadata only; never dump Secret values or full native debug configuration.
3. Preserve collector evidence with a consistent export, seal and hash manifest, retaining incomplete exports/seals too. A SQLite copy must be a supported consistent snapshot/backup; copying only a live main DB can omit WAL transactions. Preserve original bytes before conversion. Record acquisition time, byte count, SHA-256, source UID/path and custodian. If retrieval fails, document the gap and protect the existing PVC; do not restart/delete the collector merely to retrieve it.
4. Separate collection-path failure from Kafka service failure using timestamps, latency, timeouts, CPU throttling, DB/WAL growth, TLS/disk metrics and client progress. A healthy Pod or low mean CPU does not prove request success. Compare failures with heartbeat/idle/native/request timeouts.
5. The run owner applies the approved stop/drain/deadline policy if needed. C7 does not modify another owner's active experiment. Avoid automatic reruns or input edits; freeze failed outcomes and create a fresh run identity for any separately approved rerun.
6. Reconcile offline using the exact pinned C3 auditor and registered plan, then verify terminal Jobs, lifecycle timing and cluster/restart observations. A seal or matching partial counts alone is insufficient. Keep raw and derived artifacts separately, record tool revision/command/output and give C0 the scoped conclusion.

## Classification (categories can coexist)

| Evidence | Classification / required conclusion |
| --- | --- |
| Broker/quorum/network availability loss with client impact | Service incident; measure write/read and recovery separately; reconcile durable records |
| Collector/observer/native adapter error, timeout or deadline | Harness incident; test may FAIL even when every observed ACK has a receipt; service cause remains evidence-dependent |
| Planned IDs with no attempted send | Unsent demand; shortfall of workload coverage, not missing acknowledged Kafka data |
| Attempt without terminal ACK/error | Ambiguous in-flight send; reconcile Kafka/source and deduplicate by ID; never assume unsent or lost |
| ACK without required receipt after bounded reconciliation | Suspected missing accepted data; preserve offsets/IDs/hashes and investigate retention, read/ACL/config and service behavior; cannot PASS |
| Receipt without durable business effect/commit | Replay/side-effect responsibility open; receipt is not proof of external sink completion |
| Missing lifecycle/ledger/metrics/clock/Job evidence | Incomplete evidence; cannot establish the affected acceptance claim even when counts agree |
| Required unread data expired | Preservation failure/conflict; report policy expiry mechanism without waiving the no-loss objective |

The original continuity failure's 49,175 matched IDs and 50,825 unsent planned IDs illustrate the distinction. The first short run delivered 1,040 records but failed during drain. Later query counters/TLS fixes and a repeated short PASS do not erase either failure. The collector's synchronous commit-before-ACK path and durable-receipt-before-consumer-commit ordering are implementation evidence, not independent adversarial attestation or a business exactly-once guarantee.

## Retention, security and closure

Store raw ledgers, complete/incomplete seals, negative outcomes, plan/source/image fingerprints, config and timestamped metrics until C3/C0 review and the named retention owner authorizes disposition. Proposed minimum lifecycle is through release decision, incident closure and the separately selected audit period; a duration is deliberately OPEN. Verify restore/readability from the second copy and custody manifest before any cleanup. Store secrets through C6's approved custody/recovery mechanism; sanitized evidence must retain a restricted original only where policy permits. The historical credential leak is recorded in the [smoke result](../smoke-test-result-2026-11-23.md); do not infer external log erasure.

Closure record: impact, timeline, proven versus suspected cause, affected acceptance claims, exact correction/config versions, regression evidence, remaining gaps and named action owners. Restoration is not acceptance; resume/promotion requires the relevant C3/C4/C0 review. No automatic recurring checks, credential rotation or external messages are introduced.
