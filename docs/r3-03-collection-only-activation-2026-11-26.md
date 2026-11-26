# R3-03 collection-only activation package

This publication contains prepared configuration, prerequisite evidence and accepted decisions. It does not register an Application, grant permissions, sync resources or open the live change window. Email routing, all new live alert rules and producer/consumer tests remain disabled. All four existing client Jobs must remain suspended.

Start with the [execution overview](../qualification/r3/r3-03/activation-execution/README.md), [current selection](../qualification/r3/r3-03/activation-execution/selection.disabled.json), [prerequisite review](../qualification/r3/r3-03/activation-execution/prerequisites/README.md), [resource projection](../qualification/r3/r3-03/activation-execution/prerequisites/resource-verification.json) and [progress overlay](../qualification/r3/progress.json). The original plan remains pinned to `c1096073ca79dec38c3e7f1c96a436591359c31c`.

## Current disposition

User accepted persistent monitoring: two10Gi Prometheus claims plus two2Gi Thanos Ruler claims,24Gi total;24h metric retention; extra planning allowance1250mCPU/6656Mi steady and1750mCPU/9728Mi total during change;90minute window budget and disclosed broker rollout impact. Selected collection-only stages A0/A1/A2/A3/A7 total75planning minutes with15minutes slack. This is not a runtime guarantee. User is responder/custodian, explicitly no backup for sandbox. Email was explicitly deferred; future destinationgunger@redhat.com is retained. A4–A6 and notification qualification remain deferred, not passed.

Verified prerequisites include four resource server dry-runs, exact installed CMO image/packaged asset identity, eight controller access reviews, memory-only sanitized Alertmanager inspection and four suspended/inactive client Job observations. Conservative UWM projection821mCPU/5794Mi fits the accepted allowance. Actual generated Pods, injected resources, storage binding and footprint remain A1 exit checks. The sealed R2 result and active runtime source/pins are unchanged. Prior10rule parse/12fixture receipts describe local checks, not live alert evaluation.

## What this commit makes available

- Disabled platform ConfigMaps for persistent user-workload monitoring and its enablement.
- Separate broker JMX ConfigMap and PodMonitor source, plus a metrics-only patch reserved for the existing Kafka owner.
- Separate manual Project/Application templates with unbound `${RESOURCE_COMMIT}` placeholders. Do not register these templates before freezing exact resource/source pins.
- Narrow inactive PodMonitor Role/Binding: namespace-only create, exact-name update/patch, no delete or wildcard grant. Existing controller lacks this write permission; the candidate grant has not been applied or server dry-run validated.
- Credential-free observations, installed manifest copies, source references, local rule fixtures, consistency checker and artifact hashes.

Inspection scripts preserve their executed workspace paths and require the parent workspace CA/context. They are evidence sources, not portable unattended activation runners. They are not referenced by CI, active Kustomize roots or registered Applications. The disabled candidate roots can be rendered explicitly for review, but no existing active root includes them.

## Remaining before controlled activation

Freeze the resource commit from this publication and concretize registration pins; server-check/apply the narrow PodMonitor grant through controlled bootstrap and recheck effective permissions; refresh live health and compare-before-write ownership before opening the approved window. Observe actual managed resources at A1 exit before any broker promotion. No SMTP details or repeated user approval of already settled decisions are needed for collection-only scope. New publication alone does not apply anything.

Local consistency command, run from repository root: `python qualification/r3/r3-03/activation-execution/validate_preparation.py`. It renders local candidate manifests and verifies the frozen prior packages. It does not contact the cluster or run a workload. Historical preparation labels in receipts retain their original point-in-time meaning; this guide and current selection/progress define the publication disposition.
