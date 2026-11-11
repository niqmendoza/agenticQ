#!/usr/bin/env python3
"""Cuenta artefactos OBSERVABLES: no mide inferencia, caché ni razonamiento interno.
Requiere tiktoken==0.14.0. Ejecute al cerrar ambas evaluaciones.
"""
import argparse,hashlib,importlib.metadata,json,platform,sys
from pathlib import Path
import tiktoken
ENC=tiktoken.get_encoding('o200k_base')
def tokens(s):return len(ENC.encode(s,disallowed_special=()))
def record(p):
 b=p.read_bytes();t=b.decode('utf-8');return dict(path=p.as_posix(),bytes=len(b),tokens=tokens(t),sha256=hashlib.sha256(b).hexdigest())
def main():
 p=argparse.ArgumentParser();p.add_argument('--evidence',type=Path,required=True);a=p.parse_args();r=a.evidence.resolve();inv=json.loads((r/'inventario.json').read_text());raw=[(r/'fuentes'/f['path']).read_text() for f in inv['files'] if f['included']]
 common=(r/'consigna-comun.md').read_text();dispatch=json.loads((r/'despachos.json').read_text());out={'scope':'Proxy de contenido documental observable; cada pieza se cuenta una vez. Usage nativo acumulado en usage-nativo.json.','tokenizer':{'package':'tiktoken','version':importlib.metadata.version('tiktoken'),'encoding':'o200k_base','encoding_fingerprint_sha256':hashlib.sha256(b''.join(k+str(v).encode() for k,v in sorted(ENC._mergeable_ranks.items(),key=lambda x:x[1]))).hexdigest()},'environment':{'python':sys.version,'platform':platform.platform()},'corpus':{'documents':len(raw),'bytes':sum(f['bytes'] for f in inv['files'] if f['included']),'raw_tokens_sum_per_file':sum(tokens(t) for t in raw),'raw_tokens_concatenated':tokens('\n'.join(raw)),'annotated_context_tokens':tokens((r/'corpus_completo.txt').read_text()),'snapshot_revision':inv['revision']},'arms':{}}
 for arm in ['baseline','scripts']:
  d=r/arm;results=sorted((d/'lecturas').glob('*.result.*'));calls=sorted((d/'lecturas').glob('*.invocation.json'));generated=[d/'resultado.json',d/'comportamiento.md'];modality=(r/f'modalidad-{arm}.md').read_text();inputs=[common,modality,dispatch[arm]['dispatch_message']]
  if arm=='scripts':inputs.append((r/'consultas-evaluacion.json').read_text())
  native_chunks=[f.read_text() for f in results]
  if arm=='scripts':
   # 032..052 fueron consumidas por Python; sólo encabezados se presentaron.
   shown_results=[f for f in results if int(f.name.split('.')[0])<=31]
   chunks=[f.read_text() for f in shown_results]+[(d/'lecturas/revision-citas-presentada.txt').read_text()]
   inputs.extend(json.loads((r/'intervenciones.json').read_text())['during_scripts_evaluation'])
  else:shown_results=results;chunks=native_chunks
  invocations=[f.read_text() for f in calls];outputs=[f.read_text() for f in generated]
  bundle='\n\n'.join(['## Instrucción observable '+str(i+1)+'\n'+t for i,t in enumerate(inputs)]+['## Contexto documental presentado '+str(i+1)+'\n'+t for i,t in enumerate(chunks)])
  (r/f'prompt-construido-{arm}.txt').write_text(bundle)
  stats=dict(native_local_results_tokens_sum=sum(map(tokens,native_chunks)),instructions_tokens_sum=sum(map(tokens,inputs)),tool_results_tokens_sum=sum(map(tokens,chunks)),serialized_invocations_proxy_tokens_sum=sum(map(tokens,invocations)),generated_artifact_tokens_sum=sum(map(tokens,outputs)),constructed_prompt_tokens=tokens(bundle),calls=len(calls),result_files=[record(f) for f in results],generated_files=[record(f) for f in generated])
  stats['observed_artifact_sum_proxy']=stats['instructions_tokens_sum']+stats['tool_results_tokens_sum']+stats['serialized_invocations_proxy_tokens_sum']+stats['generated_artifact_tokens_sum']
  elapsed=0;dates=[]
  for f in calls:
   j=json.loads(f.read_text());elapsed+=j.get('local_seconds',0);dates.extend([j.get('started_utc',''),j.get('finished_utc','')])
  stats.update(local_tool_seconds_sum=elapsed,first_tool_utc=min(filter(None,dates),default=None),last_tool_utc=max(filter(None,dates),default=None))
  out['arms'][arm]=stats
 a0=out['arms']['baseline'];a1=out['arms']['scripts'];out['comparison']={}
 for key in ['tool_results_tokens_sum','constructed_prompt_tokens','observed_artifact_sum_proxy']:
  out['comparison'][key]={'baseline':a0[key],'scripts':a1[key],'difference':a0[key]-a1[key],'reduction_percent':100*(1-a1[key]/a0[key]) if a0[key] else None,'denominator':f'baseline.{key}'}
 out['preparation']={'index_bytes':(r/'indice.sqlite').stat().st_size,'local_llm_calls':0,'corpus_tokens_processed_locally':out['corpus']['raw_tokens_sum_per_file'],'calibration_result_tokens_sum':sum(tokens(f.read_text()) for f in (r/'calibracion').glob('*.result.json')),'notes':'Indexación/validación procesan bytes en Python sin inferencia. El coordinador leyó el corpus para diseñar el ensayo; su preparación tiene snapshot nativo separado en usage-nativo.json. No pertenece al costo por consulta del producto.'}
 (r/'medicion.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k in ('tokenizer','corpus','comparison','preparation')},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
