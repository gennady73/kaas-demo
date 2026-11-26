#!/usr/bin/env python3
"""Offline selected-config/ownership/preservation checks. Never calls a cluster."""
import hashlib,json,subprocess
from pathlib import Path
import yaml
HERE=Path(__file__).resolve().parent

def main():
 accepted=json.loads((HERE/'acceptance.json').read_text())['accepted']
 assert accepted['alert_destination']['type']=='email' and accepted['alert_destination']['to']=='gunger@redhat.com'
 assert accepted['storage']['new_PVCs']==4 and accepted['storage']['total_GiB']==24
 configs={}
 for name in ['platform','broker-scrape']:
  text=subprocess.check_output(['kubectl','kustomize',str(HERE/'candidate'/name)],text=True)
  configs[name]=list(yaml.safe_load_all(text))
  assert text==(HERE/'evidence'/('rendered-'+name+'.yaml')).read_text()
 assert {(d['kind'],d['metadata']['namespace'],d['metadata']['name']) for d in configs['platform']}=={('ConfigMap','openshift-monitoring','cluster-monitoring-config'),('ConfigMap','openshift-user-workload-monitoring','user-workload-monitoring-config')}
 uwm=next(x for x in configs['platform'] if x['metadata']['namespace']=='openshift-user-workload-monitoring')
 settings=yaml.safe_load(uwm['data']['config.yaml'])
 assert set(settings)=={'prometheus','thanosRuler','prometheusOperator'}
 for key,size in [('prometheus','10Gi'),('thanosRuler','2Gi')]:
  assert settings[key]['retention']=='24h'
  spec=settings[key]['volumeClaimTemplate']['spec']
  assert spec=={'storageClassName':'gp3-csi','accessModes':['ReadWriteOnce'],'volumeMode':'Filesystem','resources':{'requests':{'storage':size}}}
  assert 'limits' not in settings[key]['resources']
 assert {(x['kind'],x['metadata']['namespace']) for x in configs['broker-scrape']}=={('ConfigMap','kaas-kafka'),('PodMonitor','kaas-kafka')}
 for f in (HERE/'candidate/registration').glob('*'):
  d=yaml.safe_load(f.read_text());s=d['spec']
  if d['kind']=='Application':
   assert s['source']['targetRevision']=='${RESOURCE_COMMIT}'
   assert s['syncPolicy']=={'syncOptions':['FailOnSharedResource=true']}
  else:
   assert s['clusterResourceWhitelist']==[]
   assert all(x['kind'] in ['ConfigMap','PodMonitor'] for x in s['namespaceResourceWhitelist'])
   assert all(x['namespace'] in ['kaas-kafka','openshift-monitoring','openshift-user-workload-monitoring'] for x in s['destinations'])
 for parent in [HERE.parent,HERE.parent/'activation-plan']:
  manifest=json.loads((parent/'artifact-manifest.json').read_text())
  for file,digest in manifest['files'].items():assert hashlib.sha256((parent/file).read_bytes()).hexdigest()==digest,file
 refresh=HERE/'evidence/refresh'
 for f in refresh.glob('kaas-r2-native-client*.json'):
  d=json.loads(f.read_text());assert d['suspend'] is True and d['active']==0
 assert len(list(refresh.glob('kaas-r2-native-client*.json')))==4
 assert json.loads((refresh/'result.json').read_text())['status']=='COMPLETE'
 rule=json.loads((HERE/'evidence/rule-validation.json').read_text());assert rule['exit_code']==0 and rule['fixtures']==12
 for name,source in [('broker',HERE.parent/'candidate/10-broker-metrics/rules.yaml.disabled'),('sink',HERE.parent/'candidate/20-sink-rules/rules.yaml.disabled')]:
  assert yaml.safe_load((HERE/'rule-tests'/(name+'.rules.yaml')).read_text())['groups']==yaml.safe_load(source.read_text())['spec']['groups']
 selection=json.loads((HERE/'selection.disabled.json').read_text())
 assert selection['selected_stages']==['A0','A1','A2','A3','A7']
 assert all(selection[k] is False for k in ['deployment_enabled','registration_enabled','automatic_sync_enabled','prune_enabled','force_or_replace_enabled','email_routing_enabled','live_alert_rules_enabled','test_email_enabled','producer_consumer_tests_enabled'])
 assert selection['selected_stage_planning_minutes']+selection['unused_budget_minutes']==selection['approved_window_budget_minutes']==90
 assert json.loads((HERE/'email-delivery.json').read_text())['status']=='DEFERRED_BY_USER'
 result={'status':'SELECTED_CONFIG_RENDER_OWNERSHIP_AND_FROZEN_PACKAGE_PRESERVATION_PASS','rendered_objects':4,'new_selected_PVCs':4,'new_selected_GiB':24,'prior_package_hashes_verified':48,'prior_plan_hashes_verified':12,'four_Jobs_suspended_in_fresh_GET_evidence':True,'rules_have_no_active_include':True,'registration_pins':'RESOURCE_COMMIT_PLACEHOLDER_NOT_REGISTERED','remaining':['Immutable source publication and concrete registration pins','Narrow PodMonitor grant admission/application and effective permission refresh','Fresh health/compare-before-write; actual managed Pods at A1 exit'],'cluster_resources_changed':False,'workloads_run':False,'independent_review':'NOT_CLAIMED'}
 (HERE/'evidence/preparation-validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
