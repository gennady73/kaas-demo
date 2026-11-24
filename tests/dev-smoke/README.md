# DEV-SMOKE-01

Latest result, 2026-11-24: **custom xk6 PASS**, 16/16 exact boundary records including 2 MiB on four topics, 268 seconds. [Build audit/result](../../docs/xk6-build-and-smoke-2026-11-24.md). `smoke.js` is now verified with the corrected sandbox image; the original Docker Hub image remains unqualified. See `custom-extension/README.md` for source/config mapping. Historical November 23 notes below apply to that old image.

`profile.json` is a snapshot of the coordinator's proposed design contract, with user-confirmed bounds. It is not a Kubernetes manifest or direct xk6/C2 scenario input. Source versions and hashes are recorded in `../../docs/baseline-provenance.json`.

Four topics, values up to 2 MiB, at most 300 seconds for the entire client test. Proposed workload: 1 KiB, 64 KiB, 1 MiB and 2 MiB on each topic, 16 original records overall. Reconcile IDs/checksums per group, account for retries separately, and report missing evidence as INCONCLUSIVE.

The generator source remains in `https://github.com/gennady73/kafka-load-test`; additive local C2 work is not yet published there. Do not assume upstream already implements the selected boundary cases or total deadline. Map the runner, selected image/extension, effective limits/security, hard deadline and durable evidence before execution. No five-minute result establishes daily throughput, retention expiry or restart recovery.

## Offline exact boundary cases

`prepare_cases.py` prepares expected IDs, groups, exact lengths and checksums without connecting to Kafka. Example from the repository root:

```sh
python3 tests/dev-smoke/prepare_cases.py --profile tests/dev-smoke/profile.json --run-id dev-smoke-offline-20261119 --seed 20261119 --output /tmp/kaas-smoke-cases.json
```

The checked-in `expected-cases.example.json` contains all four lengths on each of four topics, 16 records / 12,849,152 original value bytes. Payload algorithm `sha256-hex-ascii-v1` is defined by the generator; a runtime adapter must implement that exact algorithm or stream its chunks. This chooses deterministic seeded ASCII for this small boundary check, not production payload representativeness. The example is labelled `execution_ready=false`; it contains no actual acknowledgements or receipts.

Executed offline checks: repeatability, independent byte-length/checksum recheck of every value, four fresh groups, unique IDs, all boundary lengths on every topic, and rejection of invalid run IDs/seeds. The xk6 mapping, actual extension, whole-test deadline, client retry semantics, security and durable runtime evidence remain unresolved. This helper leaves the C2 generator implementation unchanged.

## Observed execution, 2026-11-23

[Functional smoke result](../../docs/smoke-test-result-2026-11-23.md): PASS with `Smoke.java`, the native Kafka Java client in the deployed pinned image. `reconcile.py` independently checked all 16 ID/size/checksum/partition/offset matches and bounded normal termination. `smoke.js` is the failed xk6 adapter retained for diagnosis; do not use it with the selected image and live credentials until sensitive debug printing and message-size mapping are fixed. The original JSON profile remains a proposed input contract, with exact executed manifests/evidence in the coordinator workspace.

The Java source reads `/script/cases.tsv` (topic, sequence, ID, group, byte length, SHA-256 as tab-separated fields), `/credentials/password` and `/credentials/ca.crt`; arguments are a unique run ID and positive seed. Its submitted ConfigMap, logging configuration and Job manifest are retained as `docs/testing/runs/smoke-20261123/configmap-b.json` and `job-b.json` in the parent coordinator workspace. Those are evidence of this run, not credentials or reusable run IDs. Reproduction needs new identities and authorized Secret delivery; do not resubmit the historical Job verbatim.

Reconciliation invocation from the parent coordinator workspace:

```sh
python3 kaas-demo/tests/dev-smoke/reconcile.py --expected docs/testing/runs/smoke-20261123/expected-b.json --log docs/testing/runs/smoke-20261123/kaas-smoke-20261123-b.log --observation docs/testing/runs/smoke-20261123/kaas-smoke-20261123-b-observation.json --output /tmp/kaas-smoke-reconciliation.json
```

This closes basic delivery only. It does not qualify the xk6 generator, sustained throughput or restart recovery.

The independent checker accepts `--client xk6` for the new raw-format log. It verifies exact IDs, groups, bytes, hashes, distinct consumer locations, native size/acks output and normal bounded termination; it does not invent producer offsets/commit confirmations absent from the wrapper. Exact execution inputs/evidence are in the coordinator workspace `docs/testing/runs/xk6-20261124/`.
