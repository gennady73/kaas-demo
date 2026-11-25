# Offline profile validation

Run from the repository root with Python, PyYAML, jsonschema and a local `kubectl` providing `kustomize`. No package downloads, API access or credentials are used. The [guide](../../docs/tenant-profile-scaffolds.md) gives complete commands.

- `profile.schema.json`: strict additive input contract with explicit nullable unresolved fields and no arbitrary manifest/ACL injection.
- `profile_tool.py`: local inspection, staged readiness, rendering and exact input-to-manifest policy checks. It writes only to fresh destinations outside the implementation repository. It never applies resources or marks a profile execution-ready.
- `fixtures/`: synthetic dedicated and two-tenant shared inputs, reserved git.invalid repository and example names/budgets. These are validation fixtures, not environment selections.
- `schemas/`: exact Kafka v1 OpenAPI schema extractions from November 23 installed CRD evidence, with extraction/source SHA-256 provenance. No sensitive runtime or Secret data is included. Generic jsonschema checks do not execute Kubernetes admission, CEL or operator reconciliation.
- `readiness.py`: R0 registration, R1 controlled deployment, R2 client activation and R3 qualification input assessment. Local completeness never means execution approval.
- `bootstrap.schema.json` / `bootstrap_tool.py`: strict v0.2 plan checks, namespace/watch-scope/controller mapping and exact non-delete Namespace/Role/RoleBinding proposal validation. No operator or RBAC changes are applied.
- `test_readiness.py`: stage separation, control-plane namespace and bootstrap privilege regressions.
- `test_profiles.py`: positive schema/identity checks and negative ownership, privilege, configuration, unresolved-input and file-safety cases.
- `validate_offline.py`: runs the suite, renders fixture Kustomizations with local `kubectl kustomize`, validates those outputs, checks source/schema hashes, and saves a fresh evidence package. Optional preserved-baseline input checks existing files by hash.

The validator compares generated resources exactly with the approved input and templates; it is not an independent architecture/security reviewer. It does not assess arbitrary externally managed manifests or authorize changes relative to an existing live tenant revision. Topic/partition/retention changes and deletion need the later lifecycle/change policy, not just a successful render. Tools are available locally but no Git CI, admission policy or ArgoCD enforcement was installed.
