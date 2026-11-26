# R3-01: configuration, authority and GitOps service contracts

**OFFLINE REVIEW COMPLETE; EFFECTIVE-RIGHTS REFRESH AND LIFECYCLE EXECUTION NOT RUN.** Source baseline: kaas-demo `7a1065940bda19fd34bf3adf01078ff51fe53492`, SRS0.9 and accepted shared-first/manual-sync overlays. All four client Jobs are untouched and last observed suspended. No cluster/API/GitHub permission request, workload, sync, registration, image build, fault or credential operation occurred. The user authorized publication of this package. Its owning Git commit identifies the published snapshot; original validation receipts retain their historical preparation status.

[Disabled service contract](service-contract.json), [offline validator](validate_offline.py), [validation evidence](evidence/), [C4-NR-05 documentation reconciliation](mount-contract-reconciliation.md), [result](result.json) and [progress overlay](../progress.json). This is a C0 consolidation, not a new specialist signature. Source hashes identify the handoff sections and implementation files inspected; original handoffs, frozen contracts and historical receipts remain unchanged.

## Configuration and service boundary

| Contract | Reviewed selection / evidence | Acceptance boundary |
| --- | --- | --- |
| Hosting | Existing `kaas-kafka/kaas-dev`; Kafka/KRaft/storage/listeners owned by platform | Shared sandbox only; dedicated mode, target VSAN/planned ODF and external-client endpoints are separate claims. |
| Tenant resources | R1 resource commit `3211df93ae40d7d6f47c6334966ae6d1f658fee7`: four Topics/four Users for `kaas-sbx-a/b`; registration package `ac2f57b1faedae88028486073abf597256a172af` | Local Git blobs and exact contents checked; no re-registration/re-sync. Later publication of this review does not repin either Application. |
| Data policy | Topic1partition/RF2/minISR2, retention21,600,000ms, max.message.bytes3,145,728, cleanup.delete; broker auto.create.topics.enable=false in selected source | Producer values and protocol overhead differ. R2 used1,000-byte values; earlier2MiB smoke is distinct. Six hours is not no-loss proof; acks=all with ISR below2 cannot write under this profile. |
| Tenant access | TLS/SCRAM, literal own-topic/group ACLs; producer IdempotentWrite; per-principal quotas65,536B/s producer and consumer, requestPercentage5 | Quotas are per broker, not a global tenant throughput guarantee. Four trusted-harness credentials do not prove hostile workload/Secret isolation. |
| GitOps boundary | AppProjects permit only KafkaTopic/KafkaUser from exact repository into kaas-kafka; two Applications manually pinned to3211df9; FailOnSharedResource=true | AppProjects constrain kinds/source/destination, not every CR field/name or shared controller authority. No automated sync, prune, force/replace, finalizer or namespace-creation change selected. |
| Reconciliation owners | ArgoCD manages desired tenant CRs; Topic/User Operators reconcile Kafka backend/configuration and generated credential material | Tenant data clients are service actors outside the Kafka boundary even inside the same cluster. Git request/review/sync is a control-plane interface, separate from Kafka data-plane access. |
| R2 runtime | Source05a3f2d, image41f328c8, binary0174513d, actual JS manifest07f7bd42, sealed182-event export18ba0646 | Accepted bounded R2 fixture reused; later offline auditor manifest9af2ea57 is not a deployed-image repin or a new execution approval. |

The source policy is deliberately fixed for this sandbox. A new tenant, quota, partition, retention, ACL or trust change requires an explicit versioned contract/diff and review. Do not edit the exact allowlist merely to make an unapproved change pass. No custom claim-check, broker resize, schema rollout, Gravitino, operator upgrade or broader capacity test is introduced here.

## Authority: policy, observed capability and enforcement

| Layer | Accepted sandbox contract | Dated evidence / unresolved enforcement |
| --- | --- | --- |
| Request/review/approval | The user is sandbox owner and approver; no tenant sync delegate | A tenant service may request changes through a reviewed Git change. The current sandbox does not establish independent reviewer separation; do not invent a second approver or SSO mapping. |
| Git | Reviewed changes, exact immutable resource SHA, inspect generated diff and validation before promotion | Nov25 saved GitHub GET evidence reported public repo/main unprotected, no active branch rules/rulesets, administrative/push capability. No `.github` workflow is checked in at this baseline. Local validators are available tools; required CI, CODEOWNERS or branch enforcement is not established. Publishing a commit alone grants no execution authority. |
| ArgoCD human access | Only the accepted owner may authorize this sandbox operation; no delegated tenant role | Saved RBAC maps cluster-admin groups to role:admin, default policy empty; saved admin.enabled=true. R1 used authenticated Kubernetes API admin, not a verified ArgoCD SSO human role. No new mapping is asserted or granted. |
| Kubernetes / controller | Existing controller and operators retain their identities | Saved Nov25 reviews allowed API admin through a cluster-admin binding; controller rights include Secret reads/Kafka updates. AppProject separation does not isolate Kubernetes identities or prevent a privileged bypass. Current effective rights are not refreshed. |
| Kafka data plane | Own-topic producer/consumer roles, retained literal groups and positive controls | Successful R2 scoped denials are reused. Metadata/admin, hostile Secret access, trust negatives and revocation have their own R3-02 contracts. Broker ACLs do not enforce Git approval. |
| Evidence / operations | Seven days sandbox plus verified workspace copy; retain successful R2 at least through2026-12-03T15:12:05Z | No automatic deletion. Ongoing custodian/support/disposition joins remain R3-03/C7; this review creates no cleanup or storage operation. |

**Disposition:** owner-only sandbox policy is accepted; least-privilege production delegation, protected-review enforcement and lifecycle revocation remain OPEN. This offline request does not require a new owner decision. Before a later live change, refresh the applicable Git protections, Argo global/project/user policies, Kubernetes direct/controller permissions, admission/ownership and exact source/diff. Permission to push, register, sync, create clients, read credentials and run traffic are distinct. Historical R1/R2 authorizations have been consumed and do not authorize another run.

## Proposed lifecycle contract for any later selected case

These are preparation rules, not a runnable transaction or accepted production revocation policy. No live window, authorized diff or new run is populated in the disabled contract.

1. **Request and classify:** identify requester/service, tenant, intended data/control-plane capability, object owner and exact requested change. Preserve existing fixture topics/users/groups/offsets and sealed evidence. A service may be external to Kafka while co-located in OpenShift; outside-cluster clients need a selected network contract, not Kafka cluster interconnection.
2. **Compile and review offline:** validate names, literal ACLs, quotas, retention, schemas, identity/collision assumptions and complete generated diff. Publish only when requested, record the actual resource SHA, then prepare Application pin separately. For air-gapped deployment select an approved internal Git mirror/artifact inventory; sandbox GitHub access is not disconnected-target readiness.
3. **Authorize a concrete operation:** owner selects exact disposable canary identities, source/pin, change window, executor/stop/support/custody roles, bounded impact and non-destructive rollback. The suggested canary is a distinct later fixture; names are not reserved, checked or allocated now. No deletion/mutation of current fixtures is a default test step.
4. **Refresh relevant controls:** verify target/source/health/headroom, backend/CR ownership, effective rights, operator watch and admission. Stop on drift, competing owners or incomplete evidence. Local false flags/templates are not admission barriers; do not substitute them for effective controls.
5. **Later manual operation:** if separately authorized, selected resources only, manual sync/no prune/no force/replace; verify tenant A and preservation before any dependent B action. Source acceptance and actual operation approval are separate. No client workload follows implicitly from resource convergence.
6. **Contain and recover:** on failure hold further operations, retain evidence and inspect exact state. Prefer a reviewed forward correction; Git revert is not universally safe for Kafka partitions/retention/ownership, and deleting an Application is not a data rollback. Any destructive exception needs its own owner disposition.
7. **Revoke deliberately:** specify separate removal of Git write, Argo sync, direct Kubernetes rights, Kafka ACL/credential access, copied Secrets and existing sessions. Credential/ACL change and existing-session termination are not assumed identical. Observe intended denials and preserve accepted messages/offsets. No credential rotation, Secret deletion, ACL removal, group reset or session disruption is executed by this document.

## Review and validation

R3-01 acceptance is mapped as follows: R1/resource/registration pins and R2 image reused; NR-05 resolved **for documentation** by the additive mount overlay; malformed tenant/ACL/naming/quota changes rejected offline; authority evaluated separately with historical scope; later lifecycle changes constrained to a distinct reviewed canary/diff. Effective permissions, current health and runtime revocation are not claimed complete.

Executed now: **23 tenant-only +55 existing C4 tests PASS**, two local Kustomize renders/exact resource comparisons PASS, and **25 negative contract probes rejected**. The positive contract check verifies six actual local Git source files at their resource/registration pins, separate trust mounts, baked runtime versus runtime gate, suspended Job and exact image digest. Cached Kafka schemas and structural local comparisons do not establish live admission/CEL/operator support. No k6/SDK client or live permission probe was invoked. Previous568R3-10/11 checks are reused, not rerun.

```sh
# From kaas-demo, use a fresh output directory outside the repository.
python policies/tenant-only/validate_offline.py --output /tmp/new-r3-01-tenant-evidence
python qualification/r3/r3-01/validate_offline.py
python packaging/r2-native/validate.py
python qualification/r3/validate_plan.py
```

The generic tenant builder intentionally still has a null revision/pre-deployment status; the registration input and immutable Git blobs supply the actual3211df9 pin. Likewise the initial plan checker retains historical NW OPEN labels; the progress overlay/R3-00 result and later C3 review supply the current offline disposition. Do not rewrite historical receipts to make their labels current.

Latest owner joins inspected: C1v1.0 verifies auditor/source/evidence without rerunning; C2v0.7 correction history is superseded for publication by9467420; **C3v1.2 explicitly accepts the exact9467420 extension offline** (saved independent tests/probes and re-audit, not rerun here). C4 NR-05 is reconciled here without changing its handoff or functioning mounts. C5 remains separately disabled/conditional; C6's last direct-chat hold/review status is not overridden or contacted; C7 custody/support remains separately scoped. No C6 concurrence or owner acceptance of this new R3-01 package is invented.

Requested offline R3-01 preparation is complete. Next available offline lane is R3-02 credential/trust/network contracts, or R3-03 monitoring/support/custody joins. Neither requires automatically repeating R1/R2 or starting a workload. Production delegation decisions and any live lifecycle window are needed only when that scope is selected.
