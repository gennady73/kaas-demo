# Resource budget, retention, window and escalation — plain-language brief

This explains the staged plan; it records no resource/storage/window acceptance or deployment authority. The user authorized publication while keeping deployment/workloads disabled. Sizes and windows remain proposals.

## What does “budget” mean here?

The estimate is **extra cluster capacity**, in addition to the existing Kafka and platform allocations:

| Allowance | Extra CPU | Extra RAM |
| --- | ---: | ---: |
| Normal monitoring operation |1.25CPU|6.5GiB |
| Total allowance during the change window |1.75CPU|9.5GiB |

The second row already includes the normal allowance: do not add the rows together. The proposal includes about five UWM managed Pods plus an in-process JMX allowance in three existing broker Pods. It does not add worker nodes or resize brokers. Optional lag exporter is deferred. These are C0 engineering estimates, not measured requests, vendor minimums, enforced limits or confirmed spare capacity. The installed managed Pod/sidecar footprint still needs reconciliation before activation.

For disk, the choices remain zero new PVCs for an explicitly ephemeral sandbox pilot, or an initial persistent UWM proposal of four PVCs/24GiB total. Existing Kafka and evidence volumes remain separate. The persistent allocation is not proven TSDB sizing or whole-stack HA qualification.

No currency quote is established. A dollar estimate requires the sandbox/chargeback rate, running duration, selected storage and whether existing nodes have enough capacity or additional billed infrastructure would be needed. Translating requested CPU/RAM directly into a cloud bill would be misleading; no new node purchase is selected by this plan.

## What does 24-hour metrics retention mean?

It proposes a rolling day of numerical monitoring history: scrape/health, CPU/memory/disk and selected Kafka gauges. It does **not** change Kafka message retention (six hours), sealed evidence retention (seven days), or start a24-hour producer/consumer test.

Time retention is a target history window, not a promise every sample survives for exactly24hours. Storage/size limits, ingestion and restarts matter. An ephemeral pilot can lose its telemetry earlier after monitoring Pods are replaced; persistent storage is the option for restart-surviving history. The storage mode and actual resource/retention configuration are still to select and validate.

[OpenShift4.21 retention/storage reference](https://docs.redhat.com/en/documentation/monitoring_stack_for_red_hat_openshift/4.21/html/configuring_user_workload_monitoring/storing-and-recording-data-uwm). Publishing this explanation leaves all choices and activation flags unchanged.

## Why a90-minute window?

It is a proposed slot to make and verify the complete staged change, after offline preparation:

- 10 minutes for final baseline/source/contact checks.
- 15 minutes to enable/observe the approved UWM consumer.
- 30 minutes reserved for the metrics change and possible serial broker roll.
- 10 minutes for scrape/metric stability.
- 5 minutes for the receiver/routing gate before live rules.
- 5 minutes for broker rules, optionally5minutes for sink rules.
- 10 minutes for evidence and handoff.

Total90minutes if every listed stage is selected. These are time budgets, not measured duration guarantees; slow or unsafe progress means hold, not automatic extension. No safe notification test or lag-exporter activation is included.

This does not predict a90-minute continuous Kafka outage. The material service impact is during possible broker restarts: with RF2/minISR2, affectedacks=all writes can pause/fail until replicas recover. The window is when an authorized person must be available to observe and stop further promotions. An actual date/time and acceptance of that impact are needed only before activation.

## Monitoring, receiver and escalation — who does what?

**Monitoring** collects measurements and evaluates rules. **Alertmanager/routing** decides which approved destination receives an alert. The **receiver/channel** is the existing email, messaging or incident destination reference. The **responder** is the person/team expected to acknowledge and inspect it.

**Escalation** means contacting the agreed backup or accountable owner if the responder does not acknowledge within the agreed interval or cannot resolve the issue. The interval/contact is an operational agreement to fill in; this plan invents no24×7staffing or response-time SLO. For this sandbox, the user may choose to be the responder and custodian, with a backup if available; no such assignment is assumed automatically.

Example: evidence free space crosses the approved warning boundary → the rule fires → approved routing sends to the chosen channel → responder inspects safely → unresolved space/ingestion risk is escalated to the stop authority/user. This does not authorize automatic restart, scaling, deletion or a test notification. Natural alerts may be sent once rules are enabled, so unknown recipients block that stage even while synthetic notification tests stay disabled.

The **evidence custodian** has a separate practical job: check the saved exports/copies, track the accepted retain-through/hold and escalate any eventual disposition to the user owner. One person/team may cover both custody and monitoring response.

To populate those roles, provide names/team/runbook references, the approved receiver/channel reference and backup/escalation contact. Do not send passwords, receiver Secret contents or token-bearing webhook URLs. Existing accountable user ownership and seven-day policy remain accepted; the missing details are operational contacts and implementation choices.
