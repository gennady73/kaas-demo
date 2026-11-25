import {strictJSON} from './strict-json.mjs';
export const RUNTIME_FILES=Object.freeze(['ascii.mjs','audit.mjs','binder.mjs','engine.mjs','entrypoint.js','native-policy.mjs','plan.json','projection-lock.mjs','source-integrity.mjs','strict-json.mjs','transport.mjs']);
export function verifyRuntimeSources(read,sha,expected){
 const raw=read('runtime-source-manifest.json');
 if(typeof raw!=='string'||raw.length>8192||sha(raw)!==expected)throw Error('runtime_manifest_hash');
 const m=strictJSON(raw);
 if(m.version!==1||Object.keys(m).sort().join(',')!=='files,version'||!m.files||Object.keys(m.files).sort().join(',')!==[...RUNTIME_FILES].sort().join(','))throw Error('runtime_manifest_schema');
 for(const name of RUNTIME_FILES){if(!/^[a-f0-9]{64}$/.test(m.files[name])||sha(read(name))!==m.files[name])throw Error('runtime_source_hash');}
 return true;
}
