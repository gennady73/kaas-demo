# ArgoCD instance bootstrap

User-provided bootstrap resource, recorded 2026-11-19: create an `ArgoCD` named `kaas-demo`. The later namespace clarification reserves Kubernetes namespace `kaas-demo` for Kafka test workloads; ArgoCD instance placement remains unselected and must not be inferred from the resource name or operator namespace. `argocd.yaml.template` preserves that minimal intent with an explicit namespace parameter and empty spec. It grants no additional permissions and configures no repository or Application.

The earlier TLS-verified inventory found no `argoproj.io` API group or GitOps CSV. The user subsequently reported installing `openshift-gitops-operator.v1.20.0`, intentionally selecting operator 1.20.0. That report supersedes the earlier absence as the current reported state. Installed readiness, CRD schema, actual instances and instance namespace have not yet been re-inspected. No instance was applied by this chat. GitOps operator installation defaults to `openshift-gitops-operator`; do not infer the instance namespace or apply this template literally.

After the operator is available, inspect its supported instance namespaces and CRD, substitute the verified namespace, and perform server-side dry-run validation before creating the instance. Inspect operator defaults, effective resource usage, authentication and status. This minimal template does not assert restricted sync RBAC, SSO, route availability or a production configuration. Keep the bootstrap separate from the application it will later manage.

Use the selected GitOps **1.20** release documentation and live CRD when validating this template. Earlier 1.21 guidance was reference material, not the selected installation. Production version is still unknown; no upgrade or production parity is asserted. Operator version 1.20.0 does not identify the bundled ArgoCD application version.

Once the instance is healthy, separately configure authorized-personnel manual sync and a restricted AppProject/Application for `https://github.com/gennady73/kaas-demo.git`. The local repository still needs a reviewed published revision and deployable environment manifests. Creating the ArgoCD CR does not accomplish those steps or run the five-minute Kafka test.

## Subsequent live discovery, 2026-11-19

Operator is now observed as **1.22.0**, with default ArgoCD instance **openshift-gitops** in namespace **openshift-gitops**, reporting Available. This differs from intended operator 1.20.0 and remains unresolved; do not apply a 1.20 template against the newer schema by assumption or create an extra instance merely because the earlier inventory showed none. Events also warn that v1alpha1 is deprecated in this observed installation. The template remains an unapplied historical proposal pending version/instance choice and live schema validation. No version rollback or CR change was performed.
