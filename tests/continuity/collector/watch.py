#!/usr/bin/env python3
"""Bounded one-run observer and final offline auditor. No Kafka or Kubernetes credentials."""
import datetime,hashlib,json,os,ssl,subprocess,sys,time,urllib.request
from pathlib import Path

RAW=Path('/code/worker-0.json').read_bytes();PLAN=json.loads(RAW);DIGEST=hashlib.sha256(RAW).hexdigest();RUN=PLAN['run_id'];BASE=PLAN['environment']['evidence_sink_url']
TOKEN=Path('/auth/token').read_text().strip();CTX=ssl.create_default_context(cafile='/collector-ca/service-ca.crt');OUT=Path('/results');OUT.mkdir(exist_ok=True)
EPOCH=datetime.datetime.fromisoformat(PLAN['planned_start_utc'].replace('Z','+00:00')).timestamp();END=EPOCH+PLAN['duration_seconds'];LAST=END+PLAN['drain_limit_seconds']+PLAN['shutdown_limit_seconds']
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def log(kind,**fields):print(json.dumps({'type':kind,'run_id':RUN,'at':stamp(),**fields}),flush=True)
def request(path,body=None,export=None):
    req=urllib.request.Request(BASE+path,data=None if body is None else json.dumps(body).encode(),headers={'Authorization':'Bearer '+TOKEN,'Content-Type':'application/json'})
    with urllib.request.urlopen(req,context=CTX,timeout=300 if export else 10) as response:
        if export:
            with Path(export).open('wb') as f:
                while True:
                    part=response.read(1024*1024)
                    if not part:break
                    f.write(part)
            return {'bytes':Path(export).stat().st_size}
        return json.load(response)
def fail(reason):
    log('RUN_REQUIRES_ATTENTION',reason=reason)
    try:request('/runs/'+RUN+'/stop',{'reason':reason})
    except Exception:pass
    raise SystemExit(2)

last_counts={};last_progress={};last_success=time.monotonic();next_log=0
log('MONITOR_STARTED',generation_end_utc=datetime.datetime.fromtimestamp(END,datetime.timezone.utc).isoformat(),scope='one run; HTTPS collector only; no Kafka/API access')
while time.time()<LAST+60:
    try:
        summary=request('/runs/'+RUN+'/summary');last_success=time.monotonic()
        if summary.get('plan_sha256')!=DIGEST:fail('collector_plan_mismatch')
        if summary.get('stopped'):fail('collector_reports_'+str(summary['stopped']))
        if summary.get('disk',{}).get('used_fraction',1)>0.75:fail('collector_storage_threshold')
        for client in PLAN['clients']:
            s=summary.get('clients',{}).get(client)
            if s is None:
                if time.time()>EPOCH+15:fail('missing_client_'+client)
                continue
            if s.get('terminal') and not s['terminal'].get('complete'):fail('incomplete_client_'+client)
            metric='acknowledged' if client.startswith('producer') else 'receipt';count=s['counts'].get(metric,0)
            if client not in last_progress or last_counts.get(client)!=count:last_progress[client]=time.monotonic();last_counts[client]=count
            # This observer allows 90s to avoid sampling races; runner/auditor retain the stricter 60s acceptance bounds.
            if EPOCH<=time.time()<END and time.monotonic()-last_progress[client]>90:fail('observed_progress_stall_'+client)
        seal=request('/runs/'+RUN+'/seal')
        if seal.get('complete'):
            log('ALL_CLIENTS_COMPLETE',counts=summary['counts'],event_count=summary['event_count'])
            request('/runs/'+RUN+'/export',export=OUT/'events.ndjson');(OUT/'seal.json').write_text(json.dumps(seal,indent=2)+'\n')
            cmd=[sys.executable,'/code/continuity_reconcile.py','--plan','/code/worker-0.json','--events',str(OUT/'events.ndjson'),'--seal',str(OUT/'seal.json'),'--database',str(OUT/'ledger.sqlite'),'--output',str(OUT/'reconciliation.json')]
            audit=subprocess.run(cmd,capture_output=True,text=True,timeout=600)
            if audit.returncode!=0:fail('independent_auditor_failed')
            result=json.loads((OUT/'reconciliation.json').read_text());log('ACCOUNTING_COMPLETE_AWAITING_JOB_AND_CLUSTER_REVIEW',result=result,export_sha256=hashlib.sha256((OUT/'events.ndjson').read_bytes()).hexdigest());raise SystemExit(0)
        if time.monotonic()>=next_log:
            log('RUNNING',counts=summary['counts'],events=summary['event_count'],collector_disk=summary['disk']);next_log=time.monotonic()+300
    except SystemExit:raise
    except Exception as e:
        log('MONITOR_REQUEST_ERROR',error_class=type(e).__name__)
        if time.monotonic()-last_success>90:fail('collector_observation_gap')
    time.sleep(30)
fail('missing_clean_completion_by_envelope')
