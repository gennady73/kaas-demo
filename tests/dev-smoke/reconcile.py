#!/usr/bin/env python3
"""Independently reconcile captured Kafka smoke events against exact expected cases."""
import argparse,collections,datetime,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--client',choices=['java','xk6'],default='java');p.add_argument('--expected',type=Path,required=True);p.add_argument('--log',type=Path,required=True);p.add_argument('--observation',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
plan=json.loads(a.expected.read_text());expected={r['id']:r for r in plan['records']};events=[]
for line in a.log.read_text().splitlines():
 if line.startswith('SMOKE_EVENT '):events.append(json.loads(line[len('SMOKE_EVENT '):]))
errors=[]
def need(ok,msg):
 if not ok:errors.append(msg)
need(len(expected)==16,'exactly 16 expected IDs');need(all(e['run_id']==plan['run_id'] for e in events),'wrong run ID')
for r in expected.values():
 h=hashlib.sha256();remaining=r['value_bytes'];block=0
 while remaining:
  value=hashlib.sha256(f'{plan["seed"]}:{r["topic"]}:{r["sequence"]}:{block}'.encode('ascii')).hexdigest().encode('ascii')[:remaining];h.update(value);remaining-=len(value);block+=1
 need(h.hexdigest()==r['sha256'],'expected checksum not independently reproducible: '+r['id'])
acks={};received=collections.defaultdict(list);attempts=collections.Counter()
for e in events:
 if e['type'] in ['attempt','acknowledged','received']:
  r=expected.get(e['id']);need(r is not None,'unexpected test ID')
  if not r:continue
  for k in ['topic','value_bytes','sha256']:need(e[k]==r[k],f'{e["type"]} {k} mismatch: {r["id"]}')
  if e['type']=='attempt':attempts[e['id']]+=1
  if e['type']=='acknowledged':need(e['id'] not in acks,'duplicate ack evidence');acks[e['id']]=e
  if e['type']=='received':
   need(e['group']==r['consumer_group'],'consumer group mismatch');need(e['valid'] is True,'runner flagged invalid receipt');received[e['id']].append(e)
need(set(acks)==set(expected),'missing acknowledgement IDs');need(set(received)==set(expected),'missing delivery IDs');need(set(attempts)==set(expected) and all(n==1 for n in attempts.values()),'expected exactly one application attempt per ID')
for key,receipts in received.items():
 for r in receipts:
  ack=acks.get(key,{})
  if a.client=='java':need(all(r.get(k)==ack.get(k) for k in ['topic','partition','offset']),'ack/receipt location mismatch: '+key)
  else:need(type(r.get('partition')) is int and type(r.get('offset')) is int,'missing consumer location: '+key)
starts=[e for e in events if e['type']=='start'];ends=[e for e in events if e['type']=='end'];need(len(starts)==len(ends)==1,'missing/duplicate start or end');end=ends[0] if ends else {}
need(not any(e['type']=='error' for e in events),'client error event');need(end.get('status')=='PASS' and end.get('clean_shutdown') is True,'no clean PASS marker');need(end.get('elapsed_ms',999999)<285000,'client deadline exceeded')
if a.client=='java':need(len([e for e in events if e['type']=='offsets_committed'])==4,'four offset commit confirmations required')
if a.client=='xk6':
 locations=[(rs[0]['topic'],rs[0]['partition'],rs[0]['offset']) for rs in received.values()]
 need(len(set(locations))==16,'consumer locations not distinct')
 need('KAAS_PRODUCER_CONFIG message.max.bytes=3145728 acks=all' in a.log.read_text(),'effective native producer size/acks not evidenced')
obs=json.loads(a.observation.read_text());job=obs['job'];need(job['status'].get('succeeded')==1,'Job did not succeed');need(any(c['type']=='Complete' and c['status']=='True' for c in job['status'].get('conditions',[])),'Job not Complete');need(len(obs['pods'])==1,'unexpected Pod count')
pod=obs['pods'][0];state=pod['status']['containerStatuses'][0]['state'].get('terminated',{});need(state.get('exitCode')==0,'nonzero/missing container exit')
parse=lambda s:datetime.datetime.fromisoformat(s.replace('Z','+00:00'))
wall=(parse(state['finishedAt'])-parse(job['status']['startTime'])).total_seconds() if state.get('finishedAt') else None
need(wall is not None and wall<300,'Job-to-container-finish wall time not under 300s')
result={'status':'PASS' if not errors else 'FAIL','run_id':plan['run_id'],'client':a.client,'expected_unique_records':len(expected),'acknowledged_unique_records':len(acks),'received_unique_records':len(received),'original_value_bytes':sum(r['value_bytes'] for r in expected.values()),'duplicates':sum(len(v)-1 for v in received.values()),'client_elapsed_ms':end.get('elapsed_ms'),'job_start_to_container_finish_seconds':wall,'per_topic':{t:{'acknowledged':sum(x['topic']==t for x in acks.values()),'received':sum(expected[k]['topic']==t for k in received),'maximum_value_bytes':max(r['value_bytes'] for r in expected.values() if r['topic']==t)} for t in sorted({r['topic'] for r in expected.values()})},'errors':errors,'evidence_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [a.expected,a.log,a.observation]},'limitations':['Functional delivery only; no capacity, fault recovery, retention expiry or infrastructure durability qualification.','Native Java result does not qualify xk6.' if a.client=='java' else 'Selected corrected custom xk6 build only; wrapper does not expose acknowledged partition/offset or commit confirmation.']}
a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));raise SystemExit(bool(errors))
