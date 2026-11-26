#!/usr/bin/env python3
"""Validate offline against a retained public sandbox OpenAPI-v2 definition set."""
import argparse,copy,gzip,json
from pathlib import Path
import yaml,jsonschema
from validate import HERE,load

def verify(schema_path,rendered=None):
 doc=json.loads(gzip.decompress(schema_path.read_bytes()));doc=copy.deepcopy(doc)
 def normalize(x):
  if isinstance(x,dict):
   if x.get('format')=='int-or-string' or x.get('x-kubernetes-int-or-string'):
    x.pop('type',None);x.pop('format',None);x['anyOf']=[{'type':'integer'},{'type':'string'}]
   for v in x.values():normalize(v)
  elif isinstance(x,list):
   for v in x:normalize(v)
 normalize(doc)
 index={}
 for name,value in doc['definitions'].items():
  for gvk in value.get('x-kubernetes-group-version-kind',[]):
   api=(gvk['group']+'/' if gvk['group'] else '')+gvk['version'];index[(api,gvk['kind'])]=name
 objects,builds,pvc,*_=load()
 if rendered:objects=list(yaml.safe_load_all(rendered.read_text()))
 checked=[]
 for o in [*objects,*builds,pvc]:
  name=index[(o['apiVersion'],o['kind'])];schema={'$ref':'#/definitions/'+name,'definitions':doc['definitions']}
  errors=list(jsonschema.Draft4Validator(schema).iter_errors(o))
  if errors:raise ValueError(o['kind']+'/'+o['metadata']['name']+': '+str(list(errors[0].path))+' '+errors[0].message)
  checked.append({'kind':o['kind'],'name':o['metadata']['name'],'schema':name})
 result={'offline_schema_validation':'PASS','objects':len(checked),'definitions':len(doc['definitions']),'normalization':'Kubernetes int-or-string only','server_admission_or_dry_run':'NOT_RUN','checked':checked};return result
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--schema',required=True,type=Path);p.add_argument('--rendered',type=Path);a=p.parse_args();print(json.dumps(verify(a.schema,a.rendered),indent=2))
