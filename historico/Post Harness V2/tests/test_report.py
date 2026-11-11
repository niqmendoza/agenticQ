import importlib.util,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('build_report',Path(__file__).parents[1]/'scripts/build_report.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
class ReportTests(unittest.TestCase):
 def data(self):
  return {'iterations':[{'id':name,'title':'<dato>','usage':{'input_tokens':100,'cached_input_tokens':70,'output_tokens':20,'reasoning_output_tokens':5,'total_tokens':120},'model_responses':2,'local_calls':3,'document_tokens':10,'cases':1,'seconds':2,'documents_presented':1} for name in ['full','v1','v2']],'changes':[],'coverage':[],'limitations':[]}
 def test_native_categories_not_double_counted(self):
  d=self.data();r.validate(d);self.assertEqual(r.uncached(d['iterations'][0]),30);s=r.render(d);self.assertIn('&lt;dato&gt;',s);self.assertNotIn('@@CARDS@@',s)
 def test_reject_impossible_usage(self):
  d=self.data();d['iterations'][0]['usage']['total_tokens']=190
  with self.assertRaises(ValueError):r.validate(d)
  d=self.data();d['iterations'][0]['usage']['cached_input_tokens']=101
  with self.assertRaises(ValueError):r.validate(d)
 def test_unknown_is_not_zero(self):
  d=self.data();d['iterations'][2]['usage']={};s=r.render(d);self.assertIn('—',s);self.assertIn('Sin comparación disponible',s)
if __name__=='__main__':unittest.main()
