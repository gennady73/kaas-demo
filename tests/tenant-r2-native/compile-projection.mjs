// Offline compiler only. Never imported by the k6 entrypoint.
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {compileContract,canonical} from '../../../kafka-load-test/preflight/tenant/policy.mjs';
const sha=x=>createHash('sha256').update(x).digest('hex');
const source=JSON.parse(fs.readFileSync(new URL('../tenant-r2-integration/inputs/client-contract.json',import.meta.url)));
const c=compileContract(source,{run_id:'offline-r2-native-20261125',seed:2470,sha256:sha,
 contract_sha256:'170b9cdad28508c64bccfd804d8d675efd703b373604a7177fdcb36443b9988a',
 review_hashes:{C3:'e38b184e3563d658eebed782c89638774a8c0ac620ad7562fe74c17bfaa86bce',C6:'0e390f8953269bc49543f56cd036e300fb0ac8f6d48d3b9e8bf006ba9ce9aee2'}});
if(sha(canonical(c))!=='7a2f07d99cc2f026977e9a54b38e029e60df5846860f6e63f045b75937ff8b8d')throw Error('reviewed_source_projection_changed');
const p=JSON.parse(JSON.stringify(c).replaceAll(c.run_id,'r2-native-20261125'));
p.plan_version='tenant-native-candidate-1.1';p.mode='NATIVE_CANDIDATE';p.close_reserve_ms=8000;
p.native_mapping_status='SOURCE_COMPILED_NOT_BROKER_TESTED';
p.native_projection={source_offline_plan_sha256:sha(canonical(c)),mapping_id:'KAAS_R2_CONFLUENT_2_14_V1',module:'k6/x/kaasr2',confluent_go:'2.14.0',k6:'1.7.1',native_retries:0,idempotence:false,delivery_timeout_ms:5000,producer_delivery_wait_ms:6000,metadata_snapshot_timeout_ms:8000,consumer_poll_ms:2000,facade_commit_close_wait_ms:6000,close_bound:'BOUNDED_FACADE_WAIT_QUARANTINE_NATIVE_CANCELLATION_UNPROVEN',existing_smoke_image_usable:false};
p.write_settings_signature=sha(canonical({acks:'all',idempotence:false,native_retries:0,compression:'none',message_max_bytes:3145728,delivery_timeout_ms:5000,delivery_wait_ms:6000,max_in_flight:1}));
const hash=sha(canonical(p));
if(process.argv.includes('--write')){
 fs.writeFileSync(new URL('./plan.json',import.meta.url),JSON.stringify(p,null,2)+'\n');
 fs.writeFileSync(new URL('./projection-lock.mjs',import.meta.url),`// Generated from the reviewed source contract; changing a plan requires recompilation/review.\nexport const EXPECTED_PLAN_SHA256='${hash}';\n`);
 const u=new URL('./runtime.example.json',import.meta.url),g=JSON.parse(fs.readFileSync(u));
 if(g.execution_authorized!==false||g.tests_enabled!==false)throw Error('disabled_record_required');
 g.plan_sha256=hash;fs.writeFileSync(u,JSON.stringify(g,null,2)+'\n');
}else{
 const disk=JSON.parse(fs.readFileSync(new URL('./plan.json',import.meta.url)));
 const {EXPECTED_PLAN_SHA256}=await import('./projection-lock.mjs');
 if(canonical(p)!==canonical(disk)||hash!==EXPECTED_PLAN_SHA256)throw Error('native_projection_drift');
}
console.log(JSON.stringify({native_plan_sha256:hash,source_projection_verified:true,execution_enabled:false}));
