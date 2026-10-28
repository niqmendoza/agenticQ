#!/usr/bin/env python3
"""Lectura baseline registrada de documentos completos, con lotes explícitos."""
import argparse,json,sys,time
from datetime import datetime,timezone
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--snapshot',required=True);p.add_argument('--offset',type=int,default=0);p.add_argument('--limit',type=int,default=5);p.add_argument('--log-dir',required=True);a=p.parse_args()
tick=time.perf_counter();started=datetime.now(timezone.utc).isoformat();base=Path(a.snapshot).resolve();inv=json.loads((base/'inventario.json').read_text());files=[r for r in inv['files'] if r['included']]
if a.offset<0 or not 1<=a.limit<=10:p.error('offset >=0; limit 1..10')
parts=[]
for r in files[a.offset:a.offset+a.limit]:
 t=(base/'fuentes'/r['path']).read_text();parts.append(f"\n=== {r['path']} sha256={r['sha256']} ===\n"+''.join(f'{i}: {l}\n' for i,l in enumerate(t.splitlines(),1)))
next_offset=a.offset+a.limit if a.offset+a.limit<len(files) else None
output=json.dumps({'revision':inv['revision'],'total_documents':len(files),'offset':a.offset,'returned':len(parts),'next_offset':next_offset},ensure_ascii=False)+'\n'+''.join(parts)
d=Path(a.log_dir);d.mkdir(parents=True,exist_ok=True);n=len(list(d.glob('*.invocation.json')))+1
(d/f'{n:03}.invocation.json').write_text(json.dumps({'argv':sys.argv,'started_utc':started,'finished_utc':datetime.now(timezone.utc).isoformat(),'local_seconds':time.perf_counter()-tick},ensure_ascii=False,indent=2)+'\n');(d/f'{n:03}.result.txt').write_text(output)
print(output,end='')
