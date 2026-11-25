# Tenant resource templates

These offline structural templates render only KafkaTopic and KafkaUser resources into the owning Kafka namespace. Each tenant has independent producer/consumer identities, literal topic/group ACLs, user quota mappings and ownership labels. Topic names are `<tenant-id>-<topic-suffix>`; consumer groups are `<tenant-id>-<topic-suffix>-group`. The producer proposes only Write/Describe on its topics plus cluster IdempotentWrite; no transaction or administrative rights are generated.

RF2 and retention.ms=21600000 are fixed in the topic template. Minimum ISR, partitions and protocol-size ceilings are supplied by the input contract. The 3MiB fixture ceiling is not a 3MiB value guarantee or evidence for WP-A's 10M records. Quotas are user/principal mappings with per-broker bandwidth semantics; multiple users do not automatically share a tenant-wide aggregate cap.

No Secret, Kubernetes RBAC, workload or topic deletion is generated. Delivery references describe a pending credential/CA integration; no credential values are read or embedded. The [guide](../../docs/tenant-profile-scaffolds.md) explains the offline validation boundary.
