# Supplemental bounded R2 integration package — disabled

Prepared offline against resource3211df9 and C2 contractc2-tenant-r2-0.2. This package joins the existing four-credential preparation with a **non-applied suspended Job preview**, an isolated SQLite evidence-protocol reference, and offline validation/replay tools. It is not a deployable native runner. C2's additive native implementation is being prepared separately under `tests/tenant-r2-native`; its changed-source review and final image remain separate.

The fixture is16positive originals of1,000value bytes, four possible negative-write originals and four negative reads: eight negative operations and at most20,000original attempted value bytes. Positive controls reuse those16 originals. Native retries, replication and evidence bytes are separate. All phases together have a300-second budget:45/90/90/45/30seconds. This is a small ACL/delivery fixture, not2MiB, fairness, capacity, full-day or recovery qualification.

`package.json` retains execution/deployment/workload/readiness/autosync flags false. `job.json.disabled` has suspend=true, backoffLimit=0, restartPolicy=Never, parallelism/completions1, activeDeadlineSeconds300 and terminationGracePeriodSeconds0. It is absent from active Kustomize/Argo inputs. Its only entrypoint always throws before credentials, HTTP or Kafka activity, and the historical image pin is explicitly unqualified for the new module. Unsuspending it cannot activate the candidate. Hard termination can leave uncertain delivery or cleanup; the Job deadline is a containment proposal, not a measured exact wall-clock guarantee.

Four read-only credential mounts and public CA references reuse `../tenant-r2-preparation`; no Secret values are shipped. The single trusted harness can access all four credentials and does not qualify malicious-workload isolation. Arbitrary-UID/fsGroup readability, image pull, resource admission and actual TLS/network paths still require later evidence. No credential API permission is added to the harness. Native runtime/sink transport are intentionally absent from this preview; a live package must replace the preview after review, not enable a flag.

`offline_sink.py` implements a separate **internal local-test protocol** `r2-offline-sqlite-1`, not the continuity collector or C2's network service. It accepts disabled offline runs with a single `tenant_fixture` identity, preserves exact hashed envelopes, checks chain/order/plan binding, commits SQLite before returning an acknowledgement, makes exact retries idempotent, rejects conflicts, stops new attempt intents, and freezes exports/seals. It deliberately leaves event semantics and acceptance to the independent C2 auditor; a complete collection is not a successful test. No HTTP listener, authentication, certificate handling or runtime deployment is implemented here.2048events ×32KiB bounds the accepted original envelope content to64MiB; SQLite/WAL/index/export overhead is additional. A1Gi isolated sandbox evidence volume is a proposal only, not an allocated or measured requirement. Local process-restart persistence is not infrastructure durability.

From kaas-demo:

```sh
python tests/tenant-r2-integration/validate.py
python -m unittest discover -s tests/tenant-r2-integration/tests -v
```

The offline replay additionally needs the shared utility checkout and C3/C6 review files. From the shared workspace:

```sh
python kaas-demo/tests/tenant-r2-integration/replay_offline.py \
  --utility kafka-load-test \
  --contract config/preflight-r2/c2-two-tenant-client-contract.json \
  --c3-review docs/testing/c3-r2-implementation-review-2026-11-25.md \
  --c6-review docs/security/r2-adapter-final-review-2026-11-25.md \
  --output /tmp/r2-offline-replay-NEW
```

The output must be a new directory. The replay uses only bundled fakes, commits their182event envelopes to a temporary SQLite store, reopens/retries, seals/exports and invokes the independent auditor. It does not connect to a broker or read credentials. The source bundle and source hashes are not execution authority.

User accepted seven days of sandbox evidence retention and an exported copy in the shared workspace (`docs/testing/runs/<run-id>/`). Export creation/verification and timed cleanup remain future run actions; no recurring automation is created. No additional user input is required for this offline package. The user remains sandbox owner/approver. Technical owners must still complete native/runtime and sink integration, review the exact changed source/build, and collect credential/trust/group/health/admission evidence before a separately authorized live run. No registration, deployment, test workloads, remote publication or change to the continuity collector occurs here.
