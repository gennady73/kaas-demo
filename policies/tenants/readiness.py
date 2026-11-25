"""Stage-specific offline input assessment, never runtime approval or deployment."""
import profile_tool as tool
import bootstrap_tool

EXTERNAL_GATES = {
    'R0': ['Actual published resource revision/paths and repository access/trust',
           'Installed ArgoCD schema and effective project/global-role authorization',
           'Separate authorization to register new objects; no sync implied'],
    'R1': ['Fresh target health/budget/placement and actual namespace/operator-watch/controller permissions',
           'Selected-version schema/server validation and reviewed complete resource/source diff',
           'Explicit permitted-personnel authorization and coordinated change window'],
    'R2': ['Actual app credential/CA delivery, rotation and trust verification',
           'Positive/negative tenant access, client ack/offset/retry/size and delivery evidence'],
    'R3': ['Configuration-specific capacity, governance and operational acceptance',
           'No-loss/recovery and inherited DEP-PERSIST-01 scope/evidence'],
}
LABELS = {'R0': 'GitOps registration', 'R1': 'Controlled deployment',
          'R2': 'Client activation', 'R3': 'Service qualification'}


def assess(profile, bootstrap=None):
    tool.check_shape(profile)
    unknown = tool.unresolved(profile)
    placement_errors = []
    try:
        tool.check_placement(profile)
    except tool.Invalid as error:
        placement_errors.append(str(error))
    registration_errors = []
    if not tool.required_unresolved(profile, 'R0'):
        try:
            tool.check_registration(profile)
        except tool.Invalid as error:
            registration_errors.append(str(error))
    core_errors = []
    if not tool.required_unresolved(profile):
        try:
            tool.check_profile(profile)
        except tool.Invalid as error:
            core_errors.append(str(error))
    boot = bootstrap_tool.assess(bootstrap, profile)
    stages = {}
    for stage in tool.STAGES:
        missing = tool.required_unresolved(profile, stage)
        errors = list(placement_errors) + registration_errors
        if stage != 'R0':
            errors += core_errors
            missing += ['bootstrap:' + p for p in boot['missing']]
            errors += ['bootstrap: ' + e for e in boot['errors']]
            if stage in ('R2', 'R3'):
                missing += ['bootstrap:' + p for p in boot.get('later_unresolved', [])]
        complete = not missing and not errors
        stages[stage] = {
            'purpose': LABELS[stage],
            'local_status': ('SYNTHETIC_ONLY' if profile['synthetic_fixture'] else 'OFFLINE_INPUTS_COMPLETE')
                            if complete else 'BLOCKED',
            'own_unresolved_profile_inputs': [p for p in unknown if tool.input_stage(p) == stage],
            'cumulative_missing_inputs': sorted(set(missing)), 'local_errors': sorted(set(errors)),
            'external_gates_not_verified': [gate for earlier in tool.STAGES
                if tool.STAGES.index(earlier) <= tool.STAGES.index(stage) for gate in EXTERNAL_GATES[earlier]],
            'execution_ready': False,
        }
    return {'report_version': '0.2', 'status': 'OFFLINE_ASSESSMENT_ONLY',
            'deployment_enabled': False, 'execution_ready': False,
            'synthetic_fixture': profile['synthetic_fixture'], 'unresolved': unknown,
            'stages': stages, 'bootstrap': boot,
            'limitations': ['Filled input strings are not approval or evidence verification',
                'No published-source existence, installed-state, credential or acceptance check executed',
                'R0 reports registration inputs only; rendering a whole bundle still needs R1 profile fields',
                'Later dependencies can become earlier use-case gates; this model is the bounded internal profile baseline']}
