# Dedicated and shared tenant GitOps scaffolds

Revision 0.2, 2026-11-25. Status: implemented additive scaffolds, offline validation only; no deployment approval or production qualification. Existing dev manifests and continuity artifacts are preserved byte-for-byte.

The dedicated composition models one tenant's Kafka deployment. The shared composition models two tenants in one Kafka deployment for isolation-fixture coverage. Both separate platform Kafka/NodePool resources from tenant Topic/User resources and generate distinct proposed ArgoCD projects and manually synchronized Applications. Existing dev remains a separate composition and retains all resource ownership.

## Inputs and output

Candidate contracts live under `environments/candidates/{dedicated,shared}/profile.json`. Required tenant, environment, storage, topology, budget, actor and policy inputs remain null. `inspect` lists every unresolved path; `render` rejects missing R0/R1 resource inputs before creating output. R2 delivery references and R3 recovery/observability/governance references may remain null; reports preserve them explicitly. Empty strings, TODO/TBD/OPEN/UNRESOLVED and interpolation tokens also count as unresolved. Unrecognized fields and attempts to set deployment_enabled=true are rejected. Filling a contract permits offline rendering only: every report still states execution_ready=false and deployment_enabled=false.

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

Before any R1 execution, resolve actual tenants/owners, target cluster/app namespaces, budgets, selected storage/failure domains, topology, operator watch/bootstrap support, initial internal security/admission/lifecycle policy and Git/ArgoCD authority. R2 delivery and R3 qualification references can remain OPEN while platform preparation proceeds; an initial use case may require a specific integration earlier. Policy references are traceability inputs, not proof that services or controls have passed acceptance.

The v0.2 `gitops/profiles/bootstrap-inputs.json` reuses recorded ArgoCD/operator identity and existing-watch baseline with `bootstrap-reference-evidence.json` provenance; new target scope, mechanism, authority and delivery decisions remain unresolved. The bootstrap checker can validate exact local candidate Namespace/Role/RoleBinding proposals. No OperatorGroup/Subscription or Secret delivery is generated and nothing is applied. The existing operator watches kaas-kafka only; candidate namespaces are not thereby managed. Do not broaden that watch scope or install another reconciler by assumption. No global ArgoCD role binding/SSO mapping, Git branch protection, CI/admission enforcement, baseline-to-candidate change policy or delete workflow has been installed. Project kind restrictions cannot by themselves constrain topic names, ACL contents, Git source paths or a privileged actor. Manual sync permissions also need deletion/prune governance.

Keep the current dev manifests and run owner’s worker/collector/observer unchanged. Candidate validation neither checks the live continuity run nor authorizes interference with it. Later promotion must preserve its evidence, obtain an appropriate authorized change window, recheck live health/configuration and run configuration-specific functional/isolation/capacity/recovery checks.


## Stage-specific readiness and bootstrap checks

Profile inputs retain contract 0.1. Reports and the new bootstrap contract use revision 0.2. Existing candidate profiles remain byte-identical and disabled. The ArgoCD namespace guard now permits AppProject/Application metadata in the evidenced openshift-gitops control plane; Kafka, tenant app namespaces and bootstrap Namespace proposals remain forbidden there. Known existing kaas-demo/kaas-demo-kafka/kaas-demo-operator project/Application names are also protected in that control namespace. Other live name collisions still need fresh pre-change discovery. No new ArgoCD instance is needed to pass a scaffold guard.

| Stage | Local input scope | External boundary still open |
| --- | --- | --- |
| R0 registration | Names/owners, cluster destination, Git source/revision, project sync identities and Git authority reference | Actual source paths, installed ArgoCD schemas/roles and permission to register; no sync implied |
| R1 controlled deployment | R0 plus resources/storage/topology, initial access/admission/lifecycle and bootstrap plan | Fresh health/budget, actual namespace/watch/controller permissions, exact-version/server checks, reviewed diff and explicit change authorization |
| R2 client activation | R1 plus client credential/CA delivery references and bootstrap delivery evidence | Actual delivery/trust, client mappings and positive/negative access/accounting evidence |
| R3 service qualification | R2 plus recovery/persistence, observability and governance references | Real configuration-specific service, capacity and no-loss/recovery acceptance |

`local_status` is BLOCKED, OFFLINE_INPUTS_COMPLETE or SYNTHETIC_ONLY. All reports and stages keep execution_ready=false; deployment_enabled=false is unchanged and enforced in both input schemas. A filled reference string is not evidence validation or an approval. The R0 report can progress while R1 resource inputs remain open, but rendering the whole bundle still needs R1 profile fields. Rendering does not require a completed bootstrap plan and cannot imply bootstrap readiness: that independent plan is assessed by readiness/validation, with external gates kept visible.

```bash
python policies/tenants/profile_tool.py readiness --profile environments/candidates/shared/profile.json --bootstrap gitops/profiles/bootstrap-inputs.json
python policies/tenants/bootstrap_tool.py --input gitops/profiles/bootstrap-inputs.json --profile environments/candidates/shared/profile.json
```

The readiness command returns an assessment even when blocked (exit 0 means the assessment ran). The bootstrap checker returns exit 2 for incomplete/invalid R1 plan inputs, and exit 0 only for a locally complete plan; neither means permission to execute. Its optional `--resources /path/to/proposal.yaml` reads local YAML and requires the exact expected namespaces, candidate-only Role and controller RoleBinding. No URLs are fetched, evidence strings dereferenced or credentials read.

Watch-scope checks preserve the declared existing target namespaces, require candidate coverage and flag extra targets for coordinated multi-profile review. They do not prove the declared baseline is current or that a selected mechanism is supported. OperatorGroup/Subscription mutations are deliberately excluded from the supplied resource proposal vocabulary. Effective global roles and namespace/controller permissions must be verified later; one shared controller identity retains combined rights.

The offline harness includes synthetic bootstrap proposals and readiness reports for both fixtures and blocked real candidates. It verifies that later null references do not change generated Kafka/GitOps resources, while stage reports still block later use. No promotion/materialization into active repository paths, arming switch, live authorization probe, Secret delivery or installed enforcement was added.
