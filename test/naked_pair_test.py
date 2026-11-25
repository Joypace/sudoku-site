"""Naked Pair proof admission: exact candidates, exhaustive trials and exclusions."""
from pathlib import Path
import copy,importlib.util,json,unittest
ROOT=Path(__file__).resolve().parents[1];spec=importlib.util.spec_from_file_location('proof',ROOT/'tools/validate_lessons.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
class Pairs(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.cases=json.loads((ROOT/'learn/naked-pair/examples.json').read_text())
 def test_row_column_box_cases_are_unique_and_have_exact_pairs(self):
  self.assertEqual([c['unit'] for c in self.cases],['row','column','box'])
  for c in self.cases:p.unique_solution(c['grid']);p.naked_pair(c)
 def test_extra_candidate_is_not_a_naked_pair(self):
  c=copy.deepcopy(self.cases[0]);c['pair'][1]=c['targets'][0][0]
  with self.assertRaisesRegex(ValueError,'same two candidates'):p.naked_pair(c)
 def test_both_trial_assignments_are_required(self):
  c=copy.deepcopy(self.cases[0]);c['branches'][1]=c['branches'][0]
  with self.assertRaisesRegex(ValueError,'exhaust'):p.naked_pair(c)
 def test_eliminations_are_complete_and_outside_the_pair(self):
  for mode in ['missing','pair-cell','duplicate']:
   with self.subTest(mode=mode):
    c=copy.deepcopy(self.cases[0])
    if mode=='missing':c['targets'].pop()
    elif mode=='pair-cell':c['targets'].append([c['pair'][0],c['digits'][0]])
    else:c['targets'].append(c['targets'][0])
    with self.assertRaisesRegex(ValueError,'pair eliminations'):p.naked_pair(c)
 def test_metadata_requires_a_unit_two_cells_and_two_digits(self):
  mutations=[('unit','diagonal'),('unitIndex',9),('unitIndex',True),('pair',[65,65]),('pair',[0,70]),('digits',[1,1]),('digits',[1,0]),('digits',[1,True])]
  for key,value in mutations:
   with self.subTest(key=key,value=value):
    c=copy.deepcopy(self.cases[0]);c[key]=value
    with self.assertRaises(ValueError):p.naked_pair(c)
 def test_advanced_examples_reject_naked_and_hidden_singles_elsewhere(self):
  fixtures={'hidden': {'grid': '430007050008100040092000700000060030000000809003401000004002000250870600000500000', 'origin': 'original Sudoku Let’s Try practice puzzle', 'sourceFamily': 'ebb9518096ce4ede', 'initialStatus': 'dilemma', 'initialSingles': 0, 'unit': 'row', 'unitIndex': 7, 'pair': [65, 70], 'digits': [1, 9], 'targets': [[68, 9], [71, 1]], 'branches': [[[65, 1], [70, 9]], [[65, 9], [70, 1]]], 'solutionCount': 1}, 'naked': {'grid': '036007050008100040092000700000060030000000809003401000004002000250870600000500000', 'origin': 'original Sudoku Let’s Try practice puzzle', 'sourceFamily': 'ebb9518096ce4ede', 'initialStatus': 'dilemma', 'initialSingles': 0, 'unit': 'row', 'unitIndex': 7, 'pair': [65, 70], 'digits': [1, 9], 'targets': [[68, 9], [71, 1]], 'branches': [[[65, 1], [70, 9]], [[65, 9], [70, 1]]], 'solutionCount': 1}}
  for kind,c in fixtures.items():
   with self.subTest(kind=kind),self.assertRaisesRegex(ValueError,'forced single'):p.naked_pair(c)
if __name__=='__main__':unittest.main()
