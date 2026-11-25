> Portable publication copy. Source revisions and coordinator-only references are listed in the C7 publication provenance; historical results remain scoped to their original review dates.

# Monitoring, alerts and overload coverage

Revision 0.1, PROPOSED operational mappings; reported existing services are reused. C1 supplies actual configuration/exporter inventory, platform monitoring owner supplies collection/alert routing, C7 maps response, C3 validates acceptance. Named people/on-call groups remain OPEN; work-area ownership is not proof of staffed support.

## Inspected inventory

Saved November 25 monitoring Pod snapshot (coordinator-only reference: `docs/testing/runs/collector-fix-20261125/repeat-short-complete-metrics/monitoring-pods.json`; see publication provenance) labels report Prometheus 3.7.3, Alertmanager 0.29.0, Thanos 0.39.2, prometheus-operator 0.87.0, kube-state-metrics 2.17.0 and node-exporter 1.10.2; image references are retained there. Labels/source references are not fresh binary-version checks. Existing Thanos historical queries established access and node/API/restart samples in the maintenance assessment (coordinator-only reference: `docs/testing/continuity-maintenance-check-2026-11-25.md`; see publication provenance). Alert rules/receivers, notification delivery, TSDB retention, Kafka exporter mappings and overload policy are not yet inspected. Their absence from this package does not mean the reported capability is absent.

The collector/observer have direct source and recorded short-run evidence: 30s observer polling, 90s observation watchdog, stricter 60s runner/auditor gap criteria, observer disk stop above 75%, collector persistence rejection above 80%. These are sandbox harness controls, not proposed production SLO defaults. Worker native calls may outlive a stop signal until their outer deadline. Preserve this limitation in incident assessments.

## Coverage and response contract

Every future rule needs actual query/exporter/label mapping, scrape interval, missing-series handling, evaluation window, threshold, receiver, acknowledgement/escalation owner and a recorded alert-delivery exercise. Silence must not count as healthy if collection is absent. No PrometheusRule is installed by this package. Broker JMX names from Kafka documentation must not be guessed as exported Prometheus names.

| Coverage / acceptance | Evidence and proposed trigger | First response / implementation owner | State |
| --- | --- | --- | --- |
| Kafka availability and quorum, SC3/RST | Ready + observed generation, offline partitions, active controllers/quorum voters, leader/ISR sets; proposed immediate incident on unavailable partition or quorum | C4 checks process/storage/network; stop planned rollout; C1 owns infrastructure escalation | Specified; actual rules/routing OPEN |
| RF2 durability margin | Under-replicated / below-minISR partitions and ISR changes; condition on effective topic ISR and actual acks | C4 restores replica health; no automatic minISR reduction or unclean election | Source policy verified; alert coverage OPEN |
| Producer admission, CAP | Attempted/ACK/error/ambiguous send rates, native latency, throttles and broker errors per tenant/topic | C2/app owner bounds retry/buffer; C4 applies approved quotas/admission; C6 reviews tenant rights | Smoke/short ledger evidence only |
| Consumer progress and expiry | Per-group partition committed/current/end/start offsets, oldest unread age, age budget and catch-up rate; offset count alone is insufficient | App owner/C3 classify idle scheduling versus stall; C7 escalates shrinking preservation margin | Actual age query/SLO OPEN |
| Disk and infrastructure | Used/free bytes, time-to-full at measured growth, PVC/node/storage events, IO latency/errors and saturation | C1 supplies backend/failure domain; C4 executes reviewed capacity/rebalance response | gp3/PVC snapshots; target VSAN OPEN |
| CPU/memory/network | Worker and broker CPU/throttled periods, OOM/restarts/heap/GC, network loss/retransmit, saturation | C1/C2/C4 distinguish generator versus service bottleneck | Historical sampled metrics; envelope OPEN |
| Evidence service | Collector HTTPS latency/error/commit latency, DB/WAL growth, disk, exports, observer heartbeat and deadline | Run owner preserves ledger and controls test; C7 supports diagnosis | Idle/TLS regression and short run recorded; HA OPEN |
| Reconciliation | IDs, hashes, expected budgets, ACK/receipt/commit and lifecycle coverage; any missing ACK receipt/integrity mismatch incident | C3 classifies result; C2 fixes harness, C4 diagnoses Kafka | Existing auditor reused; RST offset evidence extension needed |
| Governance | Registry API/backends, schema retrieval/compatibility, Gravitino metadata, snapshot/restore age | C5 supplies product/version, queries, persistence/recovery and owner | Reported available; interface OPEN |
| Access and changes | Certificate expiry/rotation, failed auth/ACLs, cross-tenant attempts, ArgoCD drift/sync/audit and OLM plans | C6 defines policy/receivers; C4 maps and applies authorized changes | Dev controls only; production coverage OPEN |

Shared mode requires per-tenant and aggregate views, including multiple principals and all brokers. Dedicated mode requires per-deployment views plus contention on common workers/storage. Cardinality budgets must be approved: retain record IDs in ledgers, not Prometheus labels. Quotas per principal/broker do not guarantee a tenant-wide service cap.

## Overload procedure proposal

1. Confirm telemetry freshness and run/config identity; record admitted/offered/ACK/consumed rates separately. Check generator throttling before assigning a broker limit.
2. At reviewed warning limits (OPEN), reduce new admission using the existing approved control and alert the tenant/run owner. Preserve bounded producer queues, unsent counts and ambiguous sends. Retry storms must not convert overload into unbounded resource use.
3. At reviewed critical disk/lag/error limits (OPEN), the authorized owner stops new offered traffic through the scenario's stop mechanism and preserves reads/drain where safe. A collector stop is evidence admission, not cancellation of in-flight Kafka calls. No claim that C7 can stop an active run.
4. Recover under C4/C1/C6 ownership without changing retention/ISR/security or deleting data as an automatic mitigation. Resume only after reviewed hysteresis/stable-health interval and backlog/expiry budget. Capture rejection/throttling and recovery latency for CAP-03–05.

Production warning/critical values, backpressure interface, automation authority and safe queue capacity are SP5 inputs, or earlier if a selected activation requires them. Validate overload in a separately approved bounded scenario with explicit resource/stop budgets, rather than derive a peak multiplier from daily TB.
