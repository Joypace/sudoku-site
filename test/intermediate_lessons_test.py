"""Public intermediate examples bind named proofs to real App tutorials."""
from pathlib import Path
import copy,json,importlib.util,unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('lesson_rules',ROOT/'tools/validate_lessons.py');rules=importlib.util.module_from_spec(spec);spec.loader.exec_module(rules)
class IntermediateLessons(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.examples={slug:json.loads((ROOT/'learn'/slug/'examples.json').read_text()) for slug in rules.INTERMEDIATE}
 def test_every_original_example_has_a_complete_named_proof_and_bound_native_story(self):
  for slug,cases in self.examples.items():
   self.assertEqual(len(cases),3)
   self.assertEqual(len({c['grid'] for c in cases}),3)
   for n,c in enumerate(cases,1):
    with self.subTest(slug=slug,example=n):
     rules.unique_solution(c['grid']);rules.PROOFS[slug](c)
     story=json.loads((ROOT/'learn'/slug/f'example-{n}.json').read_text());rules._stories.validate_story(story,c)
 def test_removing_trials_targets_or_complete_native_premises_is_rejected(self):
  for slug,cases in self.examples.items():
   e=cases[0]
   changes=[('branches',e['branches'][:-1]),('targets',[]),('frames',e['frames'][:-1]),('labels',e['labels'][:-1])]
   for key,value in changes:
    with self.subTest(slug=slug,key=key):
     changed=copy.deepcopy(e);changed[key]=value
     with self.assertRaises(ValueError):rules.PROOFS[slug](changed)
 def test_native_moves_cannot_skip_copies_forced_double_taps_or_overlays(self):
  for slug in ['xy-wing','xyz-wing']:
   e=self.examples[slug][0];base=json.loads((ROOT/'learn'/slug/'example-1.json').read_text())
   for key,value in [('initialStatus','definite'),('boards',1),('validSlots',[]),('slotFills',[]),('overlays',[]),('notes',[]),('fills',[]),('revealFrameCount',0),('revealLabelCount',0)]:
    with self.subTest(slug=slug,key=key):
     changed=copy.deepcopy(base);changed['expected'][key]=value
     with self.assertRaises(ValueError):rules._stories.validate_story(changed,e)
   for operation in ['copy','single','wheel','overlay','strike','extra','early-single','late-releases']:
    with self.subTest(slug=slug,operation=operation):
     changed=copy.deepcopy(base);frames=changed['frames']
     if operation=='copy':next(f for f in frames if f['do']=='tap')['at']={'part':'slot','slot':1}
     if operation=='single':next(f for f in frames if f['do']=='tap' and f.get('count')==2)['at']['note']=1
     if operation=='wheel':next(f for f in frames if f['do']=='ready')['digit']=0
     if operation=='overlay':next(f for f in frames if f['do']=='move' and f['at'].get('part')=='slot')['at']['slot']=2
     if operation=='strike':[f for f in frames if f['do']=='down'][-1]['inputDelay']=0
     if operation=='extra':frames.append({'do':'undo'})
     if operation=='early-single':next(f for f in frames if f['do']=='tap' and f.get('count')==2)['time']=0
     if operation=='late-releases':
      for f in frames:
       if f['do']=='up':f['time']=changed['presentation']['duration']+1000
     with self.assertRaises(ValueError):rules._stories.validate_story(changed,e)
 def test_action_order_movement_completion_and_end_time_are_independent_guards(self):
  e=self.examples['xy-wing'][0];base=json.loads((ROOT/'learn/xy-wing/example-1.json').read_text())
  reordered=copy.deepcopy(base);frames=reordered['frames'];up=next(i for i,f in enumerate(frames) if f['do']=='up');release=frames.pop(up);single=next(i for i,f in enumerate(frames) if f['do']=='tap' and f.get('count')==2);frames.insert(single+1,release)
  for n,f in enumerate(frames):f['time']=500+n*2000
  reordered['presentation']['duration']=frames[-1]['time']+2000
  with self.assertRaisesRegex(ValueError,'released overlay in order'):rules._stories.validate_story(reordered,e)
  overlap=copy.deepcopy(base);frames=overlap['frames'];index=next(i for i,f in enumerate(frames) if f['do']=='move');frames[index]['ms']=frames[index+1]['time']-frames[index]['time']+1
  with self.assertRaisesRegex(ValueError,'Finish each movement'):rules._stories.validate_story(overlap,e)
  shortened=copy.deepcopy(base);shortened['presentation']['duration']=shortened['frames'][-1]['time']-1
  with self.assertRaisesRegex(ValueError,'finish its last action'):rules._stories.validate_story(shortened,e)
if __name__=='__main__':unittest.main()
