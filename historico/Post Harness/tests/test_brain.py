import importlib.util,json,tempfile,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('brain',Path(__file__).parents[1]/'scripts/brain.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
class BrainTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.root=Path(self.t.name)/'corpus';self.root.mkdir();self.db=Path(self.t.name)/'i.sqlite'
 def put(self,p,text):
  q=self.root/p;q.parent.mkdir(parents=True,exist_ok=True);q.write_text(text);return q
 def test_empty_no_results(self):
  self.assertEqual(b.index(self.root,self.db)['documents'],0);c,cfg=b.checked(self.db);self.assertEqual(b.query(c,cfg,'nada',6,0,16000)['results'],[])
 def test_incremental_invalidation_add_delete(self):
  p=self.put('one.md','# Uno\nOriginal');self.assertEqual(b.index(self.root,self.db)['changed'],1);self.assertEqual(b.index(self.root,self.db)['unchanged'],1)
  p.write_text('# Uno\nModificado')
  with self.assertRaisesRegex(ValueError,'desactualizado'):b.checked(self.db)
  self.assertEqual(b.index(self.root,self.db)['changed'],1);self.put('dos.md','Alta')
  with self.assertRaises(ValueError):b.checked(self.db)
  b.index(self.root,self.db);p.unlink();self.assertEqual(b.index(self.root,self.db)['removed'],1)
 def test_exact_extracts_and_long_section(self):
  text='---\ntitle: "Título"\nestado: antiguo\n---\n# Política\n'+ '\n'.join(f'Línea {i} excepción café' for i in range(95))
  self.put('p.md',text);b.index(self.root,self.db);c,cfg=b.checked(self.db);rows=list(c.execute('select * from chunks'));covered=set()
  for r in rows:
   self.assertEqual(r['text'],'\n'.join(text.splitlines()[r['start']-1:r['end']]));covered.update(range(r['start'],r['end']+1))
  self.assertEqual(covered,set(range(1,len(text.splitlines())+1)))
  r=b.query(c,cfg,'excepcion cafe',2,0,16000);self.assertTrue(r['results']);self.assertEqual(r['results'][0]['metadata']['estado'],'antiguo')
  page=b.show(c,cfg,'p.md',5,None,10);self.assertEqual(page['text'],'\n'.join(text.splitlines()[4:14]));self.assertEqual(page['next_line'],15)
 def test_page_and_budget(self):
  for i in range(4):self.put(f'{i}.md',f'# Tema\nPrueba límite {i}')
  b.index(self.root,self.db);c,cfg=b.checked(self.db);a=b.query(c,cfg,'prueba',1,0,4000);z=b.query(c,cfg,'prueba',1,a['next_offset'],4000)
  self.assertNotEqual(a['results'][0]['path'],z['results'][0]['path']);self.assertTrue(a['truncated']);self.assertEqual(b.query(c,cfg,'zzzz',2,0,4000)['results'],[])
  q=b.query(c,cfg,'prueba',4,0,1000);self.assertLessEqual(len(b.dump(q)),1000);self.assertTrue(q['truncated'])
 def test_fence_and_links_ambiguous_missing(self):
  self.put('A/a.md','---\ntitle: duplicado\n---\n# Real\n```python\n# no encabezado\n```\n[[duplicado]] [[ausente]] [b](../B/b.md)')
  self.put('B/b.md','---\ntitle: duplicado\n---\n# Otro')
  b.index(self.root,self.db);c,cfg=b.checked(self.db);r=b.relations(c,'A/a.md');self.assertTrue(r[0]['ambiguous']);self.assertTrue(r[1]['missing']);self.assertEqual(r[2]['resolved'],['B/b.md']);self.assertNotIn('no encabezado',[r[0] for r in c.execute('select section from chunks')])
 def test_exclusion_root_and_symlink(self):
  self.put('binary.md','a').write_bytes(b'\xff');self.put('a.txt','texto');(self.root/'link.md').symlink_to(self.root/'a.txt');self.put('.DS_Store','basura')
  r=b.index(self.root,self.db);self.assertEqual(r['documents'],1);self.assertEqual(len(r['excluded']),3)
  with self.assertRaises(ValueError):b.index(self.root,self.root/'i.sqlite')
 def test_show_bad_path_range_and_eof(self):
  self.put('a.md','dos\nlíneas');b.index(self.root,self.db);c,cfg=b.checked(self.db)
  with self.assertRaises(ValueError):b.show(c,cfg,'../a.md',1,None,20)
  with self.assertRaises(ValueError):b.show(c,cfg,'a.md',4,2,20)
  self.assertTrue(b.show(c,cfg,'a.md',20,None,20)['beyond_eof'])
 def test_other_technology_and_no_metadata(self):
  self.put('Guide.rst','Payments\n========\nRust tonic retries max_attempts = 3');b.index(self.root,self.db);c,cfg=b.checked(self.db);self.assertIn('Rust',b.query(c,cfg,'tonic retries',4,0,16000)['results'][0]['excerpt'])
if __name__=='__main__':unittest.main(verbosity=2)
