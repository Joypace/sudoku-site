"""Complete dual-house triple premises and exhaustive forced-only trials."""
from pathlib import Path
import copy,importlib.util,unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('locked_triple_rules',ROOT/'tools/validate_lessons.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
FIXTURE={'grid': '405000070003000054700534800000340000374000500000902040259716438831400706647803005', 'origin': 'original Sudoku Let’s Try practice puzzle', 'sourceFamily': '6d8c1a3d92f5d7b0', 'slug': 'locked-triple', 'pattern': {'unit': 'row', 'unitIndex': 4, 'boxIndex': 4, 'cells': [39, 40, 41], 'digits': [1, 6, 8]}, 'targets': [[32, 1], [32, 8], [43, 1], [43, 6], [43, 8], [44, 1], [49, 6], [49, 8]], 'branches': [[[39, 1], [41, 8], [40, 6]], [[39, 6], [40, 8], [41, 1]]], 'frames': [[4, 0, 1, 9], [3, 3, 3, 3]], 'labels': [[4, 3, 1], [4, 3, 6], [4, 4, 6], [4, 4, 8], [4, 5, 1], [4, 5, 8]]}
class LockedTriple(unittest.TestCase):
 def test_complete_dual_house_triple_with_two_note_cells(self):
  p.PROOFS['locked-triple'](copy.deepcopy(FIXTURE));p.unique_solution(FIXTURE['grid'])
 def test_incomplete_eliminations_premises_or_trials_are_rejected(self):
  for field,value in [('targets',FIXTURE['targets'][:-1]),('frames',FIXTURE['frames'][:1]),('labels',FIXTURE['labels'][:-1]),('branches',FIXTURE['branches'][:1])]:
   with self.subTest(field=field):
    e=copy.deepcopy(FIXTURE);e[field]=value
    with self.assertRaises(ValueError):p.PROOFS['locked-triple'](e)
  for field,value in [('boxIndex',0),('unit','box'),('cells',[0,40,41]),('digits',[1,6,9])]:
   with self.subTest(field=field):
    e=copy.deepcopy(FIXTURE);e['pattern'][field]=value
    with self.assertRaises(ValueError):p.PROOFS['locked-triple'](e)
 def test_typed_coordinates_and_extra_target_are_rejected(self):
  for field in ['targets','frames','labels','branches']:
   original=FIXTURE[field][0][0] if field=='branches' else FIXTURE[field][0]
   for i in range(len(original)):
    for value in [float(original[i]),True]:
     with self.subTest(field=field,index=i,value=value):
      e=copy.deepcopy(FIXTURE);v=e[field][0][0] if field=='branches' else e[field][0];v[i]=value
      with self.assertRaises(ValueError):p.PROOFS['locked-triple'](e)
  e=copy.deepcopy(FIXTURE);e['targets'].append([39,1])
  with self.assertRaises(ValueError):p.PROOFS['locked-triple'](e)
 def test_second_guess_cannot_replace_a_forced_move(self):
  e=copy.deepcopy(FIXTURE);e['branches'][0][1]=[43,8]
  with self.assertRaises(ValueError):p.PROOFS['locked-triple'](e)
if __name__=='__main__':unittest.main()
