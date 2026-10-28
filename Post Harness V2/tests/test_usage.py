import importlib.util,json,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('extract_usage',Path(__file__).parents[1]/'scripts/extract_usage.py');u=importlib.util.module_from_spec(spec);spec.loader.exec_module(u)
class UsageTests(unittest.TestCase):
 def test_deduplicate_deltas_not_cumulative(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'log.jsonl';rows=[]
   def add(typ,payload,t='2026-10-27T00:00:00Z'):rows.append({'type':typ,'timestamp':t,'payload':payload})
   add('turn_context',{'turn_id':'t','model':'test','effort':'high'});add('event_msg',{'type':'task_started','turn_id':'t'})
   def counts(i,o,c,r):return dict(input_tokens=i,output_tokens=o,cached_input_tokens=c,reasoning_output_tokens=r,cache_write_input_tokens=0,total_tokens=i+o)
   a=counts(10,3,7,1);b=counts(20,4,15,2);total=counts(30,7,22,3)
   first={'turn_id':'t','response_id':'one','usage':a,'turn_token_usage':a};second={'turn_id':'t','response_id':'two','usage':b,'turn_token_usage':total}
   add('token_usage_record',first);add('token_usage_record',second);add('token_usage_record',second);add('event_msg',{'type':'task_complete','turn_id':'t'},'2026-10-27T00:00:05Z');p.write_text('\n'.join(map(json.dumps,rows)))
   t=u.parse(p)['turns'][0];self.assertEqual(t['model_responses'],2);self.assertEqual(t['usage_sum'],total);self.assertTrue(t['matches_last_turn_counter']);self.assertEqual(t['usage_sum']['total_tokens'],37);self.assertEqual(t['observed_duration_seconds'],5)
if __name__=='__main__':unittest.main()
