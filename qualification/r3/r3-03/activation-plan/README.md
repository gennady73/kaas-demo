# Staged R3-03 activation plan

**Prepared offline; every execution/deployment/workload/notification flag remains false.** This plan consumes the published monitoring package at `3d7b6bae3beab549d0aae4a3c50dfe7129929bff`. It is a reviewable proposal, not activation authority. The user authorized publication of the plan; its owning Git commit identifies the published snapshot, while original validation receipts retain their historical preparation labels. No cluster was queried or changed for this task. All four client Jobs are untouched, last observed suspended/active0 during the saved discovery.

Recommended first scope: supported user-workload monitoring (UWM), narrow broker metrics/scraping and reviewed broker rules. Reuse existing Alertmanager and OpenShift metrics UI. Hold optional sink rules until the evaluator can see their source series; defer lag exporter and safe notification until separately selected. No Grafana, second Alertmanager, broker/worker addition or client run is proposed.

For the requested plain-language explanation of budget,24-hour retention,90-minute window and responder/escalation roles, see the [operator brief](operator-brief.md). No choice is marked accepted by that explanation.

## Resource estimates — proposed, not measured

[Machine-readable estimates](resource-estimates.json) distinguish planning allowances from actual Kubernetes requests. These are initial C0 sandbox estimates, **not vendor minimums, measured consumption, hard limits or proof of current free capacity**. Before enabling UWM, the platform owner must reconcile its installed-release whole-Pod defaults/sidecars and approved resource settings with this budget. Hold for revision if they do not fit; do not impose guessed limits on managed components.

| Increment | Nominal Pods | CPU allowance | RAM allowance | Basis |
| --- | ---: | ---: | ---: | --- |
| Prometheus main containers |2|500m|4096Mi|2×250m/2048Mi engineering allowance |
| Thanos Ruler main containers |2|200m|1024Mi|2×100m/512Mi engineering allowance |
| UWM Prometheus Operator main container |1|100m|256Mi|Engineering allowance |
| Combined managed sidecars/auxiliary overhead |Included above|200m|768Mi|One aggregate allowance, **not a sixth Pod**; exact release footprint still to reconcile |
| **UWM subtotal** |**about5**|**1000m**|**6144Mi (6Gi)**|Topology follows4.21 documented example; sizes are proposed |
| Broker JMX incremental utilization |0new|150m|384Mi|3×50m/128Mi allowance inside existing broker Pods; not a NodePool request/limit change |
| **Core estimated increment** |**about5**|**1150m**|**6528Mi (6.375Gi)**|Arithmetic sum |
| **Rounded steady planning reservation** |—|**1250m**|**6656Mi (6.5Gi)**|Proposal for user review |
| **Change-window planning reservation** |Topology-dependent|**1750m**|**9728Mi (9.5Gi)**|1.5×UWM allowance plus broker overhead, rounded upward; budgeting buffer, not predicted surge topology |
| Optional Kafka Exporter |+1|+50m request|+128Mi request|Published candidate: limit200m/256Mi; disabled, not included in core scope or implicitly authorized by spare buffer |

Existing broker source remains3×500mCPU/2Gi requests, with1CPU/2Gi limits each and512Mi–1Gi JVM settings. That is1.5CPU/6Gi broker requests already allocated, not available headroom. JMX must fit current CPU/heap/container limits; an observed shortage triggers a separate reviewed resource change. This planning allowance does not alter the SRS five-total-CPU target or declare that target adequate/inadequate. Existing operator/platform/sink/control-plane allocations are excluded from the incremental estimates.

**Metrics storage is a decision, not silently free:**

| Choice | Proposed increment | Consequence / boundary |
| --- | --- | --- |
| Functional sandbox pilot with ephemeral telemetry |0newPVCs; reserve about6Gi node ephemeral capacity,9Gi change-window allowance; proposed24h metric retention | Explicitly accept possible metric/rule-history loss on monitoring Pod restart. No persistent monitoring/HA claim. Verify installed-release ephemeral behavior before selecting; never use the evidence PVC as TSDB storage. |
| Persistent monitoring option |4newFilesystemPVCs:2×10Gi Prometheus +2×2Gi Thanos Ruler = **24Gi requested**, proposed gp3-csi and24h retention | Initial allocation only; verify TSDB volume/cardinality/growth and storage quota. Preserve claims/retention on rollback. Existing platform Alertmanager persistence remains its owner's responsibility; this does not certify whole-stack HA. |

Red Hat documents persistent storage for monitoring HA and warns that changing monitoring storage can recreate StatefulSets. Choose before activation rather than switch storage mid-rollout. The original candidate enables UWM but does **not** yet encode approved resource/storage/retention settings. A merged, pinned config diff reflecting the chosen option is required before A1. Existing3×20Gi Kafka and1Gi evidence claims stay untouched; sealed evidence remains seven-day sandbox+workspace with its recorded retain-through date. Metric24h proposal is separate from Kafka6h and evidence7days.

## Rollout impact

Treat the metrics-only Kafka change as capable of **up to three serial dual-role Pod restarts**. Enabling JMX changes broker runtime configuration; exact3.2.1-10 reconciliation/elapsed behavior has not been exercised. If the operator requires no restart, do not force one to match this planning assumption. If it blocks rolling or its safety checks fail, hold; do not force a restart, lower minISR or change features to make it advance.

- With RF2/minISR2, removing one replica can leave affected partitions at one ISR. `acks=all` writes to those partitions may fail/pause until ISR2 returns. Three brokers do not provide a third copy for an RF2partition. Do not promise continuous writes or infer safety from all four test Jobs being suspended; other client services might exist.
- Three dual-role controllers normally leave2of3 available during one restart, assuming both survivors and storage/network remain healthy. Another unavailable member can lose majority. No concurrent broker/controller maintenance, drains or unrelated operator upgrades belong in this window.
- Consumer leader failover/reconnect and broker catch-up can add disruption. Storage/broker identities, RF, minISR, retention, listeners, ACLs, binaries and metadata features remain unchanged. A rollback does not restore expired data or make six-hour retention a no-loss guarantee. Inspect applicable pre-outage lag/replay margin and reuse inherited persistence evidence; this is not a new durability test.
- Prefer one controlled operator reconciliation at a time. Require restored health/quorum/full ISR before allowing a subsequent **C0-initiated** change. The operator controls its own internal roll; stopping C0 promotion does not instantly stop that roll. Do not manually delete Pods or add an unreviewed pause annotation as an emergency shortcut.

## GitOps ownership before mutation

Offline source inspection found `gitops/bootstrap/kafka-project.yaml` allows Kafka/KafkaNodePool/KafkaUser/KafkaTopic only. It cannot be assumed to accept a ConfigMap, PodMonitor or PrometheusRule. Its namespace Role also explicitly grants Kafka kinds only; existing broader controller permissions do not widen the Project allowlist.

1. Keep the metricsConfig patch in the existing `kaas-demo-kafka` Application/source. Never point another Application at the same Kafka CR or sync the four-object validation render wholesale.
2. Prepare separate, narrowly scoped observability metadata: one manual Project/Application for new ConfigMap/PodMonitor/PrometheusRule in kaas-kafka; an optional second for PrometheusRule only in kaas-demo. No Kafka/Job/Pod/Deployment/PVC/Secret kind is permitted by those proposed Projects. Metadata does not add a runtime Pod allocation.
3. The UWM cluster-monitoring ConfigMap stays in the authorized **platform owner's supported Git/config workflow**. It is not placed under tenant A/B or delegated through the monitoring application Project. Preserve every unrelated config key and route; do not substitute direct `oc apply` for a missing GitOps path.
4. Check actual controller rights before activation. Prepare only genuinely missing kind/namespace-scoped non-delete grants as a separate reviewed bootstrap; no wildcard/cluster-admin escalation is selected. New monitoring source paths/commits, metadata pins and exact permissions are deliberately not invented in this plan.
5. Keep manual sync/no automated sync/no prune/no force/no replace, no hooks and no cascading deletion. Creating an Application is separate authority from syncing its resources. Removing a resource from Git with no-prune **does not remove it from the cluster**.

## Staged change window

[Disabled stage contract](plan.disabled.json). Proposed total window **90minutes**, including checks/closeout, starting only after offline preparation and user choices are complete; this is a scheduling budget, not measured runtime or an RTO qualification. Optional stages can be omitted. Each stage requires explicit selected scope and an independent proceed/hold decision; no job or client is ever unsuspended by the plan.

| Stage / budget | Exact future action | Gate before proceeding |
| --- | --- | --- |
| **A0 —10min: freeze inputs/baseline** | Confirm previously resolved budget/storage/window/contacts, merged config, narrow monitoring ownership, immutable pins and completed offline PromQL/rule validation | Capture applicable current health/identity/rights/source and4Job states, current config/route fragments, claim retention and installed defaults. No blanket R1/R2repeat. If source, fields, ownership or observability are insufficient, hold. |
| **A1 —15min: consumer only** | Enable only approved UWM configuration; no Kafka change or application rule yet | Actual managed components/resources/storage match approved footprint, operators healthy, intended namespaces selectable, no unrelated consumer/route/config regression. Review cluster-wide effect on other user projects, not just KaaS. |
| **A2 —30min: exposure** | Add approved JMX ConfigMap, then metrics-only Kafka change via current owner | Observe operator reconciliation, no second unavailable member, approved metadata evidence of quorum/ISR recovery, broker resource margin.10min per-broker progress checkpoint; whole30min budget includes final stability. This is not three guaranteed10min restarts plus extra time. Hold on abnormal progress; no automatic extension/force/second change. |
| **A3 —10min: scrape** | Enable own scoped PodMonitor; alert rules held |3/3targets up, all5expected families and labels present, actual9404named port and union of NetworkPolicies understood. Require proposed5min healthy interval within the selected stage/window budget. No absent-series healthy-zero interpretation. |
| **A4 —5min: routing gate first** | Review approved existing recipient/config; if needed merge the previously approved narrow KaaS route through its monitoring owner | Known receiver/contact and accepted routing effect before rules. **Unknown receiver means stop after scrape-only.** Config acceptance is not delivery proof; no safe-test notification. |
| **A5 —5min: broker rules** | Enable only reviewed broker rule groups after A4 | Evaluator/query plane healthy, rules parse/evaluate, labels/windows correct. Rules can send **natural alerts through existing routes**, even with no synthetic test. That effect must be within the approved change. |
| **A6 —optional5min: sink rules** | Enable existing infrastructure-signal rules only after A4 | Evaluator sees the relevant kubelet/kube-state series; no fake durableACK/error feed claim.64MiB floor retained;128MiB warning and windows accepted as proposals. |
| **A7 —10min: closeout** | Capture final read-only identities/settings/resource/target/rule state and custody | All4clientJobs still suspended; preserved sources/PVCs/tenant ownership and explicit gaps. No cleanup or client run. Record actual elapsed/impact and release limits. |

Routing must be known before A5/A6. Notification-test flags prohibit a synthetic test, but cannot prevent naturally firing enabled rules from sending messages; unknown recipients block rule enablement. A separately approved safe delivery check is outside this90minute window.

A 5min stability observation is a proposed initial activation criterion, not a production SLO. If stages need more time, the owner revises the window rather than silently extending it. No production performance, security-denial, recovery or full-service PASS follows from this monitoring activation. Optional lag exporter is outside this90min core plan; including it requires a reviewed extra phase/resource allowance and its own gate.

## Rollback and containment

See [stage-specific rollback](rollback.md). First stop further promotions, preserve evidence and inspect what the operator already owns/is doing. A source revert is not an instantaneous runtime rollback. Prefer targeted configuration repair or leave a healthy consumer in place over a risky global disable. Every actual rollback needs its precise owner-approved diff/authority; this planning request executes none.

**Never use as rollback:** prune/force/replace, deleting broker or evidence PVCs, deleting/recreating Kafka, resetting offsets, removing tenant resources, downgrading binaries/metadata, reducing ISR/RF, shortening retention, rotating credentials, restarting the sink or using whole ConfigMap/Alertmanager Secret replacement. Monitoring objects/managed Pods may be affected by a supported operator disablement only under its separately reviewed scope and storage/consumer protections; no automatic deletion is authorized.

## Inputs still needed from you

1. **Budget disposition:** accept/amend the proposed incremental1.25CPU/6.5Gi steady and1.75CPU/9.5Gi change-window planning reservation. Actual release defaults/headroom remain to reconcile; these are not hard limits or guaranteed use. Defer optional lag exporter unless explicitly included.
2. **Storage choice:** ephemeral functional sandbox pilot (0newPVCs, telemetry-loss/no-HA boundary) or persistent UWM option (proposed24Gi/4PVCs), plus acceptance/amendment of proposed24h monitoring retention. Kafka6h and evidence7days stay unchanged.
3. **Window and stop authority:** proposed90minute window, permitted broker write disruption, named authorized executor/stop/escalation contact. The user remains owner/approver; no invented second approver. Confirmation must cover any other affected clients, not merely the suspended test Jobs.
4. **Evidence custodian/backup:** person/team reference and contact for copy/retention/hold/disposition records. Accepted seven-day policy need not be repeated.
5. **Monitoring/routing responder:** owner/contact, approved existing receiver/channel reference and acknowledgement/escalation runbook. One person may fill multiple roles. Keep secrets/token-bearing URLs out of chat/Git. A safe notification remains opt-in later.

The existing API-admin/C0 executor and user stop authority can be proposed for reuse when choosing the actual window; no new role separation is demanded. The technical platform/GitOps owner can supply its existing supported configuration path, exact managed footprint and sanitized routing evidence; these are artifact joins, not requests to redesign ownership/security. After these choices, prepare the exact merged/pinned activation transaction for review. **No question or approval is pending for this offline planning task; it ends here.**

## Validation, evidence and limits

Only source/plan/resource arithmetic, stage dependency/time/flag checks and published artifact integrity were checked. No old suite, render, new native/image build, cluster API, deployment or workload ran. Source versions and [validation receipt](evidence/validation.json) identify this plan. Exact3.2.1-10 rollback/roll timing, whole-Pod requests, metric/rule behavior, supported storage behavior and receiver delivery require applicable later evidence. Existing PromQL-parser gap must be closed before enabling rules; this plan does not relabel the prepared expressions validated.

Primary references checked26November2026: [OpenShift4.21 UWM](https://docs.redhat.com/en/documentation/monitoring_stack_for_red_hat_openshift/4.21/html-single/configuring_user_workload_monitoring/index) for component topology/configuration; [monitoring storage](https://docs.redhat.com/en/documentation/monitoring_stack_for_red_hat_openshift/4.21/html/configuring_user_workload_monitoring/storing-and-recording-data-uwm) for persistence/StatefulSet implications; [Streams3.2 metrics API](https://docs.redhat.com/en/documentation/red_hat_streams_for_apache_kafka/3.2/html/streams_for_apache_kafka_api_reference/con-common-configuration-properties-reference) for enabled/absent metrics behavior; [minISR contract](https://docs.redhat.com/en/documentation/red_hat_streams_for_apache_kafka/3.2/html/kafka_configuration_properties/topic-configuration-properties-str) for conditional write availability. Budget sizes/overhead/window/allocations here are C0 proposals, not vendor sizing claims. Enabling metrics is conservatively budgeted for a roll; no exact-build restart guarantee is asserted.
