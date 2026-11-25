# Disabled ArgoCD tenant registration package

Status: **prepared and validated offline; NOT registered, NOT deployed**. No workloads may run under this preparation. Shared-first existing Kafka and the user as sandbox owner/approver remain the accepted boundary.

| Preview pair | ArgoCD namespace | Source path at pinned commit | Resource destination |
| --- | --- | --- | --- |
| kaas-sbx-tenants-a | openshift-gitops | environments/sandbox-tenants/a | kaas-kafka |
| kaas-sbx-tenants-b | openshift-gitops | environments/sandbox-tenants/b | kaas-kafka |

Repository: https://github.com/gennady73/kaas-demo.git. Both Application targetRevision values are the full verified published resource SHA **3211df93ae40d7d6f47c6334966ae6d1f658fee7**. They do not follow main/HEAD and do not reference this registration package's future commit. The resource commit and registration package are separate to avoid a self-referential revision.

## Files and disabled state

- `inputs.json`: copy of the strict tenant-only-1.0 contract with only resource_revision set to the published SHA. Registration/deployment/tests/execution_ready remain false; change_window null. The default contract elsewhere remains unchanged.
- `a.yaml.template`, `b.yaml.template`: each contains one AppProject and one Application. These are review previews, not registered objects. No root/active Application/Kustomization includes them and no Kustomization or apply/sync/arming script is supplied here.
- `package-lock.json`: hashes of the pinned four resource source files and the input/two preview files, plus exact source Git blobs and disabled flags. It deliberately contains no self-referential registration commit hash.
- `validation-summary.json`: portable source/validation receipt, scope and remaining gates.

No automatic sync/selfHeal/prune, deletion finalizers, hooks, namespace creation, cluster-resource allowlist or delegated roles/groups are added. Projects allow only KafkaTopic/KafkaUser into kaas-kafka from the exact repository; Applications select their exact source path and include FailOnSharedResource=true. The controller's existing Kubernetes rights remain broader than the Project allowlists. Projects do not restrict topic names/ACL content by themselves or establish separate controller identities. Only the validated tenant-only source at the pinned SHA defines that content.

Planning flags and `.template` filenames are not Kubernetes admission controls: manually submitting these documents would create GitOps objects. **Do not register/apply/sync these previews under this preparation.** No resources on the cluster were changed. Resource YAMLs at the source SHA contain no Kafka/NodePool/operator/RBAC/Secret/network/client change.

## Validation and repeatable review

From repository root, input inspection is offline:

```sh
python3 policies/tenant-only/tenant_only.py inspect --input gitops/registration-candidates/sandbox-tenants/inputs.json
```

To rebuild the expected full review bundle, choose a fresh directory outside the repository:

```sh
python3 policies/tenant-only/tenant_only.py build --input gitops/registration-candidates/sandbox-tenants/inputs.json --output /tmp/kaas-pinned-registration-review
python3 policies/tenant-only/tenant_only.py validate --input gitops/registration-candidates/sandbox-tenants/inputs.json --output /tmp/kaas-pinned-registration-review
```

The bundle validator checks that freshly generated bundle, not arbitrary edits to this package. Reviewers must additionally compare parsed preview documents against `registration_documents(inputs)`, verify package-lock hashes and ensure the published source Git objects match their locked hashes. The package validation receipt records those checks for this exact version. An altered document invalidates that receipt even if an unrelated rebuilt bundle passes. YAML comment text differs between package previews and generated previews; parsed objects must match exactly.

Executed: fresh Git fetch and source-revision ancestry check; Git-object extraction and2local Kustomize renders of the actual pinned source; exact8tenant-resource/4registration-object content checks;4registration objects pass structural validation against served ArgoCD CRD snapshots captured in the same sandbox on2026-11-25. Schemas were not re-fetched in this preparation. No server dry-run, CEL/admission or operator reconciliation was performed. Twelve negative probes reject rolling/different revisions, wrong repository/path/destination/project, autosync/prune, namespace creation, finalizers, wildcard/cluster-resource grants and new delegated roles. No live access tests/workloads or independent reviewer is implied.

## Before any later registration or deployment

Publication of this package, actual registration and manual sync are separate later actions. Keep registration/deployment disabled until the owner authorizes a concrete operation/window and reviews the exact diff/non-destructive rollback. Current preparation does not request or grant that authorization.

Reuse the read-only readiness results with their timestamps; refresh health/headroom/name/ownership at execution. Unmanaged backend topic/user names remain unverified without an approved Kafka administration path. Kubernetes API admin authority is verified, but end-to-end ArgoCD SSO session authority is not; verify the chosen operation path instead of assuming the API binding grants an ArgoCD UI role. GitHub main has no active branch protection/review enforcement, and no controls were changed here. The controller can read Secrets and update Kafka under its existing broader roles; no new privilege or Secret read occurred.

Registering a manual-sync Application is not an empty guarantee against a privileged person syncing or pruning. Preserve current platform/smoke ownership. Client namespace/network/Secret/CA delivery and runtime tests stay deferred to R2; full service/durability/capacity qualification remains open. See the [tenant-only workflow guide](../../../docs/tenant-only-gitops.md).
