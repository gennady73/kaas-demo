Current service-contract overlay, 2026-11-26: [R3-01 review](../qualification/r3/r3-01/README.md) records completed R1/R2 separately from the historical preparation instructions below, owner-only authority/enforcement limits, and the [native Job/separate-CA mount reconciliation](../qualification/r3/r3-01/mount-contract-reconciliation.md). No new operation is authorized by these documents.

# Tenant-only GitOps preparation for the existing sandbox Kafka

Status: **offline validated; registration, deployment and tests disabled**. The user accepted shared-first on existing kaas-kafka/kaas-dev and remains sandbox owner/approver. This accepts the boundary and authority, not a deployment operation. This dedicated workflow does not weaken the new-cluster renderer's existing namespace/name protections.

The contract is `environments/candidates/sandbox-tenants/inputs.json` (tenant-only-1.0); it deliberately differs from the new-cluster profile0.1. The fixed sandbox scope has two synthetic tenants, kaas-sbx-a/b; topics `<tenant>-events` and `<tenant>-audit`; one producer and one consumer per tenant. Four topics have1partition/RF2/minISR2/6h and3MiB batch ceilings. TLS/SCRAM and literal own-topic/group ACLs apply; producer has IdempotentWrite; no tenant admin rights. Each principal has65536byte/s producer/consumer quotas and requestPercentage5. Quotas are per broker, not a tenant-global budget.

No Kafka/NodePool, broker/controller/PVC, operator/watch-scope, Role/RoleBinding, Secret, client workload or networking change is generated. Existing platform/smoke objects retain their current owner. App namespaces, effective network access and credential distribution are R2 work; neither namespace creation nor client activation is performed here.

## Local commands

From the repository root, using installed Python, PyYAML, jsonschema and client-only kubectl/Kustomize:

```sh
python3 policies/tenant-only/tenant_only.py inspect
python3 policies/tenant-only/tenant_only.py build --output /tmp/kaas-sandbox-tenant-review
python3 policies/tenant-only/tenant_only.py validate --output /tmp/kaas-sandbox-tenant-review
python3 policies/tenant-only/validate_offline.py --output /tmp/kaas-sandbox-tenant-evidence
```

Use a **fresh** output directory outside this repository each time; existing destinations and output symlinks are rejected. No packages are downloaded and no API/Git/auth/apply/sync operation exists in these tools. `inspect`/`validate` exit0 means local validation, not execution permission. Malformed or broadened input, changed/extra files, hooks, unexpected source paths, changed ACLs/quotas, altered namespaces and automated sync/finalizers fail.

The builder writes:

- `environments/sandbox-tenants/a/` and `.../b/`: each a Kustomization with two KafkaTopic and two KafkaUser resources, all in kaas-kafka and labeled for kaas-dev/their tenant.
- `registration-preview/a.yaml.template` and `b.yaml.template`: one exact AppProject/Application pair per tenant. Projects permit only KafkaTopic/KafkaUser into kaas-kafka from the selected repository. No roles/group grants, automated sync, resource-deletion finalizers, namespace creation or test hooks are generated. FailOnSharedResource=true is included.
- `review-report.json`: disabled flags, counts and unverified external gates. Without a reviewed resource SHA, templates retain `${RESOURCE_REVISION}`. A supplied40hex revision is only syntactically checked; it is not proof the resources exist at that commit. All registration documents remain previews, and no registration command is provided.

Resource content is validated against an exact local sandbox allowlist and cached November23 Kafka v1 schemas. Whole-document order may change under Kustomize; identities and nested contents must still match exactly within each tenant component. Duplicate or moved resources are rejected. Registration content is checked exactly, **not** against installed ArgoCD admission/schema. Actual Git protections/admission checks are not installed by this workflow.

The false flags/template suffixes are not Kubernetes admission barriers. A person can manually apply a resource YAML. Keep bundles outside active GitOps paths and do not register or sync these previews under the current authorization.

## Later publication and deployment sequence — not executed

1. Inspect current Kafka/operator/schema/watch state, metadata/storage headroom and all candidate CR/backend topic/user identities. Static saved-smoke protection is not fresh name/ownership evidence. Verify no competing reconciler or existing resource with a candidate name.
2. Verify existing Application tracking/prune boundaries, source ownership and exact controller/global/human permissions. The existing controller has broader platform rights; separate Projects do not create separate Kubernetes identities or validate tenant content. No role/group membership or Secret permission is invented here. Confirm the user-controlled Git workflow and existing authorized login mapping.
3. Review the exact resource/rollback diff. If publication is requested, copy **only** the two resource components to the matching repository paths, leaving registration separate; publish those manifests and obtain the real resource commit SHA. Do not use the old scaffold/code commit as if it contained the tenant resources.
4. Set the actual40hex resource revision in the disabled input and rebuild a fresh preview. Verify the committed paths/blobs against the validated resources; validate installed ArgoCD/Kafka APIs and current intended destination. Source-resource commit and later Application pin preparation stay separate to avoid a self-referential SHA.
5. Present the concrete change/window to the sandbox owner. Only a separately authorized controlled operation may register the two Projects/Applications and manually sync the tenant resources. No broker configuration or Kafka/NodePool change is part of that diff. Manual sync/no-finalizer/Project allowlists do not prohibit all manual prune, privileged writes or data deletion; effective authority and workflow still matter.
6. Observe reconciliation and exact topic/user settings without clients. Client namespace/bootstrap/network/Secret/CA and positive/negative access tests belong to a separately prepared R2 package. Dedicated mode and R3 service qualification remain open.

Rollback initially preserves data and credentials. Stop any later candidate clients, retain evidence, review only candidate-specific changes and avoid automatic deletion/prune/ownership/retention edits. Deleting an Application without a resource-deletion finalizer is not equivalent to deleting backend Kafka data; any destructive exception needs explicit owner disposition. No failure/recovery behavior is qualified by this offline workflow.

## Validation coverage

The repeatable harness runs23new tests, the available existing C4 suite (35tests in the published scaffold;55with the separate local readiness extension) and two local Kustomize renders; compares exact compiled resources and verifies the protected new-cluster path still rejects kaas-dev/kaas-kafka. Negative cases include cross-tenant ACLs, wildcard/admin privilege, topic aliases/config changes, missing quotas, hooks/tracking/finalizers, alternate repos/branches/destinations, extra platform resources, duplicate/moved documents, arming flags and file/symlink tampering. No independent reviewer or runtime isolation test is implied.

Primary references checked2026-11-25: [ArgoCD Projects](https://argo-cd.readthedocs.io/en/stable/user-guide/projects/) for kind/source/destination scope, [Sync Options](https://argo-cd.readthedocs.io/en/stable/user-guide/sync-options/) for FailOnSharedResource, and [Declarative Setup](https://argo-cd.readthedocs.io/en/latest/operator-manual/declarative-setup/) for finalizer behavior. These upstream references explain selected fields; exact installed ArgoCD support/effective permissions remain unverified. Red Hat Streams3.2 default Topic/User namespace placement and Kafka4.2 per-broker quota scope are recorded in the coordinator's proposal research; no watch change or cluster-global quota is asserted.

Publication validation: the tenant-only package was also tested in an isolated copy of the published repository, without unrelated local C4 changes. The harness uses the existing public check_profile API to confirm active-cluster exclusion; it does not depend on the unpublished check_placement helper. See [portable validation receipt](tenant-only-validation.json).
