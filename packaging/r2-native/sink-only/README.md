Latest sink selection: the active overlay now also contains `kaas-r2-sink-config-02e-retest` and selects a separate retest database on the same PVC. Both databases are stopped/sealed and retained. See [revised runner/retest](../../../docs/r2-revised-runner-2026-11-26/README.md); the original activation record below is historical.

# R2 evidence sink activation — 2026-11-26

**SINK_AVAILABLE_1_OF_1; PVC_BOUND; STORAGE_AND_TLS_VERIFIED; CLIENT_DISABLED.** User explicitly authorized the evidence sink only, including storage/TLS verification, with no producer/consumer tests. This package records the local activation overlay applied after published baseline `8d1b368cdb5be1bd7dd87c3ec2011d3d0018678b`. The user authorized Git publication of the sink-only artifacts and evidence on 2026-11-26; the owning commit identifies the published snapshot. No GitOps registration/sync or automatic sync change occurred.

## Deployment boundary

`resources.yaml` contains only an immutable `kaas-r2-sink-arming` ConfigMap and a single-replica, unpaused `kaas-r2-evidence` Deployment. The sink mounts this separate true arming value. The existing `kaas-r2-arming-disabled` remains false and is still the only arming ConfigMap referenced by the client. No client Job was created; its baseline definition remains `suspend: true`. Client runtime authorization is false, authority/start remain null and all 11 execution gates remain OPEN.

The default `../deploy/` root remains the disabled baseline, including a paused zero-replica sink. This `sink-only/` root represents the authorized active sink. Do not apply the disabled root over the running sink without intending to stop it. Neither root is included by an active GitOps Application. Broad `deployment_enabled`/`workloads_enabled` fields retain their disabled baseline/client meaning; explicit `actual_sink_deployment_enabled: true` and the activation receipt record the actual live sink.

The pinned sink image is unchanged:

`image-registry.openshift-image-registry.svc:5000/kaas-demo/kaas-r2-sink@sha256:f730c89baceda0f8a536ab9c94696b768c996fe55d60202300095b4d450efa25`

Created just the sink Deployment and its independent arming ConfigMap. Existing Service, TLS/credential Secrets, trust/config ConfigMaps, policies, ServiceAccount and isolated PVC were reused. No source tenant credentials, Kafka policy, client configuration or existing workloads changed. Namespace snapshots prove the same 17 pre-existing Job/Deployment UIDs and specs, with only the new sink Deployment added. Memory-only authenticated sessions used verified TLS and were closed without persisting API credentials or altering default kubeconfig. No sensitive material was exported.

## Observed results

| Check | Result |
| --- | --- |
| Rollout | 1/1 Available; Pod Running/Ready, zero restarts; actual imageID matches pinned digest |
| Service | One ready EndpointSlice endpoint for the sink |
| PVC | `kaas-r2-native-evidence`, 1Gi `gp3-csi`, Bound to `pvc-d2cd40eb-6e4b-48d2-a2af-d4b5d10879a2` |
| Runtime security | UID `1000770000`, primary GID 0, groups 0/`1000770000`, restricted-v2/fsGroup `1000770000` |
| Mounted directory | UID 0, GID `1000770000`, mode 0775; database UID/GID `1000770000`, mode 0644 |
| Filesystem access | Isolated readiness file write, flush/fsync, readback, unlink and parent-directory fsync succeeded |
| Capacity at check | 1,020,702,720 filesystem bytes; 1,003,814,912 bytes free; above sink's 64MiB free-space guard |
| SQLite | Startup initialized expected run/plan identity; read-only integrity check `ok`; WAL mode; zero fixture events and zero stop/seal flags |
| Live TLS | TLS 1.3 handshake to running server, verified injected service CA and hostname `kaas-r2-evidence.kaas-demo.svc` |
| Authorization | GET `/v1/export`: anonymous 401; writer 401; owner 200 with zero bytes |

`verify_sink.py` executed inside the actual sink using `oc exec`. It trusts a supplied public service CA, connects to loopback with the service DNS name as SNI/verification identity, keeps writer/owner tokens inside the container, and prints only sanitized outcomes. It never constructs a Kafka client and sends no event POST, stop or seal request. The temporary storage probe is separate from SQLite fixture evidence and was removed. This is authorized sink verification, not a producer/consumer or load test.

Live TLS handshake proves the mounted server certificate/key work together and validates the service DNS identity against the service CA. It does not prove client-to-Service network reachability: the connection address was `127.0.0.1:8443`, bypassing Service routing/CNI. The ready Service endpoint is a separate control-plane observation. No client Pod, owner helper Pod or network probe workload was launched.

SQLite startup and the filesystem roundtrip demonstrate current write permissions and local persistence operations. They do not qualify restart recovery, host/storage loss, infrastructure durability or the inherited no-loss requirement. No restart/failure/recovery experiment was performed. The previous public certificate checks remain historical; this increment additionally verified a live handshake.

## Evidence and remaining work

`evidence/results.json` is the consolidated receipt, with exact image/Pod/PVC identities and verification limits. `runtime-verification.json`, observed Pod, deployment/PVC and EndpointSlice snapshots are alongside. Full before/after snapshots, server dry-run and PV record are in `docs/reviews/r2-sink-activation-2026-11-26/` in the shared workspace. The Pod log was empty. A terminal input-size limit interrupted the first verification dispatch before it executed; retry used a local public command file and succeeded. No failed fixture or test run occurred.

Before the bounded client test, retain this sink/PVC and evidence, freeze the published activation artifacts, verify the effective client network path and native TLS/SCRAM/broker identity, refresh health/ISR and exclusive group membership/offsets, and complete per-run authority, deadline/late-offset/support and independent export/custody records with the final C3/C6/C7/C4 joins. The accepted seven-day sandbox plus verified shared-workspace copy policy remains; no cleanup automation is enabled.

The sink is intentionally left running as authorized. Do not delete the PVC or Secrets as cleanup. If later authorized to stop the sink, scaling only its Deployment to zero preserves the claim; stopping, deleting storage, publishing or enabling the client are separate actions. **R2 client acceptance remains NOT_RUN.**
