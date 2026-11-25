> Portable publication copy. Source revisions and coordinator-only references are listed in the C7 publication provenance; historical results remain scoped to their original review dates.

# C7 — Operations, Recovery and Release

Latest concise C0 entry point: [summary, remaining owner inputs and synchronization points](C7-C0-summary-2026-11-25.md). Detailed artifact/evidence history follows below.

Initialized 2026-11-25 (Asia/Jerusalem), revision 0.1. **Ready for review: offline operational/recovery qualification package.** User designated this work area by title; the C7 brief in `docs/chat-prompts-c5-c7.md` supplied its bounded scope. No other chat was created or contacted.

## Deliverables and ownership

Entry point: [operations package](../operations/README.md). C7 owns its additive `docs/operations/` documents, local support helpers under `kaas-demo/operations/`, and this handoff. C4 retains deployment/policy/GitOps, C2 generator, C3 results/acceptance, C5 governance, C6 access, C1 environment and C0 shared SRS/context/decisions/validation baselines. No central baseline or other owner's source was edited.

| Path | Purpose / status |
| --- | --- |
| `docs/operations/monitoring-and-overload.md` | Existing stack/version snapshot, signal/alert/overload/ownership map; proposed production mapping with uninspected rules explicit |
| `docs/operations/capacity-and-evidence-budgets.md` | Derived WP-A/WP-B replica payload, retention/lag/catch-up and evidence resource/custody budgets |
| `docs/operations/incident-and-evidence.md` | Incident triage, preservation, ledger interpretation, negative outcomes and disposition |
| `docs/operations/recovery-qualification.md` | RST-01 single broker, RST-02 rolling, RST-03 full Kafka, RST-04 infrastructure; proposed common clocks and record reconciliation |
| `docs/operations/release-runbook.md` | R1 support and controlled GitOps promotion, rollback decision tree, manual operator/broker/metadata upgrade procedure |
| `docs/operations/release-matrix.json` | 23 configuration-specific recorded/open claims: five dev rows plus nine assertions in each dedicated/shared target mode |
| `kaas-demo/operations/` | Additive local budget checker, explicit synthetic fixture, 10 arithmetic/unknown/error checks and portable usage guide; no active Kustomization |
| `docs/operations/source-snapshot-2026-11-25.json`, `validation-2026-11-25.json` | Source fingerprints, commands/results and limitations |

All new implementation is local/uncommitted/unpublished; parent workspace is not Git. No commit/push requested or performed. Existing C4 and collector working changes are preserved, not staged or absorbed.

## Source versions and current evidence

SRS 0.9 (November 18), shared context/validation/coordination/briefs and latest C4 handoff/minimum-inputs assessment read November 25. Local demo HEAD `a3ff863fad2f3b1eb7a34ee543ecfa0988047bf1`; existing local C4 readiness/bootstrap and collector changes are additional sources, not contents of that commit. Deployed Kafka source `ea80ef82c6586ca1d6deaa56e37a19e888553dc0`, utility `963db2d41b6dc140d661c96e108f1c09a7c76da5`, historical collector publication `340938e4cf64e0060525418d8e549db88b775a90`. No remote head refresh.

Inspected manifests select Kafka 4.2.0/RF2/minISR2/6h, retained gp3 dev claims, internal TLS/SCRAM and a pinned image; historical deployment reports metadata 4.2-IV1, OpenShift 4.21.42, Streams 3.2.1-10, GitOps operator 1.22.3. ArgoCD server version is separate and OPEN. Version-specific primary Kafka 4.2/Streams 3.2 docs checked November 25; generic ArgoCD stable docs are explicitly not installed-version verification. URLs/findings are in the entry point. No fresh cluster health or exact target compatibility claim.

Latest local run evidence supersedes old RUNNING/fix-in-progress narratives: original day run FAIL (49,175 matched IDs; 50,825 unsent); first short FAIL during drain; repeated short recorded PASS (1,040 matched records, clean Jobs/restart review). Fresh day run `continuity-24h-20261125083551-5d08` has launch/observer receipts; the newer C0 collector-fix report records RUNNING and 23 ACK/receipt/commit records at its first checkpoint. Final acceptance is OPEN. No C7 query or control of the active test. Later collector fixes do not erase earlier negative results. A 100MB continuity PASS would not qualify TB capacity, restart recovery or production no loss.

## Owner interfaces and synchronization

| Owner / point | Concrete input or action required |
| --- | --- |
| C0 / SP1–SP3, R1 | Select actual target/tenants/change window, named support/on-call/escalation and permitted sync/rollback authority; accept R1 support scope without imposing all R3 claims as deployment prerequisites |
| C1 / SP1 and SP5 | Incremental CPU/memory/storage/evidence budget, actual free space/failure domains; existing monitoring query/rule/retention/receiver inventory; DEP-PERSIST-01 supplying project/requirement/version/owner/scope/evidence applicability |
| C4 / R1, SP3 and SP5 | Map exact pins/bootstrap/watch/permissions and reversible diff; supply version-specific restart/restoration actions and no-prune/delete authority checks; preserve Manual Kafka upgrades. Current package does not authorize `install-k4fhm` or any replacement plan |
| C2 / SP4 and SP5 | Native acks/retries/buffering/timeout/commit mappings, source queues and ambiguous-send handling; address absent ACK offsets for recovery evidence without manufacturing results |
| C3 / SP5 | Accept recovery clock/endpoints/stability/variant definitions, expected sets, expiry treatment and result format; execute separately authorized tests and validate integrity/lifecycle/resource/alert evidence |
| C5 / SP5 (earlier if tenant needs it) | Actual registry/Gravitino products/versions/backends, persistence/backup/restore/import compatibility and monitoring needs, resource/evidence budgets and recovery ordering |
| C6 / SP2–SP4 and SP5 | Effective manual sync/prune/delete authority, tenant identity/admission and actual support permissions; protected credential/CA backup/rotation/reconnect interfaces and isolation tests |

DEP-PERSIST-01 remains an inherited user-declared dependency with source/owner evidence OPEN. Reuse the supplying project's evidence rather than demand another infrastructure durability campaign before load-only pre-flight. RST-04 adds KaaS integration/replay/reconciliation evidence, not replacement infrastructure qualification. gp3 results do not qualify VSAN; ODF migration is future separate scope.

Proposals awaiting C0/C3 acceptance: conservative full disruption→healthy service+catch-up+reconciliation recovery clock, per-variant stable window, retention/age/catch-up screening, incident custody/second-copy/disposition and named operational thresholds. These do not revise accepted RF2/6h/no-loss/3h requirements. Actual telemetry coverage/notifications, support names, evidence retention destination/duration and production overload controls are OPEN; reported component presence is preserved.

## Validation and requested consolidation

Executed locally: 10 budget unit checks PASS; positive CLI fixture calculation; negative CLI nonfinite input rejection; JSON/link/source-reference/matrix/recorded-result and protected-source checks listed in the [validation receipt](../operations/validation-2026-11-25.json). No independent reviewer or Kafka/native/runtime fault qualification. Helper output is planning-only even for positive margin; no release is automatically qualified.

No cluster/API/Secret access, producer/consumer or HTTP load, live restart/fault/upgrade/migration, deployment/sync, recurring automation, commit/push or outbound message. Only public primary documentation browsing and local inspection/checks were performed.

C0 consolidation request via this file: index entry point/handoff/helpers and source/validation receipts, SRS 0.9/demo a3ff863 plus fingerprinted local overlays, OFFLINE-VALIDATED/ready-for-review status and remaining interfaces above. Preserve C3 run acceptance and all central decisions. First operational sync is R1 named deployment/rollback support; service qualification joins SP5/R3 after actual configuration and evidence are selected. No shared-context update was made by C7 because C0 owns that baseline. During validation, C0 updated project-context, validation-register and the shared prompts; C7 re-read the changed overlays and retained the initial source hashes, recording refreshed hashes separately. These concurrent coordination updates are not a C7 write or a protected-runtime modification.

## Offline input checklist and templates, 2026-11-25

User authorized the checklist/evidence-template slice, explicit unresolved inputs and protection of active continuity; keep Kustomize and record Helm as a deferred additional evaluation after earlier phases permit it.

Deliverables: [input checklist 0.1](../operations/input-checklist.md) with C7-I01–I12 mapped to existing I1–I5/SP1–SP5/R1–R3; [template guide and five JSON forms](../operations/templates/README.md) for deployment support, incident, recovery, custody and monitoring; [deferred requirement C7-FUT-HELM-01](../operations/helm-deferred-evaluation.md). Operations entry point is revision 0.2; existing release runbook links the new inputs. No existing results, release-matrix outcomes or acceptance baselines were replaced.

Source baseline: SRS 0.9, current shared context/validation/coordination, C4 minimum inputs/latest handoff and C7 operational procedures. Local demo HEAD `a0e9e7d50d1f10bf2e79da3e4c5cc60d0e0c2a12`; C0's published collector correction supersedes the earlier uncommitted-collector narrative. This is a local Git observation, not a new remote or runtime check. Collector/runtime/Kustomize sources are outside this slice.

All forms start TEMPLATE/OPEN with unresolved values null and execution_enabled=false; they are documentation, not implemented runner configuration or enforcement. Required support names, budget/pins, telemetry configuration, evidence custody/disposition, DEP-PERSIST-01 references, recovery endpoints and C2/C5/C6 interfaces remain OPEN by the relevant stage. Supplied references do not imply reviewed/pass/authorized state. No credentials or new filled result claims are included.

Helm requirement status: user-required evaluation, DEFERRED; design/implementation not selected. C0 must record preceding applicable phase outcomes/readiness and permit the follow-on evaluation; C4 owns any later packaging code, C7 its support/recovery assessment. Current Kustomize work does not wait for Helm. No chart/dependency/tool installation or technical compatibility claim was added.

Checks: local JSON/field-state/required-target/Markdown-link consistency, preserved existing repository sources and historical C7 receipts, with exact sources/results in [checklist validation receipt](../operations/checklist-validation-2026-11-25.json). No new unit tests needed for these documentation templates; earlier budget test results are not represented as rerun. No independent reviewer or live qualification.

No cluster/API/Secret/network access, continuity query/control, loads/restarts/faults/upgrades/deployments/sync, commit/push or outbound messages in this slice. New documents remain local/unpublished. C0 consolidation requested through this handoff: index checklist/templates/deferred Helm requirement and receipt with source versions and OPEN inputs; keep shared SRS/context/decisions/validation single-writer ownership and active-run results unchanged.

## Additional offline record checks, 2026-11-25

User authorized continued offline work while C0 reviews. Added `kaas-demo/operations/record_check.py` and synthetic tests reusing the five existing shared templates. [Usage and scope](../operations/offline-record-checks.md); [validation receipt](../operations/record-check-validation-2026-11-25.json). Checks cover record shape, unresolved fields, review/UTC/numeric handling and selected recovery/PASS contradictions, without opening evidence references or granting acceptance. No completed real incident/recovery record created.

C7-I01–I12 and owner interfaces are unchanged/OPEN. Next sync remains R1/SP1–SP3 support package, R2/SP4 client contract and R3/SP5 actual integrated evidence. Further offline mapping can proceed from supplied saved monitoring, rollback and budget artifacts. C0/C3 retain decisions/results. Helm stays DEFERRED, Kustomize current. Active continuity sources/resources were untouched; no API/network/Secret access, run query/control, live execution, publication or outbound message. No shared-baseline edits. All new code/docs are local/unpublished.
