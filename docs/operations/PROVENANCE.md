# C7 portable publication provenance

This package publishes C7 offline preparation and the C0-C7-RC-01 correction. Kustomize remains current and Helm evaluation deferred. It does not change any running test, GitOps application or deployment configuration.

The canonical coordination documents live in the shared kaas-solution workspace. Publication copies preserve their content and historical outcomes, adapting local Markdown links for this standalone repository. Helpers and regression tests are under operations/; five exact template copies are under docs/operations/templates/. Read the local operations README for commands.

Historical validation/source receipts retain their original workspace paths and hashes. They describe the source slice at their recorded time, not a fresh verification of every publication copy. The publication-manifest.json file maps source hashes to published-copy hashes and lists references retained only in the coordinator workspace. The C0-C7-RC-01 correction receipt supersedes its earlier defect evidence; the current code's only publication adaptation is the test template path.

References in the release-matrix and historical JSON receipts use the original coordinator workspace root unless the referenced artifact also exists here. A coordinator-only reference is not a broken public download or an assertion that raw evidence was published. Full raw ledgers, active run plans, API inventories and credential material are excluded. Supplied source references and completed forms do not establish release approval or runtime success.

This publication includes no active Kustomization, executable Job, Helm chart, deployment authorization or auto-promotion path. All blank templates remain TEMPLATE/OPEN/execution-disabled. Local consistency checks keep release_qualified and execution_ready false. The current daily run's final outcome remains pending; recorded short PASS and earlier failures retain their original scope.
