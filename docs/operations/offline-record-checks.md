> Portable publication copy. Source revisions and coordinator-only references are listed in the C7 publication provenance; historical results remain scoped to their original review dates.

# Local evidence-record consistency checks

Revision 0.1, 2026-11-25. Completed offline while C0 reviews the handoff: [record checker and usage](../../operations/README.md), using the existing [five templates](templates/README.md). No template meanings, release-matrix outcomes, acceptance targets or owner decisions changed.

The helper flags structural errors and selected recovery contradictions, including reversed/inconsistent clocks, invalid numeric values, weakened no-loss/3h targets, missing review/core result references and a PASS claim with missing data or excessive duration. It returns unknown inputs as OPEN and preserves the author's separate conclusion. It never opens evidence references or determines whether a referenced assertion is true. Forms remain documentation, not runner configuration or admission enforcement.

Validation: [new local receipt](record-check-validation-2026-11-25.json) records commands/results, synthetic negative cases, template CLI checks, source hashes and protected-file preservation. Prior checklist/package receipts remain historical; no runtime checks or independent reviewer are implied.

No additional owner input is needed to use the helper offline with copied records. Existing [C7-I01–I12](input-checklist.md) remain OPEN until their owners supply/review applicable evidence; no input is considered resolved by passing this checker. C3 retains result acceptance and C0 release/phase decisions.

Next useful work is artifact-driven: C7 can map supplied saved monitoring rules to coverage, review C4's concrete rollback/support package, or calculate supplied capacity/custody budgets. Live alert delivery, effective permissions, persistence applicability and RST execution remain with their owners and future authorization. No live checks are substituted while those inputs are unavailable.

Kustomize stays current; C7-FUT-HELM-01 stays DEFERRED. The active continuity run, worker/collector/observer sources and resources were not queried or changed. No commit/push, deployment, sync, upgrade, load, restart, fault, automation or outbound communication occurred.

## C0-C7-RC-01 correction, 2026-11-25

At the user's request, C0 added explicit checks for both critical recovery counters independently of conclusion and field-name suffixes. Supplied values must be nonnegative JSON integers, with boolean and floating-point values rejected; null remains unresolved. The expanded offline suite passes 35 tests (25 record-checker and 10 budget), and the original API/CLI review probes now reject the invalid inputs. Historical C7 validation receipts describe the earlier source and are preserved; the [C0 correction receipt](evidence/C0-C7-RC-01-fix-2026-11-25.json) records the corrected source/tests and validation. This closes the checker defect within offline scope and grants no execution or service qualification.
