# Sandbox continuity run, 2026-11-24

Status: **RUNNING**, not passed. User requested direct 24-hour / decimal 100 MB continuity execution; 15-minute and 60-minute rehearsals were not executed. Published profiles remain disabled; only the private run-specific copy is armed.

Run `continuity-24h-20261124170112-1a83`, Job `kaas-demo/kaas-continuity-24h-20261124170112-1a83`. Production window: 2026-11-24T17:02:42.136Z through 2026-11-25T17:02:42.136Z, or November 24–25, 19:02:42 Asia/Jerusalem. Allow up to 300 seconds drain and 60 seconds shutdown. Four topics, four persistent producers and four persistent consumers, 100,000 total records of 1,000 value bytes. This checks continuity and delivery, not terabyte capacity or restart durability.

## Verified checkpoint

Collector reports 500 acknowledged records, 500 receipts, 500 offset commits, all eight clients ready, and no stop/client-error event at the saved checkpoint. These are live counters, not the final independent reconciliation. Initial Java Admin guard confirmed all four fresh consumer groups absent. Worker runs the digest-pinned verified custom xk6 build; canonical utility source is commit `963db2d41b6dc140d661c96e108f1c09a7c76da5`, demo preparation `6106cbc3f90e4e1c04398eb813a1b54782f70970`. Raw plan SHA-256: `70db532a78fb8c35619771ac43dcddca6738ca5b6f33e72f69e27fbf413d5be1`.

## Evidence collector and observer provenance

Source included with this publication under `tests/continuity/collector/`: `server.py` implements the HTTPS durable evidence collector, `InitialGroups.java` performs the initial fresh-group guard, and `watch.py` is the one-run observer. These are not part of the published xk6 image. The observer mounts the exact published independent auditor `kafka-load-test/preflight/continuity_reconcile.py`. Source snapshot/manifests are retained with this run.

Collector uses a dedicated 2 GiB gp3-csi PVC, verified service-CA TLS, bearer authentication, SQLite WAL/FULL commits before evidence ACK, idempotent event IDs, and same-namespace restricted ingress. The actual HTTPS probe persisted one metadata event, deduplicated its retry, then retained it after a collector-only Pod replacement. No Kafka broker restart was performed. API/client secrets remain in memory or Kubernetes Secrets and are excluded from saved artifacts.

The observer Job `kaas-continuity-24h-20261124170112-1a83-watch` is verified Running with MONITOR_STARTED and RUNNING logs. It polls only the collector, has no Kafka or Kubernetes credentials, records progress, stops further producer attempts through the collector on detected failure, and exports/audits evidence upon clean client completion. Results in observer emptyDir are temporary; the collector PVC retains primary evidence. Accounting success still requires external worker Job and cluster review before a final PASS. Keep the sandbox running through completion and evidence retrieval.

## Acceptance still pending

Reconcile all 100,000 unique acknowledged records against receipts, checksums and offset commits; verify full-duration scheduling and progress bounds, clean client termination, worker Job success and restart deltas from the initial baseline. Review observer output and retrieve final export/seal/report into this workspace. Then document results and prepare disabled 24-hour 2 TB/20 TB profiles for an appropriately sized target. No TB test is authorized by this run.

Detailed raw evidence and armed run manifests remain in the coordinator workspace under `docs/testing/runs/continuity-24h-20261124/`; they are not published or replayed by this commit. The credential-free execution receipt is published as `docs/evidence/continuity-24h-execution-2026-11-24.json`. See the [collector guide](../tests/continuity/collector/README.md) and source manifest for mount paths and source identity. Screenshots show low broker network/storage activity compatible with the small budget, but do not prove delivery; decimal payload average is only 1,157.41 B/s, excluding protocol, replication and evidence overhead.
