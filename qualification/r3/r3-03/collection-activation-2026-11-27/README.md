# R3-03 collection-only activation result

**PASS for collection-only scope, 2026-11-27.** User-authorized A0/A1/A2/A3/A7 completed. Email/routing and KaaS live broker/sink alert rules remain deferred; full notification/service qualification is not passed. All four client Jobs remain suspended with unchanged UIDs/specs. No producer/consumer tests or test emails ran.

Resource pin: `5610bfa484b13599e3218b1bcdb366769deba13d`. Necessary derived bootstrap/Kafka metrics source was committed, pushed and fetched at `38ff7de3db7094c9b9661b2683544e556dd4f5ad` (four files; the existing Kafka spec adds only metricsConfig). This source publication was required to perform the authorized GitOps activation. The result/evidence package is included in its owning publication commit. Historical execution receipts retain their original point-in-time status; publishing results initiates no further live action.

## Results

| Stage | Observed result | Evidence |
| --- | --- | --- |
| A0 | Fresh admin/TLS, four suspended Jobs; narrow Role/Binding server-dry-run then applied; two Projects and manual Applications registered; effective PodMonitor create/patch permitted | evidence/bootstrap/ and evidence/inspect-resumed/ |
| A1 | Persistent config synced first, enablement second; five managed Pods Ready, two Prometheus and two Thanos Ruler replicas available; four gp3-csi filesystem PVCs Bound, 24Gi total, retention24h | evidence/sync-uwm-config/, evidence/sync-enable/, evidence/uwm-status-02/, evidence/closeout/ |
| A2 | JMX ConfigMap first; existing Kafka owner pinned to38ff7de; manual selected Kafka sync/no prune or force; three broker Pod UIDs replaced and all Ready, generation2 observed;58/58partitions full ISR before/after;3metadata voters, followerlag0 | evidence/sync-jmx/, evidence/sync-kafka/, evidence/roll-observation/, evidence/broker-health-before/, evidence/broker-health-after/ |
| A3 | PodMonitor manually synced from5610bfa;3/3logicaltargets up;5metricfamilies perbroker/15gauges; faultcounts0/oneactivecontroller;326.21second observation,5minminimumup=1 and10–11samples/target | evidence/sync-podmonitor/, evidence/targets-final/, evidence/collection-stability-resumed/ |
| A7 | Both new Apps, existing Kafka App and both tenant Apps manual/Synced/Healthy; all4JobUIDs/specs unchanged/suspended/active0; existing sink1/1/evidencePVCBound; no KaaS PrometheusRules or AlertmanagerConfig resources | evidence/closeout/ |

Live window started06:45:08UTC (08:45:08Asia/Jerusalem), documented closeout within15.90minutes of the approved90minute budget. The observed monitoring requests total819mCPU/5594Mi, conservatively summing init/regular containers, within the1000m/6144Mi UWM allowance. Broker requests/limits remain unchanged. This is request accounting, not measured usage, target sizing or a production resource recommendation.

The three manual Application pins are Kafka38ff7de and platform/scrape5610bfa; existing tenantA/Bpins remain3211df9. No prune, force, replace, automatic sync, operator/broker version upgrade, RF/minISR/retention/listener/authentication/ACL change or client workload was used. Active Kafka spec comparison proves metricsConfig is its sole delta. All existing data claims/sink remain in place. New storage binding/configuration does not constitute tested restart durability or24h retained-history proof. No application messages were produced or reconciled; this is neither a repeat R2test nor a no-loss/capacity/recovery qualification.

## Observation limits and helper corrections

Captured rollout snapshots showed at least two Ready brokers; this is sampled observation, not continuous proof of every transition. Post-roll Admin describe verified all58partition ISR sets and current quorum; it changed no topics/groups/offsets. Broker TLS identity stayed within its existing Pod and properties passed through /dev/fd; no credential files or exported Secret values. All API clients used strict TLS and tokens in RAM; diagnostic oc kubeconfigs used anonymous RAM memfd, closed afterward. No API Secret reads in this activation.

Retained failed helper attempts are not Kafka failures: first generic session startup permission review timed out before any execution and the narrower retry succeeded; a local import error stopped before API; empty-token receipt guard was repaired offline after successful read-only inspection; first metrics probe hit a local request-log variable collision before Thanos queries. The initial freshness gate compared different query evaluation times; correction uses each timestamp query's own time without changing75s freshness or5minhistory thresholds. Resumed history then passed. No resource rollback or threshold weakening was used to obtain success.

`execution-source/` archives the final helper versions, which evolved through those corrections; final source hashes identify these archived versions, not the bytes of every earlier attempt. They require the original parent workspace layout/CA and are evidence, not unattended portable runners. JSON evidence is copied exactly from the shared execution workspace. Publication guide, result and validation distinguish fresh executed facts from the older disabled candidates/receipts. No independent reviewer or new fault/delivery test is claimed.

## Custody and next boundary

Primary responder/custodian is the user; no backup explicitly selected for this sandbox. Seven-day existing evidence policy/workspace export remains; original sealed R2 data untouched. Metrics24h retention and Kafka6h retention are separate. Email destinationgunger@redhat.com is preserved for future selection; SMTP/routing/live rules stay deferred with no pending question. Full R3-03 notification qualification and other service cases remain explicit future scope. No automatic test, further rollout, cleanup, deletion or email follows this result.
