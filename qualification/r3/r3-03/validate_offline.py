#!/usr/bin/env python3
"""Offline render/schema/source/preservation checks only. No network or apply API."""
import copy,difflib,json,re,subprocess,yaml,jsonschema
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];DISC=HERE/'evidence/discovery'
def load(p):return yaml.safe_load(p.read_text())
def schema(name):
 d=json.loads((DISC/('schema-'+name+'.json')).read_text());return next(v['schema']['openAPIV3Schema'] for v in d['versions'] if v['name']=='v1' and v['served'])
def main():
 profile=json.loads((HERE/'profile.disabled.json').read_text())
 for key in ['execution_enabled','deployment_enabled','workloads_enabled','notification_tests_enabled']:assert profile[key] is False
 assert profile['monitoring_new_resource_budget'] is None and profile['receiver_name'] is None
 stage=HERE/'candidate/10-broker-metrics'
 render=subprocess.run(['kubectl','kustomize',str(stage)],capture_output=True,text=True,check=True)
 docs=list(yaml.safe_load_all(render.stdout));assert len(docs)==4
 kafka=next(x for x in docs if x['kind']=='Kafka');original=load(ROOT/'platform/kafka/kafka.yaml');expected=copy.deepcopy(original)
 expected['spec']['kafka']['metricsConfig']=load(stage/'kafka-metrics.patch.yaml.disabled')['spec']['kafka']['metricsConfig']
 assert kafka==expected,'Unexpected Kafka mutation'
 kschema=json.loads((ROOT/'policies/tenants/schemas/Kafka-v1.json').read_text());jsonschema.Draft4Validator(kschema).validate(kafka)
 lag=copy.deepcopy(original);lag['spec'].update(load(HERE/'candidate/30-lag-optional/kafka-exporter.patch.yaml.disabled')['spec']);jsonschema.Draft4Validator(kschema).validate(lag)
 cm=next(x for x in docs if x['kind']=='ConfigMap');jmx=yaml.safe_load(cm['data']['metrics.yml']);assert jmx['lowercaseOutputName'] is True
 expected_names=[]
 for domain,kind,names in [('server','ReplicaManager',['UnderReplicatedPartitions','UnderMinIsrPartitionCount','OfflineReplicaCount']),('controller','KafkaController',['ActiveControllerCount','OfflinePartitionsCount'])]:
  for n in names:
   bean=f'kafka.{domain}<type={kind}, name={n}><>Value';matches=[]
   for r in jmx['rules']:
    m=re.fullmatch(r['pattern'],bean)
    if m:matches.append(r['name'].replace('$1',m[1]).lower())
   assert len(matches)==1;expected_names+=matches
 paths=[stage/'podmonitor.yaml.disabled',HERE/'candidate/30-lag-optional/podmonitor.yaml.disabled',stage/'rules.yaml.disabled',HERE/'candidate/20-sink-rules/rules.yaml.disabled']
 for p in paths:
  doc=load(p);key='podmonitors' if doc['kind']=='PodMonitor' else 'prometheusrules';jsonschema.Draft4Validator(schema(key)).validate(doc)
 pm=load(stage/'podmonitor.yaml.disabled');assert pm['spec']['namespaceSelector']=={'matchNames':['kaas-kafka']}
 assert pm['spec']['selector']['matchLabels']['strimzi.io/name']=='kaas-dev-kafka'
 assert pm['spec']['podMetricsEndpoints'][0]['port']=='tcp-prometheus'
 for p in [stage/'rules.yaml.disabled',HERE/'candidate/20-sink-rules/rules.yaml.disabled']:
  d=load(p);assert all(r['labels']['kaas_service']=='kaas-dev' for g in d['spec']['groups'] for r in g['rules'])
  assert any('absent(' in r['expr'] for g in d['spec']['groups'] for r in g['rules']), 'Missing-series guard required'
 sink=load(HERE/'candidate/20-sink-rules/rules.yaml.disabled');assert '67108864' in yaml.safe_dump(sink)
 template=(HERE/'candidate/40-routing-template/route-fragment.yaml.template').read_text();assert '${APPROVED_EXISTING_RECEIVER_NAME}' in template
 assert not any('kind: Job' in p.read_text() or 'kind: Secret' in p.read_text() for p in (HERE/'candidate').rglob('*') if p.is_file())
 # New candidate cannot be pulled into an existing active root by accident.
 for f in ['platform/kafka/kustomization.yaml','environments/sandbox-tenants/a/kustomization.yaml','environments/sandbox-tenants/b/kustomization.yaml']:
  assert 'r3-03' not in (ROOT/f).read_text()
 (HERE/'evidence/rendered-broker-validation.yaml').write_text(render.stdout)
 result={'status':'OFFLINE_RENDER_SCHEMA_SOURCE_CHECKS_PASS','Kafka_change':'Onlyspec.kafka.metricsConfig','schema_checks':{'cachedKafkaV1':2,'livePodMonitorV1':2,'livePrometheusRuleV1':2},'representative_JMX_name_mappings':expected_names,'missing_series_and_floor_guards':'PRESENT','all_action_flags':False,'active_includes':'UNCHANGED','PromQL_parser_or_promtool':'NOT_AVAILABLE_NOT_RUN','CEL_admission_operator_scrape_metric_values_alerts_routing':'NOT_RUN','cluster_or_workloads':False}
 (HERE/'evidence/offline-validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
