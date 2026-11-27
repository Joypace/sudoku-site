"""A pair reserves the line AND box, with complete eliminations in both."""
from pathlib import Path
import copy,importlib.util,unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('locked_pair_rules',ROOT/'tools/validate_lessons.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
FIXTURE={'grid': '006100030130042700000803100001030070005009018090001040683000401752010003914300067', 'slug': 'locked-pair', 'unit': 'row', 'unitIndex': 7, 'boxIndex': 8, 'pair': [69, 70], 'digits': [8, 9], 'targets': [[61, 9], [66, 9], [68, 8], [78, 8]], 'branches': [[[69, 8], [70, 9]], [[69, 9], [70, 8]]], 'frames': [[7, 0, 1, 9], [6, 6, 3, 3]], 'labels': [[7, 6, 8], [7, 6, 9], [7, 7, 8], [7, 7, 9]]}
class LockedPair(unittest.TestCase):
 def test_native_vectors_and_trial_choices_reject_float_and_boolean_coordinates(self):
  for field in ['frames','labels','branches']:
   e=copy.deepcopy(FIXTURE)
   vector=e[field][0][0] if field=='branches' else e[field][0]
   for index in range(len(vector)):
    for value in [float(vector[index]),True]:
     with self.subTest(field=field,index=index,value=value):
      changed=copy.deepcopy(FIXTURE);target=changed[field][0][0] if field=='branches' else changed[field][0];target[index]=value
      with self.assertRaisesRegex(ValueError,'integer'):p.PROOFS['locked-pair'](changed)
 def test_complete_shared_pair_and_ordinary_two_assignments(self):
  p.PROOFS['locked-pair'](copy.deepcopy(FIXTURE));p.unique_solution(FIXTURE['grid'])
 def test_no_line_only_box_only_or_incomplete_eliminations(self):
  for key,value in [('unit','box'),('unitIndex',True),('boxIndex',9),('boxIndex',0),('targets',FIXTURE['targets'][:-1]),('branches',FIXTURE['branches'][:1]),('frames',FIXTURE['frames'][:1]),('labels',FIXTURE['labels'][:-1])]:
   with self.subTest(key=key,value=value):
    e=copy.deepcopy(FIXTURE);e[key]=value
    with self.assertRaises(ValueError):p.PROOFS['locked-pair'](e)
  for value in [True,1.0]:
   e=copy.deepcopy(FIXTURE);e['targets'][0][0]=value
   with self.assertRaisesRegex(ValueError,'integer'):p.PROOFS['locked-pair'](e)
 def test_extra_elimination_or_unshared_pair_is_rejected(self):
  e=copy.deepcopy(FIXTURE);e['targets'].append([e['pair'][0],e['digits'][0]])
  with self.assertRaises(ValueError):p.PROOFS['locked-pair'](e)
  e=copy.deepcopy(FIXTURE);e['pair'][1]=0
  with self.assertRaisesRegex(ValueError,'both named houses'):p.PROOFS['locked-pair'](e)
if __name__=='__main__':unittest.main()
