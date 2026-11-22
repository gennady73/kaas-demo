# Implementation status

Date: 2026-11-18. Owner: coordinating work area.

USER-SELECTED: GitOps origin `https://github.com/gennady73/kaas-demo`; operator `3.2.1-10`, OpenShift 4.20.18–4.21.x; four-topic, <=300s, <=2 MiB smoke test.

VERIFIED: repository cloned successfully and empty at clone time; local checkout has no commits. Only local scaffold files and the design-input snapshot have been prepared. No push or cluster write has been made.

PROPOSED: development source path `environments/dev`; separate platform/tenant/GitOps/test paths; manual sync; 16-record boundary test. Selecting this origin does not verify ArgoCD can reach it from the sandbox.

OPEN implementation inputs:

1. Exact operator catalog/CSV/bundle/image digest and supported Kafka broker mapping/CRD schemas.
2. Small dev broker/controller layout, CPU/memory/PVC budget and initial listener/security policy.
3. Installed GitOps version/control namespace, authorized sync roles, repository access and a published reviewed source revision.
4. Effective 2 MiB value path including batch/request overhead, follower and consumer limits.
5. Selected xk6 image/extension, executable boundary scenario, <=300s termination and complete evidence path.

The shared coordinator workspace remains the architecture baseline. Its SRS 0.9, GitOps/smoke plan 0.1, smoke profile contract 0.1 and C1/C2 handoffs inform this scaffold. Fingerprints are in `baseline-provenance.json`; source copies of sensitive cluster inventory are intentionally excluded.

Validation: Git origin and empty-branch status inspected; profile snapshot parsed and matched to the coordinator copy, including four topics/2 MiB/300s bounds and byte arithmetic. No manifest rendering/schema validation or runtime test is claimed because no deployable resources or runnable clients exist yet.

## Bootstrap update, 2026-11-19

Prepared `gitops/bootstrap/argocd.yaml.template` from the user-provided minimal resource. Namespace remains parameterized: TLS-verified read-only discovery found no ArgoCD API group or operator CSV. Operator/CRD availability is a prerequisite, not a completed installation. No ArgoCD schema validation, deployment, repository connection or sync performed. Shared evidence: `config/environments/ocp-rddgh-runtime-inventory-2026-11-19.json` in the coordinator workspace. Token excluded.

## Namespace clarification, 2026-11-19

GitOps operator defaults to `openshift-gitops-operator`; Kafka operator requires a dedicated namespace (name unresolved); `kaas-demo` hosts Kafka tests. ArgoCD instance and Kafka cluster placements are unresolved separate inputs. Bootstrap namespace parameter means instance namespace, not necessarily operator namespace. No cluster state change asserted.

## Intentional GitOps version selection, 2026-11-19

USER-REPORTED installation: CSV `openshift-gitops-operator.v1.20.0` (operator version 1.20.0). The user intentionally chose this version while production's GitOps version is unknown. Preserve this sandbox selection; no upgrade to latest is requested. This closes the selected version input, not production parity or live readiness. The earlier discovery showing no GitOps operator predates this installation report and must not be treated as the current installed-state conclusion. Operator/CRD readiness, actual ArgoCD instances and deployed ArgoCD version remain to be inspected; do not equate operator version 1.20.0 with the ArgoCD application version. No new cluster query or mutation was performed to record this report.

## Live observed GitOps state, 2026-11-19

Current diagnostics show installed operator 1.22.0 and default ArgoCD `openshift-gitops/openshift-gitops` Available. User-selected version remains 1.20.0: do not silently treat 1.22 as accepted or attempt downgrade. Subscription is latest/Manual, approved completed plan for 1.22.0, pending unapproved plan for 1.22.3. Full evidence/limitations in coordinator `docs/environment/gitops-operator-diagnosis-2026-11-19.md`. No cluster changes made. Previous installation-absence notes are historical.

## Operator installation stage, 2026-11-19

Exact selected CSV `amqstreams.v3.2.1-10` found in live Red Hat package channel `amq-streams-3.2.x`. Prepared renderable `environments/dev/operator`, manual Subscription and single target-namespace OperatorGroup; separate administrator bootstrap namespaces/AppProject/pinned-commit Application. See `deployment-sequence.md`. Proposed implementation namespaces are `kafka-operator` and `kaas-kafka`, preserving test-only `kaas-demo`. Kustomize rendering and scope/manual-approval assertions passed; no GitOps upgrade manifest, broker, PVC or test Job is included. Server validation and actual stage status are recorded separately by coordinator.

## Validation and publication hold, 2026-11-19

Initial operator-stage commit `91785f48c81265363bbd4eb7a6aeefdeb94f66f1` exists locally; push failed because GitHub credentials were unavailable. The user explicitly instructed waiting for access: do not retry publication until access is supplied. Current follow-up files are local only. This supersedes earlier unborn-branch/scaffold-only notes.

Strict server dry-run accepted both proposed namespaces, the AppProject and the Application pinned to that initial commit, without persisting resources. Rendered OperatorGroup and Subscription passed offline validation against the installed OLM OpenAPI schemas; resolver behavior and selected operator runtime are not yet tested. Exact selected CSV is available in the live catalog; broker mapping remains open until that exact bundle/CSV is inspected.

Prepared offline expected-record generator and example under `tests/dev-smoke/`; exact byte/checksum/boundary checks passed, no Kafka traffic. Shared detailed results: coordinator `docs/environment/operator-stage-preparation-2026-11-19.md`. ArgoCD sync/install must wait for publication; do not bypass GitOps using a direct operator installation. Pending GitOps 1.22.3 stays unapproved.
