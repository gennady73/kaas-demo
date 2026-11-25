# Disabled tenant-only sandbox contract

`inputs.json` records the accepted shared-first/owner boundary and the fixed proposed tenant resource values. It is **not** a Kubernetes resource, an Application, a live execution approval or a new-cluster profile. All deployment/registration/test/readiness flags stay false; actual future resource revision and change window are null.

Use the [tenant-only workflow guide](../../../docs/tenant-only-gitops.md). Output goes to a fresh directory outside this repository. No active dev Kustomization/Application includes this contract or generated output. The existing new-cluster profile guard is unchanged. A successful offline render does not certify current capacity, collisions, watch/permissions, client isolation or server admission.
