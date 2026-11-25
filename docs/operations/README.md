> Portable publication copy. Source revisions and coordinator-only references are listed in the C7 publication provenance; historical results remain scoped to their original review dates.

# C7 operations and release package

Publication update: C0 accepted the offline-preparation scope and closed C0-C7-RC-01 after correction. The standalone package passes 35 tests and five blank-template CLI checks; see [publication checks](publication-checks.json) and [correction receipt](evidence/C0-C7-RC-01-fix-2026-11-25.json). Service qualification remains OPEN. Source handoffs and earlier receipts retain their historical prepublication status.

Revision 0.2, 2026-11-25 (Asia/Jerusalem). **Ready for review; offline preparation only.** Owner: C7. Requirements: SRS 0.9 SC1–SC4, CAP-01–05, PF-01–08, RST-01–04 and DEP-PERSIST-01. C0 owns shared baselines; this package proposes operational contracts for consolidation through the [C7 handoff](../handoffs/C7-operations-release.md).

| Artifact | Purpose |
| --- | --- |
| [Minimum input checklist](input-checklist.md) | Known inputs reused; C7-I01–I12 owner/stage/evidence gaps explicit |
| [Five evidence templates](templates/README.md) | Deployment support, incident, recovery result, custody and monitoring records; blank and execution-disabled |
| [Offline record checks](offline-record-checks.md) | Repeatable local template/record diagnostics with synthetic negative cases; no evidence retrieval or acceptance |
| [Deferred Helm evaluation](helm-deferred-evaluation.md) | User-required later packaging evaluation; Kustomize remains current |
| [Monitoring and ownership](monitoring-and-overload.md) | Existing stack inventory, coverage, signals, proposed response and access/owner gaps |
| [Budgets](capacity-and-evidence-budgets.md) | Retention, catch-up, storage and evidence calculations with explicit assumptions |
| [Incident procedure](incident-and-evidence.md) | Triage, preservation, accounting classifications and evidence custody |
| [Recovery qualification](recovery-qualification.md) | Separate RST-01–04 protocols, no-loss reconciliation and inherited infrastructure interface |
| [Release runbook](release-runbook.md) | R1 support, deployment, rollback and manual upgrade gates |
| [Release matrix](release-matrix.json) | Environment/configuration-specific evidence and open qualification claims |
| [Offline helpers](../../operations/README.md) | Local calculation/check commands; no network or deployment operations |
| [Source snapshot](source-snapshot-2026-11-25.json) | Inspected local source hashes and repository revision |

## Evidence boundary

VERIFIED locally: source manifests select Kafka 4.2.0, RF2, minISR2, 6h, internal TLS/SCRAM, three dual-role nodes and retained 20Gi gp3 claims. Historical deployment evidence reports metadata 4.2-IV1, OpenShift 4.21.42, Streams CSV 3.2.1-10 and GitOps operator 1.22.3; these are not fresh health/compatibility observations. Sandbox gp3 does not qualify current-target VSAN or planned ODF. Dedicated/shared profiles remain offline scaffolds with unresolved I1–I5 inputs.

Recorded execution, read rather than rerun by C7:

- Initial 24h follow-up (coordinator-only reference: `docs/testing/continuity-followup-2026-11-25.md`; see publication provenance): FAIL after about 11h48m. 49,175 acknowledged/received/committed IDs; 50,825 planned unsent records; incomplete lifecycle. No acknowledged-record loss demonstrated in that ledger; no general no-loss qualification.
- [First short result](../evidence/collector-fix-first-short-failure-2026-11-25.json): FAIL during drain despite 1,040 deliveries, after a 30s HTTP idle limit conflicted with 30s heartbeat.
- [Repeated short result](../evidence/collector-fix-short-result-2026-11-25.json): recorded PASS for 1,040 records/1,040,000 value bytes, worker/observer exit zero, unchanged Kafka restarts. Collector source SHA `02f58ea213a7f2c40bf2173ce1b349ad314b8bef87780ffc2cb911d478926308`; only this short configuration is covered.
- Fresh 24h launch (coordinator-only reference: `docs/testing/runs/collector-fix-20261125/continuity-24h-20261125083551-5d08/launch.json`; see publication provenance): identity `continuity-24h-20261125083551-5d08`, planned generation November 25 08:37:21.488Z through November 26 08:37:21.488Z. The newer [C0 result overlay](../collector-fix-validation-2026-11-25.md) records RUNNING and an initial 23 ACK/receipt/commit checkpoint; final outcome remains pending. No live status query/control performed.

The [collector guide](../../tests/continuity/collector/README.md), original [bootstrap guide](../bootstrap-guide.md), [deployment guide](../kafka-deployment-guide.md) and C4 tenant package remain canonical implementation references; C7 adds operational integration rather than replacing them. No live restart, fault, upgrade, load, sync, migration, publication or automation is authorized by this package.

## Primary documentation checked November 25

| Source/version | Finding supported and limitation |
| --- | --- |
| [Kafka 4.2 topic settings](https://kafka.apache.org/42/configuration/topic-configs/) | ISR/acks condition, independent byte/time retention, segment granularity. Effective topic overrides still require capture. |
| [Kafka 4.2 producer settings](https://kafka.apache.org/42/configuration/producer-configs/) | Acks and idempotence configuration; selected xk6 uses librdkafka and needs its native mapping, not Java defaults. |
| [Kafka 4.2 monitoring](https://kafka.apache.org/42/operations/monitoring/) | Broker/client/quorum signal families; exporter names and deployed coverage unverified. |
| [Kafka 4.2 upgrade](https://kafka.apache.org/42/getting-started/upgrade/) | Metadata changes restrict downgrade; Git revert alone is insufficient. |
| [Streams 3.2 upgrade](https://docs.redhat.com/en/documentation/red_hat_streams_for_apache_kafka/3.2/html/deploying_and_managing_streams_for_apache_kafka_on_openshift/assembly-upgrade-str) / [downgrade](https://docs.redhat.com/en/documentation/red_hat_streams_for_apache_kafka/3.2/html/deploying_and_managing_streams_for_apache_kafka_on_openshift/assembly-downgrade-str) | Separate operator, broker, client and metadata procedure; family guidance does not prove an exact patch pair. |
| [Streams 3.2 persistent-volume recovery](https://docs.redhat.com/en/documentation/red_hat_streams_for_apache_kafka/3.2/html/deploying_and_managing_streams_for_apache_kafka_on_openshift/assembly-cluster-recovery-volume-str) | Recovery depends on preserved volumes/identities and environment-specific reconstruction. No such procedure executed here. |
| [Argo CD stable sync](https://argo-cd.readthedocs.io/en/stable/user-guide/auto_sync/) | General automatic-sync/rollback behavior only. Installed Argo CD server version remains an execution input; GitOps operator 1.22.3 is not that version. |

Checks/limits are recorded in [validation receipt](validation-2026-11-25.json). No independent human reviewer or runtime test is implied by C7's source inspection and offline program checks.

Revision 0.2 adds checklist/templates and deferred Helm requirement only. [Checklist/template validation](checklist-validation-2026-11-25.json) records local structural/link/preservation checks separately from the earlier 10 helper tests; no tests or live acceptance are inferred for these blank forms. Local demo HEAD at this slice is `a0e9e7d50d1f10bf2e79da3e4c5cc60d0e0c2a12`, following C0's collector publication. Earlier source snapshots and validation receipts remain historical and unchanged.
