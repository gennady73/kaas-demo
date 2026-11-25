# Tenant platform profile scaffolds

Revision 0.1, 2026-11-25. Offline, additive candidates for dedicated and shared Kafka deployments. These files are outside every current dev Kustomization and Application source. Nothing here changes the deployed dev configuration or the running continuity test.

Start with the [profile guide](../../docs/tenant-profile-scaffolds.md). `common/` holds structural YAML templates; `dedicated/` selects exactly one tenant and `shared/` selects at least two tenants for isolation-fixture coverage. A shared service may ultimately start with one tenant; the two-tenant scaffold rule exists to exercise shared policy checks, not as a production requirement.

The [candidate inputs](../../environments/candidates/README.md) retain nulls for unresolved environment, tenant and policy choices. The renderer refuses incomplete inputs. Complete synthetic fixtures are separate and clearly marked; their resource sizes, topology, names, repository and quotas are not deployment selections.

Templates are interpreted by `policies/tenants/profile_tool.py`; they are not raw Kustomize resources. Generated review bundles contain separate Kustomizations for platform resources, each tenant and GitOps bootstrap objects. No generated root aggregates or applies them.
