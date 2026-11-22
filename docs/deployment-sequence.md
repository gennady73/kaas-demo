# Sandbox deployment sequence

Prepared 2026-11-19. Continue using the available default ArgoCD instance in `openshift-gitops`. Preserve the pending GitOps 1.22.3 InstallPlan as unapproved; intended production GitOps version remains unknown.

1. Render `environments/dev/operator` with Kustomize. Publish a reviewed Git revision and render the Application template with its full commit SHA.
2. Bootstrap only namespaces `kafka-operator` and `kaas-kafka`, the restricted AppProject, and the manually synchronized operator Application. No extra ArgoCD instance is needed.
3. Confirm ArgoCD fetch/render of the pinned revision. Synchronize only OperatorGroup and Subscription through the operator Application.
4. Inspect the newly generated InstallPlan. Approve only a plan matching the selected `amqstreams.v3.2.1-10`; leave upgrade plans pending. If resolver chooses a different initial version, stop and inspect, rather than approving it.
5. Verify the selected operator, namespace watch scope, image mapping and installed Kafka CRD schemas. Only then finalize Kafka broker/controller topology, resources/storage and listener/security manifests. These budgeted choices remain explicit before provisioning PVCs.
6. Add a separately scoped Kafka Application, four GitOps topics and the bounded test runner. Tests run only by an explicit launch, not automatically on routine sync.

The first stage contains no Kafka brokers/PVCs and starts no traffic. Kafka resources will live in `kaas-kafka`, while producer/consumer Jobs remain in `kaas-demo`. Stage results and exact revisions must be recorded in the shared coordinator workspace; preparation is not a successful deployment claim.

The project allows only this source repository and the two intended destination namespaces; cluster resources are denied and namespaced kinds allow only OperatorGroup and Subscription. Bootstrap remains an administrator action outside application reconciliation. It does not grant cluster-admin or change the existing ArgoCD login/sync roles. Future Kafka kinds require a separate reviewed allowlist update.
