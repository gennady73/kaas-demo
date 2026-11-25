# Prepared tenant resource source — not registered or deployed

These two source components contain exactly four new KafkaTopic and four KafkaUser resources for existing kaas-kafka/kaas-dev. They were generated from the disabled [tenant-only contract](../candidates/sandbox-tenants/inputs.json) and validated with the [tenant-only workflow](../../docs/tenant-only-gitops.md).

- `a/`: kaas-sbx-a-events, kaas-sbx-a-audit, kaas-sbx-a-producer, kaas-sbx-a-consumer.
- `b/`: equivalent resources for kaas-sbx-b.

Each component is a Kustomization containing only its four Topic/User resources. Neither source component is included in an existing dev Application/Kustomization; no Application or AppProject is present in this directory. Registration/deployment/tests remain disabled in the input contract. Merely publishing these files does not deploy them. False planning flags are not an admission barrier to a person manually applying YAML.

No Kafka/NodePool/operator/watch scope, RBAC, namespace/network, Secret, PVC, test Job or client Pod is generated. Four topics have one partition, RF2, minISR2 and six-hour retention; identity permissions are literal and tenant-scoped with explicit per-principal/per-broker quotas. They do not establish tenant runtime isolation or capacity qualification.

`manifest-lock.json` records exact resource-file/input hashes for review. Obtain the actual resource commit SHA from the prepared Git commit and verify the published Git blobs/paths before pinning any later registration preview. Keep registration objects separate from this resource commit to avoid a self-reference. The input's resource_revision remains null until publication is verified.

Current live sandbox readiness and permissions must be assessed separately. No readiness result is implied by schema/Kustomize validation or a source commit. Owner-approved concrete registration/sync is outside this preparation. Do not run clients. Keep existing smoke/platform ownership and avoid destructive prune/deletion. The shared sandbox owner and approver is the user; no tenant sync delegation or additional SSO role is introduced.
