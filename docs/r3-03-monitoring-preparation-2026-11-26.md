Offline activation proposal: [stages, estimates, impact, rollback and remaining inputs](r3-03-activation-plan-2026-11-26.md). No rollout or workloads; all action flags remain disabled.

# R3-03 monitoring preparation result

[Prepared package](../qualification/r3/r3-03/README.md), [disabled profile](../qualification/r3/r3-03/profile.disabled.json), [operational inputs](../qualification/r3/r3-03/inputs-needed.json).

A bounded GET-only discovery confirmed existing platform/container telemetry but no configured Kafka broker metrics or Kafka Exporter, no cluster PodMonitors, no matching Kafka/Strimzi series in kaas-kafka, no Kafka/kaas-referenced rules in46rule resources, and only the core platform Prometheus consumer. Receiver routing stored in platform configuration Secrets was not read. This is an observed in-cluster pipeline gap, not a claim that all monitoring or an unknown external system is absent.

Prepared offline: supported user-workload monitoring prerequisite; metrics-only patch to existing Kafka owner source; narrow JMX mappings/PodMonitor/proposed alerts; optional sink infrastructure rules and scoped lag-exporter stage; nondeployable existing-receiver routing fragment. No new active include/Application, cluster resource, workload, notification, Secret or credential was created. All four existing client Jobs were observed suspended/active0. Stage order holds alert rules until actual scrape/metric availability is verified.

Local render/schema/source checks passed. PromQL parser/promtool, live admission/reconciliation, MBean/port/target selection, rule evaluation plane and notification delivery remain untested. Enabling the prerequisite would consume monitoring resources and enabling broker metrics may roll brokers; no budget or rollout approval is inferred. Lag/age, durable-ACK/errors, security event feed and fairness remain separately scoped missing signals.

Two role/reference bundles are needed: evidence technical custodian/backup, and monitoring/routing owner with approved receiver/channel reference and responder/escalation contact. Existing user accountability/seven-day policy remain accepted. Do not send credentials or token-bearing webhook URLs. No deployment approval or live test is requested to complete this offline preparation.
