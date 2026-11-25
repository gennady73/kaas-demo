# R2 two-tenant client preparation

Revision0.1, 2026-11-25. **PREPARED_ONLY; NOT_APPLIED; CREDENTIALS_NOT_DELIVERED; CLIENT_TESTS_NOT_RUN.** This package implements the environment/delivery side of C2 contract `c2-tenant-r2-0.2`. It leaves the native adapter, evidence sink and execution authorization separate. It is not included in an existing ArgoCD/Kustomize root; automatic sync is not enabled or modified.

## Fixed target and identities

Reuse existing `kaas-demo` for the trusted administrative test harness, Kafka `kaas-kafka/kaas-dev`, internal `kaas-dev-kafka-bootstrap.kaas-kafka.svc:9093`, SASL_SSL/SCRAM-SHA-512 and hostname verification. R1 reconciled both tenants at resource3211df9. A/B producer and consumer principals remain separate, literal topic/group ACLs and quotas unchanged. [bindings.json](bindings.json) maps all four source Secrets to distinct same-name destination Secrets and exact C2 mount paths. No smoke-user fallback, broker/internal admin identity, external listener or Kafka policy change.

The harness is privileged by its **four mounted tenant credentials**, even without a Kubernetes API token. This tests Kafka ACL separation, not hostile-workload Secret isolation. Separate tenant workload namespaces/Pods and role-limited mounts are a later deployment-isolation scope; do not infer those guarantees from two tenant labels in one administrative harness.

## Artifacts and execution boundary

| Artifact | Prepared behavior | Not performed |
| --- | --- | --- |
| [delivery.py](delivery.py) | Default is zero-network preparation output. A later explicitly authorized `--execute-delivery` uses existing `oc` login against exact sandbox3088 with a supplied API CA, creates only four password-only Opaque Secrets in kaas-demo and public CA ConfigMap kaas-r2-cluster-ca. Validates Ready/current source users, Secret binding/owner, all destination absences and source UID/RV stability. | No source credential value was read or delivered in this preparation. No copy Job/controller, new credentials, source password rotation, overwrite/patch/delete or periodic refresh. |
| [support/](support/kustomization.yaml) | Two ServiceAccount previews with automount disabled; two label-selected ingress/egress policies for trusted and network-denied test peers. Kustomize renders locally. | Not applied, registered, synced or published. No Role/RoleBinding, namespace, broker, PVC, Job or client Pod included. |
| [pod-and-mount-contract.json](pod-and-mount-contract.json) | Immutable role/path references, read-only mounts, no API token/host networking, non-root/restricted security proposal, resource proposal and future suspended Job bounds. | Not a Job manifest or runnable command. Native entrypoint, actual image pull/SCC/mount readability/resource allocation and sink peer remain unresolved. |
| [test_delivery.py](test_delivery.py) | Offline fake-API regression checks for scope, collision rejection, staging/rotation, partial failure and receipt redaction. | No real Secret, certificate chain, API, Kafka client or payload test. Fake TLS loader is not trust validation. |

For local preparation review only:

```sh
python3 delivery.py
python3 -m unittest -v test_delivery.py
oc kustomize support
```

These commands do not apply manifests, deliver credentials or invoke Kafka clients. Do not turn a fake adapter into a live runner by flipping flags.

## Credential/CA delivery and lifecycle

Source namespace is `kaas-kafka`; destination is `kaas-demo`. Password paths are `/credentials/<exact-principal>/password`. Only key `password` is copied; JAAS strings, other source data, labels, ownerReferences and last-applied annotations are not cloned. The public cluster CA comes from `kaas-dev-cluster-ca-cert` key `ca.crt` into ConfigMap `kaas-r2-cluster-ca`; mount `/credentials/cluster-ca/ca.crt`. A ConfigMap is suitable only for the public CA certificate, never for a password/private key.

The future delivery command requires **explicit** execution selection plus API CA file and a new receipt path; it verifies exact local cluster and admin identity and uses normal verified TLS with no redirect forwarding. It reads the four selected source Secrets and CA only when that action is separately authorized. Material stays in process memory and HTTPS request bodies; it is never rendered to Git, a YAML file, command line, shell environment or receipt. Metadata lookup negotiates PartialObjectMetadata; no existing destination data is fetched. All five destination objects must be absent before source credentials are read. Source ownership/UID/RV and CA parsing are checked before the first create. A racing conflict or partial failure stops; it never replaces an existing Secret or deletes partial creations. The receipt records only names/UIDs/resourceVersions and fixed outcome codes, with no password or password digest.

This is a one-time bounded sandbox delivery mechanism, not production secret management. It intentionally refuses destination overwrite: source credential/CA rotation requires an explicit reviewed refresh/versioning/reload procedure. No automatic rotation, revocation, cleanup or source change is selected here. Before a future test, verify current source/copy revisions, CA chain/validity/SANs, file readability under OpenShift-assigned UID/fsGroup, and actual client hostname checking. Mounts use directory projection rather than subPath, but that does not synchronize a copied Secret with its source or prove a native client reloads it. Do not log passwords/native configs; retain failed receipts and preserve source/generated resources. Rotation/revocation acceptance remains separate.

No Secret-reader RBAC is granted to the harness. The kubelet can project referenced namespace-local Secrets for an authorized Pod creator without giving that Pod Secret API permissions. Existing administrator/Pod-create powers in the shared namespace remain a trust boundary, not a claim of cross-tenant secrecy.

## Namespace and network preparation

The current C2/C3 fixture uses kaas-demo, already admitted by Kafka's generated ingress policy. No new tenant namespace or listener change is required for this harness. The source policy and existing namespace metadata were inspected read-only; standard NetworkPolicy configuration is not proof of packet delivery or CNI enforcement.

Both previews select only new `kaas.example.com/r2-runner` labels absent from captured existing Pods. Trusted egress permits Kafka9093 only to the observed Kafka pod labels in kaas-kafka, plus DNS to observed openshift-dns peers. DNS includes Service53 and named target ports `dns`/`dns-tcp`; target translation and actual reachability still need runtime verification. Ingress is empty for selected harness Pods. The network-denied peer allows DNS only and no Kafka egress. It is not deployed or instantiated and is a **separate optional bounded network test**, not one of C2's eight ACL cases.

**Evidence-sink egress is unresolved.** The trusted policy preview deliberately has no broad egress fallback. Add the exact reviewed durable-sink peer/port before applying it for a real harness. The existing continuity collector must not be assumed protocol-compatible; its ingress currently selects continuity-client labels, which this package does not borrow to bypass that boundary. Do not modify it or label new fixtures as continuity clients. NetworkPolicies are additive: other selected policies, admin/CNI controls and service translation must be checked before claiming denial. A timeout cannot prove Kafka ACL rejection.

## Bounded future client tests

Use C2/C3's reviewed small fixture, not the older 96-case/2MiB proposal:

- Sixteen positive 1,000-byte originals, four per topic, own producer/consumer credentials and literal own groups. Verify IDs/length/checksum, independent ACK/ambiguous outcomes, durable receipt before manual commit, and final offsets.
- Eight negative cases, symmetric A/B: cross-topic write, cross-topic read with own group, cross-group read on own topic, and consumer-role write. Four negative writes offer at most one1,000-byte original each. Total attempted logical originals≤20,000bytes. Reads/replication/retries are not positive ingestion.
- One global300s ceiling including startup/retries/drain/shutdown; reviewed phase caps45+90+90+45+30. Maximum one application attempt per logical ID and no automatic Job retry. Native delivery/close cancellation and startup-inclusive timing remain to be verified before creating a runnable Job.
- Positive controls must pass on the same reachable/trusted path. Only matching typed topic/group authorization error and stage pass a denial. Timeout, empty read, TLS/SASL/network/cluster-idempotence denial or unknown/wrapped native errors are INCONCLUSIVE. The consumer-write IdempotentWrite confound must be isolated without widening consumer ACLs.
- Literal group IDs cannot gain run suffixes. Snapshot exclusive group ownership/membership/committed and retained offsets first; no offset reset/delete. Close positives before reuse; negative paths never commit or auto-commit on close. Unexpected ACK, delivery or forbidden join stops the suite and preserves evidence; never delete leaked records as cleanup.

Neither this package nor the current C2 offline engine supplies a tested native entrypoint. Candidate smoke image/digest is recorded as prior evidence, not a current pull or selected negative-error mapping. Native integration, group baselines, durable evidence transport/custody, resource/SCC/image admission and explicit runtime authority remain open. Full namespace isolation, wrong-CA/password/hostname, credential lifecycle, fairness, governance, full24h/TB and recovery tests are distinct; do not claim this minimal fixture covers them.

Current parent-workspace evidence: `docs/environment/r2-preparation-2026-11-25/README.md`, live GET-only metadata and validation receipt; `config/environments/r2-tenant-preparation-2026-11-25.json`. This repository package is local/uncommitted/unpublished; parent runtime receipts and all Secret values stay outside publication.
