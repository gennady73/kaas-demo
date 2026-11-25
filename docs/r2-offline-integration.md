# R2 offline integration publication

2026-11-25. **Source publication only. Deployment, automatic sync and workloads remain disabled.** R1 resource commit3211df93ae40d7d6f47c6334966ae6d1f658fee7 remains the tenant resource pin. No ArgoCD source, Application, cluster, credential, policy or workload was changed by publication.

## Published parts

- [Credential and mount preparation](../tests/tenant-r2-preparation/README.md): four role-specific Secret references, public CA reference, create-only delivery tool and un-applied ServiceAccount/NetworkPolicy previews. No credentials were read/copied. Default delivery invocation is offline; do not invoke its explicit delivery flag without later authority.
- [Disabled integration package](../tests/tenant-r2-integration/README.md): validated bound/role/mount contract, suspended Job preview, always-refusing entrypoint, isolated reference SQLite sink, regressions and fake-engine-to-independent-auditor replay.
- [New native draft](../tests/tenant-r2-native/README.md): additive `k6/x/kaasr2` module, projected engine/binder, tenant sink and build/test sources. This is **unqualified candidate source**, not an approved native release or tested image. No `runtime.json`, client Job or activation Application is shipped. The disabled runtime example is not authorization. Prior C3/C6 offline acceptance does not cover this changed native runtime.
- [Historical prepared source bundle](r2-offline/prepared-source-bundle.tar.gz) with [entry hashes](r2-offline/prepared-source-bundle.json): frozen earlier offline increment; it deliberately excludes the newer native draft. Its SHA256 is18d1d8be8c26164e03e0e8391a3cec140d0b959e5393ee7344087621ba45e84b. It is not the complete current repository snapshot or a runtime image.
- The corresponding utility repository publishes `preflight/tenant/` (accepted offline adapter/auditor/fakes/CLI) and `preflight/tenant-native-candidate/` (supplemental pure options/codec/error/config probes). Exact cross-repository pins are recorded in [publication validation](r2-offline/publication-validation.json).

## Bounds and evidence policy

Two tenants/four topics/four role principals;16positive originals×1,000bytes, four possible negative writes and four negative reads. Maximum20,000original attempted value bytes and300seconds total across startup45, positive90, negative90, reconciliation45 and shutdown30. One application send per ID; wire retries/replication/evidence bytes are separate. No group reset/delete, new group suffix, ACL widening, destructive cleanup or automatic retry/restart. This is not full namespace isolation,2MiB, fairness, full-day/TB or recovery acceptance.

The user accepted seven days of sandbox evidence retention and an exported copy in the shared project workspace, proposed at `docs/testing/runs/<run-id>/`. Actual export/checksum verification and retention disposition are future execution work; this does not extend temporary credential retention or create a recurring automation.

## Reproduce offline checks

Clone kafka-load-test beside kaas-demo and select the utility commit from the publication validation record. From kaas-demo:

```sh
python tests/tenant-r2-integration/validate.py
python -m unittest discover -s tests/tenant-r2-integration/tests -v
python -m unittest discover -s tests/tenant-r2-preparation -p test_delivery.py -v
node tests/tenant-r2-native/test-binding.mjs
python -m unittest discover -s tests/tenant-r2-native/sink -p 'test_*.py' -v
python tests/tenant-r2-integration/replay_offline.py \
  --utility ../kafka-load-test \
  --contract tests/tenant-r2-integration/inputs/client-contract.json \
  --c3-review tests/tenant-r2-integration/inputs/C3-offline-review.txt \
  --c6-review tests/tenant-r2-integration/inputs/C6-offline-review.txt \
  --output /tmp/r2-publication-offline-NEW
```

Use a new output directory. These checks use synthetic credentials/events, temporary local SQLite stores and local handler tests; they do not access OpenShift or a Kafka broker. Go native-module unit tests need the pinned Go1.26.4/CGO dependencies; use `go test -mod=readonly -count=1 ./...` from `tests/tenant-r2-native/native`. No clients are constructed by those unit tests. Do not substitute `k6 run` for source inspection/import checks.

Publication checks rerun the accepted adapter's125tests,45supplemental native-contract tests,27disabled-package/reference-sink tests,9delivery tests and the native draft's binding/sink/pure-Go tests. Counts and source fingerprints are saved in the validation record. The offline replay must reconcile182envelopes. Pure native error objects/configuration, synthetic binding tests and local persistence checks are distinct from actual broker results.

## Before any live run

Finish/freeze the final native build/image and independent native semantic auditor; obtain changed-source C3/C6 review; close cancellable commit/close and startup-inclusive deadline bounds; select the actual authenticated/TLS tenant sink, storage/resources/network peer; deliver approved credentials/CA with readable SCC mounts; collect exclusive literal-group baselines and applicable fresh health/admission/image/network/trust evidence; complete support/export and exact execution authority. Source publication closes none of those runtime gates. Native result remains NOT_RUN.
