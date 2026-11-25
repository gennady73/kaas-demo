# Offline operations support

Revision 0.1, C7, 2026-11-25. Additive helpers outside all active Kustomizations. No cluster client, credentials, network operations, mutation commands or automatic stage promotion. The C7 guides, release matrix and five templates are included under [docs/operations/](../docs/operations/README.md). Their original shared-workspace source revisions are recorded in [publication provenance](../docs/operations/PROVENANCE.md).

From this repository root:

```bash
python3 -B -m unittest discover -s operations -p 'test_*.py' -v
python3 -B operations/budget_check.py operations/fixtures/replay-example.json
```

`budget_check.py` reads one local JSON and prints planning arithmetic. All required keys must exist; null means unknown, never zero. Daily bytes and ingress/consume rates use decimal **original value** accounting, not wire bytes. History is an externally justified effective per-partition history bound, not automatically the configured retention.ms. Catch-up uses constant rate/net drain and must be replaced by measured/windowed envelopes for changing workloads. Unknown inputs stay OPEN. Exact retention equality is unsafe. Invalid numeric values or fields exit 2.

Zero exit means calculation completed, including when the screen says UNSAFE or OPEN; it never means an execution/release gate passed. `release_qualified` is always false. Positive margin alone cannot prove losslessness, storage capacity, a recovery SLA or compatibility. The example's three-hour outage allocation plus catch-up is an illustration, not an accepted RTO decomposition. No TB scenario or load-run config is generated.

## Local documentation consistency checker

`record_check.py` checks a copied C7 record against an explicitly supplied local template directory. From this repository root in the shared workspace:

```bash
python3 -B operations/record_check.py docs/operations/templates/recovery-result.json --templates docs/operations/templates
```

It checks object/array/field shape, documentation-only execution flags, review metadata, UTC timestamps, numeric counts/durations and selected recovery clock/PASS contradictions. It prints unresolved null/OPEN/empty collection paths; it never fills them. `status` is the local consistency assessment, while `reported_conclusion` preserves the record author's separate conclusion, including FAIL. An empty collection needs human interpretation and is conservatively unresolved.

Exit 2 means invalid JSON, unsupported type/revision, missing template or a detected contradiction. Exit 0 means no checked contradiction, and may still report OPEN; it never approves an execution/release or validates a PASS. `release_qualified` and `execution_ready` remain false. It does not establish full evidence completeness or semantic validity, inspect hashes/evidence contents, dereference URLs/paths in records, authenticate, query services or alter records. Nullable free-form fields still require owner review. Supply only trusted versioned template files; validation is bounded by that template and explicit checks, not a full schema or security mechanism.

The record tests use the included templates at `docs/operations/templates/`; no parent workspace is required. They use synthetic in-memory records and temporary files, not real run outputs. No completed operational record or runtime qualification is generated. Kustomize remains current and Helm remains deferred.

Correction C0-C7-RC-01: recovery `missing_required_records` and `integrity_mismatches` are explicitly checked for every conclusion. Supplied values must be nonnegative JSON integers; booleans, floats, strings and containers are invalid. Null remains unresolved. Zero does not grant acceptance, and a positive count is a valid observation in a failure record. Invalid supplied counters produce `INVALID` and CLI exit 2.
