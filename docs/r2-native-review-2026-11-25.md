# R2 native source review and offline build

2026-11-25. Reviewed candidate5e29d34 against C3 native ND-01–04 and C6-R2-01–08. Corrected candidate1.1 remains **deployment/workloads disabled**, with no runtime.json and all actual execution gates OPEN. This publication contains source and offline tools only; no runtime or production PASS is claimed.

Corrections include: reproducible full-plan/source/executable pins; fixed/redacted native invocation/resource/record boundaries; all-input preflight; exact bounded evidence retry and settlement after stop; semantic native auditing with the C3 phase-timing correction; strict JSON/schema/authentication edges; bounded commit/close/metadata facade waiting with quarantine and uncertain late completions; explicit synthetic evidence provenance. The separate native auditor declares reported-event matches, not actual broker provenance. Original accepted offline/continuity sources are preserved.

Offline checks pass:7binding+31focused review+18local sink/export tests and10top-level Go race tests.182fake-engine events pass the actual local SQLite protocol, byte export verifier and separate semantic auditor, reconciling16reported commits. No Kafka clients, cluster/Secret access or k6 run. Go1.26.4/CGO builds k6v1.7.1 with linked librdkafka2.14.0; k6 inspect verifies Go/JS imports and the actual executable fingerprint.

Binary SHA256:7405cc006c1d05d2748aee1955bfd3db6e3edf4e6f723dd997e060bd22c6525b. Public runtime manifest SHA256:d26b13cbc6e96bc56625adc26467b95a5a09cd011f525b9b6bb4ed8376ec93c0. Projected plan SHA256:78e427f79f510efe87834000371584394fc44ccd0ed4e0a903f919d31edca13d. Build is local; target image import/compatibility remains untested.

From the shared workspace:

```sh
python kaas-demo/tests/tenant-r2-native/check_offline.py \
  --go /path/to/go1.26.4/bin/go --output /tmp/r2-offline-review-NEW
```

Both repositories must be sibling checkouts; the utility source remains888276c. The output directory must be new and outside source. This command has no execution/arming switch. Source compilation/manifest generation does not create runtime.json. Hashes must be regenerated/reviewed if source changes.

SDK cancellation is still unproven: a6s facade timeout is not cancellation; a late native commit can finish. Quarantine refuses further mutation/concurrent close; a real external process deadline and final-offset observation are still required. Metadata facade waiting is8s. Actual scheduling/cold start, real broker behavior and whole-case timing remain open; timeout means incomplete, not a larger budget.

Before the bounded test: publish/freeze corrected source, build/pin/import-check the target image, prepare real client/sink manifests, complete credential/CA/SCC/network/resource and isolated storage joins, refresh health/ISR/exclusive groups, record deadline/stop/custody and exact live authority. Keep16positive originals/eight negatives/20,000original-attempt bytes/300s. Accepted evidence retention remains seven days in sandbox plus shared-workspace export; actual export verification/disposition are future work. No further user policy input is needed for this offline increment.

Full coordinator review/decisions, command logs and exact-source receipt are retained in the shared workspace at docs/reviews/r2-native-2026-11-25/; final-build-v2/ is the authoritative final check, not earlier proof attempts. This is an agent source/test review, not independent human or automatic owner sign-off.

Retained published receipts: [offline build/source validation](r2-native-review/offline-build-validation.json), [C3/C6 traceability](r2-native-review/requirements.json), [review snapshot](r2-native-review/review-summary.json) and [pinned SDK inspection](r2-native-review/sdk-inspection.json). The review snapshot's local/unpublished field is historical; the Git commit containing this guide supplies publication identity.
