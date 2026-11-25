# Offline candidate inputs

`dedicated/profile.json` and `shared/profile.json` are scaffold contracts, not runner configurations or deployable manifests. Both have `deployment_enabled=false`, `synthetic_fixture=false` and explicit null inputs. They have no Kustomization and no Application points here. Existing `environments/dev/` is unchanged.

Use `profile_tool.py inspect` to enumerate unresolved inputs. Rendering requires R0/R1 resource and policy fields; later client delivery and R3 qualification references may remain explicitly unresolved. Filling fields does not grant execution authorization or establish readiness. The readiness command reports stage-specific missing inputs and unverified external gates. The current scaffold supports an internal TLS/SCRAM proposal and Kafka 4.2.0 / operator 3.2.1-10 schema baseline; it is not a selectable production security/compatibility matrix. External listeners, SSO and bootstrap integration remain separate work.

The dedicated candidate has one unresolved tenant. The shared candidate has two unresolved tenants for offline isolation checks. Both preserve RF2 and 6h in templates. Source/mirror revisions, physical storage/failure domains, budgets, minimum ISR, names, roles, credentials delivery and all policy references remain explicit unresolved inputs.

See the [guide](../../docs/tenant-profile-scaffolds.md) for local commands and validation scope.
