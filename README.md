# KaaS demo

GitOps implementation repository for the KaaS OpenShift development sandbox.

Status verified 2026-11-24: Kafka 4.2.0 dev cluster is Ready. The rebuilt custom xk6 passed the four-topic smoke: 16/16 records including 2 MiB values, within 268 seconds through container completion. See the [custom xk6 build audit and result](docs/xk6-build-and-smoke-2026-11-24.md), [earlier deployment result](docs/kafka-cluster-result-2026-11-23.md), and [historical Java smoke/old-image failure](docs/smoke-test-result-2026-11-23.md). The new image is sandbox-local; the original Docker Hub image is unchanged.

## Guides

- [Bootstrap guide](docs/bootstrap-guide.md): prerequisites, namespace/project/Application bootstrap, manual sync and exact initial-plan approval, readiness checks and current limits.
- [Git workflow](docs/git-workflow.md): what belongs in each local repository, credential setup, review/push and the separate ArgoCD promotion step.
- [Operator stage result](docs/operator-stage-result-2026-11-22.md): observed installation result and evidence references.

## Layout

| Path | Purpose |
| --- | --- |
| `platform/` | Operator and Kafka infrastructure configuration |
| `tenants/` | GitOps-managed tenant topics and access resources |
| `environments/dev/` | Intended development overlay and ArgoCD source path |
| `gitops/` | ArgoCD project/application definitions and sync controls |
| `tests/dev-smoke/` | Four-topic smoke contract, executed native runner and independent reconciliation |
| `docs/` | Baseline provenance and implementation status |

## Selected baseline

- Red Hat Streams for Apache Kafka operator identifier `3.2.1-10`; selected artifact/digest and broker mapping verified; exact deployed details are in the result report. This is an operator version, not the broker version.
- OpenShift 4.20.18 through 4.21.x. Development sandbox was observed on 4.21.42 with AWS EBS CSI; target storage direction remains VSAN with planned ODF migration.
- Target RF=2 and retention 6 hours. Preserve explicit dev billing/storage differences when implementing overlays.
- Immediate test: four topics, producer/consumer clients, at most 300 seconds total including startup/retry/drain/shutdown; value payload maximum 2 MiB (2,097,152 bytes).
- Proposed small test: four boundary-size records per topic, 16 originals and 12,849,152 original value bytes overall. The JSON is design input, not a runnable configuration.

## Change workflow

Review changes in Git. Only permitted personnel may initiate/authorize ArgoCD synchronization; connecting the repository does not enable automated sync. Install privileged operator/CRD resources separately from tenant changes. Keep test Jobs outside recurring application reconciliation so routine sync cannot accidentally rerun traffic.

GitHub is the selected repository origin. A disconnected target needs an accessible internal Git mirror and controlled promotion of reviewed revisions and image dependencies. Credentials/private keys belong in approved Secret storage, never in this repository.

See [implementation status](docs/implementation-status.md) for the inputs needed to produce deployable manifests.
