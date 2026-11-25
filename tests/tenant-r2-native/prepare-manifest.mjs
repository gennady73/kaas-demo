// Offline source freeze only; does not write or enable runtime.json.
import fs from 'node:fs';import {createHash} from 'node:crypto';import {RUNTIME_FILES} from './source-integrity.mjs';
const sha=x=>createHash('sha256').update(x).digest('hex');
const m={version:1,files:Object.fromEntries(RUNTIME_FILES.map(n=>[n,sha(fs.readFileSync(new URL('./'+n,import.meta.url)))]))};
const raw=JSON.stringify(m,null,2)+'\n';fs.writeFileSync(new URL('./runtime-source-manifest.json',import.meta.url),raw);
console.log(JSON.stringify({runtime_manifest_sha256:sha(raw),runtime_config_created:false}));
