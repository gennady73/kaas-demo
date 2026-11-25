#!/usr/bin/env python3
"""Preparation-only by default. Explicit future delivery creates four Secrets + public CA CM.

No Kafka clients, workload creation, RBAC, source-Secret mutation or overwrite support.
"""
import base64, datetime, json, ssl, subprocess, sys, urllib.error, urllib.request
from pathlib import Path

SERVER = 'https://api.ocp.rddgh.sandbox3088.opentlc.com:6443'
SOURCE_NS = 'kaas-kafka'
DEST_NS = 'kaas-demo'
USERS = tuple('kaas-sbx-'+t+'-'+role for t in ('a','b') for role in ('producer','consumer'))
CA_SOURCE = 'kaas-dev-cluster-ca-cert'
CA_DEST = 'kaas-r2-cluster-ca'

class DeliveryError(Exception):
    pass

SAFE_REASONS = {'DESTINATION_EXISTS_REFUSE_OVERWRITE','USER_IDENTITY_MISMATCH','USER_AUTH_MISMATCH',
    'USER_NOT_READY_CURRENT','SOURCE_BINDING_MISMATCH','SOURCE_OWNER_MISMATCH','PASSWORD_MISSING_OR_INVALID',
    'CA_SOURCE_MISMATCH','CA_BUNDLE_INVALID','SOURCE_CHANGED_DURING_STAGING','CREATE_IDENTITY_MISMATCH',
    'WRONG_CLUSTER','WRONG_EXECUTOR_IDENTITY','METADATA_NEGOTIATION_FAILED','USER_NOT_ALLOWLISTED',
    'SOURCE_NOT_ALLOWLISTED','DESTINATION_NOT_ALLOWLISTED','DESTINATION_NAMESPACE_REFUSED',
    'CREATE_SCOPE_REFUSED','RECEIPT_ALREADY_EXISTS'}

def safe_reason(error):
    value = error.args[0] if error.args and type(error.args[0]) is str else None
    if value in SAFE_REASONS: return value
    if value and len(value)==8 and value.startswith('HTTP_') and value[5:].isdigit(): return value
    return 'UNCLASSIFIED_DELIVERY_ERROR'

def require(ok, code):
    if not ok: raise DeliveryError(code)

def stamp(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def meta(obj): return {k:obj.get('metadata',{}).get(k) for k in ('name','namespace','uid','resourceVersion')}

def deliver(api, record):
    """All Secret material stays inside this call; record only UIDs/RVs, never values/hashes."""
    record.update(status='PREFLIGHT',started_at_utc=stamp(),created=[],source_metadata=[])
    # Reject all destination collisions before reading source credentials or creating anything.
    for kind,name in [('configmaps',CA_DEST)]+[('secrets',u) for u in USERS]:
        require(api.destination_metadata(kind,name) is None, 'DESTINATION_EXISTS_REFUSE_OVERWRITE')
    staged=[]
    for user in USERS:
        obj=api.user(user)
        require(obj.get('metadata',{}).get('name')==user, 'USER_IDENTITY_MISMATCH')
        require(obj.get('spec',{}).get('authentication',{}).get('type')=='scram-sha-512', 'USER_AUTH_MISMATCH')
        status=obj.get('status',{})
        require(status.get('secret')==user and status.get('observedGeneration')==obj['metadata'].get('generation') and any(c.get('type')=='Ready' and c.get('status')=='True' for c in status.get('conditions',[])), 'USER_NOT_READY_CURRENT')
        secret=api.source_secret(user)
        sm=secret.get('metadata',{})
        require(sm.get('name')==user and sm.get('namespace')==SOURCE_NS and sm.get('labels',{}).get('strimzi.io/cluster')=='kaas-dev', 'SOURCE_BINDING_MISMATCH')
        require(any(o.get('kind')=='KafkaUser' and o.get('name')==user and o.get('uid')==obj['metadata']['uid'] for o in sm.get('ownerReferences',[])), 'SOURCE_OWNER_MISMATCH')
        value=secret.get('data',{}).get('password')
        try: valid=isinstance(value,str) and bool(base64.b64decode(value,validate=True))
        except Exception: valid=False
        require(valid,'PASSWORD_MISSING_OR_INVALID')
        record['source_metadata'].append(meta(secret))
        staged.append(('secrets',{'apiVersion':'v1','kind':'Secret','metadata':{'name':user,'namespace':DEST_NS,'labels':{'kaas.example.com/component':'r2-preparation','kaas.example.com/principal':user}},'type':'Opaque','data':{'password':value}}))
    ca=api.source_secret(CA_SOURCE)
    require(ca.get('metadata',{}).get('name')==CA_SOURCE and ca.get('metadata',{}).get('namespace')==SOURCE_NS,'CA_SOURCE_MISMATCH')
    try:
        pem=base64.b64decode(ca['data']['ca.crt'],validate=True).decode('ascii')
        ssl.create_default_context().load_verify_locations(cadata=pem)
    except Exception: raise DeliveryError('CA_BUNDLE_INVALID') from None
    record['source_metadata'].append(meta(ca))
    staged.insert(0,('configmaps',{'apiVersion':'v1','kind':'ConfigMap','metadata':{'name':CA_DEST,'namespace':DEST_NS,'labels':{'kaas.example.com/component':'r2-preparation'}},'data':{'ca.crt':pem}}))
    # Metadata recheck detects rotations during staging; later rotation still needs explicit refresh.
    for old in record['source_metadata']:
        current=api.source_metadata(old['name'])
        require(all(current.get(k)==old.get(k) for k in ('name','namespace','uid','resourceVersion')), 'SOURCE_CHANGED_DURING_STAGING')
    record['status']='DELIVERING'
    for kind,obj in staged:
        created=api.create(kind,obj)
        require(created.get('metadata',{}).get('name')==obj['metadata']['name'] and created.get('metadata',{}).get('namespace')==DEST_NS,'CREATE_IDENTITY_MISMATCH')
        record['created'].append(dict(meta(created),kind=obj['kind']))
    record.update(status='DELIVERED_NOT_CLIENT_TESTED',finished_at_utc=stamp(),credential_values_in_receipt=False)
    return record

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): return None

class LiveAPI:
    def __init__(self,ca_file):
        server=subprocess.check_output(['oc','config','view','--minify','-o','jsonpath={.clusters[0].cluster.server}'],text=True).strip()
        require(server.rstrip('/')==SERVER,'WRONG_CLUSTER')
        self.token=subprocess.check_output(['oc','whoami','--show-token'],text=True,stderr=subprocess.DEVNULL).strip()
        self.opener=urllib.request.build_opener(urllib.request.HTTPSHandler(context=ssl.create_default_context(cafile=str(ca_file))),NoRedirect())
        require(self.request('/apis/user.openshift.io/v1/users/~')['metadata']['name']=='admin','WRONG_EXECUTOR_IDENTITY')
    def request(self,path,body=None,metadata=False,missing_ok=False):
        accept='application/json;as=PartialObjectMetadata;g=meta.k8s.io;v=v1' if metadata else 'application/json'
        headers={'Authorization':'Bearer '+self.token,'Accept':accept}
        if body is not None: headers['Content-Type']='application/json'
        try:
            with self.opener.open(urllib.request.Request(SERVER+path,data=None if body is None else json.dumps(body).encode(),headers=headers),timeout=20) as f:obj=json.load(f)
        except urllib.error.HTTPError as e:
            if missing_ok and e.code==404:return None
            raise DeliveryError('HTTP_'+str(e.code)) from None
        if metadata:
            require(obj.get('kind')=='PartialObjectMetadata' and 'data' not in obj,'METADATA_NEGOTIATION_FAILED')
        return obj
    def user(self,name):
        require(name in USERS,'USER_NOT_ALLOWLISTED')
        return self.request('/apis/kafka.strimzi.io/v1/namespaces/'+SOURCE_NS+'/kafkausers/'+name)
    def source_secret(self,name):
        require(name in USERS+(CA_SOURCE,),'SOURCE_NOT_ALLOWLISTED')
        return self.request('/api/v1/namespaces/'+SOURCE_NS+'/secrets/'+name)
    def source_metadata(self,name):
        require(name in USERS+(CA_SOURCE,),'SOURCE_NOT_ALLOWLISTED')
        return meta(self.request('/api/v1/namespaces/'+SOURCE_NS+'/secrets/'+name,metadata=True))
    def destination_metadata(self,kind,name):
        require((kind=='secrets' and name in USERS) or (kind=='configmaps' and name==CA_DEST),'DESTINATION_NOT_ALLOWLISTED')
        return self.request('/api/v1/namespaces/'+DEST_NS+'/'+kind+'/'+name,metadata=True,missing_ok=True)
    def create(self,kind,obj):
        require(obj['metadata']['namespace']==DEST_NS,'DESTINATION_NAMESPACE_REFUSED')
        name=obj['metadata']['name']
        require((kind=='secrets' and name in USERS and obj['kind']=='Secret' and set(obj['data'])=={'password'}) or (kind=='configmaps' and name==CA_DEST and obj['kind']=='ConfigMap' and set(obj['data'])=={'ca.crt'}),'CREATE_SCOPE_REFUSED')
        # Create-only; a racing existing object returns409 and is never patched or replaced.
        return self.request('/api/v1/namespaces/'+DEST_NS+'/'+kind,obj)

def main(argv):
    if '--execute-delivery' not in argv:
        print(json.dumps({'status':'PREPARATION_ONLY_NOT_EXECUTED','creates_if_later_authorized':{'Secrets':4,'public_CA_ConfigMap':1},'client_tests':False}))
        return 0
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute-delivery',action='store_true')
    parser.add_argument('--api-ca-file',type=Path,required=True)
    parser.add_argument('--receipt',type=Path,required=True)
    args=parser.parse_args(argv)
    require(not args.receipt.exists(),'RECEIPT_ALREADY_EXISTS')
    record={'record_revision':'0.1','source_namespace':SOURCE_NS,'destination_namespace':DEST_NS,'client_tests':False,'mutations':'CREATE_ONLY_FOUR_SECRETS_AND_ONE_PUBLIC_CA_CONFIGMAP'}
    try:
        deliver(LiveAPI(args.api_ca_file),record)
    except DeliveryError as e:
        record.update(status='HOLD_PRESERVE_PARTIAL_CREATES',reason=safe_reason(e))
    except Exception:
        # No arbitrary exception/config/body text in receipt or console.
        record.update(status='HOLD_PRESERVE_PARTIAL_CREATES',reason='UNCLASSIFIED_DELIVERY_ERROR')
    args.receipt.parent.mkdir(parents=True,exist_ok=True)
    args.receipt.write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({'status':record['status'],'created_count':len(record.get('created',[])),'client_tests':False}))
    return 0 if record['status']=='DELIVERED_NOT_CLIENT_TESTED' else 2

if __name__=='__main__':
    try:sys.exit(main(sys.argv[1:]))
    except Exception:print('{"status":"REFUSED","reason":"SAFE_PREFLIGHT_ERROR"}');sys.exit(2)
