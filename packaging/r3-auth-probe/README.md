# R3-02 AUTH probe — compiled and disabled

**R3-AUTH-SRC-02 resolved in source; compilation PASS; runtime NOT TESTED or qualified.**

The classifier now reads a correlation-checked Kafka authentication response over CA/hostname-verified TLS. Only numeric broker error58 after the SCRAM client-final proof can establish rejection. Local exceptions and wrong-layer failures cannot pass. The same pinned SDK SCRAM/protocol path runs valid-before/wrong-password/valid-after; positive controls verify the server signature and own-topic metadata with auto-creation false.

- [Current design, bounds, review and deployment steps](classifier-review.md)
- [Compilation/source evidence](evidence/classifier-review.json)
- [Disabled profile](profile.disabled.json) and [inactive suspended Job package](disabled/resources.yaml.disabled)
- [Previous compilation review](compile-review.md), historical exception-stack blocker and SDK/image provenance

No producer/consumer, group, offset or mutating operation. No new image dependency or active GitOps root. The proposed Job remains suspended; execution/deployment and external notifications remain disabled. Authority, run/window and approved profile SHA remain unset. Existing four client Jobs and R2 resources are untouched. Runtime behavior, containment, mount/TLS/network readiness and fresh image identity are not established by compilation. Do not arm this candidate without the remaining authorized validation and bounded-run preparation described above.

Only sanitized results may be retained; password is supplied via anonymous stdin. Existing three-process supervision, stdout/stderr limits and client90s/phase20s/Job120s bounds remain. Result-file observation alone never passes: timely normal exit0, expected phase sequence, matching stdout/termination/files, pinned identity and exported evidence are required. Memory emptyDir is not durable evidence storage; reuse the accepted seven-day sandbox/export custody policy. Lost or conflicting evidence is nonpassing.

`prepare_disabled.py` reproduces inert files only. Original preparation, source references and publication receipts are historical; their old stack classifier/uncompiled states are superseded by the current review, not retroactively reported as tested. No test, build-container, deployment or notification follows automatically.
