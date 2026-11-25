# Collector fix and continuity rerun, 2026-11-25

Status: **short validation PASS; fresh 24-hour run RUNNING, final result pending**.

## Cause and corrections

Inspection and isolated reproduction confirmed that summary/readiness/seal requests aggregated the growing ledger and performed expensive terminal lookups. The original server also performed TLS handshakes in the main accept path. The first eight-client probe reproduced a TLS handshake timeout. These are confirmed implementation defects and supported contributors; the original incident is not attributed to one exclusive mechanism or a proven cluster outage.

The fixed collector maintains per-run/client/type counters atomically with event inserts, with a one-time transactional backfill and a version marker. It uses an indexed terminal lookup and dedicated bounded readiness/export paths. Summary reads use a consistent SQLite snapshot. FULL/WAL commit-before-ACK, exact-envelope deduplication and independent reconciliation remain intact.

TLS handshakes now execute in request threads, bounded at 5 s, with queue 64. HTTP idle timeout is separately 180 s. Collector requests/limits changed from 100m/500m to 250m/1 CPU; RAM remains 128Mi/512Mi. Idle-only Recreate rollouts retained the same 2 GiB PVC and prior acknowledged metadata. No Kafka/topic/listener/security/operator/GitOps configuration changed.

The first query-only revision failed the concurrent TLS probe and restarted once during validation. The first native short run delivered all 1,040 records but FAILED during drain because an introduced 30 s HTTP idle timeout collided with 30 s heartbeats. That failure/export/audit is preserved. The final revision restores the original 180 s idle margin; no failed experiment is relabeled as passing.

## Validation actually executed

- Six offline regression checks PASS: commit-before-ACK, dedup/conflict/hash rejection, migration/reopen, counter rollback, bounded summary reads, deferred TLS acceptance/separate timeouts and stop handling.
- Isolated retained-ledger benchmark: 207,820 events, old median 1.566 s versus fixed 0.477 ms; fixed median 0.500 ms at 657,820 events (retained plus 450,000 offline synthetic metadata rows). Same counts/terminal states before/after migration. Local Python 3.15/SQLite 3.53.4 results, not live throughput or production qualification.
- Final live verified-HTTPS probe: 326 requests across 8 clients, 202 unique metadata events, idempotent retry, maximum 0.905 s, p95 0.703 s, no timeouts. The same TLS socket survived 35 s idle and a subsequent durable POST. No Kafka traffic in this probe.
- Repeated Kafka short run `continuity-15m-20261125081237-5917`: 15-minute generation plus 300 s consumer drain, 1,040 records / 1,040,000 original value bytes over 4 topics. Independent canonical auditor reports ACCOUNTING_COMPLETE, zero issues, all 8 complete client lifecycles. Worker and observer Jobs succeeded with exit 0, zero restarts; collector zero restarts; Kafka restart counts unchanged.
- Forty 30 s query samples from 08:14:30–08:34:00 UTC: collector CPU 0.0015–0.01284 cores, throttled-period ratio 0, restart count 0. Historical original-failure samples showed substantial throttling. These are sampled observations, not a guarantee for all future workloads.

Collector source SHA-256: `02f58ea213a7f2c40bf2173ce1b349ad314b8bef87780ffc2cb911d478926308`. Workload binary/image and four JS module hashes are unchanged; auditor originates from kafka-load-test commit 963db2d and demo commit 340938e. This publication includes the exact deployed collector source, regression tests and validation summaries. Git publication does not change the running ConfigMaps, Jobs or image pins. Existing six scenario/generated templates remain unchanged and disabled; only run-specific copies are armed.

## Fresh 24-hour run

Run `continuity-24h-20261125083551-5d08`, Job `kaas-demo/kaas-continuity-24h-20261125083551-5d08`. Generation window 2026-11-25T08:37:21.488Z through 2026-11-26T08:37:21.488Z: **November 25–26, 10:37:21 Asia/Jerusalem**. Allow up to 300 s drain and 60 s shutdown afterward. Target 100,000 records of 1,000 value bytes, total 100,000,000 decimal bytes, 25,000 records per topic. New groups and frozen plan SHA `0bc991ccdbd548a11e3ec1b210e17d96690d095659a283c7213f2821ca3b6a9f`. The recommended 60m stage was not run; user requested one short validation followed by the daily rerun, and the 15m gate passed.

The observer performs live progress/evidence checks and invokes independent reconciliation after clean completion. It does not send chat notifications. Full 24h duration/budget, final ledger/seal, clean worker/observer exits and cluster/restart review remain pending. This run cannot close TB-capacity, recovery or production service qualification. Preserve its sources/resources and keep the sandbox running through evidence retrieval.

Detailed evidence remains in the shared coordinator workspace: docs/testing/runs/collector-fix-20261125/. Repository summaries are under docs/evidence/collector-fix-*.json. Raw ledgers, active plans and credentials are excluded from Git. The previous failed daily run and first short failure remain separately retained.

Historical first live daily-run checkpoint: 23 ACKs, 23 receipts, 23 commits, all 8 clients ready, no recorded error or stop. This is progress evidence, not a full-run PASS.
