> Portable publication copy. Source revisions and coordinator-only references are listed in the C7 publication provenance; historical results remain scoped to their original review dates.

# Deferred Helm packaging evaluation

Requirement C7-FUT-HELM-01, revision 0.1, 2026-11-25. Source: user's instruction to keep Kustomize now and evaluate Helm as an additional requirement after previous phases allow it. **Status: DEFERRED; evaluation required, implementation/design not selected.** No Helm command, chart generation or dependency download is part of this slice.

## Entry gates and owners

C0 records references to preceding applicable project phase (coordinator-only reference: `docs/chat-coordination-plan.md`; see publication provenance) outcomes and R0–R3 readiness/remaining-gap dispositions, identifies the selected target and permits this follow-on evaluation. Applicable deployment/client/service interfaces must be stable enough to compare packaging without changing the experiment or re-opening ownership. Active continuity resources remain protected. Current inputs, completion references and start window are OPEN. A successful 100MB continuity run alone does not satisfy all gates or select Helm.

C4 owns any later chart/template implementation and resource ownership. C7 evaluates release/support/recovery implications; C6 reviews authority/secret boundaries, C1 disconnected supply and versions, C3 evidence parity and qualification, C5 governance interfaces where included. No messages or assignments to other chats are sent by this record.

## Questions and acceptance for the later evaluation

| Area | Required evaluation evidence / decision |
| --- | --- |
| Purpose | Identify a concrete reuse/parameterization/distribution need not already adequately met by the existing Kustomize profiles; compare retain-Kustomize, additional chart packaging and a future replacement proposal |
| Scope/ownership | Decide which existing Kafka custom resources a chart would render; preserve the selected Streams operator lifecycle, bootstrap boundaries and one authoritative source/controller per resource; no parallel broker deployment introduced by assumption |
| Compatibility | Verify selected Helm/ArgoCD/operator/CRD versions and behavior against current primary docs and installed/source evidence at evaluation time; pin tool/chart/dependency/image versions and rendered configuration |
| GitOps/security | Describe source/value precedence, namespace/tenant content validation, manual sync authority, secret references, hooks, CRD handling and deletion/prune/rollback effects; verify effective behavior rather than assume chart rollback restores Kafka data |
| Air gap | Inventory chart dependencies and accessible internal distribution/mirrors, provenance/digests and reproducible offline rendering; reuse available artifacts before requesting missing ones |
| Parity | Compare reviewed rendered object identities/specs against the accepted Kustomize baseline for dedicated/shared profiles; test unresolved/invalid values, collisions, lifecycle and privilege regressions offline |
| Operations | Assess support burden, upgrade/rollback limits, release-matrix changes, migration/adoption risks and needed requalification; document consequences and alternatives |
| Decision | C0 records adopt/reject/defer with evidence and C4 implementation scope if selected. Runtime rollout remains a separately scoped change |

This is a requirement/evaluation backlog entry, not proof of selected-version Helm compatibility or of a supported chart already existing. Technical verification belongs to the later evaluation; the present work records scope, gates and acceptance only. Current [release procedure](release-runbook.md) continues to use Kustomize.
