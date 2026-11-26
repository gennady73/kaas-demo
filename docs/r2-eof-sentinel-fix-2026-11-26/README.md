# R2 EOF sentinel correction — offline checkpoint

The preceding incomplete image/build/retest checkpoint is published at `dce30cff87b92d979846a8c5d90fbf3c2c7f7368`. The user authorized publication of this correction and its offline evidence. The owning Git commit identifies the published snapshot; original validation receipts retain their historical local/uncommitted status. This correction is validated offline only. R2 acceptance remains incomplete. No cluster access, image build, deployment or live test occurred during this correction. Both client Jobs were untouched; their last saved API states are suspended.

## Source condition and correction

The pinned Confluent Go/librdkafka 2.14.0 SDK constructs `PartitionEOF` from a partition-level event and copies its nonzero error field. The prior implementation rejected every non-nil EOF error. Normalize a typed, nonfatal `ErrPartitionEOF` only inside a validated actual `PartitionEOF` event, then retain the existing assignment and offset checks. Nil-error EOF remains supported. Text lookalikes, authorization/transport errors, fatal EOF, foreign topic/partition, negative offsets and standalone error events remain rejected. No producer canary or guessed position is introduced.

Cached primary source inspected: `kafka/event.go` (EOF conversion), `kafka/kafka.go` (`setupTopicPartitionFromCrktpar`) and vendored `rdkafka.h`, all from `github.com/confluentinc/confluent-kafka-go/v2@v2.14.0`. Paths and hashes are recorded in `primary-source-inspection.json`. The actual live event was not captured in the previous attempt: this closes a demonstrated source condition, while confirmation against the broker remains pending.

## Executed offline validation

- Full helper: seven binding, 32 review, 18 sink/export checks, 20 top-level Go race tests, native compilation and public `k6 inspect` passed.
- New regressions cover direct/wrapped typed SDK EOF, nonzero offsets, forbidden error shapes, standalone errors and invalid topic/partition/offset. A temporary reject-all-non-nil control fails the new SDK-shaped regression as expected.
- Synthetic evidence replay passed with 182 events and 16 reported commits; these are synthetic, not broker deliveries.
- Four additional local synthetic k6 exit checks passed: legacy throw exits zero, incomplete/error abort exits 108, success exits zero. These stub dependencies and do not construct Kafka clients or use HTTP.

Go 1.26.4/CGO, k6 1.7.1 and SDK/librdkafka 2.14.0 were used with module network lookup disabled. Full-helper command:

```sh
python tests/tenant-r2-native/check_offline.py \
  --go /home/gunger/go/pkg/mod/golang.org/toolchain@v0.0.1-go1.26.4.linux-amd64/bin/go \
  --output /tmp/kaas-r2-eof-sentinel-offline-20261126
python tests/tenant-r2-native/test_exit_offline.py \
  --binary /tmp/kaas-r2-eof-sentinel-offline-20261126/k6
```

The full helper itself does not execute k6 iterations; the separate exit suite executes local synthetic iterations only. Receipts, source fingerprints, logs and the expected-failure control are retained alongside this guide.

Candidate executable SHA256: `e0294b2a2916408eb61805fbbeffcf785066c75105f665b61c325e7401ee3be3`. The binary remains outside Git under `/tmp` and can expire. The public JavaScript runtime manifest is unchanged: `a8ff40449e28da9f46aded0bca19b669c4d5dc8c2fa53fc5fc3d9e396270877e`. All 41 source fingerprints match the new offline receipt.

## Remaining finite step

The actual image pin remains `sha256:d82a1444de832a824a135d66eef9c7486d8587299b54b5c490bccc194c42dabe`; it does **not** contain this newest correction. `next-build-inputs.json` is disabled and has no candidate image digest. A verified revised image and an explicitly authorized bounded broker retest remain before R2 acceptance. No new readiness cycle or automatic retry is implied. R2-LIVE-02 remains live-confirmed fixed; R2-LIVE-01 is corrected offline but remains open for live acceptance. Both historical incomplete exports, their seals and custody records are preserved.
