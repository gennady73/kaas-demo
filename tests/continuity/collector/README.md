# Continuity evidence collector and results monitor

These components support the four-topic sandbox continuity test. They are separate from the custom xk6 image. The workload and independent auditor originate in [kafka-load-test at 963db2d](https://github.com/gennady73/kafka-load-test/tree/963db2d41b6dc140d661c96e108f1c09a7c76da5/preflight). See the [running-test checkpoint](../../../docs/continuity-24h-run-2026-11-24.md); no final PASS is claimed.

| File | Purpose |
| --- | --- |
| `server.py` | HTTPS evidence API backed by persistent SQLite |
| `watch.py` | One-run progress observer and final auditor invocation |
| `InitialGroups.java` | Read-only Kafka Admin guard: all proposed consumer groups must be absent |
| `continuity_reconcile.py` | Exact independent auditor snapshot from the pinned utility commit |
| `source-manifest.json` | SHA-256 hashes matched to saved submitted ConfigMap source snapshots |
| `validation-summary.json` | Prior local handler/SQLite checks; not a full-duration result |

## Deployment and dependency contract

This directory contains source, not an automatically applied deployment. Current test resources live in `kaas-demo`, outside the ArgoCD application source paths. Publishing changes here does not synchronize or recreate them. Keep the existing run's source ConfigMaps, frozen plan, Secrets, PVC and Jobs unchanged until evidence is retrieved. These scripts have no automatic stage promotion or recurring schedule.

The deployed Python/Java host image is pinned to `registry.redhat.io/amq-streams/kafka-42-rhel9@sha256:ce7dc91b664600c6f06e1df3d6b56a4684bb779865d9c28b4df648addd89189d`. It supplies Python 3 with SQLite/SSL and Java 21/Kafka libraries. The worker uses the separately verified custom xk6 image documented in the existing smoke build guide. Collector and observer run without a service-account token, as non-root with restricted security settings.

For a separately authorized future deployment, assemble and review resources with these interfaces; these are requirements for assembly, not commands to alter the current run:

- Collector `kaas-continuity-collector`: one Deployment replica, ClusterIP Service TCP 8443, ConfigMap mounting `server.py` into `/code`, command `python3 -u /code/server.py`. Mount a dedicated PVC at `/data`, bearer Secret text at `/auth/token`, and OpenShift service-serving certificate Secret at `/tls/tls.crt` and `/tls/tls.key`. Defaults may be overridden with `CONTINUITY_DATA` and `CONTINUITY_TOKEN_FILE`. Serving certificate paths and listen port are fixed in this implementation.
- Current persistence: `kaas-continuity-collector-data`, 2 GiB, `gp3-csi`. Current requests/limits after the November 25 fix are 250m/1 CPU and 128Mi/512Mi RAM. Collector strategy is Recreate; migrate only while no continuity Jobs are active. This is a sandbox selection, not the production VSAN/ODF storage decision. A single collector Pod/PVC is not a highly available service or disaster-recovery guarantee.
- Use an OpenShift service-CA-injected ConfigMap for client trust. The certificate must cover `kaas-continuity-collector.kaas-demo.svc`. No plaintext endpoint or TLS-verification bypass is used. NetworkPolicy permits same-namespace Pods labeled `kaas-continuity-client=true` on 8443. There is no public Route.
- Worker source ConfigMap includes `InitialGroups.java`; the init container uses the Kafka image's Java source launcher/classpath and receives four fresh group IDs as arguments. The guard reads `/credentials/password` and `/credentials/ca.crt`, uses `kaas-smoke-client` and `kaas-dev-kafka-bootstrap.kaas-kafka.svc:9093`, with SASL_SSL/SCRAM-SHA-512 and hostname verification. These sandbox endpoint/account selections are explicit in source, not generic parameters. Existing, unauthorized or uninspectable groups fail the guard.
- Observer is a separate, single-run Job with `restartPolicy: Never`, `backoffLimit: 0`, no Kubernetes/Kafka credentials, and label `kaas-continuity-client=true`. Mount `watch.py`, `continuity_reconcile.py`, and the **exact raw registered** `worker-0.json` in `/code`; collector bearer token at `/auth/token`; service CA at `/collector-ca/service-ca.crt`; writable results volume at `/results`. Command: `python3 -u /code/watch.py`. JSON reformatting changes the plan hash.
- Current observer resources: requests 100m CPU/128Mi RAM/512Mi ephemeral storage; limits 1 CPU/1Gi RAM/3Gi ephemeral storage. Results use a 2Gi `emptyDir`. Current worker active deadline is 86,880 seconds; observer deadline is 87,780 seconds. These are outer Job caps, not proof that each synchronous native operation is interruptible.

Secrets and private keys must be supplied through approved Secret storage, never copied into Git. This publication contains no armed plan, Secret resource, SQLite database, full event export, or automatically runnable Job manifest. Existing `scenarios/` and `generated/` review profiles remain disabled. Future runs require fresh identity/groups, reviewed start time and limits, explicit arming, collector registration, and separately authorized execution.

## Evidence API

All endpoints except `/healthz` require the collector bearer token over verified HTTPS. JSON request bodies are limited to 65,536 bytes, sufficient for metadata events; Kafka message values are not uploaded here.

| Endpoint | Contract |
| --- | --- |
| `GET /healthz` | Database/disk status; not a proof of full-run durability |
| `POST /register` | Exact `plan_json` string and its `plan_sha256`; registers an armed eight-client continuity plan |
| `POST /events` | Exact `event_json` string and `event_sha256`; persists before returning event ID/hash and `durable: true` |
| `GET /runs/<run>/readiness?plan_sha256=<hash>` | Registered plan and ready-client barrier |
| `GET /runs/<run>/summary` | Counts, per-client terminal states, stop state and disk usage |
| `GET /runs/<run>/export` | Stable SQLite transaction snapshot of exact event/hash envelopes as NDJSON |
| `GET /runs/<run>/seal` | Completeness assertion only when all eight clients report complete and the run is not stopped |
| `POST /runs/<run>/stop` | Marks the run stopped and rejects subsequent new producer-attempt events |

The database uses WAL and `synchronous=FULL`; transactions commit before ACK. Schema version 2 maintains client/kind counters in the same transaction through an insert trigger, with one-time backfill of existing events. Summary/readiness reads no longer aggregate the full ledger. A `(run,client,kind,n)` index bounds terminal-event lookup. TLS handshakes execute in request threads with a five-second handshake limit, a separate 180-second HTTP idle timeout, and a 64-connection accept queue; a slow peer does not serialize the accept loop. Identical event retries deduplicate; conflicting identities or body hashes fail. A client error marks the run stopped. The worker persists receipt evidence before manual consumer offset commit. The collector's seal is an input to independent reconciliation, not a PASS by itself. The shared bearer authenticates the test clients; this is not adversarial attestation or a production multi-tenant authorization system.

## Monitoring and completion

The observer polls every 30 seconds and logs a progress snapshot roughly every five minutes. It checks plan identity, client presence/progress, terminal errors and disk usage. Its 90-second progress watchdog allows polling margin; the runner and final auditor retain stricter 60-second acceptance limits. The observer fails above 75% disk use; the collector rejects new persistence above 80%.

On a detected failure the observer requests a collector stop and exits nonzero. This blocks new producer attempts that require evidence ACK; it does not delete the worker Job, cancel an in-flight native call, or replace its deadline. Collector observation gaps over 90 seconds also fail the observer. It does not send chat/email notifications.

After all clients complete, the observer exports events and a seal, runs the independent SQLite auditor, and writes `/results/{events.ndjson,seal.json,ledger.sqlite,reconciliation.json}`. Auditor success emits `ACCOUNTING_COMPLETE_AWAITING_JOB_AND_CLUSTER_REVIEW`. Final acceptance also needs successful worker/observer terminal states, clean client closure, full timing coverage and review of cluster/restart deltas. The observer has no API permission to do that final cluster review.

Retrieve the final export, seal and report before cleaning up resources. Observer `emptyDir` is temporary; primary evidence remains on the collector PVC. If the observer results are unavailable, re-export from the collector and run the pinned auditor offline using its CLI help. Retain the exact registered plan. Do not delete the PVC or change the current run to reproduce a result.

## Validation and limits

Previously executed checks include local SQLite commit-before-ACK, duplicate/conflict/hash rejection, authentication, scoped readiness, stop handling and incomplete-seal rejection. The live HTTPS probe verified trust/hostname and deduplication; its acknowledged metadata survived a collector-only Pod replacement. No Kafka broker restart was part of that probe. The current workload and observer were observed Running; this does not establish 24-hour success, terabyte throughput, or production durability.

Publication validation checks source syntax, exact deployed-snapshot hashes, exact upstream auditor identity, disabled candidate flags, documentation links and credential exclusion. It does not execute any Kafka load or modify cluster resources. Full raw evidence remains in the coordinator workspace; the repository includes a credential-free execution receipt and historical checkpoint only.

## November 25 correction

The initial 24h run stopped early. Summary scans and serialized TLS handshakes were corrected before a new run. See [fix validation](../../../docs/collector-fix-validation-2026-11-25.md) for measured query scaling, live concurrency checks and stage outcomes. Six offline regression checks run with `python3 -m unittest discover -s tests/continuity/collector -p test_server.py -v` from the repository root. Existing disabled scenario templates and frozen xk6 runtime are unchanged.
