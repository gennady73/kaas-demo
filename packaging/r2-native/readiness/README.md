# R2 dependency readiness — 2026-11-26

**DEPENDENCIES_PREPARED; RUNTIME_READINESS_PARTIAL; CLIENT_AND_SINK_NOT_DEPLOYED; TESTS_NOT_RUN.** This increment was explicitly authorized after image publication `9b5033d88ac13c4a7d998eee41588e6b35f819e6`. The user authorized Git publication of this readiness record and updated configuration on 2026-11-26; the owning commit identifies the published snapshot. Earlier preparation/build receipts retain their historical status; this record supersedes their undelivered/unallocated wording for the dependencies listed below.

## Completed actions and evidence

| Area | Observed result | Remaining limit |
| --- | --- | --- |
| Tenant credentials | Reviewed create-only delivery helper created four password-only Opaque Secrets in `kaas-demo`, bound to the four literal KafkaUser principals | No live SASL/client authentication performed; source rotation requires reviewed refresh |
| Kafka CA | Copied public CA to `kaas-r2-cluster-ca`; parsing, self-signature and current validity checked; expires 2027-11-23 11:32:38 UTC | Broker leaf SAN/chain/expiry and actual hostname-checked connection remain unverified |
| Sink capabilities | Created separate random writer and owner Secrets, each with its own 48-byte random input represented as a URL-safe token | No endpoint authentication or custody/export operation performed; owner token is not mounted in the client |
| Sink TLS | Created annotated ClusterIP Service and CA-injected ConfigMap; controller generated TLS Secret; public certificate chain and DNS hostname verified with OpenSSL | TLS private key was not exported; key-pair match/live TLS handshake not checked |
| Support | Created nine objects selected from the published package: two SAs, four CMs, Service and two NetworkPolicies | Job/Deployment explicitly excluded; no active GitOps include or workload authority added |
| Storage | Created isolated 1Gi RWO `gp3-csi` PVC, status Pending; class `WaitForFirstConsumer`; CSI fsGroup policy `File` | No backing PV binding, mounted filesystem, free-space or persistence proof until authorized scheduling |
| Admission | Both exact Pod templates accepted by server dry-run as admin using restricted-v2, with fsGroup `1000770000` and assigned nonroot UID/security defaults | No Pod persisted; admission is not scheduling, image pull, file access or runtime verification |
| Permissions | Both SAs may use restricted-v2 and read internal image layers through existing namespace binding; neither may GET Secrets; automount false; image-pull Secret references generated | No actual kubelet pull/projection verification; no additional RBAC created |
| Network configuration | Only the new respective R2 policy selects each candidate's labels; Kafka ingress permits `kaas-demo` on 9093; DNS and Kafka peer labels observed | Effective CNI/cluster policy, DNS, TLS and TCP reachability remain runtime checks |
| Preservation | Existing 17 Job/Deployment UIDs/specs identical before and after; no R2 client Job or sink Deployment exists; sink has no ready endpoints | No client or sink readiness claim |

The sink certificate is valid from 2026-11-26 11:42:56 UTC until 2028-11-25 11:42:57 UTC. Its SANs include `kaas-r2-evidence.kaas-demo.svc` and `kaas-r2-evidence.kaas-demo.svc.cluster.local`; chain and hostname verification used the injected service CA. Public certificate report is saved alongside this guide. Validity and identity must be refreshed at activation.

Source password values stayed in process memory and TLS request bodies. No password, password digest, private key, sink token or API bearer was printed, written to local evidence or added to Git. The four source users' readiness/current generation, Secret owner bindings and source UID/resourceVersion stability were checked before create-only delivery. See `credential-delivery.json` for names/UIDs/RVs only. No source Secret changed and no existing destination was overwritten. The API session used memory-only credentials and closed without changing the default kubeconfig.

`sink-capability-creation.json` records generated Secret identities only. These remain sandbox Kubernetes Secrets, not a production secrets-management system. No automatic rotation, refresh, seven-day deletion or cleanup is enabled. Do not delete the PVC/evidence based solely on age; accepted custody policy remains seven days plus verified export to the shared workspace.

The initial image permission command used `imagestreams/layers` as a resource/name rather than specifying a subresource. The corrected command uses `get imagestreams.image.openshift.io --subresource=layers`, with the service-account identity and normal service-account/authenticated groups. It returned yes for both accounts. Existing `system:image-pullers` already covers the namespace service-account group, so no grant was necessary. A conventional broker Secret name lookup returned NotFound; no broker leaf inspection is claimed from it.

Server-side Pod admission used `--dry-run=server`, and certificate checks operated on public certificate files. No regression suite, integration test, load test, Kafka CLI client, producer/consumer fixture, sink server, endpoint probe or binder Pod ran. Root evidence includes the exact dry-run outputs, namespace snapshots, source delivery receipts, public CA/cert reports, quota/class/CSI/SA/policy observations and permission outputs under `docs/reviews/r2-readiness-2026-11-26/` in the shared workspace. Namespace quota and limit-range lists were empty; this does not prove node or cloud capacity.

## Prepared next activation record and remaining work

`next-activation-record.json` is disabled and has null authority/start fields. It records the remaining joins without marking execution gates complete. No further policy answer is needed for this preparation; the sandbox owner/approver and seven-day/shared-workspace custody policy are already selected.

Before a bounded client run:

1. After publication, refresh current credential-source revisions, CA validity and final-source C3/C6/C7/C4 review evidence. The image pins remain the published verified digests.
2. Obtain explicit authorization for sink deployment and later client execution. Schedule the single sink only after per-run review; let the WFFC PVC bind naturally. Verify actual image pull, UID/fsGroup/Secret projection, disk headroom, SQLite/WAL persistence and service TLS/key-pair/hostname. The sample arming flag is false, so merely scaling the sample would terminate at its guard.
3. Verify effective DNS/Kafka/sink network paths and typed TLS/SCRAM behavior in the authorized activation stage. Check actual broker certificates. Configuration/admission alone does not satisfy this requirement.
4. Establish the exclusive literal consumer-group ownership/membership and committed/retained starting offsets without resetting/deleting offsets. Refresh Kafka health/ISR immediately before execution; CR Ready is insufficient for partition acceptance.
5. Close startup-inclusive 300s/external-stop/late-offset/final-reconciliation and failure/support arrangements, independent export/auditor and owner custody/second-copy records. Prepare the real per-run authority, start clock and reviewed immutable ConfigMap replacements/overlay; no gate can be closed by changing a boolean alone.
6. Only then authorize the bounded 16-positive/eight-negative fixture. Deployment and execution remain separate from this dependency preparation. No production isolation, durability/recovery or capacity acceptance follows from these readiness checks.

Current local manifests retain suspended client Job, paused zero-replica sink, false arming and runtime authorization, null executor authority/start clock and all 11 actual gates OPEN. The sink Service and Secrets exist without endpoints or running sink. The optional PVC remains excluded from the deployment root even though its authorized claim has now been created; its annotation/status records the pending first consumer. No cleanup or further live action is implied.
