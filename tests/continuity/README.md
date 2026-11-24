# Sandbox continuity preparation

Preparation history: originally prepared and validated **offline only**. The direct user-authorized 24h/100 MB run is now in progress; see the [run checkpoint](../../docs/continuity-24h-run-2026-11-24.md) and [collector/monitor guide](collector/README.md). The following preparation statements describe the original offline stage. No Kafka/k6 process, HTTP collector, test Job, ArgoCD sync or cluster mutation was executed for these scenarios. See [implementation/collector contract](../../docs/continuity-adapter-offline.md) and [staged plan](../../docs/staged-xk6-continuity-plan.md).

| Stage | Measured time | Value bytes | Records of 1,000 bytes |
| --- | --- | ---: | ---: |
| 15m | 15 minutes | 1,040,000 | 1,040 |
| 60m | 60 minutes | 4,168,000 | 4,168 |
| 24h | 24 hours | 100,000,000 | 100,000 |

`scenarios/` contains disabled planner inputs; `generated/` contains reproducible disabled worker plans and hashes. `continuity-plan.json` is the coordination/review contract. `runtime/preflight/` is a frozen, hash-checked copy of the canonical utility's continuity JS modules and future entrypoint; it is not a separate implementation to edit. All plans carry execution_ready=false and execution_enabled=false, offline-prefixed run IDs, and null runtime inputs. No executable Job or automatic stage progression is supplied.

The separate planner mode keeps WP-A/WP-B terabyte safeguards intact. Producer and consumer clients are persistent and independent; a reviewed durable collector ACK is required before each manual offset commit. The collector was subsequently deployed and checked, including a collector-only Pod replacement; final full-duration timing/commit/close acceptance is still pending. Do not arm plans or execute the entrypoint during preparation. The corrected image contains the native binary, not these new mounted scripts.

Canonical source is pinned to [kafka-load-test commit `963db2d`](https://github.com/gennady73/kafka-load-test/tree/963db2d41b6dc140d661c96e108f1c09a7c76da5/preflight). The bundle is provided here so later reviewed Job configuration can mount exactly the source hashes recorded in a plan. Generated source fingerprints, runtime bundle and canonical modules must match. Offline command examples and evidence semantics are in the implementation document.

Final 2 TB/20 TB profile generation/publication remains deferred until successful 100 MB/24h continuity validation. No test has been run under this preparation, and no stage is enabled by merely committing these files.

`requirements-contract.json` is an exact snapshot of the existing requirements input used to generate the plans. It is not executable and does not arm or finalize any terabyte profile. Its digest matches each plan's contract input hash.
