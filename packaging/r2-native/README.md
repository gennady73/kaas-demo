Latest result: [Revised runner build and bounded retest](../../docs/r2-revised-runner-2026-11-26/README.md). Revised image built; exit handling confirmed live, initial-position check still incomplete. Both client Jobs are suspended.

Latest code status: [R2-LIVE-01/02 fixes validated offline](../../docs/r2-live-fixes-2026-11-26/README.md). Revised image not built or deployed; no live rerun.

Latest execution result: [Single bounded R2 attempt — incomplete](../../docs/r2-bounded-2026-11-26/README.md). No send was attempted; client is re-suspended and sink evidence is stopped/sealed. Earlier readiness reports are historical.

Latest client status: [Read-only client connectivity, TLS/SCRAM, health and group readiness](client-readiness/README.md). Client fixture remains disabled; evidence sink remains deployed.

Latest runtime status: [R2 evidence sink deployment and verification](sink-only/README.md). The sink is deployed; the client remains disabled. Earlier readiness/build records below are historical snapshots.

# R2 native images and disabled manifests

Latest continuation: [EOF sentinel correction](../../docs/r2-eof-sentinel-fix-2026-11-26/README.md) is validated offline and authorized for publication with its regression tests and evidence. Actual image pins remain at the published incomplete revised-runner checkpoint; a new image has not been built. Both client Jobs remain untouched, last observed suspended. The original preparation instructions below are historical; use the dated build/result records for current status.

Status: see `image-build-results.md` for the subsequent authorized build, verification and pinned-image record. **DEPLOYMENT_AND_WORKLOADS_DISABLED**. The paragraphs and validation receipts below describe the original preparation baseline; image build status and pins are superseded by the build result. The user authorized Git publication of this disabled package on 2026-11-26. No resource, build, credential delivery or client workload was started. The earlier native implementation is published at `afb9c7c7b2f3901a8a4e2c456029a931a9db00b6`; that commit identifies the native source, while this directory is added by the later packaging commit. Saved preparation receipts retain their original local/unpublished status as historical evidence.

## Inputs and boundaries

`inputs.json` pins the reviewed native binary, public source manifest and logical plan. `prepare_contexts.py` checks all 39 reviewed native source fingerprints and the exact binary before constructing two deterministic binary-build archives. It reopens the archives and checks every file. The compiled binary is supplied externally; it is never committed here. Runtime scripts and sink code come from `tests/tenant-r2-native/`, without modifications in this increment.

Both Dockerfiles reuse the exact Kafka/RHEL9 image digest recorded in the historical collector Deployment (`docs/testing/runs/collector-fix-20261125/collector-deployment-before-upgrade.json` in the shared workspace). That Deployment ran Python in this image. Reusing layers avoids introducing an additional Python base; the Kafka base is large. Historical use does not establish current pull availability, native ABI compatibility or a successful new image build. No packages are downloaded by these Dockerfiles. Runner build checks include checksum verification, `timeout` availability and public `k6 inspect`; sink build checks include Python SSL/SQLite imports. These image build steps remain **NOT_RUN**.

`required-inputs.json` contains names and keys only. Tenant principals remain separate literal users. Kafka CA and sink service CA are separate. The writer token mounts in client and sink; the separate owner token mounts only in the sink and a later authorized custodian, never in the client. No credential values or Secret manifests are supplied.

## Disabled objects

| Location | Contents | Execution protection |
| --- | --- | --- |
| `deploy/` | 11 objects: two ServiceAccounts, four ConfigMaps, Service, client Job, sink Deployment, two NetworkPolicies | Job suspended; sink replicas zero and paused; immutable arming flag false; runtime authorization false and all 11 gates OPEN |
| `build/buildconfigs.yaml.disabled` | Two Binary BuildConfigs and two empty output ImageStreams | Outside deployment root; no triggers or image imports; no Builds created |
| `optional-storage/pvc.yaml.disabled` | Proposed isolated 1Gi RWO `gp3-csi` PVC | Outside deployment root; not allocated |

The deploy root is isolated from active GitOps roots. Images use explicit `invalid.invalid/...@sha256:000...` sentinels, and actual image digest inputs are null. They must be replaced with independently recorded output digests before future activation. Candidate build output tags are not acceptable runtime identity pins.

ServiceAccounts do not mount Kubernetes API tokens or add RBAC grants. Pods request restricted security, an arbitrary nonroot UID, read-only image roots and writable bounded `/tmp`. Client egress is limited to selected DNS, Kafka and sink peers; sink ingress is limited to the client and a separate owner-labelled operations peer. Labels, admission, filesystem group access and effective network policy require live verification. No owner Pod is included.

The proposed Service requests a service serving certificate and a public CA-injected ConfigMap. Required trust/Secret mounts deliberately block startup until supplied. This uses OpenShift's documented [service certificate and CA injection mechanisms](https://docs.redhat.com/en/documentation/openshift_container_platform/4.20/html/security_and_compliance/configuring-certificates); no certificate generation or injection was performed. Kafka trust remains the reviewed Kafka cluster CA.

The optional PVC is isolated from continuity evidence. Its class comes from a saved sandbox NodePool, not a fresh capacity check, and does not change the production VSAN-to-ODF direction. Requests for the future client and sink total 200m CPU/256Mi memory; limits total 1 CPU/768Mi. Each proposed build requests 100m/128Mi with 500m/512Mi limits. Run future builds sequentially to bound added resources; `Serial` is per BuildConfig, not a global lock. No additional CPU, memory or storage has been allocated.

## Offline reproduction

From the `kaas-demo` repository, with Python, PyYAML, jsonschema and local `oc` available:

```sh
python -m unittest discover -s packaging/r2-native -p test_package.py -v
python packaging/r2-native/validate.py
oc kustomize packaging/r2-native/deploy > /tmp/r2-disabled-rendered.yaml
python packaging/r2-native/validate_schema.py --schema packaging/r2-native/validation/sandbox-openapi.json.gz --rendered /tmp/r2-disabled-rendered.yaml
python packaging/r2-native/prepare_contexts.py --binary /tmp/kaas-r2-final-validated-native/k6 --output /tmp/r2-new-context-directory
```

Use a new output directory for context generation. The exact reviewed binary SHA256 is `7405cc006c1d05d2748aee1955bfd3db6e3edf4e6f723dd997e060bd22c6525b`; rebuilding a different executable requires a new review receipt, not bypassing the check. Do not run these assertion-based validators with Python optimization enabled. Offline schemas retain 205 public definitions from the sandbox's GET `/openapi/v2` (Kubernetes API schema 1.34). Only Kubernetes int-or-string representations are normalized. Schema validation does not execute admission, defaulting, RBAC, scheduling or network checks.

Retained receipts under `validation/` record 16 regression tests, 11 rendered objects, 16 schema-checked objects (including four manual build resources and optional PVC), and verified archives with 17 runner / 6 sink entries. The archives themselves remain under `/tmp/kaas-r2-image-contexts-20261126/`, not in Git. They may be lost when temporary storage is cleared; regenerate them from the pinned source and binary.

## Future build and activation sequence — not executed

After explicit authorization, check registry/base availability, supported build permissions and sandbox budget. Register the two empty ImageStreams and manual BuildConfigs, then submit each verified archive to its corresponding binary build, one at a time. OpenShift [binary source builds](https://docs.redhat.com/en/documentation/openshift_container_platform/4.20/html/builds_using_buildconfig/creating-build-inputs) require an explicit streamed build request; this package does not create one. The proposed 600-second build deadline follows [BuildConfig deadline semantics](https://docs.redhat.com/en/documentation/openshift_container_platform/4.20/html/builds_using_buildconfig/advanced-build-operations), beginning when the build Pod is scheduled, including builder image pull time. It is not a total human workflow deadline.

Record successful build IDs and immutable output digests; verify public native identity/import in the actual runner image and SSL/SQLite/sink imports in the sink image without constructing Kafka clients. Local Podman inspection failed due runtime-directory permissions, so no local image build or container import check is asserted. Do not substitute an older smoke image.

Prepare a reviewed per-run overlay with real image pins, unique execution identity, actual authority and clock, explicit gate evidence, and new/replaced immutable arming/runtime ConfigMaps. The preserved `r2-native-20261125` plan label is a frozen source identifier, not evidence that a run started on that date. Never enable the sample by merely scaling or unsuspending it.

The proposed client has no retries, a 300-second Job deadline, zero termination grace, and a container guard of 285 seconds plus at most five seconds before forced kill. The guard begins at container entry; the Job deadline begins with Job execution and includes startup. An unanswered SDK wait is not cancellation. Validate startup-inclusive timing, external termination observation, late-offset disposition and final reconciliation with C3/C6 before activation. A [suspended Job](https://v1-34.docs.kubernetes.io/docs/concepts/workloads/controllers/job/) does not create Pods, and resuming resets its start/deadline accounting; do not suspend/resume a live R2 attempt to extend or retry it. Deadline exhaustion is INCOMPLETE, not a passing result.

## Remaining before the bounded test

1. Publish/freeze this new packaging, build and verify the two actual images, then record immutable digests. No image has been built or pushed in this increment.
2. Complete create-only four-role password/CA delivery, separate writer/owner credentials, service TLS/trust, and actual SCC/filesystem/network/registry checks. Reuse the reviewed delivery proposal; do not read/export passwords for validation.
3. Accept/provision the isolated evidence PVC and verify storage headroom, SQLite/WAL permissions and limits, custodian access and export path. The accepted policy is seven days in the sandbox plus a verified shared-workspace copy under `docs/testing/runs/<run-id>/`; enforcement/export is not yet proven.
4. Refresh Kafka health/ISR, literal group ownership, membership and starting offsets; complete external deadline, final-offset, support/stop and evidence custody records against the final image/package. Historical readiness is insufficient.
5. Complete changed-package C3/C6/C7/C4 joins, populate the per-run execution record and obtain explicit activation/run instruction. R2 still targets 16 positive records and eight negative cases, at most 20,000 attempted original value bytes and 300 seconds. This is not a capacity or production recovery qualification.

No additional policy question is pending for this preparation. The user's rule is recorded in `inputs.json`: if an approval question remains unanswered for more than 300 seconds, suspend processing. Elapsed time never implies approval.

Primary documentation checked 2026-11-26; direct sandbox schema provenance is retained with the validation receipts. No live admission/dry-run, Secret read, resource registration, ArgoCD sync, workload or publication occurred.
