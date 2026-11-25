// k6 inspect only. No credentials, HTTP, Kafka constructors or client operations.
import native from 'k6/x/kaasr2';
import {runNativeTenantFixture} from './engine.mjs';
import {bindNative} from './binder.mjs';
import {evidenceTransport} from './transport.mjs';
for(const name of ['start','now','openProducer','openConsumer','produce','consume','position','probeState','commit','close','snapshot']){
 if(typeof native[name]!=='function')throw new Error('missing_native_api');
}
if(typeof runNativeTenantFixture!=='function'||typeof bindNative!=='function'||typeof evidenceTransport!=='function')throw new Error('missing_binding');
export const options={vus:1,iterations:1};
export default function(){throw new Error('inspection_only_do_not_run');}
