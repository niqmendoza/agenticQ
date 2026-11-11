#!/usr/bin/env python3
"""Combina dos brazos históricos intactos y el primer turno terminado V2.
Conteo de contenido por o200k_base separado de usage nativo. No calcula precios.
"""
import argparse,hashlib,json,sys,importlib.metadata
from pathlib import Path
import tiktoken
from extract_usage import parse
from extract_transcript import extract
ROOT=Path(__file__).resolve().parents[1];OLD=ROOT.parent/'Post Harness';E=ROOT/'evidencias';ENC=tiktoken.get_encoding('o200k_base')
def count(text):return len(ENC.encode(text,disallowed_special=()))
def read(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--rollout',type=Path,required=True);p.add_argument('--coordinator',type=Path);a=p.parse_args();native=parse(a.rollout)
 if not native['turns'] or not native['turns'][0]['completed_utc']:raise ValueError('Esperar el turno completo antes de comparar')
 turn=native['turns'][0];native['scope']='Primer turno V2 completo. Seguimientos se conservan separados; no sumar snapshots acumulativos.';native['semantics']='cached_input ⊂ input; reasoning_output ⊂ output. Total=input+output. Suma de usage por response_id único contrastada contra último turn_token_usage.'
 (E/'usage-v2.json').write_text(json.dumps(native,ensure_ascii=False,indent=2)+'\n');trans=extract(a.rollout,E/'evaluacion/presentado');(E/'transcript-v2.json').write_text(json.dumps(trans,ensure_ascii=False,indent=2)+'\n')
 old_native=read(OLD/'evidencias/usage-nativo.json');old_content=read(OLD/'evidencias/medicion.json');old_validation=read(OLD/'evidencias/validacion-evidencias.json');iterations=[]
 for id,arm,title in [('full','baseline','Lectura completa'),('v1','scripts','Scripts V1')]:
  t=old_native['arms'][arm]['turns'][0];iterations.append({'id':id,'title':title,'usage':t['usage_sum'],'model':t['model'],'effort':t['effort'],'model_responses':t['model_responses'],'local_calls':old_content['arms'][arm]['calls'],'documents_presented':old_validation['arms'][arm]['documents_presented'],'document_tokens':old_content['arms'][arm]['tool_results_tokens_sum'],'cases':old_validation['arms'][arm]['cases'],'seconds':t['observed_duration_seconds'],'quality_note':'Evaluación histórica conservada.'})
 d=E/'evaluacion';calls=sorted((d/'lecturas').glob('*.call.json'));document_tokens=0;paths=set();lines={};literal_errors=[];actual_budgets=[];root=Path(read(OLD/'evidencias/inventario.json')['root'])
 for call in calls:
  argv=read(call)['argv'];cmd=next((x for x in argv if x in ('pack','show','headings','links','verify','status','index')),None);result_file=call.with_name(call.name.replace('.call.json','.result.json'));r=read(result_file)
  if cmd in ('pack','show','headings','links'):document_tokens+=count(result_file.read_text())
  if cmd in ('pack','show'):
   for passage in r.get('passages',[]):
    source=r['sources'][passage['source']];path=source['path'];paths.add(path);original=(root/path).read_text().splitlines();shown=passage['text'].splitlines();expected=[f'{i}|{original[i-1]}' for i in range(passage['start'],passage['end']+1)]
    if shown!=expected:literal_errors.append({'log':result_file.name,'path':path})
    lines.setdefault(path,set()).update(range(passage['start'],passage['end']+1))
   actual_budgets.append({'log':result_file.name,'tokens':count(result_file.read_text()),'chars':len(result_file.read_text()),'limits':r.get('budget')})
 result=read(d/'resultado.json');iterations.append({'id':'v2','title':'Scripts V2','usage':turn['usage_sum'],'model':turn['model'],'effort':turn['effort'],'model_responses':turn['model_responses'],'local_calls':len(calls),'documents_presented':len(paths),'document_tokens':document_tokens,'cases':len(result['cases']),'seconds':turn['observed_duration_seconds'],'quality_note':'Revisión manual pendiente.'})
 integrity=read(E/'v1-integridad-inicial.json');changed=[path for path,h in integrity.items() if not (OLD/path).exists() or sha(OLD/path)!=h];frozen=read(E/'congelado-pre-evaluacion.json');frozen_changed=[path for path,h in frozen['files'].items() if sha(ROOT/path)!=h];source_inv=read(OLD/'evidencias/inventario.json');source_changed=[f['path'] for f in source_inv['files'] if f['included'] and sha(root/f['path'])!=f['sha256']]
 validation={'v1_files_checked':len(integrity),'v1_changed':changed,'frozen_inputs_changed':frozen_changed,'corpus_changed':source_changed,'literal_errors':literal_errors,'unique_source_lines_v2':sum(map(len,lines.values())),'document_payloads':actual_budgets,'all_native_sums_match':all([turn['matches_last_turn_counter']]+[old_native['arms'][arm]['turns'][0]['matches_last_turn_counter'] for arm in ['baseline','scripts']]),'model_effort_equal':len({(x['model'],x['effort']) for x in iterations})==1,'evaluator_reported_elision_repaired':('elisión' in (d/'comportamiento.md').read_text().lower() and any('--replay' in read(f)['argv'] for f in calls)),'terminal_truncation_notice_in_recorded_outputs':any('Warning: truncated output' in (d/'presentado'/item['file']).read_text() for item in trans['items'] if item['category']=='tool_results' and 'file' in item)}
 (E/'validacion-comparativa.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n')
 metrics={'tokenizer':{'package':'tiktoken','version':importlib.metadata.version('tiktoken'),'encoding':'o200k_base','fingerprint_sha256':hashlib.sha256(b''.join(k+str(v).encode() for k,v in sorted(ENC._mergeable_ranks.items(),key=lambda x:x[1]))).hexdigest()},'iterations':iterations,'changes':[], 'coverage':[], 'limitations':[], 'v1_report_sha256':integrity['reporte.html'],'integrity_ok':not changed,'content_scope':'Payload documental CLI registrado, contado una vez con tiktoken 0.14.0 / o200k_base proxy. V1 corrige transformaciones conocidas. V2 tuvo una elisión reportada y reparada con replay, no cuantificable exactamente desde el rollout. Distinto de usage nativo acumulado.','comparison_kind':'Regresión exploratoria histórica de un mock conocido; sin equivalencia causal/estadística.'}
 review_path=E/'revision-calidad.json'
 if review_path.exists():
  review=read(review_path)
  for iteration in iterations:iteration['quality_note']=review.get('quality_notes',{}).get(iteration['id'],iteration['quality_note'])
  for k in ['coverage','limitations','changes']:metrics[k]=review.get(k,[])
 (E/'metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2)+'\n')
 if a.coordinator:
  coord=parse(a.coordinator);current=coord['turns'][-1];cut=turn['started_utc'];records=current['records'];prep=[r for r in records if r['timestamp']<cut];after=[r for r in records if r['timestamp']>=cut];keys=['input_tokens','cached_input_tokens','output_tokens','reasoning_output_tokens','total_tokens'];preparation={'scope':'Snapshot parcial del turno actual del coordinador, preparación anterior a despacho V2 separada de coordinación/informe posterior. No suma al costo por consulta.','turn_id':current['turn_id'],'cutoff_utc':cut,'preparation_responses':len(prep),'preparation_usage':{k:sum(r['usage'][k] for r in prep) for k in keys},'coordination_responses_so_far':len(after),'coordination_usage_so_far':{k:sum(r['usage'][k] for r in after) for k in keys},'source_sha256_at_export':coord['source_sha256_at_export']};(E/'preparacion-usage-parcial.json').write_text(json.dumps(preparation,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'iterations':[{k:x[k] for k in ['id','model_responses','local_calls','documents_presented','document_tokens','cases']}|{'total_tokens':x['usage']['total_tokens']} for x in iterations],'validation':{k:v for k,v in validation.items() if k!='document_payloads'}},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
