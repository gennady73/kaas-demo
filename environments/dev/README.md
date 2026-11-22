# Development environment

Intended ArgoCD source directory: `environments/dev` in `https://github.com/gennady73/kaas-demo.git`. The first renderable stage is `environments/dev/operator`; use the pinned-revision Application template in `gitops/bootstrap/`. The root directory is not an Application source. Kafka resources and test Jobs are later separate stages.

Use the bounded development sandbox, preserving its billing/storage constraints. OpenShift 4.21.42 and AWS EBS CSI were observed; no Strimzi API or Kafka workload was observed during the 2026-11-18 inventory. Namespace `kaas-demo` already exists. Do not infer that its absence of a ResourceQuota permits unlimited resources. Record actual resource/PVC budget, image digests, broker selection, security and supported storage settings in the overlay.

Production and real pre-production are separate configurations and qualification stages. No credentials, API token, kubeconfig or private keys belong here.

## Namespace roles, 2026-11-19

GitOps operator: `openshift-gitops-operator`. Kafka operator: its own dedicated namespace, name not selected. `kaas-demo`: Kafka test workloads. Kafka cluster and ArgoCD instance namespaces remain separate placement inputs. Keep operator installation, Kafka workload resources and test Jobs distinct; do not infer CR/watch scope or cross-namespace permissions from this layout.
