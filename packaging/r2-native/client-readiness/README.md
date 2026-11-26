# Final R2 client-path readiness — 2026-11-26

**READONLY_CONNECTIVITY_TLS_SCRAM_HEALTH_GROUPS_PASS; CLIENT_FIXTURE_NOT_RUN.** User authorized final connectivity, TLS/SCRAM, health and group-offset checks while retaining the suspended client Job and prohibiting producer/consumer tests. The user authorized publication of these readiness artifacts and the DNS correction on 2026-11-26. Their owning commit follows baseline `ed89aa48be2a93a4a9bbdf684d2465574678090b`; saved execution receipts retain their original preparation-time publication status.

## Executed checks

A temporary 180-second-deadline Pod used the exact published runner image, `kaas-r2-harness` ServiceAccount, restricted security, client network-policy labels and four separate credential/CA projections. It mounted no fixture arming/runtime configuration, owner token or writer token, and did not invoke the fixture entrypoint. The trusted administrative harness can read all four mounted credentials; this does not demonstrate hostile-tenant Secret isolation.

`check.py` performed DNS/TLS and a read-only sink GET, then invoked **`k6 inspect`**, not `k6 run`. `admin.js` invoked only native input/identity startup and Admin-only `snapshot` operations. Inspected native source implements those with own consumer-principal group metadata and own producer-principal log-offset Admin calls, without constructing Producer or Consumer handles. No subscription, poll, group join, heartbeat, commit, reset or message transfer occurred. A Java **Admin** client independently described topic partitions/replicas/ISR using each tenant producer identity. It read credentials into memory, with no password configuration file, value, digest, command-line argument or environment export.

| Check | Observed result |
| --- | --- |
| Native runtime identity | Actual binary SHA256 `7405cc006c1d05d2748aee1955bfd3db6e3edf4e6f723dd997e060bd22c6525b`, native `2.14.0`, expected mapping |
| Client mounts and permissions | All four exact credential files and Kafka CA readable under assigned UID `1000770000`; exact verified runner image pulled |
| Kafka connectivity and authentication | Native Admin calls succeeded using all four own principals over SASL_SSL / SCRAM-SHA-512 with certificate chain and hostname verification |
| Bootstrap TLS | TLS 1.3 to the actual bootstrap Service; certificate SAN includes bootstrap and advertised broker identities; inspected leaf expires 2027-11-23 11:32:42 UTC |
| Sink client path | DNS, actual ClusterIP routing, service-CA/hostname TLS and GET `/v1/export` worked from the client-labelled Pod; unauthenticated request returned expected 401 |
| Control plane health | Kafka, four KafkaTopics and four KafkaUsers Ready at current generations; three broker Pods Ready |
| Topic health | Four logical partitions, each with valid leader, RF2 and matching two-member ISR |
| Credential freshness | Source password/CA UID and RV unchanged since delivery; destination password/capability UID/RV unchanged since creation |

Observed partition leaders/ISR at approximately **2026-11-26 12:19:21 UTC**:

| Topic | Leader | Replicas | ISR |
| --- | --- | --- | --- |
| `kaas-sbx-a-events` | 0 | 0,1 | 0,1 |
| `kaas-sbx-a-audit` | 1 | 1,2 | 1,2 |
| `kaas-sbx-b-events` | 0 | 0,1 | 0,1 |
| `kaas-sbx-b-audit` | 2 | 2,0 | 0,2 |

Each literal group `<topic>-group` was absent in its own principal's complete, error-free native group listing: **zero members, no committed offset (`null`), log-start 0 and log-end 0**. Null means no committed position; it is not offset zero. No group was created to inspect it, and no offset was initialized, reset or deleted. These are timestamped observations, not an exclusive reservation or a production no-loss result. Refresh immediately before execution.

## DNS blocker corrected

The first diagnostic failed without stage detail; the second localized failure to bootstrap DNS resolution (`gaierror`), before native authentication or topic/group Admin calls. The live DNS Service exposes port 53 and targets observed DNS Pod port 5353. The existing policy allowed port 53 and named `dns`/`dns-tcp` entries, but the diagnostic could not resolve the bootstrap hostname.

Replaced those named entries with **explicit UDP/TCP 5353**, retaining UDP/TCP 53 and the same narrow OpenShift DNS namespace/Pod selectors. Kafka9093 and sink8443 peers were unchanged; no wildcard, external egress, broker policy or RBAC grant was added. Updated the live `kaas-r2-native-client` policy and `../deploy/resources.yaml`, and added an exact DNS-port guard to the offline contract validator (syntax inspected; no regression suite executed). The third readiness attempt passed all checks after this correction.

This is an observed remedy, not proof that every OVN version lacks named-port support. Actual DNS Service/Pod observations are authoritative for this sandbox. Red Hat's [OpenShift 4.20 network-security examples](https://docs.redhat.com/en/documentation/openshift_container_platform/4.20/html-single/network_security/index) also show selected DNS egress on numeric 5353 (checked 2026-11-26); they do not independently establish the cause of this particular named-port failure.

## Preservation and evidence

All three diagnostic Pods and their immutable script ConfigMaps were removed after evidence capture. The successful Pod exited normally with zero restarts. The existing **18** Job/Deployment UIDs/specs—including the running sink—were unchanged. No R2 fixture Job exists; its definition remains suspended, original arming remains false, runtime authority/start clock null and all 11 actual execution gates OPEN. Sink remains 1/1 Available. No client Job deployment, native fixture, producer/consumer test, fixture event, topic/user/ACL change or offset mutation occurred.

`evidence/results.json` summarizes the checks, identities, scope and limits. Successful log/Pod, both earlier diagnostic outcomes, credential-revision result and policy before/after are retained alongside. Raw CR/broker/DNS/network/before-after snapshots remain in shared `docs/reviews/r2-client-readiness-2026-11-26/`. No Secret values/private keys/API bearer or password hashes are in evidence. API credentials remained in memory-only sessions and were closed without default context change. No publication or automation was performed.

`probe.yaml.disabled` is a manual diagnostic reproduction package, excluded from GitOps roots. It is not the suspended fixture Job, and applying it starts an Admin-only readiness Pod. Do not apply it automatically or equate its success with the bounded fixture outcome. Scripts, source image, application guards and execution authority remain separate. No original native source changed.

## Prepared final run record and remaining joins

`bounded-run-preparation.json` binds the four exact empty group baselines and retains **false execution authorization/tests enabled, null authority/window/start**. It separates pre-run prerequisites from evidence produced only during/after the fixture, avoiding a requirement for successful future test evidence before running the test.

The observed connectivity, native authentication, actual mount permissions, sink network path, current topic health and current group baseline gaps are closed for this snapshot. Remaining before the bounded run:

1. Reference the exact published DNS/readiness commit in the final execution/support record.
2. Refresh health/ISR and literal group ownership/membership/offsets immediately before launch; establish the controlled execution window and avoid competing group use. Metadata is not a lock.
3. Complete the final C3/C6/C7/C4 source/support/custody record using existing reviewed native/build evidence; bind the startup-inclusive deadline, external stop and late-offset disposition, independent export/auditor and accepted seven-day/shared-workspace custody procedure. Actual post-run reconciliation/export will be acceptance obligations, not already-completed results.
4. Obtain explicit bounded-client execution instruction, record authority/start clock, and prepare the reviewed immutable ConfigMap/Job changes. No real gate is closed solely by this document or by flipping flags. **R2 fixture acceptance remains NOT_RUN.**

No additional access credential or policy decision is required from the user to complete this readiness increment. No unanswered approval question is pending.
