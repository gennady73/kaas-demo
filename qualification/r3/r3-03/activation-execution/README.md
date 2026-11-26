# R3-03 accepted persistent monitoring preparation

This execution overlay records the user's acceptance after published plan `c1096073ca79dec38c3e7f1c96a436591359c31c`. The original disabled plan and its receipts remain unchanged. No live change window has started.

## Settled decisions

Extra planning allowance: 1250m CPU / 6656Mi steady; 1750m CPU / 9728Mi total during the change. Window budget: 90 minutes, including the disclosed conditional broker write disruption. Metrics retention: 24h. Persistent monitoring: two Prometheus PVCs at 10Gi and two Thanos Ruler PVCs at 2Gi, totaling 24Gi. User is primary responder and evidence custodian, explicitly with no backup for this sandbox. Approved alert destination: `gunger@redhat.com`. Kafka retention remains 6h; evidence retention remains seven days with a workspace copy.

## Prepared configuration

`candidate/platform/` contains supported configuration candidates with explicit requests for the three main components, 24h retention and filesystem RWO gp3-csi storage. These request settings are not hard usage limits. PVCs are created by the managed StatefulSets, not four separately applied PVC manifests. Two replicas per component must be checked on the actual managed objects. The two configuration objects were absent in the fresh read; compare absence/resource versions again before publication/sync so concurrent ownership is preserved.

`candidate/broker-scrape/` renders only the JMX ConfigMap and PodMonitor. `candidate/kafka-owner/` is a metrics-only patch to be merged into the existing Kafka Application source. It must never be owned by a second Application. Registration templates separate platform configuration from broker scrape ownership; they are manual, contain no automated sync, and require a real immutable resource commit in place of `${RESOURCE_COMMIT}`. No active root references this directory. Rules and optional exporter are excluded from both deployable Kustomize roots. No client, sink, new node, Grafana or second Alertmanager is included.

## Executed checks

Bounded strict-TLS/memory-only GET refresh: 15 requests, 10.037 seconds, no resource writes. All four client Jobs suspended/active zero; five Ready nodes; Kafka Ready. gp3-csi exists with WaitForFirstConsumer, expansion enabled and Delete reclaim policy. Selected namespaces have no resource quotas. This does not prove cloud volume quota, binding, filesystem permissions or metric durability. Preserve metrics PVCs; deleting claims can delete backend volumes.

Request-accounting projection of 352 Pod records leaves about 63.9 CPU and 247.1Gi memory across nodes. This is derived request arithmetic, not measured free usage or scheduling proof: it sums all init requests conservatively, does not capture Pod-level resources, and does not validate attach limits or actual operator placement. Exact capacity receipt retains per-node values.

Official checksum-verified upstream promtool 3.7.3 parsed all ten rules and passed twelve fixtures. Cases cover normal behavior, down/absent scrape, missing required family, minimum ISR, replication, offline partitions, controller count, evidence warning/critical space, missing PVC metric and unavailable sink. Local semantic checks do not establish live evaluation or alert delivery. No rule activation was performed.

## Exact remaining activation gates

1. Reconcile exact installed CMO/Prometheus Operator templates and injected sidecars against the accepted envelope. Installed CMO image is pinned in `evidence/exact-build-source-hold.json`. Its registry rejected anonymous metadata access. Archived immutable release-family source is a reference, not exact-build proof; no pull Secret was read. This is a technical provenance gate, not a request to reconfirm budget.
2. Publish/freeze concrete resource and registration pins, perform exact schema/admission/effective-permission checks, and refresh compare-before-write/live health gates before opening the change window. No registration or sync has happened.
3. Alert email destination is accepted as `gunger@redhat.com`; the recipient question is closed. Existing email receiver/SMTP relay, sender, STARTTLS/trust and credential references still need technical verification. Previous discovery did not read platform Alertmanager effective receiver configuration, so SMTP availability is unverified, not absent. A4–A6 remain held pending the exact working transport/routing disposition. No test email or live notification was sent. See `email-delivery.json`; no mail infrastructure is inferred from the recipient domain.

Current result: A0 preparation partially complete; A1–A7 not executed. All four client Jobs remain untouched. Full R3-03 live qualification remains open; no workload or repeat R2 test ran.

## Latest prerequisite review

See [prerequisites/README.md](prerequisites/README.md). Exact installed packaged-asset provenance is now verified directly; conservative resource projection fits the approved envelope, with actual generated Pods checked at A1 exit. Four server dry-runs passed. Narrow PodMonitor permissions are missing and prepared offline. Actual Alertmanager configuration has no SMTP integration; SMTP references or a defer disposition are pending. No live activation or test email occurred. This section supersedes earlier open-source/SMTP-unknown statements for these scopes.

## Accepted email deferral

User explicitly selected “defer email”. SMTP/routing is therefore deferred and no longer blocks the collection-only scope. No unanswered input question remains. Selected stages: A0/A1/A2/A3/A7,75minutes of the approved90minute budget; remaining15minutes are slack, not a runtime guarantee. A4–A6 remain deferred: no email route or live broker/sink alert rules. Notification qualification is not passed or waived. `selection.disabled.json` in the execution directory records current selection; it does not register or deploy anything. Publication/pins, narrow permission server-check/application and fresh health/compare-before-write remain before activation. All four client Jobs remain suspended; no producer/consumer tests or test email.
