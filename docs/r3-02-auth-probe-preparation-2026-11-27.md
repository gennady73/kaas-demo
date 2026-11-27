# R3-02 AUTH diagnostic readiness

**Source blocker resolved offline; compilation PASS; not deployed or tested.**

See the [current classifier review and remaining deployment steps](../packaging/r3-auth-probe/classifier-review.md) and [bound compilation evidence](../packaging/r3-auth-probe/evidence/classifier-review.json).

The candidate replaces unavailable exception-origin stacks with a direct correlation-checked SaslAuthenticate response over verified TLS. Only numeric error58 after SCRAM client-final proof establishes broker rejection. It uses the same pinned SDK SCRAM/protocol path for both positive controls and the wrong password; positive authentication includes server-signature verification and exact own-topic metadata without auto-creation. This is not AdminClient/xk6 exception mapping qualification.

Package remains disabled, with no authority/run/window/profile approval. All four previous client Jobs stay protected/suspended; external notifications disabled. No test or cluster change occurred. Before a bounded run: publish the revision, obtain authorization for remaining behavioral validation, refresh applicable live readiness and freeze the unique approved run package. No repeated R2 payload fixture or24-hour soak is required for this source correction.
