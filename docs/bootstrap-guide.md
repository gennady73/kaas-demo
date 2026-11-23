# Kafka operator bootstrap guide

Revision 1.0, 2026-11-23. This guide documents the operator stage actually executed on 2026-11-22 and provides a controlled reproduction procedure. It does not deploy Kafka brokers or run a test.

## Scope and existing state

| Role | Namespace / resource |
| --- | --- |
| OpenShift GitOps operator | `openshift-gitops-operator` |
| Existing ArgoCD instance | `openshift-gitops/openshift-gitops` |
| Kafka operator | `kafka-operator`, selected CSV `amqstreams.v3.2.1-10` |
| Kafka workload destination | `kaas-kafka`; namespace created, brokers not provisioned in this stage |
| Producer/consumer test workloads | `kaas-demo` |
| Scoped ArgoCD project | `openshift-gitops/kaas-demo` |
| Operator Application | `openshift-gitops/kaas-demo-operator` |

The GitOps operator was initially selected at 1.20.0. The user subsequently approved its upgrade; live discovery on November 23 reports GitOps 1.22.3 installed and the ArgoCD instance Available. Kafka remains at the selected 3.2.1-10 operator version, with Manual approval and a newer version advertised. These are operator versions, not Kafka broker versions.

**For this existing sandbox, start with the verification section.** Do not reinstall an already healthy operator, create another ArgoCD instance or approve the newer Kafka update merely to replay the guide. Read the [stage result](operator-stage-result-2026-11-22.md) for the executed evidence and the [Git workflow](git-workflow.md) for repository boundaries.

## 1. Preconditions

- Running, reachable OpenShift sandbox; an authenticated administrative client session using your approved credential method. Keep token material out of files and command examples committed to Git.
- API hostname and certificate-chain verification enabled. The coordinator obtained the API signer from the user-selected `kaas-demo/kube-root-ca.crt` ConfigMap through the authenticated console. Use a CA already verified for this environment; do not assume a service-serving CA signs the external API, and do not bypass TLS.
- Red Hat OpenShift GitOps operator ready and the existing ArgoCD instance Available. Operator installation namespace and ArgoCD instance namespace are distinct roles.
- Reachable Red Hat operator catalog and required image sources, or their approved disconnected mirrors. Confirm `amq-streams-3.2.x` still offers exact CSV `amqstreams.v3.2.1-10` before a fresh installation. A later channel head is not the selected initial version.
- Reviewed Git source already published and reachable by ArgoCD. Browser/Git authentication and OpenShift authentication are separate.

The commands below assume `oc` is authenticated; verifying a token through the coordinator's in-memory API client does not create a persistent local `oc` kubeconfig session.

```sh
oc whoami
oc get csv -n openshift-gitops-operator
oc get argocd openshift-gitops -n openshift-gitops
oc get applications.argoproj.io -n openshift-gitops
```

An existing resource with unexpected ownership/specification must be inspected before modification. The actual coordinator tool stopped on conflicting bootstrap specifications rather than overwriting them.

## 2. Inspect and render the published operator stage

```sh
cd /home/gunger/Projects/kaas-solution/kaas-demo
git status --short --branch
git fetch origin
git show 7542a93c5aee9aad281c62ba074e1de7db7b7624:platform/operator/subscription.yaml
oc kustomize environments/dev/operator
```

For a fresh reproduction, use a clean checkout of the reviewed revision; do not assume an edited local tree matches its SHA. The original deployed revision above contains:

- Namespace-local `OperatorGroup/kaas-kafka` in `kafka-operator`, targeting only `kaas-kafka`.
- `Subscription/amq-streams` in `kafka-operator`, package `amq-streams`, source `redhat-operators` in `openshift-marketplace`, channel `amq-streams-3.2.x`, `startingCSV: amqstreams.v3.2.1-10`, `installPlanApproval: Manual`.

The desired operator resources are under `platform/operator/`; ArgoCD reads their dev overlay at `environments/dev/operator`. Do not apply those resources directly as a shortcut around GitOps.

## 3. Bootstrap namespaces and the scoped ArgoCD project

Administrative bootstrap is separate from application synchronization. The namespace/project manifests are stored in Git but are not managed by the restricted operator Application itself.

```sh
oc apply --dry-run=server -f gitops/bootstrap/namespaces.yaml
oc apply --dry-run=server -f gitops/bootstrap/project.yaml
```

After reviewing the server response and any existing resource differences:

```sh
oc apply -f gitops/bootstrap/namespaces.yaml
oc apply -f gitops/bootstrap/project.yaml
```

The namespaces are `kafka-operator` and `kaas-kafka`; existing `kaas-demo` remains the test namespace. AppProject `kaas-demo` allows only this repository and the two intended destinations. Its cluster-resource whitelist is empty and its namespaced whitelist contains only OperatorGroup and Subscription. It does not grant cluster-admin or widen existing ArgoCD login/sync roles.

For historical accuracy, the coordinator used strict API create dry-runs followed by create requests, not these `oc apply` commands. The commands above are the documented CLI reproduction path and were not executed while writing this guide.

## 4. Render the exact-revision Application

The template has an unresolved revision intentionally. Render it to a temporary file without changing the checked-in template:

```sh
export KAAS_REVISION=7542a93c5aee9aad281c62ba074e1de7db7b7624
python3 - <<'PY'
import os
from pathlib import Path
revision = os.environ['KAAS_REVISION']
if len(revision) != 40 or any(c not in '0123456789abcdef' for c in revision):
    raise SystemExit('A full reviewed commit SHA is required')
text = Path('gitops/bootstrap/operator-application.yaml.template').read_text()
text = text.replace('${GIT_REVISION}', revision)
if '${' in text:
    raise SystemExit('Unresolved template input')
Path('/tmp/kaas-demo-operator-application.yaml').write_text(text)
PY
oc apply --dry-run=server -f /tmp/kaas-demo-operator-application.yaml
```

Review its repository, source path, SHA, project and destination, then apply the rendered Application through the administrator bootstrap workflow:

```sh
oc apply -f /tmp/kaas-demo-operator-application.yaml
oc get application kaas-demo-operator -n openshift-gitops -o yaml
```

For a future change, replace the SHA only with a published reviewed revision. Confirm repository fetch/render completes without conditions and `status.sync.revision` matches the intended SHA. Missing operator resources before the first sync are expected. A fetch/render error must be resolved before synchronization.

The Application has no automated sync policy, does not prune automatically, and uses `FailOnSharedResource=true`. The separate `argocd.yaml.template` is an earlier proposal for creating an instance; it was **not** used because the default ArgoCD instance was already available.

## 5. Manually synchronize only the operator Application

An authorized ArgoCD user selects `kaas-demo-operator`, reviews the two-resource diff and revision, and performs a manual sync with pruning disabled. If using an authenticated ArgoCD CLI session:

```sh
argocd app diff kaas-demo-operator
argocd app sync kaas-demo-operator --revision "$KAAS_REVISION"
argocd app wait kaas-demo-operator --sync --timeout 180
```

Do not add `--prune`. Stop on unexpected resources, source conditions or permissions failures. The historical coordinator verified the existing controller's permissions using SubjectAccessReview and triggered the manual operation through the Kubernetes Application API. No additional controller role binding was required.

At this point the Subscription may await installation approval; successful sync alone does not prove that its operator is Ready. See [ArgoCD sync options](https://argo-cd.readthedocs.io/en/stable/user-guide/sync-options/) for the shared-resource guard.

## 6. Inspect and approve only the initial Kafka installation

For a **fresh installation**:

```sh
oc get subscription amq-streams -n kafka-operator -o yaml
oc get installplans -n kafka-operator
oc get operatorgroup kaas-kafka -n kafka-operator -o yaml
```

Select the plan referenced by the intended Subscription and inspect it with `oc get installplan <plan-name> -n kafka-operator -o yaml`. Before approval, confirm:

- Approval is Manual and approved is false; the Subscription has no already installed Kafka CSV.
- Its entire CSV list is exactly `amqstreams.v3.2.1-10`, not the newest channel version.
- All resolving steps belong to that CSV. Review the CRDs, operator/RBAC resources and exact bundle/CSV image references.
- OperatorGroup scope resolves to the intended Kafka namespace, and the selected bundle supports that installation mode.

The actual plan used an unpacked bundle ConfigMap reference, not inline CSV YAML. Its binary entries required base64 decoding, then decoding the compressed representation and gzip decompression. The selected CSV and image digest were verified before approval. See the result report and local coordinator evidence for the inspected artifact.

Only after that review, an authorized administrator approves the **chosen initial plan**, for example using the console. Never approve every pending plan or select it solely by age. The coordinator's approval tool required the exact initial CSV, Subscription reference, verified image and resourceVersion before patching approved=true. Do not replay historical plan `install-msmqg`: it is already complete.

`startingCSV` selects the initial version; it is not an ongoing version lock. Manual approval is what keeps later plans pending. [OLM Subscription documentation](https://olm.operatorframework.io/docs/concepts/crds/subscription/) explains this workflow.

## 7. Verify the existing deployment and keep upgrades explicit

```sh
oc get application kaas-demo-operator -n openshift-gitops
oc get csv amqstreams.v3.2.1-10 -n kafka-operator
oc get deployment,pods -n kafka-operator
oc get operatorgroup kaas-kafka -n kafka-operator -o jsonpath='{.status.namespaces}'
oc get subscription amq-streams -n kafka-operator -o yaml
oc get installplans -n kafka-operator
```

Require application Synced/Healthy at the intended revision, selected CSV Succeeded, and the operator deployment/pod Ready. Record actual restarts, images, target namespace, pending-plan approval state and observation time. `Running` alone or an old CSV Succeeded history entry is insufficient.

On November 22 these checks passed for 3.2.1-10, and the newer Kafka plan `install-k4fhm` for 3.2.2-9 was unapproved. November 23 read-only discovery again found installed CSV 3.2.1-10, current advertised CSV 3.2.2-9, Manual approval, and ArgoCD Available. The latter discovery did not re-execute the bootstrap or a load test. Recheck the actual current InstallPlan before any upgrade decision.

## 8. Handoff to Kafka and testing

This completes the operator stage. Broker/controller resource and PVC budgets, initial listener/security settings and message limits still need a concrete dev configuration. A later reviewed GitOps stage will deploy Kafka and four topics; test clients run in `kaas-demo` with at most 300 seconds total runtime and values up to 2 MiB. The current AppProject deliberately does not yet allow Kafka/KafkaTopic/Job resources. No successful operator installation qualifies throughput, durability, recovery or the smoke test.

If bootstrapping fails, retain the application conditions, pod state, events and bounded relevant logs. Do not delete CRDs, operator namespaces or PVCs as a troubleshooting shortcut. Resume from observed state and reviewed Git; no teardown procedure is authorized by this guide.

References checked 2026-11-23: actual repository manifests at deployed SHA, November 22 execution evidence, November 23 read-only discovery, ArgoCD and OLM primary documentation linked above. This guide was checked against those inputs; its CLI reproduction commands were not rerun as mutations.
