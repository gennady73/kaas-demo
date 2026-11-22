# KaaS demo

GitOps implementation repository for the KaaS OpenShift development sandbox.

Status: Kafka operator installation manifests prepared, 2026-11-19. Start with [deployment sequence](docs/deployment-sequence.md). Kafka broker manifests and the executable smoke runner remain subsequent stages; preparation does not claim deployment.

## Layout

| Path | Purpose |
| --- | --- |
| `platform/` | Operator and Kafka infrastructure configuration |
| `tenants/` | GitOps-managed tenant topics and access resources |
| `environments/dev/` | Intended development overlay and ArgoCD source path |
| `gitops/` | ArgoCD project/application definitions and sync controls |
| `tests/dev-smoke/` | Four-topic smoke-test input snapshot and later runner integration |
| `docs/` | Baseline provenance and implementation status |

## Selected baseline

- Red Hat Streams for Apache Kafka operator identifier `3.2.1-10`; exact artifact/digest and supported broker mapping still require inspection. This is an operator version, not the broker version.
- OpenShift 4.20.18 through 4.21.x. Development sandbox was observed on 4.21.42 with AWS EBS CSI; target storage direction remains VSAN with planned ODF migration.
- Target RF=2 and retention 6 hours. Preserve explicit dev billing/storage differences when implementing overlays.
- Immediate test: four topics, producer/consumer clients, at most 300 seconds total including startup/retry/drain/shutdown; value payload maximum 2 MiB (2,097,152 bytes).
- Proposed small test: four boundary-size records per topic, 16 originals and 12,849,152 original value bytes overall. The JSON is design input, not a runnable configuration.

## Change workflow

Review changes in Git. Only permitted personnel may initiate/authorize ArgoCD synchronization; connecting the repository does not enable automated sync. Install privileged operator/CRD resources separately from tenant changes. Keep test Jobs outside recurring application reconciliation so routine sync cannot accidentally rerun traffic.

GitHub is the selected repository origin. A disconnected target needs an accessible internal mirror and controlled promotion of reviewed revisions and image dependencies. Credentials/private keys belong in approved Secret storage, never in this repository.

See [implementation status](docs/implementation-status.md) for the inputs needed to produce deployable manifests.
