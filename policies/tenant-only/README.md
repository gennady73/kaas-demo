# Offline tenant-only workflow

This distinct path prepares exactly four KafkaTopic and four KafkaUser resources for existing kaas-kafka/kaas-dev; it does not adapt or bypass the new-cluster profile guard. See the [workflow guide](../../docs/tenant-only-gitops.md) and [disabled input](../../environments/candidates/sandbox-tenants/inputs.json).

- `inputs.schema.json`: strict sandbox contract; no arbitrary resource, ACL or delegate injection; execution flags false.
- `tenant_only.py`: local inspect/build/validate, exact tenant identity/content checks, cached Kafka schema checks, registration previews, fresh-directory/file-tampering controls; no live actions.
- `test_tenant_only.py`:23positive/negative scope, permission and file/CLI regressions.
- `validate_offline.py`: local tests plus the available existing C4 suite (35published,55with the separate local readiness extension), two Kustomize renders and unchanged new-cluster guard check; fresh external evidence output required.

The selected user is the accountable sandbox owner, not an invented SSO/Kubernetes account or group mapping. Installed ArgoCD schemas, effective permissions and live state remain external gates. Publication, registration, sync and traffic are not performed by this toolset.
