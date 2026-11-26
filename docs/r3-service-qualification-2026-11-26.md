Current contract update: [R3-01 configuration, authority and GitOps review passed offline](../qualification/r3/r3-01/README.md), including additive C4-NR-05 mount reconciliation. Effective permissions and lifecycle execution were not refreshed/run. Latest C3v1.2 accepts the exact published auditor extension offline; C6 concurrence remains separate.

Current coverage update: [R3-10/11 sink failure and deadline regressions passed offline](../qualification/r3/r3-10-11/README.md): 550 native/helper checks plus 18 packaging checks. Runtime failure-path qualification remains separate; no live action or image-pin change.

Current progress, 2026-11-26: [R3-00 auditor correction and sealed R2re-audit passed offline](../qualification/r3/r3-00/README.md). See [progress overlay](../qualification/r3/progress.json); the original planning statuses and copied evidence below remain historical. All four Jobs untouched/lastobservedsuspended; no workload ran.

# R3 service qualification plan

Revision0.1, 2026-11-26. **OFFLINE_PLAN_VALIDATED; DEPLOYMENT, REGISTRATION AND WORKLOADS DISABLED.** This plan selects no run window and grants no new live authority. The existing four client Jobs are untouched and last observed suspended. No cluster access, probes, workloads, faults or notifications occurred in this preparation. The user authorized publication of this plan; publication grants no live execution authority. Original preparation receipts retain their historical status.

Planning contract: [plan.json](../qualification/r3/plan.json). Owner/source review: [C1–C7 handoff review](../qualification/r3/handoff-review.md). Offline consistency checker: [validate_plan.py](../qualification/r3/validate_plan.py). It reads local files only and cannot execute a scenario. Preserved [offline review and validation receipts](../qualification/r3/evidence/README.md) accompany the plan.

## Starting point and assurance disposition

Use published evidence commit `072eb185b32ca39b6ecaebf5b6c78e9569145d2e`, with [successful R2result](r2-05a3f2d-retest-2026-11-26/README.md), [closeout](r2-05a3f2d-retest-2026-11-26/r2-closeout.json), [reconciliation](r2-05a3f2d-retest-2026-11-26/message-offset-reconciliation.json) and [seal](r2-05a3f2d-retest-2026-11-26/seal.json). Native source05a3f2d/image41f328c8... delivered16positive records and passed8typed negative cases in29,528ms external elapsed, with no missing/duplicate receipts or uncertain commits. Group committed/log-end offsets were8, members0. These are dated observations, not fresh health checks or fixed future starting positions. R1creation at3211df9 and the earlier2 MiB smoke remain separately scoped reusable evidence.

**R2 runtime PASS remains recorded. Two standalone-auditor assurance findings are OPEN.** New C3/C6handoffs identify C3-NW-01(required fields/types/case-record links) andC3-NW-02(impossible offset domains) in the unchanged auditor. Their synthetic, correctly rehashed malformed transcripts were accepted. They do not demonstrate corruption of the actual live export. Planning inspection verifies that the182 real events contain the specifically implicated case/durable links and valid offset domains; this does not fix the general auditor defects or generally certify the standalone auditor. C3 handoff0.9 now explicitly accepts the successful bounded R2 fixture and keeps auditor hardening separate.

The first R3 work package is therefore **offline auditor correction, regression coverage and re-audit of these same sealed bytes**. Keep the original outputs; append corrected tool/source/hash/disposition. Do not rerun R2 clients merely because an offline verifier changes. The published scoped closeout is historical evidence, while the new C0assurance overlay records the outstanding review condition.

## Service boundary and actors

Tenant producer/consumer services are actors outside the Kafka service boundary even when they run in the same air-gapped OpenShift cluster. Outside-cluster applications remain in scope when their actual network/advertised endpoints are selected. Human request/review/sync authority belongs to the GitOps control interface. Registry/identity/monitoring/persistence services are supporting interfaces whose evidence must be attributed to the relevant Kafka-only or composite KaaS claim. Co-location does not turn a supporting service into proof that its integration is qualified. Kafka cluster interconnection is still outside current scope.

## Scope and exclusions

Propose sandbox-core qualification first: shared tenants on existingkaas-dev, internal TLS/SCRAM, RF2/minISR2, retention21,600,000ms, existing broker/operator/GitOps namespaces and user as accepted sandbox owner/approver. Reuse existing storage and evidence services after applicable later headroom/health checks; no new brokers/nodes/PVCs are allocated by this plan. ProductionVSAN/plannedODF and dedicated-per-tenant deployment remain required distinct configurations, not properties proved by this sandbox.

Three result tracks prevent an oversized release gate:

1. **Offline assurance and preparation:** source/auditor repair, evidence reconciliation, policy/contracts, monitoring mapping and runnable-package design. These can progress without sandbox workloads.
2. **Selected sandbox service cases:** only specific uncovered functional/security/operations claims with bounded traffic, exact inputs and later explicit authorization. Reuse already passing R1/R2claims.
3. **Conditional or target qualification:** registry, payload/quota, recovery, full-day continuity and real target capacity/dedicated/external-client combinations, each with its own prerequisites and result. A sandbox-core milestone is not a full-service or production acceptance waiver.

Gravitino remains user-deferred. Kustomize stays current; Helm evaluation is deferred. ODFmigration, VM/baremetalKafka provisioning and independent Kafka-cluster interconnection are not introduced. Outside-OpenShift applications remain in scope, with their specific endpoint/firewall profile unqualified until supplied and selected.

## Finite case sequence and exit criteria

All cases below are PLANNED_NOT_EXECUTED. Owner assignments are artifact responsibilities, not new messages to other chats. Exact acceptance/dependencies are in the JSON.

| ID | Qualification package | Evidence reused / exit condition |
| --- | --- | --- |
| R3-00 | Offline evidence assurance (C2/C3/C6/C0) | Fix NW-01/02; all mandatory/type/link/offset mutations reject after proper rehash; real sealed182-event export still passes; preserve historical outputs. No new live fixture. |
| R3-10 | Evidence-sink failure boundaries (C2/C1/C3/C7) | Map and reuse the18existing sink tests covering crash/commit/ACK/reopen/retry/conflict/disk/read-only/export boundaries; add only uncovered version/protocol cases. Local process persistence is not inherited infrastructure survival. |
| R3-11 | Deadline/late-call containment (C2/C3/C4/C7) | Reuse bounded/quarantine/late-success/exit regressions; identify actual stalled-send/poll/commit/sink/close and external-stop gaps. Normal R2completion does not prove a timeout path or SDKcancellation. |
| R3-01 | GitOps/lifecycle/configuration (C1/C4/C6/C7) | Reuse R1creation/manual governance and currentpins; reconcile C4-NR-05document/mount mismatch; validate unauthorized changes offline and actual actor rights at the later boundary. Any live canary update uses a separately reviewed reversible diff. |
| R3-02 | Trust, credentials and network boundaries (C6/C1/C4/C3) | Reuse eight typedR2denials; cover selected missing wrong-password/CA/hostname, metadata/admin or forbidden-peer cases with working controls and intended-layer failures. No inference of hostile Secret isolation from the trusted four-credential harness. |
| R3-03 | Observability, stop/support and custody (C1/C7/C3/C4) | Inventory existing metrics/rules/receivers, map service symptoms to actionable ownership; approved safe signal/delivery evidence; named run custodian and verified seven-day/export controls. Component presence remains reported/deployed, coverage is what needs verification. |
| R3-04 | Current tenant payload boundary (C2/C3/C1/C4) | Reuse historical2 MiB smoke with exact scope; if selecting a new tenant-path claim, a capable reviewed client handles four2 MiB values plus declared controls and reconciliation. No implicit >2MiBlive test or offloading. |
| R3-05 | Quota scope and bounded interference (C2/C3/C6/C1/C7) | Freeze user/client/broker quota scope and Aoffered-load/Bcontrol schedule; observe throttle and agreed Bimpact/lag; reconcile originals. Configured quotas alone do not establish aggregate tenant admission/fairness. |
| R3-06 | Governance/registry branch (C5/C6/C4/C7/C3) | After budget/Secret/import/window approval, stage operator→DB/realm→registry, preserve existing SSO, test compatibility/role/audience/ownership, persistence and replay. Existing C5source fixes are not applied grants or deployment evidence. |
| R3-07 | RST-01–04 no-loss recovery (C1/C2/C3/C4/C6/C7) | Versioned non-delete actions, source buffering/uncertainty ledger, inherited storage scope, approved clock/variant and reconciliation within10,800s. Begin with one controlled broker only after explicit disruptive authorization. |
| R3-08 | Final continuity / target capacity (C2/C3/C1/C7) | Previous16011record run stays stopped/reconciled, not24hPASS. Later final-phase100MB/24hcontinuity is separate;2TB/20TBprofiles run separately on suitable target infrastructure, not this small sandbox. |
| R3-09 | Configuration-specific release assessment (C0+C1–C7) | Publish a claim/evidence matrix naming scope, verified/deferred/open rows and residual risks. R3 sandbox-core requires00–03plus the applicable failure/containment evidence in10–11; selected conditional claims add their own cases. Whole-service/production qualification requires all applicable mandatory requirements, not merely the sandbox-core rows. |

## Proposed budgets and adapter gaps

No budget below is allocated or an executable profile. Future per-case approvals must freeze actual offered-byte/record/event limits and a startup-inclusive deadline; no unbounded retry, drain or end-spike is permitted.

| Profile proposal | Maximum client time | Original value-byte ceiling | Additional condition |
| --- | --- | --- | --- |
| Small functional/trust case | 300s | 20,000 | Values≤1,000-bytes; case-specific adapter required, no rerun of closed R2matrix merely to fill time |
| Tenant2MiBboundary | 300s | 10,000,000 | Four2,097,152byte values=8,388,608bytes, leaving1,611,392bytes for explicitly declared controls; no payload>2MiB |
| Quota/interference | 300s | 4,000,000 | Values≤1,000-bytes; offered rate/duration and fairness/lag thresholds remain null until agreed; saved principal quota65,536B/s is not a future effective-state guarantee |
| Recovery observation | Separately selected | Not set | Three-hour recovery objective does not authorize a three-hour client Job or reuse the five-minute fixture as recovery tooling |
| Final continuity | Later24h | 100,000,000 | Separate qualified continuity/evidence implementation and explicit final-phase instruction; not selected now |

Inspected R2native Produce accepts exactly1,000-byte values and at most20 unique sends. Its logical plan/source bindings are frozen. The tenant Store caps1,024events,32 MiB database and requires64 MiB free space. The actual R2export is133,054bytes/182-events; this is an observation, not a sizing upper bound. Payload/quota/continuity/recovery cases need explicit adapter and evidence-volume work; changing JSON values or unsuspending an old Job cannot supply those capabilities. No client/evidence cap is relaxed in this preparation. Existing1 GiB PVC free space, WAL/export coexistence and retained failed attempts must be budgeted before a later case, with no automatic evidence cleanup.

C5 branch resource proposal is950mCPU/1152Mi requests,3CPU/2816Mi limits and a new10GiPVC. Import-overlap totals1050m/1408Mi requests and3.5CPU/3328Mi limits exclude OLM/rollout overhead and existing Keycloak/platform use. These are inspected C5numbers, not approved/admitted allocations. Use corrected bootstrap707da20 while retaining four resource Application pins atd8dac19; ordinary future plan/admission/authority checks still apply. Secret/trust delivery and administrator one-shot creation-only kaas-c5-pocrealm import need named owner/window; existing OpenShift SSO remains protected. This branch is not a hidden prerequisite to preparing broker-only cases.

## Recovery and capacity contract

Preserve RF2/6h/no-loss/3h objectives. With acks=all and ISR below minimumISR2, affected writes can be unavailable; a write rejection is distinct from loss of acknowledged records. Quorum placement matters on three dual-role pods. [Kafka 4.2 topic semantics](https://kafka.apache.org/42/configuration/topic-configs/) underpin the plan; no automatic RF/ISR/retention reduction or unclean election is a recovery action.

C7 proposes t0=first disruption/impact and t1=restored required service/quorum/ISR, caught-up/reconciled records and stable progress. Proposed stability window300 s needs approval before recovery execution; the three-hour maximum remains10,800s. Preserve acknowledged, ambiguous, unsent, received, committed and replayed sets; durable receipt before commit does not imply exactly-once external side effects. R2's stop-on-error/no-buffer fixture is not a restart/replay harness. Define source buffering/side-effect idempotence and evidence outside the affected failure domain before any disruption.

Use `oldest_unread_age + outage_to_service + catchup + safety_margin < effective_history`; if using an observed complete RTO already including catch-up, do not add catch-up twice. Expiry does not waive the no-loss objective. Reuse DEP-PERSIST-01 supplying project/owner/version/failure scope and evidence; no duplicate infrastructure destruction test is added as a load-only prerequisite. RST-04 is later Kafka integration evidence against inherited survival, not a second storage certification.

For decimal uniform producer values and RF2, six-hour retained replica payload is about1TB at2TB/day or10TB at20TB/day, excluding protocol/index/skew/reserve/storage redundancy. Sandbox3×20Gi=64,424,509,440allocated bytes is not target capacity. Keep alternatives separate and avoid a fixed burst factor; application timing may be unknown. Assess the reported five-total-CPU target through explicit xk6envelopes rather than invent a CPU minimum. WP-A's upper10Mpayload still needs target size feasibility beyond current3MiBprotocol ceiling; no custom claim-check selected.

## Execution, evidence and stopping rules for later packages

Every later case needs a concrete reviewed source/image/configuration, expected outcomes, exact budget and unique physical Job/database/run identity. Refresh only relevant health/ISR/headroom/policy/trust/group positions at that boundary; never infer zero/8/latest or reset offsets from old evidence. Select idle owned groups with a retained reconciled baseline. Keep all four R2 Jobs suspended; do not rearm consumed runtime ConfigMaps or write into sealed databases.

Stop traffic and later cases on unexpected access, evidence/durable-ACK failure, unresolved client outcomes, budget/deadline exhaustion, shrinking retention margin or unapproved Bimpact. No retry extends the authorized experiment. Observe actual process termination before sink stop/seal/export, reconcile late outcomes and offsets, and retain FAIL/INCONCLUSIVE honestly. Apply the native/process/Job/external deadline appropriate to the new harness; facade wait bounds do not cancel SDKcalls. No prune/delete/restart/credential rotation/operator upgrade is an automatic cleanup or recovery step.

Maintain distinct attempted/acknowledged/definitively rejected/unresolved/unsent original value bytes and per-group consumption/replay. Required evidence includes immutable source/image/profile/seed, pre/post configuration/offsets, typed negative controls, lifecycle/deadline observations, metrics, sealed event export/hash/chain and independent schema/semantic audit plus actual external provenance. Ledger size/event/data-retention guards must be planned before execution. Preserve prior artifacts and seven-day sandbox/workspace copies, at least through2026-12-03T15:12:05Z for R2; no deletion automation. Confirm ongoing custodian/disposition with C7. A reference string or DRAFTtemplate is not an enforced policy or independent signature.

## Decisions needed later, not to finish this offline plan

Resolved and reused: sandboxshared-first/kaas-dev, user as owner/approver, existing TLS/SCRAM, RF2/minISR2/6h, manual GitOps and seven-day+workspace evidence policy. Do not re-request them.

- Decide whether/when the registry branch joins the sandbox milestone and approve its explicit additional resource/Secret/import package.
- Before disruption, approve exact restart category/variant/window and proposed recovery clock/stability/preservation contract; obtain inherited storage evidence from its owner.
- Before claiming performance/fairness or external-client service, select the operating envelope/SLOs and actual external network/endpoint fixture. These are not required for offline auditor repair.
- At each selected future live step, authorize the concrete reviewed package and window. No approval is requested or pending now; no five-minute unanswered-question timer is active.

Next recommended task: correct C3-NW-01/02 offline, add regression tests and re-audit the original R2export with versioned tools, keeping all four Jobs suspended. Do not add a live R2repeat unless changed runtime behavior or actual evidence defects justify it.

Primary checks made2026-11-26: [Kafka 4.2 topic configuration](https://kafka.apache.org/42/configuration/topic-configs/), [authorization boundaries](https://kafka.apache.org/42/security/authorization-and-acls/), [quota entity operations](https://kafka.apache.org/42/operations/basic-kafka-operations/). Version-specific behavior is reviewed; exact target compatibility, runtime coverage and future SLOperformance remain unqualified.


Concurrent-source observation: during final planning checks, the working auditor and runtime-source manifest changed outside C0's declared planning edit scope. They were preserved, not executed or accepted as part of this plan. Use the published baseline above; consume a completed owner correction/test handoff for R3-00 rather than duplicate or overwrite ongoing work. Exact observed hashes are in shared `docs/coordination/r3-preparation-2026-11-26/concurrent-source-observation.json`.
