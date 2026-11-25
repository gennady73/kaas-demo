# Dedicated and shared tenant GitOps scaffolds

Revision 0.1, 2026-11-25. Status: implemented additive scaffolds, offline validation only; no deployment approval or production qualification. Existing dev manifests and continuity artifacts are preserved byte-for-byte.

The dedicated composition models one tenant's Kafka deployment. The shared composition models two tenants in one Kafka deployment for isolation-fixture coverage. Both separate platform Kafka/NodePool resources from tenant Topic/User resources and generate distinct proposed ArgoCD projects and manually synchronized Applications. Existing dev remains a separate composition and retains all resource ownership.

## Inputs and output

Candidate contracts live under `environments/candidates/{dedicated,shared}/profile.json`. Required tenant, environment, storage, topology, budget, actor and policy inputs remain null. `inspect` lists every unresolved path; `render` rejects them before creating output. Empty strings, TODO/TBD/OPEN/UNRESOLVED and interpolation tokens also count as unresolved. Unrecognized fields and attempts to set deployment_enabled=true are rejected. Filling a contract permits offline rendering only: every report still states execution_ready=false and deployment_enabled=false.

Independent synthetic fixtures under `policies/tenants/fixtures/` use fixture names, `https://git.invalid/fixture/kaas.git`, a dummy immutable Git SHA and a fixture storage class. Their pinned Kafka image comes from the current local dev source. Their three dual-role nodes, 20Gi claims, 100m/512Mi requests per process, 500m/1Gi limits and user quotas are declared test inputs, not proposed production allocations or available infrastructure. No connection is attempted. Host rack/anti-affinity mappings are illustrative, not physical failure-domain evidence. Pool labels were found in saved November 23 NodePool status; scheduling has not been executed for these profiles.

The scaffold currently models internal TLS/SCRAM, simple authorization, literal topic/group ACLs and idempotent producers. This is a proposed starting shape based on the dev profile, not acceptance of production security. Minimum ISR is an explicit input and is not inferred from `offset 2`. With RF2/minISR2 and acks=all, affected writes are unavailable at one ISR; client ack/offset/replay behavior and the no-loss/3h objectives still need separate evidence. No claim-check, external listener or SSO implementation is selected here.

Generated bundles contain:

- `environments/candidates/<profile-id>/platform/`: Kafka and selected NodePools, retained claims, declared resources and namespace listener peers.
- `environments/candidates/<profile-id>/tenants/<tenant-id>/`: RF2/6h topics and separate producer/consumer users with exact topic/group rights, quota values and owner labels.
- `environments/candidates/<profile-id>/gitops/`: AppProject/Application pair for the platform and for every tenant, with exact source revision/destination, separate kind allowlists and scoped get/sync group roles.
- `review-report.json`: profile hash, component/schema counts, derived resource sums and limitations; always not execution-ready.

Every component has its own resources.yaml and Kustomization. No root Kustomization aggregates the components. The candidate source paths in generated Applications are future package paths, not published Git paths. The GitOps bootstrap objects are a separate administrator review package, not recursively deployed by the platform Application.

## Local commands

Run these from `kaas-demo/`. Python dependencies and kubectl must already be available; these commands do not install anything. Replace `/tmp/c4-review-example` with a fresh directory when rerunning.

```bash
python policies/tenants/profile_tool.py inspect --profile environments/candidates/shared/profile.json
python -m unittest discover -s policies/tenants -p 'test_*.py' -v
python policies/tenants/validate_offline.py --output /tmp/c4-review-example
```

The harness runs only local `kubectl version --client` and `kubectl kustomize` commands. It saves command logs, rendered fixture bundles and validation-result.json. It calls no API, workload, producer/consumer or deployment command. Output must be new and outside the implementation repository so it cannot overwrite current source, tests or active Kustomizations.

To inspect a single fixture locally:

```bash
python policies/tenants/profile_tool.py render --profile policies/tenants/fixtures/dedicated.json --output /tmp/c4-dedicated-example
python policies/tenants/profile_tool.py validate --profile policies/tenants/fixtures/dedicated.json --output /tmp/c4-dedicated-example
```

Do not treat annotations or false report flags as Kubernetes admission barriers: rendered files are ordinary Kubernetes resource descriptions. There is no apply/deploy command or arming mechanism in these tools. Actual promotion needs separately authorized execution, reviewed real inputs and fresh runtime checks.

## Validation coverage

The local suite covers positive dedicated/shared renders and cached Kafka v1 schema checks; complete and deterministic resource sets; literal ACLs for neighboring tenant names; denial of unapproved resources, cross-tenant privileges, automated sync, broad project kinds, mutable revisions, RF/retention/cleanup edits, invalid quota/size/resource values, live identity reuse and unresolved inputs. It rejects extra files/Kustomize rewiring and generated-resource tampering against the supplied contract. Current inputs intentionally have no arbitrary ACL or manifest field.

The validation harness additionally runs Kustomize for each component and compares the rendered objects against the same approved contract and templates. Kafka schemas are extracted from the saved installed 3.2.1-10 operator-era v1 CRDs, captured November 23; provenance is in `policies/tenants/schemas/provenance.json`. jsonschema provides structural/type checks, not Kubernetes CEL/admission/operator behavior. No cached ArgoCD schema was available; AppProject/Application checks are local exact policy/content checks, not schema/server acceptance. A second reasoning or test pass is not an independent reviewer.

RF2/6h settings are fixed in templates. A 3MiB fixture protocol ceiling is not evidence that production WP-A 10M values fit. User bandwidth quotas are per broker and require multi-principal/tenant budget analysis and runtime throttling tests. The included topic/partition admission checks operate on this contract only; they do not inventory existing tenants or compute cluster-wide admission.

## Open integration work

Before any execution, resolve actual tenants/owners, cluster/app namespaces, budgets, VSAN storage interfaces/failure domains, topology and operator namespace/watch-scope support. Supply reviewed security/external access, Secret/CA delivery and rotation, quotas/admission, lifecycle/deletion, recovery/persistence, telemetry, governance and Git/ArgoCD authority references. Policy references are traceability inputs, not proof that those services or controls have passed acceptance.

The separate `gitops/profiles/bootstrap-inputs.json` keeps administrator/watch-scope/permission decisions unresolved. No Namespace, OperatorGroup/Subscription, Kubernetes controller RBAC or Secret delivery is generated. The existing operator watches kaas-kafka only; candidate namespaces are not thereby managed. Do not broaden that watch scope or install another reconciler by assumption. No global ArgoCD role binding/SSO mapping, Git branch protection, CI/admission enforcement, baseline-to-candidate change policy or delete workflow has been installed. Project kind restrictions cannot by themselves constrain topic names, ACL contents, Git source paths or a privileged actor. Manual sync permissions also need deletion/prune governance.

Keep the current dev manifests and run owner’s worker/collector/observer unchanged. Candidate validation neither checks the live continuity run nor authorizes interference with it. Later promotion must preserve its evidence, obtain an appropriate authorized change window, recheck live health/configuration and run configuration-specific functional/isolation/capacity/recovery checks.
