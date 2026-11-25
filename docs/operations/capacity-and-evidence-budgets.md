> Portable publication copy. Source revisions and coordinator-only references are listed in the C7 publication provenance; historical results remain scoped to their original review dates.

# Capacity, replay and evidence budgets

Revision 0.1. DERIVED planning references, not performance or free-capacity measurements. Decimal original value bytes, uniform input, RF2 and no compression are explicit initial assumptions. Daily alternatives are not combined.

| Workload | Mean original ingress | 6h original values | RF2 replica payload |
| --- | --- | --- | --- |
| WP-A: 2 TB/day | 23,148,148.15 B/s | 500,000,000,000 B | 1,000,000,000,000 B |
| WP-B: 20 TB/day | 231,481,481.48 B/s | 5,000,000,000,000 B | 10,000,000,000,000 B |

Replica payload excludes keys/headers/serialization, indexes/segments, internal topics, skew, rebuild/reassignment reserve, free-space operating reserve, storage-layer redundancy, evidence and supporting services. Compression must be measured. Daily means cannot size unknown concentrated traffic. For each topic/partition use a measured/declared maximum-window arrival envelope for storage planning. Three 20Gi dev PVCs are 64,424,509,440 allocated bytes, not available disk or a TB-profile allowance. No invented CPU minimum: assess the confirmed 5-CPU deployment total using xk6 plus worker/broker throttling. C1 supplies incremental allocations and actual units for RAM/CPU growth.

## Retention and catch-up

Proposed conservative feasibility screen: `oldest_unread_age + outage_to_service + catchup + safety_margin < effective_history`. All terms are seconds for the same partition/group. The boundary at equality is unsafe. This is a planning bound, not a prediction of segment deletion time or proof of no loss. Effective history must account for retention.ms, retention.bytes per partition, cleanup policy, timestamps/segment behavior, topic overrides and actual log-start offsets. Do not credit deletion delays as guaranteed extra retention.

For stable rates with a stalled consumer, backlog after recovery is `preexisting_backlog_bytes + ingress_Bps * outage_s`; catch-up is `backlog / (consume_Bps - ingress_Bps)`. If consume <= ingress, finite catch-up is impossible in that model. Use per-partition rates/skew and an approved upper bound for changing arrivals. A scheduled source pause can change this model only when explicitly selected. Three hours to service restoration does not itself establish full replay within three hours; the recovery acceptance proposal includes reconciliation and catch-up in its clock. Do not double-count catch-up when recording a measured total RTO.

Synthetic fixture: 1h oldest age + 3h outage + 0.5h catch-up + 0.5h safety = 5h, leaves 1h planning slack in 6h. With 2h oldest age the same terms reach 6h and must be rejected. These are arithmetic examples, not allowed tenant lag or outage allocations. Retention expiry of required unread data is an acceptance failure/open preservation conflict; labelling it normal expiry cannot waive no-loss. C0/data owner must define the preservation contract and prevention/replay response before the relevant recovery qualification.

## Evidence resources

Observed failed-run export was 158,037,965 bytes / 49,175 delivered records, about 3,213.79 exported bytes per record including that run's heartbeat/lifecycle metadata. Simple scaling to 100,000 yields about 321,378,678 bytes per export, not a sizing upper bound: heartbeats vary with duration/client count and failed/full lifecycle mixes differ. SQLite DB + WAL + export + auditor SQLite + logs + metrics snapshots + retained failed runs and margin must be budgeted separately. Actual row/disk/WAL/query rates and concurrent export peaks are required. Never apply this sandbox estimate to tiny-record TB tests or assume Kafka input bytes equal evidence bytes.

Current harness references: collector 2Gi PVC (250m/1 CPU, 128Mi/512Mi memory), observer 2Gi emptyDir/3Gi ephemeral limit. Retained outputs on emptyDir disappear with Pod removal; preserve externally first. Inspect measured free space and shared filesystem usage before a later run; a nominal 2Gi request is not free capacity. Preserve 75% observer/80% collector guard semantics from the inspected implementation; configure any future profile's earlier warning/retention/export budget with the run owner.

Proposed evidence custody: immutable original plan/source/image pins and append-only raw exports, checksums, access-controlled second copy, audit DB and metrics over pre-fault through catch-up. Retention duration, storage destination/quota, legal hold and deletion authority remain OPEN owner inputs; never auto-clean negative results to make room. C5 supplies governance backend backup sizes/RPO and replay dependencies; C6 supplies protected credential/trust recovery interfaces. Infrastructure DEP-PERSIST-01 is separate from evidence-storage custody.

Run [offline budget helper](../../operations/README.md) for reproducible arithmetic and explicit unresolved inputs. Its successful exit confirms calculation only; no deployment or release passes as a result.
