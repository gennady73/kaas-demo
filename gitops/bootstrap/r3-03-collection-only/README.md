# R3-03 controlled collection-only bootstrap

Derived from user-selected resource commit `5610bfa484b13599e3218b1bcdb366769deba13d`. Registration contains two narrow Projects and two manual Applications pinned to that resource commit. No auto-sync, prune, force, live rules, email or test workload.

The PodMonitor grant is namespace/kind-scoped create plus exact-name update/patch; existing read grants are reused. Apply only through the current authorized controlled bootstrap after fresh checks and server dry-run.

Apply the platform Application selectively: user-workload-monitoring-config first, cluster-monitoring-config enablement second. Verify actual UWM resources, four bound PVCs and health before touching Kafka. Apply broker JMX ConfigMap before the existing Kafka owner's metrics-only change; apply PodMonitor after broker readiness. The existing Kafka Application must be pinned to this owning commit for the metrics patch; no second Application owns Kafka.

This Git commit prepares the source. Actual execution/health/timing are recorded separately; source publication does not prove deployment. All four client Jobs stay suspended.
