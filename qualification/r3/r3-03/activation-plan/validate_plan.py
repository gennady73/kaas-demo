#!/usr/bin/env python3
"""Local consistency/arithmetic and published-package integrity; no runner/network."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent

def main():
 p=json.loads((HERE/'plan.disabled.json').read_text());r=json.loads((HERE/'resource-estimates.json').read_text())
 assert all(p[x] is False for x in ['execution_enabled','deployment_enabled','workloads_enabled','notification_tests_enabled'])
 assert p['client_Jobs_must_remain_suspended'] is True and p['lag_exporter_selected'] is False
 assert all(p[x] is None for x in ['selected_stages','resource_budget_approval','storage_option','change_window','named_executor_and_stop_contact','custodian','receiver_reference_and_ack_contact','new_source_resource_commits_and_registration_pins'])
 ids=[x['id'] for x in p['stages']];assert ids==['A'+str(i) for i in range(8)]
 assert sum(x['planning_minutes'] for x in p['stages'])==p['planning_window_minutes']==90
 assert p['stages'][3]['planning_minutes']>=2*p['time_policy']['healthy_stability_minutes_proposal']
 assert p['unknown_receiver_blocks_live_rule_enablement'] and p['natural_alert_delivery_possible_when_rules_enabled'] and not p['safe_notification_test_in_90min_scope']
 assert 'Receiver/routing' in p['stages'][4]['title'] and 'broker rules' in p['stages'][5]['title']
 uwm_cpu=sum(x['replicas']*x['cpu_m_each'] for x in r['new_uwm_components']);uwm_mem=sum(x['replicas']*x['memory_MiB_each'] for x in r['new_uwm_components'])
 assert uwm_cpu==r['uwm_steady']['cpu_m']==1000 and uwm_mem==r['uwm_steady']['memory_MiB']==6144
 factor=r['uwm_change_window_reserve_factor'];assert uwm_cpu*factor==r['uwm_change_window_allowance']['cpu_m'];assert uwm_mem*factor==r['uwm_change_window_allowance']['memory_MiB']
 b=r['broker_metrics_overhead'];assert b['replicas']*b['cpu_m_each']==b['total_cpu_m']==150 and b['replicas']*b['memory_MiB_each']==b['total_memory_MiB']==384
 totals=r['core_totals'];assert totals['steady_cpu_m']==uwm_cpu+b['total_cpu_m'] and totals['steady_memory_MiB']==uwm_mem+b['total_memory_MiB']
 assert totals['change_window_cpu_m']==uwm_cpu*factor+b['total_cpu_m'] and totals['change_window_memory_MiB']==uwm_mem*factor+b['total_memory_MiB']
 reserve=r['proposed_rounded_planning_reservation']
 for key in totals:assert reserve[key]>=totals[key]
 storage=r['storage_options'];assert storage['selected'] is None and storage['ephemeral_sandbox_pilot']['new_PVCs']==0
 durable=storage['persistent_monitoring'];assert durable['total_new_requested_GiB']==durable['prometheus_replicas']*durable['prometheus_each_GiB']+durable['thanos_ruler_replicas']*durable['thanos_ruler_each_GiB']==24
 assert durable['new_PVCs']==durable['prometheus_replicas']+durable['thanos_ruler_replicas']==4
 parent=HERE.parent;manifest=json.loads((parent/'artifact-manifest.json').read_text())
 for f,h in manifest['files'].items():assert hashlib.sha256((parent/f).read_bytes()).hexdigest()==h,f
 result={'status':'OFFLINE_PLAN_ARITHMETIC_STAGE_ORDER_AND_PARENT_INTEGRITY_PASS','stages':8,'minutes_budget':90,'UWM_main_and_combined_sidecar_allowance_cpu_m':uwm_cpu,'UWM_memory_MiB':uwm_mem,'core_estimated_totals':totals,'rounded_proposed_reservation':reserve,'storage_choice_unset':True,'parent_artifact_files_unchanged':len(manifest['files']),'unknown_receiver_blocks_rules':True,'planning_not_sizing_measurement':True,'resource_budget_approved':False,'cluster_accessed':False,'deployment_or_workloads_run':False,'rollback_runtime_tested':False,'independent_reviewer':'NOT_CLAIMED'}
 (HERE/'evidence/validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
