# R2 native image build results — 2026-11-26

**BUILT_AND_VERIFIED; CLIENT_AND_SINK_DEPLOYMENT_DISABLED; TESTS_NOT_RUN.** The user authorized building/verifying both images and recording digest pins. The user authorized Git publication of these pins, manifests and evidence on 2026-11-26; the owning commit identifies the published package. Images were pushed only to the sandbox's internal registry.

| Image | Completed build | Immutable manifest digest |
| --- | --- | --- |
| Client | `kaas-demo/kaas-r2-runner-1` | `sha256:dec50714130f1244403f8bb1a79847dc28821b7e87a02507bbd923d081fe2d8d` |
| Evidence sink | `kaas-demo/kaas-r2-sink-1` | `sha256:f730c89baceda0f8a536ab9c94696b768c996fe55d60202300095b4d450efa25` |

The full references in `inputs.json` and `deploy/resources.yaml` use `image-registry.openshift-image-registry.svc:5000/kaas-demo/kaas-r2-{runner,sink}@<digest>`. The disabled runtime ConfigMap also pins the client digest. Candidate tags are build output labels; runtime references use digests. These registry URLs are sandbox-internal, not production mirrors.

## What executed

Authenticated as admin with trusted TLS and a memory-only kubeconfig; session closed without storing credentials or changing the default context. Inspected existing namespace resources and quota/limit definitions (none listed). Created only the two manual BuildConfigs and two output ImageStreams from the prepared build package, then submitted two binary archives sequentially. No client/sink manifest, Secret, evidence PVC or GitOps registration was applied.

Both builds pulled the pinned Kafka/RHEL9 base successfully. Client build ran 11:32:46–11:35:02 UTC (136 seconds); sink build ran 11:35:28–11:36:51 UTC (83 seconds). Each completed within its 600-second build deadline. Some 45-second observation waits expired while builds were still progressing; neither build failed or required retry. BuildConfigs retain empty triggers and source `Binary`; no recurring/image-triggered rebuild was enabled.

The client archive exactly matches the previously verified context (`6545ef4d7160b898b154ec4c665dd1f9f95011544e1713a72f2057ea7d94a534`). The sink Dockerfile was strengthened to import the actual `server`, `store` and `verify_export` modules alongside SSL/SQLite, without invoking their main functions. Its resulting context hash is `ff3c5fd6c0f5ba4a32b5c59640387ccf0709154043c7a6b9ff105507598852f6`. Native source and executable remain unchanged. Exact recipes, source hashes and archive entry verification are retained in `validation/image-build/build-contexts.json`.

## Image verification evidence

- Client build verified `/usr/local/bin/k6` SHA256 `7405cc006c1d05d2748aee1955bfd3db6e3edf4e6f723dd997e060bd22c6525b`. Its `k6 inspect /r2/inspect.js` loaded the native extension, engine/binder/transport/auditor imports and reported matching executable identity, native version `2.14.0` and mapping `KAAS_R2_CONFLUENT_2_14_V1`. Inspection constructs no Kafka client and runs no test iteration.
- Sink build reported `R2_SINK_MODULE_IMPORT_OK` after importing SSL, SQLite and the three actual sink modules. No server listener, database, credential file or evidence endpoint was opened by this verification.
- For each image, completed Build output digest equals ImageStreamTag image identity and final registry-push log digest. Metadata reports `amd64`, final user `1001:0`, `/tmp` working directory and the expected explicit guard entrypoint. Reported image sizes are 446,645,955 bytes client / 371,338,554 bytes sink; these are image metadata sizes, not added billable disk usage or new-layer totals.
- Builder metadata represents `CMD []` as `['/bin/sh','-c','null']`. The explicit guard entrypoints ignore positional arguments, so that representation does not launch the inherited Kafka command or a shell from the guard. No separate final-image container execution was performed. Arbitrary OpenShift UID/SCC, volume permissions, effective networking, TLS credentials and actual client/server operation remain unverified.

Full build records, logs, ImageStreamTag metadata and summarized results are under `validation/image-build/`. Parent coordinator raw snapshots are under `docs/reviews/r2-images-2026-11-26/` in the shared workspace. They contain no credential values. The previous `validation/validation.json` and `validation/publication-checks.json` remain historical preparation/publication receipts, including their earlier NOT_RUN image status and 16-test results; those tests were not repeated here.

## Disabled state and limits

Local Kustomize render contains 11 objects. Client Job remains `suspend: true`; sink Deployment remains `replicas: 0`, `paused: true`. Immutable arming remains false, both runtime authorization flags remain false, authority/start clock remain null and all 11 execution gates remain OPEN. Image identity is now populated; it does not grant execution authority. Inputs retain execution/deployment/workload/build enable flags false to prevent automatic future action. No active GitOps root includes this package.

Before/after namespace snapshots show the same 17 Job/Deployment objects, identical UIDs and specs. Neither the R2 client Job nor sink Deployment exists in those snapshots. Build Pods are the only new compute used by this work. No evidence PVC allocated, no Secret values read, no client/sink deployed, no sync or test performed.

`validate.py` was adapted to accept exact nonzero verified digest pins while continuing to require disabled flags. Its syntax and mapping were inspected; it and the regression suite were not executed in this increment, respecting the instruction not to run tests. Static YAML/JSON parsing, matching image/runtime pins, disabled-state checks, local Kustomize render and Git whitespace checks succeeded. See `disabled-and-workload-proof.json`.

## Remaining before the bounded test

After publication, complete create-only credential/Kafka-CA delivery, separate sink writer/owner credentials and service TLS/trust; accept/provision isolated evidence storage and verify custody/export; validate actual SCC/UID/filesystem/network/registry access; refresh Kafka health/ISR and exclusive group membership/offsets; complete final C3/C6/C7/C4 deadline, late-offset, support/stop and per-run authority records. Final-image runtime verification must occur within the next authorized activation step. No additional owner policy answer is required for this completed build increment. **R2 live acceptance remains NOT_RUN.**
