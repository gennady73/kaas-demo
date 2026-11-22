# Kafka infrastructure

Place reviewed operator/bootstrap configuration and Kafka/KafkaNodePool resources here. Keep privileged operator/CRD installation separate from tenant synchronization.

Before writing apply-ready resources, inspect the selected `3.2.1-10` catalog/bundle/image, supported Kafka broker versions and served schemas. Resource allocation, persistent capacity, topology and initial listener/security policy remain explicit deployment inputs. Do not copy the older static Kafka 4.0.0 reference as a validated configuration for this release.

## Namespace roles, 2026-11-19

GitOps operator: `openshift-gitops-operator`. Kafka operator: its own dedicated namespace, name not selected. `kaas-demo`: Kafka test workloads. Kafka cluster and ArgoCD instance namespaces remain separate placement inputs. Keep operator installation, Kafka workload resources and test Jobs distinct; do not infer CR/watch scope or cross-namespace permissions from this layout.
