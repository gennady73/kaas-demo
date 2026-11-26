# R2 bounded native fixture passed — 05a3f2d

**R2 bounded client-integration acceptance passed.** One user-authorized fixture ran, all16positive records and all8negative cases reconciled, and the separate evidence auditors passed. R2-LIVE-01/02/03 are closed for this bounded scope. No retry or additional fixture ran. The user authorized publication of these verified pins and successful results. The owning Git commit identifies the published snapshot; original execution receipts retain their historical publication status. All four client Jobs are suspended after confirmed process termination.

## Exact source, build and pins

Native/runtime source is `05a3f2dcb551c7aa7ed12b4108c7ef488113aed9`; all42fingerprints match the published offline receipt. The submitted runner archive had17entries, reopened and checked byte for byte. Only build recipe/receipt selection and manifest pins changed locally; the native/JavaScript implementation and frozen logical plan were unchanged. The sink source/schema/image were unchanged and the sink was not rebuilt.

| Item | Verified value |
| --- | --- |
| Build | `kaas-demo/kaas-r2-runner-05a3f2d-1`, Complete |
| Build interval | 2026-11-26 15:07:07–15:09:16 UTC |
| Runner image | `image-registry.openshift-image-registry.svc:5000/kaas-demo/kaas-r2-runner-05a3f2d@sha256:41f328c85ee3d3e9d8834ce12e516b5ef52506067117b1c4f1145511b493998a` |
| Binary SHA256 | `0174513d51947fb65aa17ae70f85fea19f7ed5a605aae0ca6d016d8e1cd94cc0` |
| Runtime-source manifest SHA256 | `07f7bd428716626f2d0ca3a229fd4d4d346c5a5a5ff8dff92fa119827ee27b59` |

The actual image build passed executable checksum and public `k6 inspect` native identity/import checks (SDK/librdkafka2.14.0). Build output, registry push log and ImageStreamTag agree on the digest. Actual test Pod imageID matches it. Disabled Job/runtime pins now use this image, binary and source manifest. Sixteen packaging regressions and the disabled contract validator passed before launch. Polling build completion timed out within one45second polling window while the build was still running; the same build subsequently completed, with no resubmission.

## Fresh precheck and isolated attempt

TLS-verified memory-only admin sessions were used; no default kubeconfig or credential file was written. Kafka, brokers and tenant CRs were Ready. Client-labelled metadata-only checks using the new image passed native identity, TLS/SCRAM, sink TLS, topic leadership/RF2/ISR2 and group readiness. Each of the four groups had zero members, committed offset4 and topic log end4. These were existing records from the preceding attempt; no topics, groups or offsets were reset.

Verified all three historical database exports against their saved seals read-only (event counts8,8,140) and left their Jobs suspended. A new immutable sink configuration selected `/var/lib/r2/evidence-05a3f2d-retest.sqlite` on the existing1GiPVC and single sink replica. No added PVC was allocated. Job `kaas-r2-native-client-05a3f2d-r2` and physical attempt `05a3f2d-retest-20261126` identify this fresh execution.

The frozen logical plan/record IDs remain `r2-native-20261125`. They repeat across historical attempts, so evidence is scoped by JobUID, database, export and starting offsets. Never merge attempt streams or claim global key uniqueness from this run's receipt counts.

## Single bounded execution and accounting

Job start: **2026-11-26 15:11:40 UTC**. Container finish: **15:12:05 UTC**. Native reported result duration25,446ms (terminal event25,439ms); conservative external completion observation29,528ms. Exit0, JobComplete, NATIVE_COMPLETE, no forced stop or retry. This was one bounded iteration completed within the300second maximum, not five minutes of sustained load. Job, native-process and external stop bounds remained active; their timeout paths were not exercised.

| Topic | New acknowledged / received / committed | Receipt offsets | Final log end / committed offset / members |
| --- | --- | --- | --- |
| `kaas-sbx-a-events` | 4 / 4 / 4 | 4–7 | 8 / 8 / 0 |
| `kaas-sbx-a-audit` | 4 / 4 / 4 | 4–7 | 8 / 8 / 0 |
| `kaas-sbx-b-events` | 4 / 4 / 4 | 4–7 | 8 / 8 / 0 |
| `kaas-sbx-b-audit` | 4 / 4 / 4 | 4–7 | 8 / 8 / 0 |

All16newpositive IDs/checksums match their receipts, durable receipt acknowledgements and manual commits. There are no missing positive records, duplicate receipts within this attempt or uncertain commits. Independent post-run Admin snapshots confirm log ends8, commits8 and zero members for all four groups. The four-record per-topic increase exactly matches the authorized positive sends.

All eight negative cases passed with typed broker denials and their positive controls:

| Tenant | Case | Denial / stage |
| --- | --- | --- |
| A | Cross-topic write | Topic authorization / produce |
| A | Cross-topic read | Topic authorization / consume |
| A | Cross-group read | Group authorization / consume |
| A | Consumer-role write | Topic authorization / produce |
| B | Cross-topic write | Topic authorization / produce |
| B | Cross-topic read | Topic authorization / consume |
| B | Cross-group read | Group authorization / consume |
| B | Consumer-role write | Topic authorization / produce |

Original value-byte accounting is complete: **20,000attempted =16,000acknowledged +4,000definitively rejected**, zero unresolved, zero planned/unattempted. Protocol, replication and evidence traffic are excluded. No forbidden write increased a topic log. No unexpected record/access event occurred; negative paths made no offset commit. Group-state snapshots correctly observed each group's established fixture partition at offset8before/after negative cases, preserving group membership/offset checks without forbidden-topic Admin calls. They do not directly describe committed offsets for every forbidden topic/group pair.

## Evidence and final state

Owner stop/seal/export produced182events, terminal present. Export SHA256: `18ba064608624da60e80101aaea81af9f0e8bfe9f4edbed126cc5903dd66c96e`. Workspace bytes match the sink seal. Python byte/hash/chain verifier exits0/VERIFIED; separate JavaScript semantic auditor exits0/NATIVE_EVIDENCE_MATCHED, fourpositive/eightnegative cases matched and no issues. Its accounting, minimal isolation matrix, duration, evidence and cleanup dimensions pass. Those offline auditor outputs alone do not attest live execution; exact-image Pod/controller observations and independent pre/post Admin metadata supply runtime provenance. This is separate validation tooling, not an invented independent specialist signature.

After confirmed process termination, suspended the new Job. All four Jobs are suspended:

- `kaas-r2-native-client`
- `kaas-r2-native-client-02e2e2f-r2`
- `kaas-r2-native-client-351528d-r2`
- `kaas-r2-native-client-05a3f2d-r2`

Native cleanup reports all handles closed. Sink is1/1Available, PVCBound, and this attempt's evidence is stopped/sealed. Temporary metadata Pods/ConfigMap were removed. Previous data/Jobs and all three prior sealed exports remain preserved. No message/topic/group/offset deletion/reset was performed.

Retain the sandbox PVC plus verified shared-workspace second copy through at least **2026-12-03 15:12:05 UTC**, following the accepted seven-day policy. Sandbox lifetime remains external; no cleanup automation was created. Full orchestration, exact per-run configuration, observations and custody files are in shared `docs/testing/runs/r2-native-05a3f2d-retest-20261126/`. Sanitized portable results and receipts accompany this guide; no password/private-key/token values are exported.

## R2 closure and next sync

`r2-closeout.json` records acceptance of the reviewed **16positive/eightnegative bounded native fixture**. R2-LIVE-03 is now live-confirmed fixed; R2-LIVE-01/02 remain closed. This completes the bounded R2 loop and supplies evidence for the C1–C7 joins and next R3/SP5service-qualification planning. No further generic readiness/test cycle is needed for this closed fixture.

This result does not qualify the full96caseACLmatrix, hostile Secret isolation, 2MiBpayloads, capacity, recovery, full24hcontinuity or production service. Native source baseline labels remain frozen historical build inputs; this execution record supersedes their untested status for this scope only. Baseline deployment/execution flags remainfalse, Job suspended, automatic sync disabled, and the single run's authority consumed. Further live work requires a new scoped user instruction; no R3execution occurred here. Publication authorizes no further live test.
