> Portable publication copy. Source revisions and coordinator-only references are listed in the C7 publication provenance; historical results remain scoped to their original review dates.

# C7 evidence templates

Revision 0.1, 2026-11-25. Blank documentation records, not runner inputs, approvals or observed results. Reuse the existing [input checklist](../input-checklist.md), runbooks, C3 auditor/results and C4 readiness contract; these forms capture references and review rather than replace those systems.

| Template | Fill from / owner | Completion boundary |
| --- | --- | --- |
| [Deployment support](deployment-support.json) | C4 I1–I5 package, C1 budget, C6 authority and named support contacts | Stage-specific R1 support; R2/R3 gaps do not silently become R1 blockers |
| [Incident](incident.json) | Run-owner exports, C1/C4 observations, C2 diagnosis and C3 accounting | Preserve separate service/harness/unsent/ambiguous/missing/incomplete/expiry classifications and negative outcomes |
| [Recovery result](recovery-result.json) | Approved C4 actions, C1 inherited evidence, C2 client contract, C3 reconciliation | One record per environment/mode/RST category/controlled-or-abrupt variant; no-loss and <=10,800s remain required |
| [Evidence custody](evidence-custody.json) | Original export/hash manifest, storage/custodian and data-owner policy | Raw and derived artifacts, complete/incomplete evidence and failed outcomes remain identifiable; no automatic cleanup |
| [Monitoring evidence](monitoring-evidence.json) | Existing stack configuration and actual query/rule/receiver/execution records | Distinguish configured rule, observed signal and verified notification delivery |

## Filling and review

1. Copy the needed template into a separately named C7 record under `docs/operations/records/<record-id>/` when evidence is available. No record directory or apparently completed result is created by this slice. Keep raw run exports in their established evidence store; do not move them or place private evidence in the public demo repository.
2. Keep record IDs/environment/mode/version/config/source and original run identities explicit. `execution_enabled: false` is fixed metadata for these documentation records; changing it does not authorize or implement a run. `record_status` starts TEMPLATE, can become DRAFT and then REVIEWED after a real reviewer/date is recorded. REVIEWED does not imply a passing conclusion or permission to deploy.
3. Null means unresolved/unobserved. Empty arrays mean unfilled template collections, not proof of no gaps. Add OPEN items with owner, phase needed, acceptance criterion and next artifact. Do not substitute zero, false, dummy names or presumed approvals. A boolean observation such as `complete` or `raw_negative_outcomes_preserved` must stay null until established.
4. Expand placeholder evidence/coverage/artifact entries to one entry per real item, removing only unused placeholders. Use `evidence_type` values INSPECTED, INHERITED, EXECUTED, DERIVED or PROPOSED. Keep review status OPEN, SUPPLIED, REVIEWED or REJECTED separate from conclusion OPEN, PASS, FAIL, INCONCLUSIVE or NOT_APPLICABLE. State the reason/scope/reviewer for NOT_APPLICABLE; it cannot waive the no-loss requirement or a required RST category.
5. References identify an accessible local path or approved evidence-store URL and immutable version/hash where available. Template `procedure_reference` values are relative to the shared workspace root. References are not fetched or checked for authorization automatically. Never paste Secret/token/private-key values, credential-bearing URLs or unfiltered debug output. Refer to the approved credential-delivery record instead.
6. Use UTC ISO 8601 timestamps and record clock uncertainty. Counts and byte lengths are nonnegative integers only when measured; hashes are SHA-256 of exact original bytes. State whether bytes are original values, serialized/wire, replica storage or evidence. Store set/offset references, not millions of IDs in the form. Preserve original bytes before normalization/redaction; record permitted sanitization/custody separately.
7. In recovery records, keep actual native acks/ISR/offset/reset/retry behavior and pre-outage lag/expiry/catch-up evidence in referenced config/reconciliation records. Total recovery is t0→t1 under the C0/C3-approved definition; attach intermediate times and required stable window. Rolling recovery includes each step and aggregate time. No claimed PASS from a seal, matching partial counts, inherited persistence alone or a successful Git sync.
8. C3 reviews actual result conclusions; C0 consolidates acceptance/release decisions. Named owners and review/authorization records remain mandatory for the relevant later stage. Offline form completion cannot create R1/R2/R3 execution readiness.

## Inputs still external

For optional local shape/consistency checks before review, use the [offline record checker](../offline-record-checks.md). Its exit status is not acceptance; unresolved fields remain OPEN and evidence references are not opened.

DEP-PERSIST-01 source/owner/scope evidence, real support names, evidence destination/retention, effective alert and permission coverage, selected target budgets and agreed recovery endpoints remain OPEN. Supply existing artifacts on demand rather than duplicate platform testing. Do not acquire evidence by querying, stopping, restarting or changing the active continuity run under this request.
