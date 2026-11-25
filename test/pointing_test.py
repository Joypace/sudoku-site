"""Pointing proof admission: exhaust box candidates before excluding line notes."""
from pathlib import Path
import json,copy,importlib.util,unittest
ROOT=Path(__file__).resolve().parents[1];spec=importlib.util.spec_from_file_location('proof',ROOT/'tools/validate_lessons.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
class Pointing(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.cases=json.loads((ROOT/'learn/pointing/examples.json').read_text())
 def test_row_pair_column_pair_and_triple(self):
  self.assertEqual([len(c['positions']) for c in self.cases],[2,2,3]);self.assertEqual([c['line'] for c in self.cases[:2]],['row','column'])
  for c in self.cases:p.unique_solution(c['grid']);p.pointing(c)
 def test_all_box_candidates_must_be_shown(self):
  for mode in ['omit','duplicate','foreign']:
   with self.subTest(mode=mode):
    c=copy.deepcopy(self.cases[2])
    if mode=='omit':c['positions'].pop()
    elif mode=='duplicate':c['positions'].append(c['positions'][0])
    else:c['positions'][0]=c['targets'][0]
    with self.assertRaisesRegex(ValueError,'every candidate'):p.pointing(c)
 def test_wrong_line_does_not_support_pointing(self):
  c=copy.deepcopy(self.cases[0]);c['line']='column';c['lineIndex']=4
  with self.assertRaisesRegex(ValueError,'named line'):p.pointing(c)
 def test_only_complete_outside_box_eliminations_are_allowed(self):
  for mode in ['missing','inside','duplicate','off-line']:
   with self.subTest(mode=mode):
    c=copy.deepcopy(self.cases[0])
    if mode=='missing':c['targets'].pop()
    elif mode=='inside':c['targets'].append(c['positions'][0])
    elif mode=='duplicate':c['targets'].append(c['targets'][0])
    else:c['targets'].append(0)
    with self.assertRaisesRegex(ValueError,'pointing eliminations'):p.pointing(c)
 def test_box_line_and_digit_metadata_are_validated(self):
  for key,value in [('boxIndex',9),('boxIndex',True),('line','diagonal'),('lineIndex',9),('lineIndex',True),('digit',0),('digit',True)]:
   with self.subTest(key=key,value=value):
    c=copy.deepcopy(self.cases[0]);c[key]=value
    with self.assertRaises(ValueError):p.pointing(c)
 def test_cell_indices_are_integers(self):
  for key in ['positions','targets']:
   with self.subTest(key=key):
    c=copy.deepcopy(self.cases[0]);c[key][0]=float(c[key][0])
    with self.assertRaisesRegex(ValueError,'cell indices'):p.pointing(c)
 def test_native_animation_binds_all_trials_marks_and_box_labels(self):
  for n,c in enumerate(self.cases,1):
   data=json.loads((ROOT/f'learn/pointing/example-{n}.json').read_text());p.pointing_animation(data,c)
   mutations=[('expected','slotFills',[]),('expected','boards',99),('expected','validSlots',[0]),('expected','overlays',[]),('expected','notes',[]),('expected','revealFrameCount',2),('expected','revealLabelCount',1),('reveal','frames',[[0,0,1,1]]),('reveal','labels',[])]
   for group,key,value in mutations:
    with self.subTest(example=n,group=group,key=key):
     changed=copy.deepcopy(data);target=changed['expected'] if group=='expected' else changed['presentation']['choiceReveal'];target[key]=value
     with self.assertRaises(ValueError):p.pointing_animation(changed,c)
 def test_forced_moves_elsewhere_reject_advanced_start(self):
  c=copy.deepcopy(self.cases[0]);c['grid']='532790010007000500010205407108000004964020070000069000700906001080152703001340000'
  with self.assertRaisesRegex(ValueError,'forced single'):p.pointing(c)
if __name__=='__main__':unittest.main()
