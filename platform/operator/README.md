# Kafka operator installation stage

Package `amq-streams`, Red Hat catalog `redhat-operators`, namespace `openshift-marketplace`; selected CSV `amqstreams.v3.2.1-10` was found in channel `amq-streams-3.2.x` by live API discovery on 2026-11-19. Operator installs in `kafka-operator` and targets `kaas-kafka`; tests remain in `kaas-demo`.

Manual InstallPlan approval is required. `startingCSV` chooses the initial version; it is not an ongoing pin. Before approving the first plan, verify its complete CSV list, exact selected version and related image/permission changes. Later plans remain pending unless explicitly authorized. Do not approve a newer channel head merely to complete the installation.

This stage provisions no brokers, PVCs, Kafka topics, credentials, load Jobs or GitOps operator upgrades. Inspect the installed exact operator/broker mapping and CRDs before producing the next stage. Live catalog availability is not proof of an offline image mirror.
