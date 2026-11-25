// No shipped runtime.json: preparation cannot start a native client by default.
import native from 'k6/x/kaasr2';
import crypto from 'k6/crypto';
import http from 'k6/http';
import {sleep} from 'k6';
import {verifyRuntimeSources} from './source-integrity.mjs';
import {validateExecution} from './native-policy.mjs';
import {bindNative} from './binder.mjs';
import {evidenceTransport} from './transport.mjs';
import {runNativeTenantFixture} from './engine.mjs';
const sha=value=>crypto.sha256(value,'hex');
const plan=JSON.parse(open('/r2/plan.json'));
// All readiness checks precede credentials, native construction and HTTP.
const gate=validateExecution(plan,JSON.parse(open('/r2/runtime.json')),sha);
verifyRuntimeSources(name=>open('/r2/'+name),sha,gate.package_sha256);
if(__ENV.K6_HTTP_DEBUG||__ENV.K6_VERBOSE==='true')throw new Error('unsafe_debug_configuration');
const identity=native.identity();
if(identity.ok!==true||identity.binary_sha256!==gate.binary_sha256||!identity.native_version.startsWith('2.14.0'))throw new Error('native_binary_identity');
const writerToken=open('/evidence-auth/writer-token').trim();
if(writerToken.length<32)throw new Error('evidence_auth_required');
// Trust store must contain the separately verified sink CA AND Kafka CA.
export const options={insecureSkipTLSVerify:false,maxRedirects:0,scenarios:{fixture:{executor:'shared-iterations',vus:1,iterations:1,maxDuration:'270s',gracefulStop:'0s'}}};
export default function(){
 const transport=evidenceTransport(http.post,gate.sink_origin,writerToken,()=>native.now());
 const deps=bindNative(native,transport,plan,gate,sha,sleep);
 const result=runNativeTenantFixture(plan,deps);
 // No record values, exceptions, options or credentials in console evidence.
 console.log(JSON.stringify({run_id:result.run_id,status:result.status,duration_ms:result.duration_ms,cleanup_complete:result.cleanup_complete}));
 if(result.status!=='NATIVE_COMPLETE')throw new Error('tenant_fixture_incomplete');
}
