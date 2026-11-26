// k6 inspect only: native Admin metadata; no fixture engine or client handles.
import native from 'k6/x/kaasr2';
const started = native.start(Date.now());
if (!started.ok) throw new Error('readonly_admin_start_failed');
console.log('R2_ADMIN ' + JSON.stringify({type: 'identity', result: started}));
for (const topic of ['kaas-sbx-a-events', 'kaas-sbx-a-audit', 'kaas-sbx-b-events', 'kaas-sbx-b-audit']) {
  const result = native.snapshot(topic, topic + '-group');
  console.log('R2_ADMIN ' + JSON.stringify({type: 'group_snapshot', topic, group: topic + '-group', result}));
  if (!result.ok) throw new Error('readonly_admin_snapshot_failed');
}
export const options = {vus: 1, iterations: 1};
export default function () { throw new Error('inspection_only_do_not_run'); }
