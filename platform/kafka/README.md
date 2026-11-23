# Small development Kafka cluster

Prepared 2026-11-23 for operator `amqstreams.v3.2.1-10`, using its exact Kafka 4.2.0 image mapping and served v1 CRDs. See [deployment guide](../../docs/kafka-deployment-guide.md).

- Namespace `kaas-kafka`, cluster `kaas-dev`, three combined broker/controller nodes.
- Three 20Gi gp3-csi PVCs (60Gi requested total), deleteClaim=false. This is below the reference dev total of 100Gi; it is not an independently established billing ceiling or free-space measurement.
- Each Kafka node requests 500m CPU/2Gi memory, limits 1 CPU/2Gi; heap 512m initial/1g max. Entity operators each request 100m/256Mi and limit 500m/512Mi. Combined requests are 1.7 CPU/6.5Gi; limits 4 CPU/7Gi, excluding the already installed platform/operator components. Adequacy is to be measured, not asserted.
- Required anti-affinity distributes the three Kafka pods across distinct hosts. Current preflight found five untainted schedulable nodes; this does not establish physical rack/zone independence.
- Target RF=2 and 6h retention. Explicit minimum ISR=2 is a new dev configuration choice, not an interpretation of the earlier undefined offset 2. With producer acks=all, affected partitions stop accepting writes while only one replica is in sync.
- Internal 9093 TLS/SCRAM listener and simple authorization; allow client namespace peers only from kaas-kafka and kaas-demo. Initial credentials are generated in a cluster Secret by the User Operator; no password is in Git. This dev choice does not settle future production/SSO policy.
- Four one-partition/RF2 smoke topics, a narrowly scoped smoke user, a 3MiB transport/batch limit to accommodate at most 2MiB original test values plus overhead, and 4MiB follower-fetch setting. No custom offload. Client-side size/retry/ack/deadline mappings remain to be verified.

Combined KRaft roles are a development choice; this is not the production topology or proof of capacity/recovery. No test Job or automatic load hook is part of this Application.
