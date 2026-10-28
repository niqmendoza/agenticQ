#!/usr/bin/env python3
"""Exporta SÓLO telemetría numérica de rollouts locales autorizados.
No copia prompts, texto razonado, herramientas, claves, credenciales ni mensajes.
El formato JSONL local es evidencia de esta versión, no una API estable prometida.
"""
import argparse,collections,hashlib,json
from datetime import datetime, timezone
from pathlib import Path
KEYS=('input_tokens','cached_input_tokens','cache_write_input_tokens','output_tokens','reasoning_output_tokens','total_tokens')
def parse(path):
 meta={};contexts=[];events=[];records=[];last_event=None
 with path.open() as stream:
  for line in stream:
   j=json.loads(line);p=j.get('payload',{});typ=j.get('type')
   if typ=='session_meta':meta={k:p.get(k) for k in ('id','source','model_provider')}
   elif typ=='turn_context':contexts.append({'timestamp':j['timestamp'],**{k:p.get(k) for k in ('turn_id','model','effort')}})
   elif typ=='token_usage_record':
    records.append({'timestamp':j['timestamp'],'turn_id':p.get('turn_id'),'response_id_sha256':hashlib.sha256(p['response_id'].encode()).hexdigest(),'usage':{k:p['usage'].get(k,0) for k in KEYS},'turn_token_usage':{k:p['turn_token_usage'].get(k,0) for k in KEYS}})
   elif typ=='event_msg' and p.get('type') in ('task_started','task_complete','turn_aborted'):events.append({'timestamp':j['timestamp'],'type':p['type'],'turn_id':p.get('turn_id')})
   elif typ=='event_msg' and p.get('type')=='token_count':last_event=p.get('info',{}).get('total_token_usage')
 unique={r['response_id_sha256']:r for r in records};records=list(unique.values());turns=[]
 for tid in dict.fromkeys(c['turn_id'] for c in contexts):
  ctx=next(c for c in contexts if c['turn_id']==tid);rr=[r for r in records if r['turn_id']==tid];summed={k:sum(r['usage'][k] for r in rr) for k in KEYS};ev=[e for e in events if e['turn_id']==tid];starts=[e['timestamp'] for e in ev if e['type']=='task_started'];ends=[e['timestamp'] for e in ev if e['type']=='task_complete'];duration=(datetime.fromisoformat(ends[-1].replace('Z','+00:00'))-datetime.fromisoformat(starts[0].replace('Z','+00:00'))).total_seconds() if starts and ends else None
  turns.append({'turn_id':tid,'model':ctx['model'],'effort':ctx['effort'],'model_responses':len(rr),'usage_sum':summed,'matches_last_turn_counter':bool(rr) and summed==rr[-1]['turn_token_usage'],'started_utc':starts[0] if starts else None,'completed_utc':ends[-1] if ends else None,'observed_duration_seconds':duration,'records':rr})
 return {'source_file':str(path),'source_sha256_at_export':hashlib.sha256(path.read_bytes()).hexdigest(),'metadata':meta,'turns':turns,'last_event_total_token_usage':last_event}
def main():
 p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--scripts',type=Path,required=True);p.add_argument('--coordinator',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args();data={x:parse(getattr(a,x)) for x in ('baseline','scripts')};out={'exported_at_utc':datetime.now(timezone.utc).isoformat(),'scope':'Usage nativo registrado en rollouts locales; suma de respuestas únicas del primer turno de cada evaluador. No es factura.','documentation':['https://learn.chatgpt.com/docs/app-server','https://developers.openai.com/api/docs/guides/agents-api/observability'],'arms':data}
 A=data['baseline']['turns'][0]['usage_sum'];B=data['scripts']['turns'][0]['usage_sum'];out['comparison']={k:{'baseline':A[k],'scripts':B[k],'difference':A[k]-B[k],'reduction_percent':100*(1-B[k]/A[k]) if A[k] else None,'denominator':A[k]} for k in KEYS}
 out['post_evaluation_followup']={'scripts_turns_excluded':[t for t in data['scripts']['turns'][1:]],'reason':'Aclaración de serialización de stdout posterior al congelado; no generación de casos.'}
 A_uncached=A['input_tokens']-A['cached_input_tokens'];B_uncached=B['input_tokens']-B['cached_input_tokens']
 out['comparison']['uncached_input_tokens']={'baseline':A_uncached,'scripts':B_uncached,'difference':A_uncached-B_uncached,'reduction_percent':100*(1-B_uncached/A_uncached),'denominator':A_uncached}
 out['field_semantics']='cached_input_tokens es subconjunto de input_tokens; reasoning_output_tokens es subconjunto de output_tokens. total_tokens=input_tokens+output_tokens. No se suman subconjuntos dos veces. usage se suma por response_id único y se contrasta con último turn_token_usage.'
 if a.coordinator:
  coord=parse(a.coordinator);cut=min(data[x]['turns'][0]['started_utc'] for x in ('baseline','scripts'));records=[r for t in coord['turns'] for r in t['records']];prep=[r for r in records if r['timestamp']<cut];rest=[r for r in records if r['timestamp']>=cut]
  out['coordinator_snapshot']={'cutoff_preparation_utc':cut,'scope':'Snapshot parcial: preparación previa al despacho y coordinación/informe posterior. La tarea del coordinador aún seguía; NO total final del proyecto.','preparation_responses':len(prep),'preparation_usage':{k:sum(r['usage'][k] for r in prep) for k in KEYS},'after_dispatch_responses_so_far':len(rest),'after_dispatch_usage_so_far':{k:sum(r['usage'][k] for r in rest) for k in KEYS},'source_sha256_at_export':coord['source_sha256_at_export'],'last_record_observed_utc':max(r['timestamp'] for r in records)}
 a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'comparison':out['comparison'],'turns':{x:[{k:t[k] for k in ['model','effort','model_responses','usage_sum','matches_last_turn_counter','observed_duration_seconds']} for t in data[x]['turns']] for x in data}},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
