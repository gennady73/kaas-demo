# R2 native wiring and tenant evidence candidate

Revision 0.1, 2026-11-25. **Implemented locally; client tests, deployment and automatic sync remain disabled.** This additive package preserves the accepted offline adapter, its source contract and the existing smoke/continuity clients and collector. It requires a new reviewed image: the historical `f66c3f8…` image does not contain `k6/x/kaasr2`.

`entrypoint.js` joins the projected 16-record/eight-negative fixture, `binder.mjs`, an additive Go module and the dedicated tenant evidence transport. No `runtime.json` is shipped. The disabled example rejects before credential reads, HTTP or native client construction. Enabling the old offline flags cannot activate this package. The native projection retains the original disabled source contract, links its compiled-plan hash and explicitly declares the changed native settings. Review hashes inherited from that contract describe the original offline review, **not acceptance of this changed source**.

## Native boundary

`native/module.go` registers `k6/x/kaasr2`, using k6 1.7.1 and confluent-kafka-go 2.14.0 directly. The existing `k6/x/kafka` wrapper was not edited. Its error/logging surface and missing explicit native controls were the reasons for the separate boundary; this remains an xk6 solution using the same Go/native Kafka client family.

| Concern | Implemented mapping | Evidence boundary |
| --- | --- | --- |
| Credentials | Four fixed principal → mounted password paths; public Kafka CA path; values stay in Go and never enter JS options or error envelopes | File/mount delivery and broker authentication not executed |
| TLS | SASL_SSL/SCRAM-SHA-512, certificate verification and hostname algorithm explicitly enabled, fixed internal bootstrap | Source/config checks; public CA dates observed; leaf SAN/chain and every advertised broker still untested |
| Producer | `acks=all`, idempotence=false, native retries=0, max in flight=1, compression=none, 3 MiB message limit, 5 s native message timeout | Same settings for all positive and negative writes; no topic/ACL change |
| Acknowledgement | Only a successful native delivery report acknowledges; enqueue success is insufficient; six-second wait timeout stays unresolved | No real delivery report captured |
| Errors | Actual `kafka.Error.Code()` plus fixed calling stage, allowlisted category and private JS error association | Synthetic native error values checked; no text matching or raw native messages/config logging |
| Consumer | `enable.auto.commit=false`, `enable.auto.offset.store=false`, explicit next-offset commit after durable receipt acknowledgement | No consumer constructed; commit/close behavior not runtime-qualified |
| Negative reads | Subscription/rebalance state checked after polling too; unexpected join/assignment or record fails; native commit additionally refuses cross-tenant/nonfixture topic-group combinations | Broker denials and membership behavior remain NOT RUN |
| Metadata | Read-only scoped Admin calls using the owning group/topic identities, complete group listing before description, retained/log-end/committed offsets, zero-member guard | Scoped native Admin access remains untested; separate existing broker Admin observation is saved |
| Clock/budget | Monotonic elapsed time anchored to a conservative recorded pre-Job timestamp, phase caps 45/90/90/45/30, no new native operations after 270 s, planned Job hard bound 300 s | Native synchronous commit/close cancellation is OPEN; overrun/forced termination cannot pass |

Explicit non-idempotence is a diagnostic fixture choice shared by the positive write controls. It avoids consumer-role writes being denied first at Cluster IdempotentWrite. It is not a production delivery recommendation; ambiguous outcomes are preserved and never retried by the application. No broker ACL is widened. The minimal fixture remains at most 20 distinct 1,000-byte originals, 20,000 original-attempt bytes and 300 seconds including startup/evidence/drain/shutdown. It does not exercise the separate 2 MiB ceiling.

The native engine is a separate derivative of `kafka-load-test/preflight/tenant/engine.mjs`. Changes include a k6-compatible pure policy import, a distinct mapping/mode/result, reviewed plan-hash gate, explicit native settings, an eight-second close reservation, metadata-call reservation, post-poll unauthorized membership checks and FAIL precedence for negative offset mutation during settlement. The frozen offline source is unchanged. The source diff is retained in C1's evidence directory for changed-source review.

## Durable evidence transport

The isolated `sink/` implements `kaas-tenant-evidence-v1`; it never opens the continuity database or accepts continuity registration. A future owner configuration binds one run ID/plan hash and distinct writer/owner token files. HTTPS is mandatory, TLS handshake and request reads are bounded, redirects are disabled in the sender, and diagnostics use fixed allowlisted errors. The sink requires a verified certificate/key and persistent database path supplied later; none is generated or deployed here.

`POST /v1/events` accepts only versioned, allowlisted event envelopes for `tenant_fixture`. Exact event JSON bytes and hashes are retained with sequential IDs and a hash chain. SQLite WAL + synchronous FULL commits before a matching nested `ack` is returned. Exact retries are idempotent; conflicting IDs, chain/hash/schema mismatches, storage exhaustion and writes after seal cannot receive success. The sender currently makes one bounded HTTP attempt; lost/malformed/mismatched ACK stops admission and prevents the subsequent Kafka commit. It does not infer rejection or resend a Kafka record.

Owner-only `/v1/stop` closes new `attempt_intent` admission; settlement evidence is still accepted. `/v1/seal` requires stop and freezes a stable ordered `/v1/export`, with byte hash/count/identity and terminal-presence evidence. A partial export may be sealed but never thereby passes. `verify_export.py` checks those bytes/identity/chain and deliberately leaves fixture acceptance and second-copy custody unassessed. The existing offline auditor is not silently relabelled for native events; independent native semantic auditing/review remains a gate.

Local process cuts before DB commit, after commit/before ACK return and after local ACK return, plus reopen/retry, conflicts, injected disk-full/read-only failures and export corruption are checked using disposable temporary stores. Handler requests are in memory; no live HTTPS endpoint was exercised. This establishes a local process/SQLite boundary, not target-volume, machine/power-loss or infrastructure survival. DEP-PERSIST-01 remains inherited.

Bounds: 1,024 events, 16 KiB event JSON, 32 MiB database/WAL threshold and 64 MiB minimum filesystem free space. These are admission limits, not measured storage reservations; JSON/SQLite/WAL/index/export overhead is separate. `pod-and-sink-contract.json` proposes resources and mounts only. No PVC, network allowance, Service, Deployment, Job, source inclusion or billing allocation was created. The existing network preview intentionally lacks an unspecified evidence peer. Reuse the accepted seven-day sandbox evidence policy and shared-workspace exported copy recorded by C0; final allocation, support/custodian and verified second copy remain technical execution work.

## Checks and remaining join

From the shared workspace, the C1 validation tool runs **offline checks and `k6 inspect` only**, never `k6 run`:

```sh
python3 tools/c1_validate_r2_native.py
```

It uses the already cached Go 1.26.4 toolchain/dependencies, compiles a local binary, verifies actual Go-to-JS exported method names with `k6 inspect`, tests pure config/error values (no native clients), synthetic binding/ACK envelopes and isolated local SQLite/handler/export behavior, and checks original collector regressions and source preservation. Local binary compilation/import is distinct from a target image build/pull or broker test.

Current runtime gates remain false: frozen target-compatible image/package, C3/C6 changed-source review, independent native semantic auditor, credential/CA delivery and mount/SCC access, actual client-to-broker/sink TLS/network paths, final persistence/storage/custody join, cancellable native commit/close bounds and a concrete later execution record. Fresh topic/group metadata is an observation and must be refreshed at the eventual run boundary. No client test result is claimed.

Primary configuration semantics were checked on 2026-11-25 against [librdkafka 2.14.0 configuration](https://github.com/confluentinc/librdkafka/blob/v2.14.0/CONFIGURATION.md), with API behavior checked against the pinned local Go module source and [Confluent's Go API documentation](https://docs.confluent.io/platform/current/clients/confluent-kafka-go/index.html). Exact source hashes/line mappings and executed commands are in `docs/environment/r2-native-wiring-2026-11-25/` in the shared workspace. No independent review is claimed by this implementation.
