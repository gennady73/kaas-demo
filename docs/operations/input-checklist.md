> Portable publication copy. Source revisions and coordinator-only references are listed in the C7 publication provenance; historical results remain scoped to their original review dates.

# C7 minimum input checklist

Revision 0.1, 2026-11-25. Offline preparation is authorized and can continue now. This checklist reuses C4 I1–I5 and stage definitions (coordinator-only reference: `docs/platform/tenant-profile-minimum-inputs-2026-11-25.md`; see publication provenance) and the latest C4 handoff (coordinator-only reference: `docs/handoffs/C4-kafka-platform-gitops.md`; see publication provenance); it does not create a second platform input contract. C0 consolidates shared decisions. A work-area owner below identifies responsibility, not a named person already assigned.

Use references to existing versioned artifacts. Do not supply credentials. Keep unknown values null/OPEN; an artifact being supplied or a reference being filled does not establish review, runtime success or authorization. Record requirement, source/version/date, environment, owner, acceptance criterion, evidence type (inspected/inherited/executed/derived/proposed), review status and remaining gap in the corresponding template.

## Known inputs to reuse

| Input | Reuse / limit |
| --- | --- |
| Baseline | SRS 0.9 plus latest dated C0 overlays; RF2, 6h, no loss and 3h recovery remain selected |
| Packaging | User instruction: keep Kustomize. Existing Streams operator and Kafka custom-resource path remain; Helm evaluation is deferred below |
| Existing deployment | [Dev source/runtime evidence](README.md) gives historical gp3/Kafka/operator/security details; refresh at a later authorized execution boundary, never infer target VSAN suitability |
| Repository | Selected kaas-demo origin and existing ArgoCD control namespace are known; actual candidate resource SHA/path and effective authorization still come from C4/C6 |
| Harness/evidence | [Incident procedure](incident-and-evidence.md), collector guide and retained failed/short-run evidence are reused; the active day run's final acceptance belongs to C3/C0 |
| Presence of services | Monitoring/overload and registry/Gravitino are reported present; request configuration/version/coverage artifacts rather than reopen presence as unknown |

## Minimum additional inputs by gate

All entries below remain OPEN for the selected future deployment unless accepted applicable evidence is attached. No real tenant, budget, contact, endpoint or approval has been invented.

| ID | Minimum answer / evidence | Owner | Needed by / template |
| --- | --- | --- | --- |
| C7-I01 | Reuse I1: selected target, dedicated/shared scope, tenant/cluster/namespaces, initial workload boundary and resource collision exclusions | C0/C1/C4 | R1; deployment support |
| C7-I02 | Reuse I2: approved incremental CPU/RAM/PVC/evidence allocation, actual units/storage interfaces/failure domains; reference C4 topology and C1 measurements | C1/C4 | R1 allocation; R3 performance; deployment support |
| C7-I03 | Named change executor, incident lead/backup, infrastructure/security escalation route, rollback decision authority and window | C0/C4/C6 | R1; deployment support |
| C7-I04 | Reuse I3–I5: initial access/admission/lifecycle policy, watch/controller scope, approved Git revision/path, sync/prune/delete authority, rendered diff and reversible boundary | C4/C6 | R1; deployment support. C7 does not edit their manifests |
| C7-I05 | Credential/CA delivery and recovery references, native acks/retry/buffering/group/commit mapping, client stop/deadline limits | C6/C2/C4 | R2 activation; recovery result. Not a universal offline/R1 prerequisite |
| C7-I06 | Existing monitoring versions/exporters, actual query/rule/label/window/threshold definitions, missing-series handling, receiver/escalation, retention and overload-control authority | C1/platform monitoring owner/C4 | R1 support visibility as agreed; full coverage R3; monitoring evidence |
| C7-I07 | Evidence store/custodian, accessible destination, quota/free-space observation, second-copy/restore method, retention period/legal hold and deletion authority | C7/C1/C3/C6/data owner | Before any later evidence-producing execution; custody manifest |
| C7-I08 | DEP-PERSIST-01 supplying project, requirement/version, accountable owner, failure/restart scope, acknowledgement boundary, restore obligations and evidence applicability to selected PVs | C1/infrastructure owner/C0 | R3/RST-04; recovery result. Reuse inherited evidence, no duplicate infrastructure campaign |
| C7-I09 | C0/C3 agreement on t0/t1/stability window, controlled/abrupt variants, accepted/in-flight/replay sets, expiry protection and external sink responsibility | C0/C3 with C2/C4 | Before the applicable RST qualification; recovery result |
| C7-I10 | Registry/Gravitino version/backend/persistence/restore/compatibility/replay and monitoring interface, component owners and resource needs | C5 | R3; earlier only for a selected tenant dependency; recovery/monitoring evidence |
| C7-I11 | Profile-specific arrival/size/skew/fan-out envelope, lag/latency/overload limits, source buffering and measured net catch-up/resource data | C2/C3/C1/C4 and application owner | R3 capacity/replay; existing budget helper and recovery result |
| C7-I12 | Exact authorization/run owner/window/action package and protected active-run handoff, with fresh applicable health/configuration evidence | C0/user/C4/C3 | Any later live execution; deployment support/recovery result. No execution is enabled here |

## Work C7 can close offline now

The checklist and [five blank evidence templates](templates/README.md) are delivered in this slice. They reuse existing runbooks and release-matrix claim IDs rather than replacing C3 accounting or C4 stage readiness. C7 can subsequently map supplied saved monitoring configuration, check provided manifests/pins, calculate provided budgets and assemble review packages using local copies. Missing owner decisions remain OPEN. An offline fixture or filled form is never an operational PASS.

Runtime alert delivery, effective permissions, current free capacity, restoration timing, complete recovery/replay and the continuity run's final result require their actual evidence. Do not query/control/restart the worker, collector or observer to fill these forms. Use existing run-owner exports only after the owner supplies them.

## Deferred Helm requirement

**C7-FUT-HELM-01 — evaluate Helm as an additional packaging requirement.** User-authorized evaluation requirement; deferred work, not an accepted chart design or a dependency of current R0–R3 preparation. Kustomize remains current. See the [deferred evaluation brief](helm-deferred-evaluation.md).

Helm work starts after C0 records that preceding applicable project phases and their acceptance gaps allow it. The existing coordination plan's phases 1–4 and R0–R3 provide the reference gates; C0 must identify the actual completed/deferred scope rather than C7 guessing readiness or treating every future optional feature as a blocker. There is no automatic chart generation, installation or promotion when a test finishes.
