// Runtime projection is compiled/validated offline, then bound by its exact hash
// in a separately reviewed execution record. No offline plan mode is enabled.
export const ERROR_CATEGORIES=['topic_authorization_denied','group_authorization_denied','cluster_authorization_denied','authentication_failed','tls_failed','network_failed','timeout','unknown'];
export const STAGES=['produce','consume','group_join'];
export const SAFE_SEVERITIES=['FAIL','INCONCLUSIVE'];
export const SAFE_REASONS=['internal_policy_failure','clock_invalid','budget_exhausted','durable_evidence_unavailable','unknown_binding','credential_unavailable','trust_unavailable','close_failed_or_overrun','group_ownership_or_membership_unverified','record_budget','unknown_record','generated_payload_mismatch','unexpected_negative_ack','late_positive_ack','unprocessed_initial_records','initial_position_unverified','positive_send_unresolved','consume_shape','foreign_or_unplanned_record','receipt_integrity_or_offset_gap','commit_result_unresolved','committed_offset_unverified','positive_control_missing','positive_consumer_still_open','unexpected_negative_join','unexpected_negative_record','negative_offset_changed','negative_failure_layer_unproven','consumer_write_layer_confounded','unsafe_client_or_debug_configuration','client_or_evidence_failure','total_deadline_exceeded','terminal_evidence_missing','stop_requested','phase_overrun'];
export function require(ok,code){if(!ok)throw new Error(code);}
export function canonical(x){if(x===null||typeof x!=='object')return JSON.stringify(x);if(Array.isArray(x))return '['+x.map(canonical).join(',')+']';return '{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+canonical(x[k])).join(',')+'}';}
export function freeze(x){if(x&&typeof x==='object'){Object.values(x).forEach(freeze);Object.freeze(x);}return x;}
export function valueFor(seed,record,sha){let value='';for(let n=0;value.length<1000;n++)value+=sha(`${seed}:${record.tenant}:${record.topic}:${record.sequence}:${record.case_id}:${n}`);return value.slice(0,1000);}
export function validatePlan(plan,deps){
 require(plan.plan_version==='tenant-native-candidate-1.0'&&plan.mode==='NATIVE_CANDIDATE','native_plan');
 require(deps.runtimeAuthorized===true&&deps.sha256(canonical(plan))===deps.reviewedPlanHash,'reviewed_native_plan_required');
 require(plan.maximum_total_seconds===300&&plan.maximum_logical_value_bytes===20000&&plan.records.length===16&&plan.negative.length===8,'fixture_bounds');
 require(plan.execution_enabled===false&&plan.tests_enabled===false,'preparation_plan_required');
 return freeze(plan);
}
export function validateExecution(plan,gate,sha){
 require(gate&&gate.protocol==='kaas-r2-execution-v1'&&gate.execution_authorized===true&&gate.tests_enabled===true,'execution_not_authorized');
 require(gate.plan_sha256===sha(canonical(plan)),'plan_hash');
 require(typeof gate.authority_reference==='string'&&gate.authority_reference.length>0,'authority_reference');
 const required=['native_image_and_source','C3_changed_source_review','C6_changed_source_review','credentials_delivered','CA_chain_SAN_expiry','namespace_network_SCC','fixture_group_ownership','sink_TLS_auth_persistence','custody_retention_second_copy','native_cancellation_close_bounds','independent_export_auditor'];
 require(required.every(k=>gate.gates?.[k]==='VERIFIED'),'execution_gates_open');
 require(/^sha256:[a-f0-9]{64}$/.test(gate.image_digest||'')&&/^[a-f0-9]{64}$/.test(gate.package_sha256||''),'immutable_package');
 require(Number.isSafeInteger(gate.job_start_unix_ms)&&gate.job_start_unix_ms>0,'job_start_required');
 require(typeof gate.sink_origin==='string'&&/^https:\/\/[a-z0-9.-]+:8443$/.test(gate.sink_origin),'sink_origin');
 require(Array.isArray(gate.exclusive_fixture_groups)&&gate.exclusive_fixture_groups.length===4&&plan.positive.every(p=>gate.exclusive_fixture_groups.includes(p.group)),'fixture_ownership');
 return freeze(gate);
}
