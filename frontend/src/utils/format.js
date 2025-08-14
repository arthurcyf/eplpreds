export function fmtRange(a,b){ return `${a} → ${b}`; }
export function fmtTime(iso){ try{ return new Date(iso).toLocaleString(); }catch{ return iso; } }
