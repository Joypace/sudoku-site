"""Basic-technique proofs and their bindings to real native demonstrations."""
from pathlib import Path
import json,copy,importlib.util,unittest
ROOT=Path(__file__).resolve().parents[1];spec=importlib.util.spec_from_file_location('proof',ROOT/'tools/validate_lessons.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
class Basic(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.data={slug:json.loads((ROOT/'learn'/slug/'examples.json').read_text()) for slug in ['naked-single','claiming','hidden-pair']}
 def test_nine_original_cases_and_native_contracts(self):
  for slug,cases in self.data.items():
   for n,c in enumerate(cases,1):
    with self.subTest(slug=slug,n=n):
     p.unique_solution(c['grid']);p.PROOFS[slug](c);story=json.loads((ROOT/'learn'/slug/f'example-{n}.json').read_text());{'naked-single':p.naked_single_animation,'claiming':p.claiming_animation,'hidden-pair':p.hidden_pair_animation}[slug](story,c)
 def test_single_requires_sole_candidate_and_eight_original_witnesses(self):
  c=self.data['naked-single'][0]
  for key,value in [('digit',0),('digit',True),('cell',81),('exclusions',c['exclusions'][:-1])]:
   with self.subTest(key=key):
    changed=copy.deepcopy(c);changed[key]=value
    with self.assertRaises(ValueError):p.naked_single(changed)
  changed=copy.deepcopy(c);changed['exclusions'][0]['given']=changed['cell']
  with self.assertRaisesRegex(ValueError,'peer clue'):p.naked_single(changed)
  changed=copy.deepcopy(c);changed['cell']=next(i for i,v in enumerate(c['grid']) if v!='0')
  with self.assertRaisesRegex(ValueError,'exactly one'):p.naked_single(changed)
 def test_hidden_pair_requires_both_digits_only_in_two_cells(self):
  c=self.data['hidden-pair'][0]
  for key,value in [('unit','diagonal'),('unitIndex',9),('pair',[c['pair'][0]]*2),('digits',[c['digits'][0]]*2),('digits',[0,1]),('digits',[2,3]),('targets',[]),('branches',[c['branches'][0]]*2)]:
   with self.subTest(key=key,value=value):
    changed=copy.deepcopy(c);changed[key]=value
    with self.assertRaises(ValueError):p.hidden_pair(changed)
  changed=copy.deepcopy(c);changed['targets'].append([c['pair'][0],c['digits'][0]])
  with self.assertRaisesRegex(ValueError,'other notes'):p.hidden_pair(changed)
 def test_proof_witnesses_targets_and_trials_require_integer_values(self):
  for value in [float(self.data['naked-single'][0]['exclusions'][0]['digit']),True]:
   with self.subTest(witness=value):
    changed=copy.deepcopy(self.data['naked-single'][0]);changed['exclusions'][0]['digit']=value
    with self.assertRaisesRegex(ValueError,'witness digits must be integers'):p.naked_single(changed)
  for group in ['targets','branches']:
   for coordinate in [0,1]:
    for kind in ['float','bool']:
     with self.subTest(group=group,coordinate=coordinate,kind=kind):
      changed=copy.deepcopy(self.data['hidden-pair'][0]);choice=changed[group][0] if group=='targets' else changed[group][0][0];choice[coordinate]=float(choice[coordinate]) if kind=='float' else True
      with self.assertRaisesRegex(ValueError,'cells and digits must be integers'):p.hidden_pair(changed)
 def test_claiming_requires_the_entire_line_to_be_inside_the_box(self):
  c=self.data['claiming'][0]
  for key,value in [('boxIndex',9),('line','box'),('lineIndex',True),('digit',0),('positions',c['positions'][:-1]),('positions',c['positions']+[c['positions'][0]]),('targets',[]),('targets',c['targets']+[c['positions'][0]])]:
   with self.subTest(key=key):
    changed=copy.deepcopy(c);changed[key]=value
    with self.assertRaises(ValueError):p.claiming(changed)
  changed=copy.deepcopy(c);changed['boxIndex']=(c['boxIndex']+1)%9
  with self.assertRaisesRegex(ValueError,'inside the named box'):p.claiming(changed)
 def test_native_checks_cannot_be_omitted_or_point_elsewhere(self):
  for slug,cases in self.data.items():
   c=cases[0];base=json.loads((ROOT/'learn'/slug/'example-1.json').read_text());check={'naked-single':p.naked_single_animation,'claiming':p.claiming_animation,'hidden-pair':p.hidden_pair_animation}[slug]
   mutations=[('checks','slotFills',[]),('checks','boards',99),('checks','validSlots',[]),('reveal','labels',[]),('reveal','frames',[])]
   if slug!='naked-single':mutations += [('checks','overlays',[]),('checks','notes',[]),('checks','revealLabelCount',99),('checks','revealFrameCount',None)]
   else:mutations += [('checks','initialStatus','dilemma'),('checks','initialSingle',[0,0,1]),('checks','overlays',[[1,0]]),('checks','fills',[])]
   for kind,key,value in mutations:
    with self.subTest(slug=slug,key=key):
     changed=copy.deepcopy(base);target=changed['expected'] if kind=='checks' else changed['presentation']['choiceReveal'];target[key]=value
     with self.assertRaises(ValueError):check(changed,c)
 def test_single_uses_only_one_cell_centered_forced_double_tap(self):
  c=self.data['naked-single'][0];base=json.loads((ROOT/'learn/naked-single/example-1.json').read_text());p.naked_single_animation(base,c)
  action=next(f for f in base['frames'] if f['do']=='tap');wrong=copy.deepcopy(action);wrong['at']={'part':'cell','cell':[c['cell']//9,c['cell']%9],'note':c['digit']}
  for frames in [[],[action,action],[{**action,'count':1}],[{**action,'do':'down'}],[wrong]]:
   with self.subTest(frames=frames):
    changed=copy.deepcopy(base);changed['frames']=frames
    with self.assertRaisesRegex(ValueError,'cell-centered forced double tap'):p.naked_single_animation(changed,c)
if __name__=='__main__':unittest.main()
