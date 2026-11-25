> Portable publication copy. Source revisions and coordinator-only references are listed in the C7 publication provenance; historical results remain scoped to their original review dates.

# Controlled release, rollback and support

Revision 0.1. Reviewable procedure for a later authorized execution; C4 owns manifests/bootstrap/deployment, C6 authority, C3 results and C0 release decision. R1 deployment support does not require all R3 qualification to be complete. Existing [deployment guide](../kafka-deployment-guide.md) and C4 handoff (coordinator-only reference: `docs/handoffs/C4-kafka-platform-gitops.md`; see publication provenance) retain implementation authority.

User instruction, 2026-11-25: keep Kustomize for the current path. Use the [C7 input checklist](input-checklist.md) and [deployment-support template](templates/deployment-support.json) for the concrete review package. [C7-FUT-HELM-01](helm-deferred-evaluation.md) records a deferred additional packaging evaluation after preceding applicable phases allow it; no chart or Helm rollout is selected here.

## R1 support interface

Before the selected deployment, resolve I1 target/tenant identity, I2 incremental resources/storage/failure domains, I3 initial access/admission/non-destructive lifecycle, I4 namespaces/operator watch/controller authority and I5 approved Git/source/sync principals. Record a named change owner, C4 executor, C1 infrastructure escalation, C6 security support and C7 incident lead/backup with a real contact route and change window. Do not invent names or infer them from work-area IDs.

Attach package resource SHA/path, bootstrap SHA, existing ArgoCD instance/controller identity, compatibility/schema checks and known-good configuration, image/catalog/related-image digests mirrored to accessible disconnected registries, Git mirror revision equality, trust/certificate references and rollback decision tree. Offline helpers remain outside active Kustomizations. C4's newest staged readiness/bootstrap result supersedes earlier guard-gap text; unresolved real candidate inputs and effective authority gates remain.

## Deployment checklist

1. Authorized executor refreshes health, active-run ownership/window, effective configuration, storage/free resources, installed operator/watch scope, ArgoCD version/permissions and Git pins. Stop if a conflicting active test is not released by its owner. Never infer current health from November 23 snapshots.
2. Review exact rendered diff/schema/content/namespace/tenant ownership and non-delete permissions against the published resource SHA. Ensure manual sync, reviewed no-prune/no-force/no-replace behavior and no cascade deletion/finalizer surprise. Absence of automated prune does not prohibit a permitted manual prune; validate effective Git/global/project/controller RBAC with C6/C4.
3. Register/sync only the authorized Application/path/revision through C4's procedure. Record initiator/approver, operation receipt and resulting actual image/config/generation/PV identities. No direct application of Kafka manifests as a GitOps workaround.
4. Verify operator reconciliation, required Ready/generation/quorum/ISR, intended resource allocation, endpoints and alerts/evidence access. Keep no-client R1 deployment separate from R2 credential delivery/client activation and R3 capacity/governance/isolation/recovery acceptance. Record stage-specific unresolved items in the release matrix.

## Rollback decision tree

| Change type | Reviewed response | Evidence / owner |
| --- | --- | --- |
| Reversible config/manifest regression | Freeze further promotion, preserve evidence; C4 prepares a revert commit or approved known-good resource revision, reviews rendered diff and requests authorized manual sync without prune/force/replace | C4/C6 verify exact source, permissions and resulting effective state; C3 checks impact |
| Topic retention/cleanup/partition/lifecycle change | Stop and evaluate data disposition/irreversibility before any revert; deleted/expired data and partition increases are not undone by reverting text | Data owner/C0 plus C4; preserve raw outcomes, no routine deletion |
| Broker binary/metadata/operator upgrade | Use version-specific supported recovery/downgrade plan; do not point Git at an old binary/CSV blindly. If downgrade unsupported, hold and use reviewed forward repair or recovery procedure | Exact compatibility, metadata/features and vendor path; C4/C1 |
| Registry/Gravitino schema/backend change | Apply C5's selected product/backend restore/import and compatibility plan; do not assume binary rollback restores data/schema state | C5 supplies backup/replay/test evidence |
| Credentials/trust/listeners | C6 supplies staged overlap/revocation and application reconnect procedure; no secret values in Git or incident output | C6/C4 verify clients and affected identities |

Retained PVCs are not an independent backup; no PVC deletion/rebinding, cluster ID reconstruction or storage migration is automatic rollback. RST-04 persistent-volume recovery requires exact topology/identity/storage plan and inherited contract. Define rollback triggers (health, error/lag margin, security or evidence failure), authorized decision owner and latest safe rollback point in the concrete change record. Numeric thresholds/time budget remain scenario inputs.

## Manual upgrades

Keep Kafka Subscription Manual. Recorded installed CSV is `amqstreams.v3.2.1-10`; later `install-k4fhm` / `3.2.2-9` was unapproved at last evidence. Refresh names/state before a later proposal; no approval here. GitOps 1.22.3 was already user-approved, not pending 1.22.0 work. Operator, ArgoCD server, Kafka broker/client and Kafka metadata versions are separate.

Prepare exact from→to matrix for OpenShift/Streams/Kafka/metadata/clients/CRD APIs and related images using selected-version vendor evidence, air-gap mirrored digests and installed schemas. Review all InstallPlan resources/permissions and impact on every watched Kafka cluster. Approve only the named reviewed plan under a separate user-scoped change, execute supported operator/broker/client/metadata sequence, observe rolling invariants and preserve each receipt. Hold metadata/features advancement until its compatibility and rollback consequences are reviewed. Requalify affected release claims rather than carry old results across version/storage/security/topology changes.

ODF migration is future separately scoped work: C1/C4/C5/C6/C7 must define data/trust/governance/evidence preservation, rollback feasibility and full applicable requalification. No VM Kafka, Kafka-to-Kafka inter-cluster link or production deployment is introduced.
