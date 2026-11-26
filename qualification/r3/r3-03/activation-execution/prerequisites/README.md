# Remaining R3-03 prerequisites: technical review

User authority: proceed with SMTP/routing and installed-build resource verification; retain all four suspended client Jobs, no producer/consumer tests or test email.

Fresh bounded packet: 28 API requests in 14.527 seconds, including eight nonpersistent SubjectAccessReviews, four server dry-runs, and two specifically named Alertmanager configuration Secret GETs. Both configuration documents were decoded in memory and only credential-free routing/SMTP projections saved. All four Jobs suspended/active zero. Four candidate resources admitted in dry-run; this does not validate the string-embedded CMO configuration semantics or prove ArgoCD controller authorization.

## Installed build and resources

Registry access is no longer required for packaged-asset provenance: a Pod GET verified the exact running CMO image and imageID, then three `oc exec -- cat` diagnostics read `/assets/` manifests. No shell, image build, new Pod/Job, client test or email was run. Credentials stayed in an anonymous RAM memfd kubeconfig, closed on exit; no filesystem credential file. Three actual YAML asset hashes and image identity are saved. This supersedes the previous registry hold for manifest provenance only.

Projected requests: UWM821m CPU/5794Mi; with broker in-process allowance971m/6178Mi. Applying the planning1.5 UWM factor yields1381.5m/9075Mi total during change. These fit accepted1250m/6656Mi steady and1750m/9728Mi during change. Projection conservatively counts both Thanos resource entries and sums init/regular reloader requests. Installed reloader flags provide1m/10Mi per reloader; upstream0.87.1 source supports the six-container model. That tag is not asserted to be exact downstream source: observed downstream revision lookup failed. Actual generated whole-Pod resources/sidecars and placement must be observed at A1 exit before broker promotion. This is a planning check, not a measured consumption or admission-mutation guarantee. Storage remains4PVC/24Gi,24h metrics; broker/evidence retention unchanged.

## Effective permissions

Existing ArgoCD controller may create/patch ConfigMaps in all three selected namespaces. It cannot create/patch PodMonitors. Prepared Role/Binding grants only namespace-scoped PodMonitor create and exact-name update/patch, no deletion or wildcard. Kubernetes cannot constrain create by resourceNames; kind/namespace are the create boundary. Existing broad read grants supply get/list/watch. The new Role/Binding has not been applied or server dry-run validated; no permission changed. Both ownership AppProjects/Applications remain inactive templates and require immutable published source pins.

## SMTP and routing

Actual base and generated Alertmanager configs contain no SMTP relay, sender or email receiver. Default/Watchdog/Critical receivers have no integration. User recipient `gunger@redhat.com` is settled; it does not supply transport. Required pending input is approved host:port, sender, credential/CA references or explicit defer-email disposition. No password request, SMTP probe, DNS inference from redhat.com, email or notification was attempted.

Inactive routing template scopes KaaS service+two namespaces and prepends its branch before the existing critical catch-all; appending would let that branch intercept KaaS critical alerts. Existing receivers, other routes and two inhibition rules must remain. No shared Secret rewrite, route change, rule activation, registration, sync or cluster resource change occurred. Email and live alert rules remain held. No new user choice is needed for already accepted storage/budget/window/recipient/no-backup.

The five-minute unanswered-input rule applies to the pending SMTP question; do not start dependent work while it is unanswered. Existing source/artifacts and sealed R2 evidence remain preserved. This package is local/uncommitted.

## Accepted email deferral

User explicitly selected “defer email”. SMTP/routing is therefore deferred and no longer blocks the collection-only scope. No unanswered input question remains. Selected stages: A0/A1/A2/A3/A7,75minutes of the approved90minute budget; remaining15minutes are slack, not a runtime guarantee. A4–A6 remain deferred: no email route or live broker/sink alert rules. Notification qualification is not passed or waived. `selection.disabled.json` in the execution directory records current selection; it does not register or deploy anything. Publication/pins, narrow permission server-check/application and fresh health/compare-before-write remain before activation. All four client Jobs remain suspended; no producer/consumer tests or test email.
