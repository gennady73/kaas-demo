// k6 inspect only. No credentials, HTTP, Kafka constructors or client operations.
import native from 'k6/x/kaasr2';
import {runNativeTenantFixture} from './engine.mjs';
import {bindNative} from './binder.mjs';
import {evidenceTransport} from './transport.mjs';
import {auditNativeEvidence} from './audit.mjs';
for(const name of ['identity','start','now','openProducer','openConsumer','produce','consume','position','probeState','commit','close','snapshot']){
 if(typeof native[name]!=='function')throw new Error('missing_native_api');
}
if(typeof auditNativeEvidence!=='function')throw new Error('missing_auditor');
if(typeof runNativeTenantFixture!=='function'||typeof bindNative!=='function'||typeof evidenceTransport!=='function')throw new Error('missing_binding');
const identity=native.identity();
if(identity.ok!==true||!/^[a-f0-9]{64}$/.test(identity.binary_sha256)||!identity.native_version.startsWith('2.14.0'))throw new Error('native_identity_invalid');
console.log('R2_NATIVE_IDENTITY '+JSON.stringify(identity));
export const options={vus:1,iterations:1};
export default function(){throw new Error('inspection_only_do_not_run');}
