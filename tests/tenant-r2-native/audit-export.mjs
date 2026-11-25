#!/usr/bin/env node
// Offline semantic review of reported evidence. No Kafka or native client imports.
import fs from 'node:fs';import {createHash} from 'node:crypto';import {auditNativeEvidence} from './audit.mjs';
const files=process.argv.slice(2);
if(files.length!==4)throw Error('usage: audit-export.mjs PLAN EXPORT SEAL OBSERVATION');
try{
 const [plan,raw,seal,observation]=files.map((p,i)=>{if(fs.statSync(p).size>32*1024*1024)throw Error('file_limit');const s=fs.readFileSync(p,'utf8');return i===1?s:JSON.parse(s);});
 const r=auditNativeEvidence(plan,raw,seal,observation,s=>createHash('sha256').update(s).digest('hex'));
 console.log(JSON.stringify(r));if(r.status!=='NATIVE_EVIDENCE_MATCHED')process.exitCode=2;
}catch(_){console.error('native evidence audit failed');process.exitCode=2;}
