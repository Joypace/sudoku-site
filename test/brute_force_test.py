from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import copy,unittest
import brute_force as b
GRID='809530002000000090000906000024700905950000087080359240295673010648192753000845629'
OPEN={'steps':[],'end':{'kind':'open'}}
def rejected(d):
 steps=[{'do':'fill','choice':q} for q in [[7,6],[31,6],[38,6]]];s=list(map(int,GRID));s[1]=d
 for step in steps:s[step['choice'][0]]=step['choice'][1]
 return {'steps':steps,'end':{'kind':'contradiction','witness':next(w for w in b.contradictions(s,b.candidates(s)) if w['kind']=='crowded')}}
def tree():return {'grid':GRID,'tree':{'steps':[],'end':{'kind':'decision','cell':1,'children':[{'digit':1,'node':rejected(1)},{'digit':6,'node':copy.deepcopy(OPEN)},{'digit':7,'node':rejected(7)}]}}}
def nested():
 children=[{'digit':d,'node':copy.deepcopy(OPEN)} for d in range(1,10)]
 children[0]['node']={'steps':[],'end':{'kind':'decision','cell':1,'children':[{'digit':d,'node':copy.deepcopy(OPEN)} for d in range(2,10)]}}
 return {'grid':'0'*81,'tree':{'steps':[],'end':{'kind':'decision','cell':0,'children':children}}}
class SearchProof(unittest.TestCase):
 def test_real_ordinary_conflicting_obligations_and_contextual_exclusions(self):
  self.assertEqual(b.validate(tree())['outcome'],'open')
  e={'grid':GRID,'tree':{'steps':[{'do':'exclude','choice':[1,d],'proof':rejected(d)} for d in [1,7]]+[{'do':'fill','choice':[1,6]}],'end':{'kind':'open'}}}
  self.assertEqual(b.validate(e)['outcome'],'open')
 def test_exhaustive_nested_open_children_do_not_refute_ancestor(self):
  e=nested();self.assertEqual(b.validate(e)['outcome'],'open');proof=e['tree']['end']['children'][0]['node']
  bad={'grid':'0'*81,'tree':{'steps':[{'do':'exclude','choice':[0,1],'proof':proof}],'end':{'kind':'open'}}}
  with self.assertRaisesRegex(ValueError,'rejected assumption subtree'):b.validate(bad)
  proof['end']['children'].pop()
  with self.assertRaisesRegex(ValueError,'Exhaust'):b.validate(e)
 def test_no_second_guess_no_false_solved_no_steps_after_warning(self):
  e=tree();e['tree']['end']['children'][0]['node']['steps'][0]['choice']=[0,1]
  with self.assertRaises(ValueError):b.validate(e)
  e=tree();e['tree']['end']['children'][0]['node']['steps'].append({'do':'fill','choice':[0,1]})
  with self.assertRaisesRegex(ValueError,'first contradiction'):b.validate(e)
  e=tree();e['tree']['end']['children'][1]['node']['end']={'kind':'solved'}
  with self.assertRaisesRegex(ValueError,'every cell'):b.validate(e)
 def test_exact_ordinary_witness_types_and_no_uniqueness_surrogate(self):
  for w in [{'kind':'uniqueness'},{'kind':'empty-cell','cell':0},{'kind':'crowded','constraints':[[False,4,6]]}]:
   e=tree();e['tree']['end']['children'][0]['node']['end']['witness']=w
   with self.assertRaises(ValueError):b.validate(e)
  e=tree();e['tree']['end']['children'][0]['node']['end']['witness']['constraints'].pop()
  with self.assertRaises(ValueError):b.validate(e)
  e=tree();e['tree']['end']['children'][0]['digit']=True
  with self.assertRaises(ValueError):b.validate(e)
 def test_no_fabricated_mask_or_decision_with_singles(self):
  e=tree();e['tree']['steps']=[{'do':'exclude','choice':[1,1],'proof':copy.deepcopy(OPEN)}]
  with self.assertRaises(ValueError):b.validate(e)
  e=tree();e['tree']['end']['children'][0]['node']={'steps':[],'end':{'kind':'decision','cell':7,'children':[]}}
  with self.assertRaisesRegex(ValueError,'zero singles'):b.validate(e)
 def test_budget_raw_root_and_duplicate_alternatives(self):
  with self.assertRaisesRegex(ValueError,'budget'):b.validate(nested(),max_nodes=2)
  e=tree();e['grid']='1'*81
  with self.assertRaises(ValueError):b.validate(e)
  e=tree();e['tree']['end']['children'].append(copy.deepcopy(e['tree']['end']['children'][0]))
  with self.assertRaisesRegex(ValueError,'Exhaust'):b.validate(e)
class AtomicWaves(unittest.TestCase):
 def certificate(self):
  e=tree();node=e['tree']['end']['children'][0]['node']
  node['steps']=[{'do':'wave','fills':[[6,4],[7,6],[10,6]]},
                 {'do':'wave','fills':[[5,7],[18,4],[25,7],[31,6],[34,3],[53,6],[60,8],[62,4]]}]
  node['end']={'kind':'contradiction','witness':{'kind':'crowded','constraints':[[0,4,2]]}}
  return e
 def test_all_preproved_wave_choices_commit_atomically(self):
  self.assertEqual(b.validate(self.certificate())['outcome'],'open')
 def test_midwave_new_single_is_not_preproved_and_duplicate_cells_rejected(self):
  for extra in [[31,6],[6,4]]:
   e=self.certificate();e['tree']['end']['children'][0]['node']['steps'][0]['fills'].append(extra)
   with self.assertRaises(ValueError):b.validate(e)
 def test_stop_after_first_contradictory_wave_and_count_wave_fills_in_budget(self):
  e=self.certificate();e['tree']['end']['children'][0]['node']['steps'].append({'do':'fill','choice':[9,5]})
  with self.assertRaisesRegex(ValueError,'first contradiction'):b.validate(e)
  with self.assertRaisesRegex(ValueError,'budget'):b.validate(self.certificate(),max_steps=4)

if __name__=='__main__':unittest.main()
