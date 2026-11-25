# C5 Registry deployment candidate — preparation only

User-selected operator/package: **Red Hat build of Apicurio Registry 3, 3.3.4-r1**. Realm: **kaas-c5-poc**. Reuse the existing Keycloak service; create a separate registry PostgreSQL instance and PVC. Do not modify the existing `sso`/`master` realms, OpenShift OAuth, `idp-4-ocp`, Keycloak CR/operator/database, Kafka or existing ArgoCD Applications.

**Nothing here is deployed or registered.** Inputs keep deployment, registration and tests false. There is no root Kustomization, ApplicationSet or existing development overlay reference to this directory. `preview/` and `registration/` contain immutable source pins and are for review only. These conventions are not Kubernetes admission controls: manually applying files bypasses local checks and is not authorized.

## Exact release identity

`redhat-release-lock.json` records `apicurio-registry-3.v3.3.4-r1` and immutable operator/app/UI/bundle references from the Red Hat catalog, independently corroborated by its public Pyxis API. The renderer rejects alternate CSV/app/UI pins. The exact bundle was retrieved using the existing Podman login and verified by digest. Its CSV/default images match the lock, and its downstream CRD spec/strict-field checks pass. The full parsed downstream schema equals the cached upstream3.3.4 schema. The renderer now uses the checksum-pinned downstream copy.

## Published resource and registration boundary

`rendered/{operator,postgres,realm,registry}` contains the reviewed resource stages for immutable Git pinning. No bootstrap or Application is included in these source paths, and no existing composition references them. `resource-source-lock.json` records their content hashes. `inputs.json`, previews and `registration/` pin all four Applications to published resource revision `d8dac192d30a98c1ad7c3a1e9c077b8dea85c248`; existing Applications are unchanged. Publication does not authorize registration, sync or deployment. Remaining readiness evidence must be reviewed before execution.

## Layout and offline use

| Path | Purpose |
| --- | --- |
| `inputs.json` | Selected versions, proposed environment values, explicit missing inputs and promotion evidence |
| `templates/bootstrap/` | New namespace, two isolated AppProjects, four manual Application candidates and registry-namespace controller Role/RoleBinding |
| `templates/operator/` | Own-namespace OperatorGroup and Manual Subscription; catalog-verified starting CSV pinned |
| `templates/postgres/` | Separate PostgreSQL Deployment/Service/PVC, TLS configuration/CA injection and ingress NetworkPolicies |
| `templates/realm/` | One-shot KeycloakRealmImport for only kaas-c5-poc, secret placeholders and bounded resource requests |
| `templates/registry/` | ApicurioRegistry3, API/UI edge Routes and limited ingress |
| `admin-review/` | Optional high-privilege realm-import controller grant, deliberately excluded from all compositions |
| `validation/schemas/` | Exact Red Hat3.3.4-r1 Registry schema plus historical upstream Registry and installed Keycloak served schema plus historical family snapshots; not installation manifests |
| `preview/` | Locally rendered, syntactically reviewable Kustomize stages; **not a deployment candidate** |

From this directory:

```bash
python -m unittest -v test_render
python render.py --mode preview --out /tmp/c5-registry-preview-review
oc kustomize /tmp/c5-registry-preview-review/registry
python render.py --mode candidate --out /tmp/c5-registry-promotion-review
```

The last command **must reject the shipped inputs** before writing output: operational promotion evidence remains incomplete even though source/CSV/image pins are resolved. Commands render/check local files only. PyYAML and jsonschema are required. No renderer command talks to a cluster, obtains credentials, imports a realm or changes authorization flags.

The four resource stages under `governance/c5-registry/rendered/` are published and verified, and the separate registration manifests pin that exact resource revision. The rendered source commit must exist before registering Applications. Bootstrap/Application registration files do not need to be part of the same pinned resource commit. Do not commit a dummy SHA, change existing Application pins, or assume an empty `syncPolicy` starts an operation.

## Security and lifecycle contract

- TLS/SCRAM Kafka and existing OpenShift SSO are untouched. This package contains no Kafka, Keycloak-server or OpenShift OAuth configuration.
- New namespace `kaas-c5-registry`; existing namespace `keycloak` receives only the reviewed realm import if later authorized. Its namespace or labels are never managed by this package.
- Registry API and UI use HTTPS edge Routes with redirect. **Router-to-registry traffic is HTTP** inside the cluster; this is an explicit PoC proposal, not end-to-end TLS qualification. OIDC TLS verification is required and JDBC uses verify-full with the service CA. If C6 requires encrypted router-to-pod transport, revise to reencrypt/passthrough before promotion.
- UI uses authorization-code/PKCE S256; API validates explicit audience `c5-registry-api`. Publisher uses a separate confidential client/service account. Password grants, anonymous reads, broad authenticated read access and self-registration are disabled.
- Owner/group write checks are enabled. A reader role permits schema reads within this isolated experiment. This **does not prove private schema visibility between shared production tenants**; the no-role user is an authorization-denial fixture, not a full tenant isolation model.
- PostgreSQL uses a separate 10Gi gp3-csi PVC and user/database `registry`. Existing Keycloak PostgreSQL data and credentials are never reused. PG server enables TLS; the app requires verified TLS. The supplied PG configuration does not itself reject every possible non-TLS connection; NetworkPolicy limits peers and later negative tests must exercise the intended boundary.
- Service-serving certificate Secret uses mode 0440, root ownership/group access supplied by OpenShift SCC/volume handling; confirm effective group readability and PostgreSQL key checks. No fixed UID, privileged container, root initContainer, anyuid grant or permission-changing hook is supplied.
- The CA-injected ConfigMap is operator-owned data; the PostgreSQL Application ignores `/data` with RespectIgnoreDifferences to avoid wiping injection on subsequent sync.
- No embedded Secret values. Use [the Secret contract](secret-contract.json); do not commit generated credentials, imported Keycloak secrets or TLS private keys.
- PVC and realm-import resources have Prune=false/Delete=false; Applications have no automated sync/finalizers. Removal of the import CR does not delete the realm, and changing the CR after import does not update the realm. Record completion and retire it through a separately reviewed administrative cleanup. Do not keep it as a continuously reconciled realm controller.

## Privilege and deployment boundaries

The namespace Role in bootstrap grants six non-delete verbs on only the listed C5 registry resources; no Secret or wildcard/cluster-admin grant. AppProjects limit destinations/kinds but do not grant RBAC. Administrator bootstrap, OLM InstallPlan approval and Secret delivery are separate actions.

Realm import is more privileged than its single CR kind suggests: the Keycloak operator can expand placeholders from its namespace's Secrets/environment. **Keycloak documentation requires namespace-admin-level trust for RealmImport writers.** Prefer an authorized namespace administrator's reviewed one-shot import. The optional realm Application must not be registered/synced until controller authority is explicitly accepted; the excluded `admin-review/realm-import-rbac.yaml.template` is a concrete alternative for that separate decision. Kubernetes namespace RBAC and AppProject kind filters cannot restrict which realm name the CR body requests. No such grant is applied here.

Before any later application: verify exact target/health/collisions, exact downstream CSV/bundle/images/CRDs and install mode, SCC/probes/TLS/CA/network behavior, resources/admission, credentials and named authority/window. Inspect every InstallPlan: `startingCSV` and a Manual policy do not prove the plan installs only the requested build. Do not approve upgrades or assume disconnected readiness from a catalog label.

## Resource proposal and acceptance

One app, UI, PostgreSQL and operator replica. Proposed steady requests: **950m CPU / 1152Mi RAM**; limits **3 CPU / 2816Mi RAM**, plus **10Gi PVC**, excluding existing Keycloak/platform and temporary import Job. Import Job adds 100m/256Mi requests and 500m/512Mi limits while running. These are proposed allocations, not measured capacity or production HA.

After separately authorized rollout, require Ready operator/registry/database, successful isolated realm import, unchanged baseline OpenShift SSO, valid UI login/logout and account-console SSO, API admin/writer/reader/no-role tests, invalid audience/token rejection, schema compatibility and serialization fixtures, verified JDBC/OIDC trust, restart/restore preserving schema IDs, and no-egress qualification for any air-gapped claim. Readiness alone is not acceptance. Kafka OAuth authorization remains outside this rollout.

The coordinator workspace holds the deployment plan, source/validation evidence and C5 handoff. The package's `sources.json` and `redhat-release-lock.json` record exact catalog CSV/app/UI/bundle identities and supplementary upstream source versions. Exact Registry bundle schema checks pass offline; Keycloak RealmImport uses the installed Red Hat26.4.18 served schema; full parsed schema equals the retained upstream snapshot. Server validation and live execution remain OPEN.

## Read-only readiness result

See `readiness-summary.json`. Read-only checks are complete with execution disabled. Keycloak and GitOps are available, C5 names are absent, served CRD checks and workstation image/DNS/TLS checks pass. The cluster retains a same-schema Apicurio CRD with OLM labels for an absent prior CSV; no matching Subscription/Deployment/CSV or Registry instance was found. Do not delete it or assume adoption: inspect actual initial InstallPlan ownership before any approval. The existing global OperatorGroup is untouched.

New Secrets, actual namespace/image-pull/admission/SCC/PVC behavior, pod network/trust, concrete execution window and runtime acceptance remain open. They cannot be established by these GET-only checks. Existing controller global read/other broad grants remain; the scoped proposed bootstrap Role does not revoke existing rights. The optional realm Application remains gated on the accepted privileged import path. No registration, sync, OLM approval, realm import or SSO change occurred.
