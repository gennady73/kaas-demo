# R3-02 AUTH probe: current compilation review

**Compilation passed; R3-AUTH-SRC-02 blocks execution.** See the [current source/SDK/image review](../packaging/r3-auth-probe/compile-review.md). Exact SDK4.2.1.redhat-00003 pins are populated; origin classification remains fail-closed. No tests or deployments occurred. The following preparation entry is historical and superseded where noted in that review.

## Original preparation

[Candidate source, disabled configuration and limits](../packaging/r3-auth-probe/README.md) implement only the selected AUTH subcase: wrong Kafka password bracketed by valid-credential own-topic metadata controls. No existing R2 fixture or runtime is changed.

- Three cold Java Admin processes; only the password differs for the negative phase.
- SASL_SSL, verified CA and hostname, SCRAM-SHA-512; no producer/consumer, group, offset or mutation API.
- Typed broker-response SASL failure required; wrong-layer, local, timeout or unproven outcomes cannot pass.
- Wrong password stays in RAM/anonymous stdin. Only sanitized enums/results, no credentials or raw SDK diagnostics.
- Distinct proposed Job remains suspended; immutable mounted profile has execution/deployment disabled and live/SDK pins unset. External notifications disabled; four existing Jobs untouched.

Preparation includes source, source lock, inactive four-object manifest and proposed90s client/20s phase/120s Job bounds. Static inspection was performed; **no Java compilation, tests, probe execution, image/cluster/Secret access or deployment**. The existing pinned R2 image is a candidate toolchain only; exact Java jar/version/hash, classification/containment behavior, per-run authority and live readiness still need verification before execution. This does not qualify runtime AUTH or all R3-02.

Current result: [preparation receipt](../packaging/r3-auth-probe/result.json). The owning commit publishes this preparation only; no test, deployment or further live action follows.
