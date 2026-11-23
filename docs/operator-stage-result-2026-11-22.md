# Kafka operator GitOps stage result

Date: 2026-11-22. Status: **operator installation verified**, Kafka brokers and load-test execution remain subsequent stages.

## Verified result

| Component | Observed result |
| --- | --- |
| ArgoCD Application | `openshift-gitops/kaas-demo-operator`, Synced and Healthy |
| Deployed source | `7542a93c5aee9aad281c62ba074e1de7db7b7624`, path `environments/dev/operator` |
| Operator installation | `amqstreams.v3.2.1-10`, CSV Succeeded in `kafka-operator` |
| Operator pod | Running and Ready, zero restarts at observation |
| OperatorGroup | Target namespace resolved to `kaas-kafka` |
| Initial InstallPlan | `install-msmqg`, exact selected CSV, approved and Complete |
| Later Kafka InstallPlan | `install-k4fhm`, `amqstreams.v3.2.2-9`, unapproved/RequiresApproval |
| GitOps operator | `openshift-gitops-operator.v1.22.3`, Succeeded; upgrade approval reported by user and observed completed |
| ArgoCD instance | Existing `openshift-gitops/openshift-gitops`, Available |

Created bootstrap resources: namespaces `kafka-operator` and `kaas-kafka`, restricted AppProject `kaas-demo`, and the pinned, manually synchronized operator Application. No additional ArgoCD instance was created. Existing controller permissions were checked with SubjectAccessReview; no extra Role/ClusterRole binding was granted. ArgoCD, rather than a direct operator apply, created the OperatorGroup and manual Subscription.

## Exact selected artifact inspection

The initial plan referenced the Red Hat catalog's unpacked bundle ConfigMap. Its compressed binary entries were decoded and inspected before approval. All 20 plan steps resolved to the selected CSV, and the plan's CSV list contained only `amqstreams.v3.2.1-10`. The selected bundle supports the single target-namespace installation mode and serves v1 Kafka/KafkaNodePool/KafkaTopic CRDs (older served versions also present).

Operator image reference: `registry.redhat.io/amq-streams/strimzi-rhel9-operator@sha256:72da52b47b90fab432581ca8d1661e31d92fd090e883845ca5ce68fd23155589`. Running container imageID reports `sha256:464727b8c5a57d58f86d3f5e5c704ed283b890951a7fa0f0f45fe039afee3f6b`; retain reference and runtime digest separately rather than assuming they identify the same OCI manifest level.

Selected CSV broker-image mappings:

- Kafka 4.1.0 → `registry.redhat.io/amq-streams/kafka-41-rhel9@sha256:7ae5bdd78e89ecfcb8bfb8bb916fa9520326217cadf73d079d9841fa2c58b700`.
- Kafka 4.2.0 → `registry.redhat.io/amq-streams/kafka-42-rhel9@sha256:ce7dc91b664600c6f06e1df3d6b56a4684bb779865d9c28b4df648addd89189d`.

These mappings were inspected in the exact selected artifact. They are not evidence that either broker image was pulled or Kafka workload deployed. Release-family guidance identifies 4.1 as an upgrade path; use the selected release's supported new-cluster version when preparing brokers.

## Executed checks and evidence

TLS/hostname verification remained enabled with the previously obtained API CA. Refreshed token authenticated as `admin` and was kept in memory. The earlier unreachable-sandbox state is resolved. Bootstrap create requests passed fresh strict server-side dry-run before creation. ArgoCD fetched and rendered the published exact revision, then the explicit manual sync succeeded. The initial Kafka plan was reviewed and approved through an optimistic-concurrency guarded PATCH that accepts only the exact selected first plan; later Kafka plans were not approved. GitOps upgrade approval was performed by the user, not this coordinator.

Shared workspace evidence:

- `config/environments/gitops-kafka-preparation-discovery-2026-11-22.json`: resumed read-only discovery.
- `config/environments/operator-bootstrap-execution-2026-11-22.json`: bootstrap, revision/source comparison and controller authorization queries.
- `config/environments/operator-sync-execution-2026-11-22.json`: explicit sync result and observed approved GitOps plan.
- `config/environments/initial-kafka-plan-approval-2026-11-22.json`: guarded initial-plan approval receipt.
- `config/environments/operator-stage-observation-2026-11-22-01.json` through `-03.json`: plan progression, operator/ArgoCD health, pending Kafka update. The final observation began 10:17:14 UTC / 12:17:14 Asia/Jerusalem.
- `config/environments/selected-kafka-bundle-2026-11-22.json`, `selected-kafka-csv-3.2.1-10.json`, and selected-schema JSONs: exact bundle/image/configuration evidence.
- `tools/bootstrap_kafka_operator_stage.py`, `tools/sync_kafka_operator_stage.py`, `tools/operator_stage_session.py`: token-in-memory execution/observation tools. These are diagnostic/bootstrap tools, not production automation; inspect current state before any reuse.

## Remaining scope

No Kafka broker/controller cluster, broker PVC, KafkaTopic/KafkaUser, schema/governance service or producer/consumer workload was provisioned in this stage. No throughput, message-size delivery, durability/recovery or five-minute runtime acceptance was tested. Namespace `kaas-demo` remains reserved for Kafka test clients. Existing inherited infrastructure persistence remains a separate dependency.

Next is the budgeted dev Kafka deployment using the verified operator/schema/image mapping, followed by four GitOps-managed topics and the bounded <=300s, <=2 MiB test. Resource/PVC allocation, initial listener/security configuration, effective message limits, test image/xk6 mapping and durable runtime accounting remain explicit inputs. The prepared offline 16-record case manifest is not a runnable or passed Kafka test.
