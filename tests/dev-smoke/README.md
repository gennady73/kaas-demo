# DEV-SMOKE-01

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
