# R3 read-only refresh — completed with explicit coverage gaps

**Completed2026-11-26,18:45:25–18:45:52UTC.** The renewed credential authenticated as `admin` through strict API TLS/hostname verification. It was supplied through a non-echoing prompt, held only in process memory, and discarded when the process exited. No `oc login`, kubeconfig update or credential file was performed. The earlier401attempt is preserved separately and is not a current authentication blocker.

The resumed attempt made38remote requests in26.424seconds and read192,745body bytes. Combined with the earlier single identity401request,39requests remained within the40request budget. No automatic retries, resource mutations, Secret API reads, Pod exec/logs, workload, notification or Job changes occurred. Six POSTs were explicitly authorized, **nonpersistent SelfSubjectAccessReviews**, not cluster-resource changes. The remaining requests were GETs. Execution completed with one optional404: no `cluster-monitoring-config` ConfigMap at that exact name; this is not a monitoring-stack failure.

## Freshly verified observations

| Item | Observation / limit |
| --- | --- |
| Four existing client Jobs | **All suspend=true, active=0**, individually observed before other inspection. Old failed/succeeded counters remain historical; no Job was rearmed or rerun. |
| Tenant Applications and Projects | Both Apps Synced/Healthy at exact resource3211df93ae40d7d6f47c6334966ae6d1f658fee7, manual policies and reviewed source/destination/Project specs match, no pending operation. No re-registration/sync occurred. |
| Kafka | kaas-dev Ready/current generation,4.2.0; selected source settings still TLS/SCRAM9093, RF2/minISR2,6h retention and auto-create=false. No backend Admin/ISR/offset/client call was made; CR readiness is not fresh message durability or recovery evidence. |
| Storage/sink | Three broker20GiPVCs Bound; existing evidence deployment1/1Available and evidence1Gi gp3-csi PVC Bound. No new allocation. |
| Current API capability | All six selected self-access reviews allowed: named Application patch, Topic/User list, named Job get, PrometheusRule list and named ArgoRBAC ConfigMap get. No patch was issued. This does not establish delegated-user denials or an ArgoSSO human session. |
| Argo controls | Selected admin/exec/tracking/RBAC fields match saved Nov25values. Default Argo policy empty; cluster-admin group mappings remain; controller identity/ClusterRoleBinding confirmed. Existing controller has wildcard get/list/watch across resources and broad management permissions in selected API groups. Project separation remains no substitute for a distinct Kubernetes identity/field-level admission. No rights were granted or narrowed. |
| Network/trust references | Existing network policies in the two selected namespaces and public Kafka/sink CA ConfigMap keys/hashes captured. HTTP sink service-ca.crt and native Kafka ca.crt remain separate references. No private material, new handshake/client enforcement or CA leaf-expiry claim. |
| Platform monitoring | Prometheus k8s Available/Reconciled, declared retention15d; Alertmanager main Available/Reconciled with2replicas. Retention configuration is not a verified15daystorage/persistence result. |
| Kafka-specific objects inspected | **Zero ServiceMonitor and zero PrometheusRule objects in each of kaas-kafka and kaas-demo.** These are exact namespace/kind observations. PodMonitor/global rule, other scrape, remote or user-workload configuration was not exhaustively inspected, so do not infer monitoring is globally absent. |
| Evidence filesystem metric | Existing Thanos query returned capacity1,020,702,720bytes and available999,993,344bytes: approximately953.67MiBfree,97.97%. Derived filesystem used19.75MiB. This is aggregate filesystem usage, not SQLite DB size, an allocation per future case or a growth guarantee. |
| Custody | Current workspace182-event export still hashes to18ba064608624da60e80101aaea81af9f0e8bfe9f4edbed126cc5903dd66c96e and matches saved seal. No remote DB/export content was read. Retain sandbox/workspace at least through2026-12-03T15:12:05Z; expiry does not authorize deletion. |

The source/control/config projections are evidence for this observation window only. No new GitHub branch-protection query was selected; its current state remains unrefreshed. Existing broad controller/admin rights are transparently recorded, not a new least-privilege acceptance or proof that a hostile tenant is isolated.

## Remaining exact inputs and next action

The authentication hold is resolved for this attempt. No repeat R1/R2, image build, broad regression or workload is needed to record this result.

- **R3-03 coverage:** existing monitoring owner should supply a sanitized reference/export mapping Kafka and evidence-sink signals to actual scrape selectors, rules, windows/thresholds and no-series behavior. The inspected namespaces have no ServiceMonitor/PrometheusRule objects; first resolve whether coverage exists through another approved source before preparing a narrowly scoped configuration change.
- **Receiver/escalation:** supply an approved sanitized routing/receiver reference and operational acknowledgement contact. Alertmanager's data/config Secret was intentionally not read, and no test notification was sent. Receiver metadata or an Available Pod does not prove delivery.
- **Custody:** identify the ongoing technical evidence custodian/contact and retention/hold/disposition enforcement reference. The user is already accountable owner/approver and the seven-day policy is accepted; those are not reopened.
- **C6:** its separate offline-review hold/concurrence remains unresolved; this read-only refresh did not substitute for that review or its unprepared negative cases.

These references/role inputs let C0 prepare one selected R3-02/03 service case or a narrow monitoring configuration proposal. No new configuration/deployment/receiver test or live canary is authorized by this result. Optional registry, payload runtime, quotas/fairness, failure/recovery, full-day/target capacity and dedicated/external claims remain separately scoped and unqualified. No automatic peer dispatch or workload follows.

## Records and preservation

[Execution intent](execution-intent.json) binds the user-directed resumed session and source hash. [Sanitized remote evidence](evidence/result.json) lists each request/status/size; [consolidated result](result.json) and [local custody check](local-custody-check.json) separate fresh from inherited observations. [Artifact manifest](artifact-manifest.json) and integrity/source receipts identify these bytes. Every evidence file is projected, not a dump of cluster credentials or environment variables. Original401attempt, owner artifacts, runtime source/image pins, original plan and sealed R2evidence remain unchanged. Changes are local and uncommitted; no publication requested.
