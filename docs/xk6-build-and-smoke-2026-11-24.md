# Custom xk6 build audit and smoke rerun — 2026-11-24

## Build audit conclusion

The inspected custom source supports configurable message limits. **The Docker Hub image used in the failed November 23 test did not contain that custom size reader.** This was a build/source mismatch, not evidence of an inherent xk6 inability to handle 2 MiB values. **The rerun passed with the rebuilt custom xk6:** all 16 records acknowledged and delivered, including 2 MiB on each of four topics, within 268 seconds. Independent reconciliation passed with no missing/duplicate/checksum errors.

| Inspected input | Identity / finding |
| --- | --- |
| GitHub workload project | `gennady73/kafka-load-test`, HEAD `f7ea2a3496362214db6b44ff9d37b853244b5c9d`; local tracked files clean, C2 `preflight/` remains separate/untracked and unchanged |
| Actual custom Go source | `/home/gunger/Projects/xk6-kafka`, upstream HEAD `85fb8f25cecd85506d078b75219ce3a82f18791a`; pre-existing uncommitted edits in confluent_config.go, producer.go and writer.go; original checkout left untouched |
| Old image | `docker.io/gennady73/k6v2ubi9@sha256:9d924b0bff1afd5a42ddad8f2b10cc31a9c0c15af09be1c9699778eef36a1421`; both `latest` and `0.0.5` resolved here during inspection |
| Old binary | SHA-256 `81d82612432e8d59d5cd6fdf7af585e057b1dcb32c14d47fce5a5a653bc83dbb`; k6 1.8.1, Go 1.26.5 Red Hat, extension replaced by local `/opt/app-root/src/xk6-kafka` development module; no source commit recorded |
| Binary mismatch evidence | Old executable lacks literals `XK6_KAFKA_MAX_BYTES`, `/script/kafka-client-limits.txt` and the custom reader symbol; contains the old full-config debug printer; original runtime config dump had no larger message.max.bytes entry |
| Corrected binary | SHA-256 `6c705c09c17c9773158ef08d4446531855d37ab0b20ad5aaee41decd949604ec`; k6 **1.7.1**, Go **1.26.4**, CGO enabled; pinned to the inspected source's go.mod, deliberately different from the mutable old image's k6 1.8.1 |
| New sandbox image | `image-registry.openshift-image-registry.svc:5000/kaas-demo/kaas-xk6-verified-20261124@sha256:f66c3f86f2365b219c590d1d3c580ea41fcc4ab2ba74fc1efb2ae72d93be0df2` |

The workload project's Dockerfile imports `./xk6-kafka` from a local `shared-context` and updates dependencies to `latest`. The custom Go files are not embedded in that GitHub repository; its commit therefore cannot prove the source content used in a published image. Exact old-image source provenance remains unavailable. Image labels inherited from UBI describe the base, not the custom extension commit. This audit does not claim a bit-for-bit reconstruction of the old build.

## Source/configuration mapping

The custom source reads `/script/kafka-client-limits.txt` first, then `XK6_KAFKA_MAX_BYTES`, otherwise defaults to **52,428,800 bytes**, once per process via sync.Once. The test file contains **3,145,728 bytes**, providing transport overhead room for **2,097,152-byte values**. This limit is a client setting, not a request for larger generated values. Changing the file after client initialization does not reload it in the running process.

A separate mismatch exists in the workload framework: it passes `CLIENT_MAX_BYTES` through `extraConfig`, whereas the inspected WriterConfig has no extraConfig field. That route does not establish the custom environment reader's value. Consumers' maxBytes maps to fetch.max.bytes; it is not the producer's message.max.bytes. No framework files or C2 adapter were edited in this task.

Two corrections were necessary in an isolated source copy: restore the missing fmt import used by writer.go, and remove Java-only `max.request.size` from the librdkafka ConfigMap. Native `message.max.bytes` is retained. Native `debug=msg,broker` was removed. Full connection-config printing was already commented in the current local source and remains disabled; a narrowly allowlisted line reports only final producer message.max.bytes and acks. No credentials or complete config are printed. Configuration names/default/native bounds were checked against [librdkafka 2.14.0 primary documentation](https://github.com/confluentinc/librdkafka/blob/v2.14.0/CONFIGURATION.md), accessed November 24. Configurable size does not mean unrestricted size: client, topic, broker, protocol and resource limits still apply.

Build preparation encountered host Go 1.27/toolchain and VCS-stamping issues. Selected the installed Go 1.26.4 toolchain, disabled VCS stamping for the temporary generated main, and retained actual source/dependency hashes instead. Resolved go.mod/go.sum are saved. This controls the evidence for this build, not reproducibility across arbitrary future dependency resolution.

## Executed checks before Kafka traffic

- Targeted native Go test passed: a 3 MiB environment input reached message.max.bytes, the invalid Java-only key was absent, and librdkafka accepted producer construction. No Kafka authentication or data traffic in that test.
- Sandbox binary image build completed successfully and pushed only to its internal registry. No Docker Hub or GitHub publication.
- A credential-free Job verified the runtime executable hash against the locally built binary and printed k6/Go versions. Its file was set to 3 MiB while the environment was deliberately set to 1 MiB; the final native producer configuration reported **3 MiB and acks=all**, proving file precedence in the actual container. It deliberately targeted localhost:1 and logged a connection refusal; this is not a Kafka-service failure or a delivery test.
- The independent evidence checker still accepts the historical complete Java log and rejects a fixture with one received-record event removed. These are offline checker checks, not additional Kafka runs.

## Execution/evidence boundary

Run `xk6smoke20261124c`, Job `kaas-demo/kaas-smoke-20261124-c`: four existing topics, one producer/consumer pair per topic, fresh group IDs; exactly 1 KiB, 64 KiB, 1 MiB and 2 MiB values per topic; 16 originals / 12,849,152 value bytes. Input baseline SRS 0.9 / DEV-SMOKE-01 contract 0.1. TLS CA/hostname verification and existing scoped SCRAM user; temporary namespace-local credential copy. No broker, topic, user CR, GitOps pin or operator upgrade change.

Producer `requiredAcks=-1` maps to native acks=all; source awaits native delivery reports and throws on delivery failure. The wrapper does not return acknowledged partition/offset. Therefore this rerun can reconcile each successful producer call with the exact ID/bytes/checksum received, and retain consumer partition/offset, but cannot claim Java-style acknowledgement-location matching or consumer offset commit confirmation. Native retries remain library-managed within the configured 10-second delivery timeout; the wrapper's MaxAttempts is not evidence of an enforced native retry count. Application attempts are one per ID. No exactly-once or crash-durability claim.

The Job has a 300-second active deadline, no retries/restarts; k6 maxDuration 285s and gracefulStop 0s. The script stops new sends by 180s, polling near 265s, then closes clients. The entire successful run, including startup and shutdown, must finish before 300s. This is a bounded functional case set followed by continued polling, not sustained throughput for five minutes. No fault injection or 24-hour load qualification.

Evidence directory in the coordinating workspace: `docs/testing/runs/xk6-20261124/`. It retains image/binary audit, original custom diff, isolated corrections, corrected extension source archive (upstream testdata/keys omitted), dependency metadata, binary hash, unit-test record, internal image BuildConfig/build receipt, credential-free probe, exact smoke ConfigMap/Job/cases, redacted captured logs, observations and reconciliation. Reviewable source corrections also reside in `kaas-demo/tests/dev-smoke/custom-extension/`. No passwords, bearer tokens or private keys are included. Images/build/test resources remain sandbox-scoped; temporary client Secret is removed after completion. The source archive includes the original source license.

## Final verified result

| Topic | Successful acknowledged sends | Unique verified deliveries | Largest value | Consumer partition / offsets |
| --- | ---: | ---: | ---: | --- |
| kaas-dev-smoke-01 | 4 | 4 | 2,097,152 bytes | 0 / 6–9 |
| kaas-dev-smoke-02 | 4 | 4 | 2,097,152 bytes | 0 / 4–7 |
| kaas-dev-smoke-03 | 4 | 4 | 2,097,152 bytes | 0 / 4–7 |
| kaas-dev-smoke-04 | 4 | 4 | 2,097,152 bytes | 0 / 4–7 |

**PASS**: 16 originals / 12,849,152 value bytes; zero missing, duplicates, checksum mismatches, unresolved producer calls or runner errors. Final marker reports clean shutdown. Four runtime producer lines each confirm message.max.bytes=3145728 and acks=all. All expected hashes were independently reconstructed by Python, and exact ID/topic/group/byte/checksum sets plus distinct consumer locations checked. The check does not infer producer-side offsets that the xk6 wrapper does not expose.

Job UID `09402267-32d0-4883-b994-a77860598c8c`; Pod `kaas-smoke-20261124-c-p2rqb`. Job start **2026-11-24 14:11:32 UTC (16:11:32 Asia/Jerusalem)**; container start 14:11:33Z, finish 14:16:00Z; Job Complete 14:16:02Z, exit 0. Client elapsed **266.453 seconds**; Job-to-container finish **268 seconds**; Job-to-Complete **270 seconds**. The supplied five-minute upper bound was met. The selected fixed-case budget is functional verification, not a capacity benchmark; the k6 summary's native-network data_sent/data_received=0 does not count extension Kafka traffic and must not replace the event/native Kafka byte counters.

The temporary Secret `kaas-demo/kaas-smoke-20261124-c` was removed and its absence verified. The prior regenerated source credential remains in the existing KafkaUser-managed Secret; no further rotation was needed or performed in this rerun, and no sensitive config dump appeared. Postflight Kafka Ready and all broker/entity containers Ready. Broker restart counts were 1/0/1 and entity containers 0/0; their timing was not captured by this run's preflight, so this report does not claim zero restarts or attribute these counts to the smoke test. No intentional restart/fault was introduced.

Independent reconciliation: `runs/xk6-20261124/reconciliation.json`; final environment/cleanup snapshot: `postflight.json`; machine handoff: `config/environments/xk6-smoke-result-2026-11-24.json`. Original November 23 Java PASS and old-image failure remain historical evidence. This result supersedes the statement that custom xk6 cannot deliver 2 MiB; it qualifies this specific corrected custom build for these functional cases only. The original Docker Hub digest is unchanged and remains unsuitable for this test configuration. Promoting corrected source/image to the user's normal GitHub/Docker Hub release process remains a separate action; no external publication or Git commit/push occurred here.
