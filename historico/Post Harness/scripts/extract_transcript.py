#!/usr/bin/env python3
"""Exporta payloads visibles del primer turno sin copiar razonamiento ni instrucciones ocultas.
Conteo una vez por ítem del rollout. No es el total acumulado (usar usage nativo).
"""
import argparse,hashlib,json
from pathlib import Path
import tiktoken
ENC=tiktoken.get_encoding('o200k_base')
def serial(v):return v if isinstance(v,str) else json.dumps(v,ensure_ascii=False,separators=(',',':'))
def tok(s):return len(ENC.encode(s,disallowed_special=()))
def extract(path,dest):
 dest.mkdir(parents=True,exist_ok=True);items=[];started=False;counter=0
 for line in path.open():
  j=json.loads(line);p=j.get('payload',{});typ=j.get('type')
  if typ=='event_msg' and p.get('type')=='task_started':
   if started:break
   started=True
  if typ=='event_msg' and p.get('type')=='task_complete':break
  if typ!='response_item':continue
  it=p.get('type');body=None;category=None;save=True
  if it=='additional_tools':category='tool_definitions';body=serial(p.get('tools',[]))
  elif it in ('custom_tool_call','function_call'):category='tool_invocations';body=serial(p.get('input',p.get('arguments','')))
  elif it in ('custom_tool_call_output','function_call_output'):category='tool_results';body=serial(p.get('output',''))
  elif it=='agent_message':category='coordination_messages';body=serial(p.get('content',''))
  elif it=='message':
   role=p.get('role','unknown');category='message_'+role;body=serial(p.get('content',''));save=role not in ('system','developer')
  if body is None:continue
  counter+=1;row={'timestamp':j['timestamp'],'category':category,'tokens_once':tok(body),'bytes':len(body.encode()),'sha256':hashlib.sha256(body.encode()).hexdigest(),'serialization':'raw string' if isinstance(p.get('output',p.get('input',p.get('arguments'))),str) else 'compact JSON proxy'}
  if save:
   name=f'{counter:03}-{category}.txt';(dest/name).write_text(body);row['file']=name
  else:row['withheld']='Sólo conteo y hash; no se exportan instrucciones system/developer'
  items.append(row)
 totals={k:sum(x['tokens_once'] for x in items if x['category']==k) for k in sorted(set(x['category'] for x in items))}
 return {'source_file':str(path),'scope':'Ítems observables del primer turno, contados una vez; razonamiento cifrado excluido; contenedores JSON son proxy de serialización.','items':items,'category_tokens_once':totals,'sum_tokens_once':sum(totals.values())}
def main():
 p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--scripts',type=Path,required=True);p.add_argument('--out-dir',type=Path,required=True);a=p.parse_args();data={arm:extract(getattr(a,arm),a.out_dir/arm/'presentado') for arm in ['baseline','scripts']};(a.out_dir/'transcript-conteos.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v['category_tokens_once'] for k,v in data.items()},indent=2))
if __name__=='__main__':main()
