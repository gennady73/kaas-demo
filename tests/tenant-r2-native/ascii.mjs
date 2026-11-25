export function ascii(value) {
  if(typeof value==='string') return value;
  if(value instanceof ArrayBuffer) value=new Uint8Array(value);
  if(!value || typeof value.length!=='number') throw new Error('unsupported extension byte representation');
  const chunks=[];
  for(let i=0;i<value.length;i+=4096) {
    const end=Math.min(i+4096,value.length); let s='';
    for(let j=i;j<end;j++) { if(!Number.isInteger(value[j]) || value[j]<0 || value[j]>127) throw new Error('non-ASCII bytes'); s+=String.fromCharCode(value[j]); }
    chunks.push(s);
  }
  return chunks.join('');
}
