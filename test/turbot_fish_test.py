"""A complete four-candidate chain uses strong–weak–strong implications."""
from pathlib import Path
import copy,importlib.util,unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('turbot_rules',ROOT/'tools/validate_lessons.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
FIXTURE={'grid': '000000200810300900000009005000503090034000001000087003300000150056030009009025340', 'origin': 'original Sudoku Let’s Try practice puzzle', 'sourceFamily': '7decffdabb9e45dd', 'slug': 'turbot-fish', 'pattern': {'digit': 1, 'units': [{'unit': 'row', 'unitIndex': 8}, {'unit': 'box', 'unitIndex': 4}], 'links': [[75, 72], [48, 31]], 'bridge': {'unit': 'column', 'unitIndex': 3}}, 'targets': [[27, 1]], 'branches': [[[72, 1]], [[72, 7], [75, 1], [31, 1]]], 'frames': [[8, 0, 1, 9], [3, 3, 3, 3], [0, 3, 9, 1]], 'labels': [[3, 4, 1], [5, 3, 1], [8, 0, 1], [8, 3, 1]]}
class TurbotFish(unittest.TestCase):
 def test_box_line_chain_with_complete_targets(self):
  p.PROOFS['turbot-fish'](copy.deepcopy(FIXTURE));p.unique_solution(FIXTURE['grid'])
 def test_incomplete_strong_link_or_unconnected_bridge_is_rejected(self):
  mutations=[('links',[[75,72],[48,0]]),('units',FIXTURE['pattern']['units'][:1]),('bridge',{'unit':'row','unitIndex':0}),('digit',2)]
  for key,value in mutations:
   with self.subTest(key=key):
    e=copy.deepcopy(FIXTURE);e['pattern'][key]=value
    with self.assertRaises(ValueError):p.PROOFS['turbot-fish'](e)
 def test_incomplete_targets_trials_or_reveals_are_rejected(self):
  for key in ['targets','branches','frames','labels']:
   with self.subTest(key=key):
    e=copy.deepcopy(FIXTURE);e[key]=e[key][:-1]
    with self.assertRaises(ValueError):p.PROOFS['turbot-fish'](e)
  e=copy.deepcopy(FIXTURE);e['targets'].append([0,1])
  with self.assertRaises(ValueError):p.PROOFS['turbot-fish'](e)
 def test_an_available_second_guess_cannot_replace_the_forced_chain(self):
  e=copy.deepcopy(FIXTURE);e['branches'][1][1]=[0,4]
  with self.assertRaisesRegex(ValueError,'Only the founding fill may be a guess'):
   p.PROOFS['turbot-fish'](e)
 def test_link_bridge_and_native_coordinates_reject_nonintegers(self):
  for value in [True,1.0]:
   for path in [('pattern','digit'),('pattern','links',0,0),('pattern','units',0,'unitIndex'),('pattern','bridge','unitIndex'),('targets',0,0),('frames',0,0),('labels',0,0),('branches',0,0,0)]:
    with self.subTest(path=path,value=value):
     e=copy.deepcopy(FIXTURE);node=e
     for key in path[:-1]:node=node[key]
     node[path[-1]]=value
     with self.assertRaises(ValueError):p.PROOFS['turbot-fish'](e)
if __name__=='__main__':unittest.main()
