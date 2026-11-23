# Development Kafka deployment stage

Prepared 2026-11-23. This follows the completed operator stage. Preparation/schema dry-run success is separate from deployment readiness; actual execution/evidence is maintained by the coordinator.

## Desired deployment

Cluster `kaas-dev` lives in `kaas-kafka`. Node pool `dual-role` has three broker/controller nodes with 20Gi EBS gp3-csi persistent claims each, retained on Kafka resource deletion. The requested total is 60Gi, compared with 100Gi in the user-supplied dev reference. Resource requests/limits and dev-specific tradeoffs are stated in `platform/kafka/README.md`; the five-minute workload does not justify production-size brokers or a daily-volume run.

Selected broker version is 4.2.0 with explicit image digest from the verified 3.2.1-10 CSV. The operator selects its compatible metadata version; record the effective version in runtime evidence. Do not reuse older Kafka 4.0 reference metadata settings.

The internal listener uses TLS and SCRAM-SHA-512, with operator-managed certificates and generated credentials. Network-policy peers restrict client traffic to the Kafka and test namespaces. `KafkaUser/kaas-smoke-client` can read/write/describe only the `kaas-dev-smoke-` topic prefix and read/describe that group prefix; its cluster IdempotentWrite permission supports idempotent client use without granting unrelated topic reads/writes. This is a dev implementation choice, not a completed production identity/isolation qualification.

Four GitOps topics (`kaas-dev-smoke-01` through `-04`) have one partition, RF=2, 6h retention and max.message.bytes=3MiB. Application test values remain limited to 2MiB. Kafka auto topic creation is disabled. Min ISR=2/acks=all makes affected writes unavailable when a partition has only one in-sync replica; this preserves the intended acknowledgement policy rather than silently lowering it.

## Source and promotion

1. Review `platform/kafka/` and render `environments/dev/kafka` using `oc kustomize`. Validate all seven objects against installed v1 CRDs and with strict server dry-run. Confirm no pre-existing cluster/topic/user will be overwritten.
2. Commit and publish the revision. Record its full SHA.
3. Bootstrap `gitops/bootstrap/kafka-project.yaml`: a separate AppProject limited to this repository, destination kaas-kafka, and Kafka/KafkaNodePool/KafkaTopic/KafkaUser kinds. It grants no cluster resources and leaves the operator AppProject unchanged.
4. Render `kafka-application.yaml.template` with the published SHA and validate/create it in openshift-gitops. Check existing controller authorization; do not add cluster-admin.
5. Wait for ArgoCD to fetch/render the exact revision without conditions. Only then manually sync `kaas-demo-kafka` with pruning disabled. No automated sync or automatic test launch is configured.
6. Watch Kafka conditions, operator events/logs, pod readiness/placement and PVC binding. Wait for observed generation and Kafka Ready, three Ready Kafka pods, four Ready topics and the Ready smoke user. ArgoCD Healthy alone is insufficient to prove every CR is Ready.
7. Record effective Kafka/metadata version, bootstrap endpoint, image identities, PVC allocation and actual resource/placement information. Do not label binding/capacity as free-space or throughput evidence.

The listener's expected DNS endpoint is `kaas-dev-kafka-bootstrap.kaas-kafka.svc:9093`; confirm actual listener status. User Secret `kaas-smoke-client` and public cluster CA Secret `kaas-dev-cluster-ca-cert` remain in kaas-kafka. Kubernetes test pods in kaas-demo cannot directly mount another namespace's Secret: prepare an approved credential/CA distribution method as part of the test stage. Do not copy Secret contents into Git or diagnostic output.

## Verification commands

With an authenticated administrative oc session:

```sh
oc get application kaas-demo-kafka -n openshift-gitops
oc get kafka kaas-dev -n kaas-kafka -o yaml
oc get kafkanodepool dual-role -n kaas-kafka -o yaml
oc get pods -n kaas-kafka -o wide
oc get pvc -n kaas-kafka
oc get kafkatopics,kafkausers -n kaas-kafka
oc get installplans -n kafka-operator
```

The newer Kafka operator plan remains unapproved; deploying Kafka does not authorize an operator upgrade. GitOps 1.22.3 was separately approved by the user and is already installed.

No producer/consumer Job is included. The subsequent smoke test still requires the selected xk6 image, verified security/size/retry/ack mappings, the <=300s total client deadline and durable record accounting. No success claim for throughput, message delivery, recovery or inherited infrastructure persistence follows from cluster readiness. Do not delete namespaces/PVCs as a troubleshooting shortcut; no teardown was requested.

Sources checked 2026-11-23: exact installed CRD schemas and selected operator CSV/image mapping; fresh live namespace/node/storage/operator inspection; Red Hat Streams 3.2 [deployment configuration](https://docs.redhat.com/en/documentation/red_hat_streams_for_apache_kafka/3.2/html/deploying_and_managing_streams_for_apache_kafka_on_openshift/overview-str) and [securing access](https://docs.redhat.com/en/documentation/red_hat_streams_for_apache_kafka/3.2/html/deploying_and_managing_streams_for_apache_kafka_on_openshift/assembly-securing-access-str). Runtime acceptance is reported separately from documentation/schema validation.
