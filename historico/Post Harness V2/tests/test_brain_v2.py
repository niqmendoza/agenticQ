import json,sqlite3,sys,tempfile,unittest,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'scripts'))
import brain as b
class V2Tests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.root=Path(self.t.name)/'corpus';self.root.mkdir();self.db=Path(self.t.name)/'i.sqlite'
 def put(self,p,t):
  f=self.root/p;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(t);return f
 def context(self):
  b.index(self.root,self.db);c,cfg,settings=b.checked(self.db);self.addCleanup(c.close);return c,cfg,settings,b.session_load(None,cfg['revision'])
 def test_empty(self):
  c,cfg,st,s=self.context();r=b.pack(c,cfg,st,s,['nada'],b.Budget(10000));self.assertEqual(r['passages'],[]);self.assertEqual(r['queries'][0]['matching_documents'],0)
 def test_literal_numbered_lines(self):
  original='---\ntitle: "Guía"\n---\n# Política\nNo borrar | antes de confirmar.\n## Excepción\nPendiente.';self.put('a.md',original);c,cfg,st,s=self.context();r=b.pack(c,cfg,st,s,['Política'],b.Budget(10000))
  for p in r['passages']:
   text='\n'.join(line.split('|',1)[1] for line in p['text'].splitlines());self.assertEqual(text,'\n'.join(original.splitlines()[p['start']-1:p['end']]))
  self.assertTrue(r['sources'][b.sid('a.md')]['document_complete'])
 def test_session_dedupe_replay(self):
  self.put('a.md','# Renovar\nUna regla\nOtra regla');c,cfg,st,s=self.context();first=b.pack(c,cfg,st,s,['Renovar'],b.Budget(10000));second=b.pack(c,cfg,st,s,['Renovar'],b.Budget(10000));self.assertTrue(first['passages']);self.assertEqual(second['passages'],[]);self.assertEqual(second['seen_lines_skipped'],3);self.assertTrue(b.show(c,cfg,s,'a.md',1,None,120,b.Budget(10000),True)['passages'])
 def test_range_complete_distinct_document_complete(self):
  self.put('a.md','# Largo\n'+'\n'.join(f'L{i}' for i in range(99)));c,cfg,st,s=self.context();r=b.show(c,cfg,s,'a.md',1,20,120,b.Budget(10000));self.assertTrue(r['range_complete']);self.assertFalse(r['document_complete']);self.assertEqual(r['sources'][b.sid('a.md')]['missing_ranges'],[[21,100]])
  r=b.show(c,cfg,s,'a.md',1,100,120,b.Budget(20000));self.assertEqual(r['passages'][0]['start'],21);self.assertTrue(r['document_complete'])
 def test_strict_char_budget_and_pending(self):
  self.put('a.md','# Política\n'+'\n'.join('Regla '+str(i)+' '+('z'*80) for i in range(120)));c,cfg,st,s=self.context();r=b.pack(c,cfg,st,s,['Política'],b.Budget(3500));self.assertLessEqual(len(b.dump(r)),3500);self.assertGreater(r['pending_total'],0);self.assertFalse(r['sources'] or r['passages']) # 40 líneas enteras no caben; nunca corte silencioso
 def test_partial_budget_can_advance(self):
  self.put('a.md','# Política\n'+'\n'.join('Regla '+str(i)+' '+('z'*20) for i in range(120)));c,cfg,st,s=self.context();r=b.pack(c,cfg,st,s,['Política'],b.Budget(3500));self.assertTrue(r['passages']);self.assertLessEqual(len(b.dump(r)),3500);self.assertFalse(r['sources'][b.sid('a.md')]['document_complete']);self.assertTrue(r['pending'])
 def test_graph_expansion_generic_other_stack(self):
  self.put('rpc.md','# Rust tonic\nContrato retries. Ver [[Standard]].');self.put('Standard.md','# Standard\n## Restricción\nNo retry para operación no idempotente.');c,cfg,st,s=self.context();r=b.pack(c,cfg,st,s,['Rust tonic'],b.Budget(18000),seeds=1,related=1);paths={d['path'] for d in r['sources'].values()};self.assertEqual(paths,{'rpc.md','Standard.md'})
 def test_incremental_hash_invalidation_and_stats(self):
  p=self.put('a.md','# Regla\nUno');b.index(self.root,self.db);self.assertFalse(b.index(self.root,self.db)['search_rebuilt']);p.write_text('# Regla\nDos')
  with self.assertRaises(ValueError):b.checked(self.db)
  self.assertTrue(b.index(self.root,self.db)['search_rebuilt']);c,cfg,st=b.checked(self.db);self.addCleanup(c.close)
  session=Path(self.t.name)/'s.json';b.atomic(session,{'revision':'vieja'})
  with self.assertRaises(ValueError):b.session_load(session,cfg['revision'])
 def test_headings_ignore_code_and_verify_coverage(self):
  self.put('a.md','# Real\n```py\n# comentario\n```\n## Regla\nTexto');c,cfg,st,s=self.context();b.show(c,cfg,s,'a.md',1,2,120,b.Budget(8000));r={'cases':[{'id':'C1','criteria':['A'],'oracle':['P1'],'expected':['x'],'kind':'propuesto','sources':[{'path':'a.md','start':5,'end':6,'section':'Regla'}]}]};v=b.verify(c,cfg,s,r);self.assertEqual(v['invalid_or_unseen_citations'],1)
  b.show(c,cfg,s,'a.md',3,6,120,b.Budget(8000));v=b.verify(c,cfg,s,r);self.assertEqual(v['invalid_or_unseen_citations'],0);self.assertNotIn('comentario',[x[0] for x in c.execute('SELECT title FROM headers')]);self.assertEqual(v['criteria_without_case'],list('BCDEFG'))
 def test_unresolved_links_visible_and_same_title(self):
  self.put('one/a.md','---\ntitle: shared\n---\n# A\n[[shared]] [[missing]]');self.put('two/b.md','---\ntitle: shared\n---\n# B');c,cfg,st,s=self.context();rows=[json.loads(x[0]) for x in c.execute('SELECT data FROM unresolved')];self.assertTrue(any(x['ambiguous'] for x in rows));self.assertTrue(any(x['missing'] for x in rows))
 def test_logs_not_inside_corpus_even_index(self):
  script=Path(__file__).parents[1]/'scripts/brain.py';r=subprocess.run([sys.executable,str(script),'--db',str(self.db),'--log-dir',str(self.root/'logs'),'index',str(self.root)],capture_output=True,text=True);self.assertEqual(r.returncode,2);self.assertFalse((self.root/'logs').exists())
 def test_no_ontology_and_sources_stable(self):
  self.put('billing.txt','Idempotence\nRetries max_attempts 3');c,cfg,st,s=self.context();r=b.pack(c,cfg,st,s,['idempotence'],b.Budget(10000));self.assertEqual(len(r['sources']),1);self.assertEqual(next(iter(r['sources'])),b.sid('billing.txt'))
 def test_requirements_and_open_decisions(self):
  self.put('a.txt','regla');c,cfg,st,s=self.context();r={'cases':[{'id':'C','oracle':['P1'],'expected':['decidir'],'criteria':['F'],'kind':'propuesto','open_questions':['Q1'],'sources':[]}]};v=b.verify(c,cfg,s,r,['P1','P2']);self.assertEqual(v['requirements_without_case'],['P2']);self.assertEqual(v['inference_cases_for_review'],['C']);self.assertTrue(v['warnings'])
 def test_token_budget_optional(self):
  try:import tiktoken
  except ImportError:self.skipTest('Tokenizer opcional no instalado en este intérprete')
  self.put('a.md','# Política\n'+'\n'.join('regla larga número '+str(i) for i in range(120)));c,cfg,st,s=self.context();budget=b.Budget(30000,1200);r=b.pack(c,cfg,st,s,['política'],budget);self.assertLessEqual(budget.size(r)[1],1200)
if __name__=='__main__':unittest.main(verbosity=2)
