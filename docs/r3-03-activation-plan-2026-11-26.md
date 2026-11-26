# R3-03 staged activation proposal

[Complete staged plan](../qualification/r3/r3-03/activation-plan/README.md), [resource model](../qualification/r3/r3-03/activation-plan/resource-estimates.json), [rollback](../qualification/r3/r3-03/activation-plan/rollback.md), [inputs](../qualification/r3/r3-03/activation-plan/inputs-needed.json).

Prepared offline against published3d7b6ba; no cluster access, rollout, resource creation, workloads or notifications. Four client Jobs are untouched, last observed suspended. Every action flag remainsfalse. Resource figures are C0 planning estimates and unapproved, not observed consumption/vendor minimums or exact managed-Pod defaults.

Proposed additional planning reservation:1.25CPU/6.5GiRAM steady,1.75CPU/9.5Gi during the change window. UWM nominally adds about5managed Pods; narrow JMX stays within3existing broker Pods with a proposed150mCPU/384Mibuffer included in totals. Optional lag exporter is deferred. Storage remains a choice: ephemeral functional pilot with0newPVCs/nopersistent-monitoringHAclaim, or proposed4PVCs/24Gi persistent UWM allocation. OriginalKafka/evidencePVCs and retention policies stay intact.

The90minute proposed window runs only after offline preparation/choices are complete: freezebaseline→UWMconsumer→metrics-onlybrokerchange→scrapeverification→knownreceiver/routinggate→brokerrules→optionalsinkrules→closeout. Enabling rules can send natural alerts, even with notification testsdisabled; unknown recipient means stop at scrape-only. No safe notification test is included.

Budget up to3serial broker/controller restarts. WithRF2/minISR2, affectedacks=allwrites can pause/fail until required ISR returns; one-of-three controller restart assumes both survivors remain healthy. Do not force rolling, lower ISR, change versions or delete Pods. The existing KafkaProject cannot accept monitoring kinds: keep Kafkaownership and prepare a narrow separate monitor ownership path before any mutation.

Rollback is current-state-specific, preserve-first and manual: a metricsConfig reversal can trigger a second roll; no-prune file removal does not stop live rules/scrapes; UWMdisablement can affect other projects/telemetry/PVCretention. Prefer targeted repair/hold and protect current data/claims/routes. No runtime rollback is tested or automatically authorized.

Inputs: budget disposition; storage/24hmetric-retention choice;90minute window/write-impact/executor-stopcontact; technicalcustodian/backup; receiver/monitoringresponder/escalationreference. Existinguserowner/evidence7daypolicyaccepted. FullPromQL/rulefixtures, managedwhole-Podfootprint and current source/headroom/ISR/routing protection are technical artifact joins before activation, not permission granted by this plan. No approval question is pending for this completed offline task.
