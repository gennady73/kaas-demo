# Tenant configuration

Place declarative KafkaTopic and approved user/access resources here. Initial proposed topics are `kaas-dev-smoke-01` through `kaas-dev-smoke-04`, one partition each, target RF=2 and 6h retention. Cluster labels, served CRD version, effective message limits and the dev-specific policy require verification before rendering manifests. Test clients must not create topics implicitly.
