#!/usr/bin/env python3
"""Prepare exact offline binary Docker build inputs. Never builds/pushes/runs images."""
import argparse,gzip,hashlib,io,json,tarfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
NATIVE=REPO/'tests/tenant-r2-native'

def sha(raw):return hashlib.sha256(raw).hexdigest()
def prepare(binary,output):
 cfg=json.loads((HERE/'inputs.json').read_text());assert cfg['build_enabled'] is False
 public=json.loads((NATIVE/'runtime-source-manifest.json').read_text())
 for name,digest in public['files'].items():assert sha((NATIVE/name).read_bytes())==digest,name
 receipt=(REPO/cfg.get('source_validation_receipt','docs/r2-native-review/offline-build-validation.json')).resolve()
 assert REPO in receipt.parents,'receipt_outside_repository'
 validation=json.loads(receipt.read_text())
 assert validation['status']=='OFFLINE_BUILD_AND_REVIEW_CHECKS_PASS'
 assert validation['binary_sha256']==cfg['binary_sha256']
 assert validation['runtime_manifest_sha256']==cfg['runtime_manifest_sha256']
 for name,digest in validation['source_sha256'].items():assert sha((NATIVE/name).read_bytes())==digest,name
 raw_binary=binary.read_bytes();assert sha(raw_binary)==cfg['binary_sha256'],'reviewed_binary_required'
 output.mkdir(parents=True,exist_ok=False)
 reports={}
 for role in ['runner','sink']:
  data={'Dockerfile':(HERE/'build'/(role+'.Dockerfile')).read_bytes()}
  if role=='runner':
   data['k6']=raw_binary;data['client-guard.sh']=(HERE/'build/client-guard.sh').read_bytes()
   for name in [*public['files'],'runtime-source-manifest.json','inspect.js']:data['r2/'+name]=(NATIVE/name).read_bytes()
  else:
   data['sink-guard.sh']=(HERE/'build/sink-guard.sh').read_bytes()
   for name in ['server.py','store.py','verify_export.py']:data['sink/'+name]=(NATIVE/'sink'/name).read_bytes()
  manifest={'role':role,'base_image':cfg['base_image'],'source_commit':cfg['source_commit'],'source_commit_scope':cfg['source_commit_scope'],'actual_image_build':'NOT_RUN','files':{name:sha(raw) for name,raw in data.items()}}
  data['BUILD-INPUTS.json']=(json.dumps(manifest,indent=2)+'\n').encode()
  dest=output/(role+'-context.tar.gz')
  with dest.open('wb') as f:
   with gzip.GzipFile(fileobj=f,mode='wb',mtime=0,filename='') as gz:
    with tarfile.open(fileobj=gz,mode='w') as t:
     for name,raw in sorted(data.items()):
      entry=tarfile.TarInfo(name);entry.size=len(raw);entry.mode=0o755 if name=='k6' or name.endswith('.sh') else 0o644;t.addfile(entry,io.BytesIO(raw))
  with tarfile.open(dest) as t:
   assert set(t.getnames())==set(data)
   for name,raw in data.items():assert t.extractfile(name).read()==raw,name
  reports[role]={'path':str(dest),'sha256':sha(dest.read_bytes()),'bytes':dest.stat().st_size,'archive_entries_verified':len(data),'actual_image_build':'NOT_RUN','files':manifest['files']}
 (output/'contexts.json').write_text(json.dumps(reports,indent=2)+'\n');print(json.dumps({k:{x:v[x] for x in ['path','sha256','bytes','archive_entries_verified']} for k,v in reports.items()}))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--binary',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args();prepare(a.binary.resolve(),a.output.resolve())
