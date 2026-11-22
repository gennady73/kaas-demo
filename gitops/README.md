# ArgoCD integration

Selected source: `https://github.com/gennady73/kaas-demo.git`; intended development path `environments/dev`. No committed revision or deployed ArgoCD Application exists for this scaffold yet. Pin/review the actual revision before synchronization.

Prepare the AppProject and Application after identifying the installed GitOps release, its control namespace, the allowed namespace/resources and the rendered dev configuration. Use manual synchronization by authorized personnel; do not add automated sync, automated pruning, broad wildcard permissions or plaintext repository credentials. Grant tenant resources separately from privileged operator installation.

Test Jobs require explicit run IDs and a separate controlled launch path. Do not include a recurring Job or auto-running test hook in the infrastructure application. No GitHub webhook is required merely to poll Git; GitHub reachability from the cluster remains unverified. Air-gapped targets use an internal mirror.

## Bootstrap discovery, 2026-11-19

The refreshed read-only cluster inventory found no `argoproj.io` API group or GitOps/ArgoCD operator CSV. See [bootstrap template and prerequisites](bootstrap/README.md). The user-proposed instance is named `kaas-demo`; its operator namespace remains unresolved until installation/discovery. No instance was created.

## Namespace roles, 2026-11-19

GitOps operator: `openshift-gitops-operator`. Kafka operator: its own dedicated namespace, name not selected. `kaas-demo`: Kafka test workloads. Kafka cluster and ArgoCD instance namespaces remain separate placement inputs. Keep operator installation, Kafka workload resources and test Jobs distinct; do not infer CR/watch scope or cross-namespace permissions from this layout.

## Intentional GitOps version selection, 2026-11-19

USER-REPORTED installation: CSV `openshift-gitops-operator.v1.20.0` (operator version 1.20.0). The user intentionally chose this version while production's GitOps version is unknown. Preserve this sandbox selection; no upgrade to latest is requested. This closes the selected version input, not production parity or live readiness. The earlier discovery showing no GitOps operator predates this installation report and must not be treated as the current installed-state conclusion. Operator/CRD readiness, actual ArgoCD instances and deployed ArgoCD version remain to be inspected; do not equate operator version 1.20.0 with the ArgoCD application version. No new cluster query or mutation was performed to record this report.
