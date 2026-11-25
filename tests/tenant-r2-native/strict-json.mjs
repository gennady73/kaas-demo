// Bounded duplicate-key-rejecting JSON parser for evidence, not executable data.
export function strictJSON(raw){
 if(typeof raw!=='string'||raw.length>32768)throw Error('json_limit');let pos=0;
 const bad=()=>{throw Error('invalid_json');};
 const ws=()=>{while(/[\t\r\n ]/.test(raw[pos]??'x'))pos++;};
 function string(){const start=pos++;while(pos<raw.length){const c=raw[pos++];if(c==='"')return JSON.parse(raw.slice(start,pos));if(c==='\\')pos++;}bad();}
 function value(depth){if(depth>16)bad();ws();let c=raw[pos];
  if(c==='"')return string();
  if(c==='{'){pos++;ws();const out=Object.create(null),keys=new Set();if(raw[pos]==='}'){pos++;return out;}while(true){ws();if(raw[pos]!=='"')bad();const k=string();if(keys.has(k))bad();keys.add(k);ws();if(raw[pos++]!==':')bad();out[k]=value(depth+1);ws();const sep=raw[pos++];if(sep==='}')return out;if(sep!==',')bad();}}
  if(c==='['){pos++;ws();const out=[];if(raw[pos]===']'){pos++;return out;}while(true){out.push(value(depth+1));ws();const sep=raw[pos++];if(sep===']')return out;if(sep!==',')bad();}}
  for(const [text,v] of [['true',true],['false',false],['null',null]])if(raw.startsWith(text,pos)){pos+=text.length;return v;}
  const n=raw.slice(pos).match(/^-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?/);if(!n)bad();pos+=n[0].length;const number=Number(n[0]);if(!Number.isFinite(number))bad();return number;
 }
 const result=value(0);ws();if(pos!==raw.length)bad();return result;
}
