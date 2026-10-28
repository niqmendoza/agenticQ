#!/usr/bin/env python3
"""Comprueba integridad, trazabilidad y cobertura material de citas; no valida semántica."""
import argparse,hashlib,json
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--evidence',type=Path,required=True);a=p.parse_args();r=a.evidence.resolve();base=r.parent;inv=json.loads((r/'inventario.json').read_text());source={f['path']:f for f in inv['files'] if f['included']};out={'source_integrity':[],'frozen_inputs':[],'arms':{}}
 for path,meta in source.items():
  b=(Path(inv['root'])/path).read_bytes();snap=(r/'fuentes'/path).read_bytes()
  if hashlib.sha256(b).hexdigest()!=meta['sha256'] or b!=snap:out['source_integrity'].append(path)
 for path,h in json.loads((r/'pre-evaluacion-congelado.json').read_text()).items():
  if hashlib.sha256((base/path).read_bytes()).hexdigest()!=h:out['frozen_inputs'].append(path)
 for arm in ['baseline','scripts']:
  d=r/arm;result=json.loads((d/'resultado.json').read_text());seen={};coverage={};literal_errors=[]
  for f in sorted((d/'lecturas').glob('*.result.*')):
   if arm=='scripts' and int(f.name.split('.')[0])>=32:continue  # cuerpos no mostrados; ver sólo encabezados en revision-citas-presentada
   if arm=='baseline':
    first=f.read_text().splitlines()[0];j=json.loads(first)
    paths=[x['path'] for x in inv['files'] if x['included']][j['offset']:j['offset']+j['returned']]
    for path in paths:coverage.setdefault(path,set()).update(range(1,source[path]['lines']+1))
   else:
    j=json.loads(f.read_text());items=j.get('results',[]) if 'results' in j else [j]
    for item in items:
     path=item.get('path');start=item.get('start');end=item.get('end');text=item.get('excerpt',item.get('text'))
     if path in source and start is not None and end is not None and text is not None:
      lines=(r/'fuentes'/path).read_text().splitlines();expected='\n'.join(lines[start-1:end])
      if text!=expected:literal_errors.append({'log':f.name,'path':path,'start':start,'end':end})
      coverage.setdefault(path,set()).update(range(start,end+1))
      raw=item.get('metadata',{}).get('frontmatter_raw')
      if raw and raw=='\n'.join(lines[:len(raw.splitlines())]):coverage[path].update(range(1,len(raw.splitlines())+1))
  citations=[]
  def walk(obj,location=''):
   if isinstance(obj,dict):
    if 'path' in obj and 'start' in obj and 'end' in obj:
     path=obj['path'];s=obj['start'];e=obj['end'];valid=path in source and isinstance(s,int) and isinstance(e,int) and 1<=s<=e<=source.get(path,{}).get('lines',0)
     presented=valid and set(range(s,e+1)).issubset(coverage.get(path,set()))
     citations.append({'location':location,'path':path,'start':s,'end':e,'range_valid':valid,'entire_range_presented':presented})
    for k,v in obj.items():walk(v,location+'/'+k)
   elif isinstance(obj,list):
    for i,v in enumerate(obj):walk(v,location+'/'+str(i))
  walk(result);frozen=json.loads((d/'congelado.json').read_text());freeze_errors=[]
  # Acepta diccionario filename->hash y wrappers comunes; el coordinador conserva el archivo original.
  for name in ['resultado.json','comportamiento.md']:
   expected=hashlib.sha256((d/name).read_bytes()).hexdigest()
   if expected not in json.dumps(frozen):freeze_errors.append(name)
  case_keys=[]
  for case in result['cases']:case_keys.append(json.dumps([case.get('preconditions'),case.get('steps'),case.get('expected')],ensure_ascii=False,sort_keys=True))
  dup=len(case_keys)-len(set(case_keys))
  out['arms'][arm]={'documents_presented':len(coverage),'unique_source_lines_presented':sum(map(len,coverage.values())),'source_lines_total':sum(f['lines'] for f in source.values()),'literal_extract_errors':literal_errors,'citations':citations,'invalid_citations':sum(not c['range_valid'] for c in citations),'citations_not_fully_presented':sum(not c['entire_range_presented'] for c in citations),'freeze_errors':freeze_errors,'exact_duplicate_cases':dup,'cases':len(case_keys)}
 previous=json.loads((r/'html-previos-hashes.json').read_text());out['previous_html_modified']=[name for name,h in previous.items() if hashlib.sha256((base.parent/name).read_bytes()).hexdigest()!=h]
 (r/'validacion-evidencias.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='arms'},ensure_ascii=False));print(json.dumps({k:{x:y for x,y in v.items() if x!='citations'} for k,v in out['arms'].items()},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
