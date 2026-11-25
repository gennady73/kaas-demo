"""Offline byte/identity/chain verifier. Never declares Kafka fixture acceptance."""
import argparse
import json
import re
from pathlib import Path
from store import PROTOCOL, digest, parse

def verify(raw,seal):
    if seal.get('protocol')!=PROTOCOL or seal.get('export_sha256')!=digest(raw):raise ValueError('seal_hash')
    if raw and not raw.endswith(b'\n'):raise ValueError('truncated')
    rows=raw.splitlines();previous=None;last_ms=-1;terminal=0
    if len(rows)!=seal.get('event_count') or len(rows)>1024:raise ValueError('count')
    for n,line in enumerate(rows):
        envelope=parse(line)
        if set(envelope)!={'event_json','event_sha256'} or digest(envelope['event_json'].encode())!=envelope['event_sha256']:raise ValueError('envelope_hash')
        e=parse(envelope['event_json'])
        if e.get('version')!=1 or e.get('run_id')!=seal.get('run_id') or e.get('plan_sha256')!=seal.get('plan_sha256') or e.get('client_id')!='tenant_fixture' or e.get('event_id')!=seal['run_id']+'/tenant_fixture/'+str(n):raise ValueError('identity')
        if e.get('previous_event_sha256')!=previous:raise ValueError('chain')
        if type(e.get('at_ms')) is not int or not last_ms<=e['at_ms']<=300000:raise ValueError('clock')
        if terminal:raise ValueError('after_terminal')
        if e.get('type')=='fixture_terminal':terminal+=1
        previous=envelope['event_sha256'];last_ms=e['at_ms']
    if seal.get('terminal_present')!=(terminal==1):raise ValueError('terminal')
    return {'byte_integrity':'VERIFIED','event_count':len(rows),'terminal_present':terminal==1,'fixture_acceptance':'NOT_ASSESSED','custody_second_copy':'NOT_ASSESSED'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--export',dest='export_path',required=True);p.add_argument('--seal',required=True);args=p.parse_args()
    try:result=verify(Path(args.export_path).read_bytes(),parse(Path(args.seal).read_bytes()))
    except Exception:raise SystemExit('export verification failed') from None
    print(json.dumps(result))
if __name__=='__main__':main()
