"""Proof-rule and native-gesture admission for row, column and box hidden singles."""
from pathlib import Path
import importlib.util,unittest,json,copy,tempfile,shutil
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('lesson_contract',ROOT/'tools/validate_lessons.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class HiddenSingle(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.examples=json.loads((ROOT/'learn/hidden-single/examples.json').read_text())
 def test_row_column_box_proofs_use_only_starting_clues(self):
  self.assertEqual([x['unit'] for x in self.examples],['row','column','box'])
  for example in self.examples:module.hidden_single(example)
 def test_wrong_target_unit_or_digit_rejected(self):
  for key,value in [('cell',63),('unitIndex',0),('digit',3),('unit','diagonal')]:
   with self.subTest(key=key):
    x=copy.deepcopy(self.examples[0]);x[key]=value
    with self.assertRaisesRegex(ValueError,'Hidden.single|hidden.single'):module.hidden_single(x)
 def test_naked_single_cannot_be_mislabeled_hidden_single(self):
  x=copy.deepcopy(self.examples[0]);g=list(x['grid']);g[13]='3';g[58]='7';x['grid']=''.join(g);x['candidates']=[1]
  with self.assertRaisesRegex(ValueError,'multiple cell candidates'):module.hidden_single(x)
 def test_incomplete_exclusions_and_wrong_given_witnesses_rejected(self):
  for change in ['missing','duplicate','wrong-digit','non-peer','candidate-list']:
   x=copy.deepcopy(self.examples[0])
   if change=='missing':x['exclusions'].pop()
   if change=='duplicate':x['exclusions'][1]=x['exclusions'][0]
   if change=='wrong-digit':x['exclusions'][0]['given']=0
   if change=='non-peer':x['exclusions'][0]['given']=21
   if change=='candidate-list':x['candidates']=[1,3]
   with self.subTest(change=change),self.assertRaisesRegex(ValueError,'witness|candidates'):module.hidden_single(x)
 def test_second_possible_place_refutes_single(self):
  x=copy.deepcopy(self.examples[0]);g=list(x['grid']);g[36]='0';g[55]='0';x['grid']=''.join(g)
  with self.assertRaisesRegex(ValueError,'exactly one place'):module.hidden_single(x)
 def test_export_requires_proved_initial_choice_full_unit_and_centered_tap(self):
  with tempfile.TemporaryDirectory(prefix='hidden-single-contract-') as temp:
   root=Path(temp);shutil.copytree(ROOT/'learn',root/'learn');path=root/'learn/hidden-single/example-1.json';original=json.loads(path.read_text())
   for change in ['initial','geometry','labels','mode','tap-offset','extra-fill','slot-fill','validity']:
    scene=copy.deepcopy(original)
    if change=='initial':scene['expected'].pop('initialSingle')
    if change=='geometry':scene['presentation']['choiceReveal']['frames']=[[7,4,1,1]]
    if change=='labels':scene['presentation']['choiceReveal']['labels']=[[7,4,3]]
    if change=='mode':scene['style']='standard'
    if change=='tap-offset':scene['frames'][1]['at']['note']=1
    if change=='extra-fill':scene['frames'].append({'do':'tap','at':{'part':'cell','cell':[0,0]},'count':2,'time':9500})
    if change=='slot-fill':scene['expected']['slotFills']=[]
    if change=='validity':scene['expected']['validSlots']=[]
    path.write_text(json.dumps(scene))
    with self.subTest(change=change),self.assertRaisesRegex(ValueError,'runtime assertion|Hidden.single|Hidden-single|highlight'):module.validate(root)
if __name__=='__main__':unittest.main()
