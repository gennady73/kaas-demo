#!/usr/bin/env python3
"""Verify a previously downloaded skopeo dir bundle offline. Never runs images."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import render


def verify(image_dir):
    lock = json.loads((ROOT / 'redhat-release-lock.json').read_text())
    raw = (image_dir / 'manifest.json').read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if lock['bundle_image'].split('@sha256:')[1] != digest:
        raise ValueError('bundle manifest digest mismatch')
    manifest = json.loads(raw)
    for item in [manifest['config']] + manifest['layers']:
        blob = image_dir / item['digest'].split(':')[1]
        if blob.stat().st_size != item['size'] or hashlib.sha256(blob.read_bytes()).hexdigest() != item['digest'].split(':')[1]:
            raise ValueError('bundle blob size/digest mismatch')
    # This exact vendor bundle is a single-layer, non-runnable manifest image.
    if len(manifest['layers']) != 1:
        raise ValueError('unexpected bundle layering; review extraction semantics')
    with tarfile.open(fileobj=io.BytesIO((image_dir / manifest['layers'][0]['digest'].split(':')[1]).read_bytes())) as archive:
        def read(name):
            return yaml.safe_load(archive.extractfile(name).read())
        csv = read('manifests/apicurio-registry-3.clusterserviceversion.yaml')
        crd = read('manifests/registry.apicur.io_apicurioregistries3.yaml')
        annotations = read('metadata/annotations.yaml')['annotations']
    if csv['metadata']['name'] != lock['starting_csv'] or csv['spec']['version'] != lock['version']:
        raise ValueError('CSV release mismatch')
    if annotations['operators.operatorframework.io.bundle.package.v1'] != lock['package']:
        raise ValueError('bundle package mismatch')
    container = csv['spec']['install']['spec']['deployments'][0]['spec']['template']['spec']['containers'][0]
    env = {v['name']: v for v in container['env']}
    if container['image'] != lock['operator_image']:
        raise ValueError('operator image mismatch')
    for env_key, lock_key in [('RELATED_IMAGE_REGISTRY_APP_IMAGE', 'app_image'), ('RELATED_IMAGE_REGISTRY_UI_IMAGE', 'ui_image')]:
        if env[env_key]['value'] != lock[lock_key]:
            raise ValueError('operator default image mismatch')
    if not {lock[k] for k in ['operator_image', 'app_image', 'ui_image']} <= {v['image'] for v in csv['spec']['relatedImages']}:
        raise ValueError('related image mismatch')
    if not any(v['type'] == 'OwnNamespace' and v['supported'] for v in csv['spec']['installModes']):
        raise ValueError('OwnNamespace unsupported')
    watch = env['APICURIO_OPERATOR_WATCHED_NAMESPACES']['valueFrom']['fieldRef']['fieldPath']
    if watch != "metadata.annotations['olm.targetNamespaces']":
        raise ValueError('unexpected watched namespace source')
    if crd['metadata']['name'] != 'apicurioregistries3.registry.apicur.io':
        raise ValueError('wrong CRD')
    version = next(v for v in crd['spec']['versions'] if v['name'] == 'v1' and v['served'])
    schema = version['schema']['openAPIV3Schema']
    if schema != json.loads((ROOT / lock['crd_schema_file']).read_text()):
        raise ValueError('cached downstream schema differs from bundle')
    stages, missing = render.load(json.loads((ROOT / 'inputs.json').read_text()))
    render.validate(stages)
    return {'result': 'PASS_EXACT_BUNDLE_OFFLINE', 'manifest_sha256': digest,
            'csv': csv['metadata']['name'], 'version': csv['spec']['version'],
            'blob_sha256_checks': len(manifest['layers']) + 1,
            'registry_cr_schema': 'PASS_SPEC_AND_STRICT_FIELDS',
            'watch_mapping': watch, 'missing_values': missing,
            'keycloak_schema': 'upstream26.4.7 family only',
            'server_admission_runtime_signature_validation': 'NOT_EXECUTED'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image-dir', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.image_dir), indent=2))
