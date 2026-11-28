"""A conditional corner swap requires an actually unique original root."""
from pathlib import Path
import copy,importlib.util,unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('rectangle_lesson',ROOT/'tools/validate_lessons.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
FIXTURE={'slug': 'unique-rectangle', 'grid': '280040000070000900004600000352487090807000425000000873000260307720034569030009210', 'solutionCount': 1, 'initialStatus': 'dilemma', 'initialSingles': 0, 'pattern': {'type': 1, 'rows': [0, 3], 'columns': [6, 8], 'boxes': [2, 5], 'corners': [6, 8, 33, 35], 'roof': 6, 'digits': [1, 6], 'extras': [7], 'eliminations': [[6, 1], [6, 6]]}, 'targets': [[6, 1], [6, 6]], 'branches': [[[6, 1], [8, 6], [33, 6], [35, 1]], [[6, 6], [8, 1], [33, 1], [35, 6]], [[6, 7]]], 'branchOutcomes': [{'kind': 'uniqueness-contradiction', 'witness': {'kind': 'rectangle-digit-swap', 'corners': [6, 8, 33, 35], 'digits': [1, 6]}}, {'kind': 'uniqueness-contradiction', 'witness': {'kind': 'rectangle-digit-swap', 'corners': [6, 8, 33, 35], 'digits': [1, 6]}}, {'kind': 'valid'}], 'frames': [[0, 6, 1, 1], [0, 8, 1, 1], [3, 6, 1, 1], [3, 8, 1, 1]], 'labels': [[0, 6, 1], [0, 6, 6], [0, 6, 7], [0, 8, 1], [0, 8, 6], [3, 6, 1], [3, 6, 6], [3, 8, 1], [3, 8, 6]], 'uniquenessPremise': {'kind': 'unique-root', 'solutionCount': 1}, 'nativeQualification': 'required', 'sourceFamily': '02040fc51e37a374', 'origin': 'original Sudoku Let’s Try practice puzzle'}
class RectangleProof(unittest.TestCase):
 def test_unique_two_box_rectangle_and_both_swap_assumptions(self):
  p.PROOFS['unique-rectangle'](copy.deepcopy(FIXTURE))
 def test_only_the_original_root_is_checked_for_uniqueness(self):
  with patch.object(p,'unique_solution',wraps=p.unique_solution) as count:
   p.PROOFS['unique-rectangle'](copy.deepcopy(FIXTURE))
  count.assert_called_once_with(FIXTURE['grid'])
  with patch.object(p,'unique_solution',side_effect=ValueError('not unique')):
   with self.assertRaisesRegex(ValueError,'not unique'):p.PROOFS['unique-rectangle'](copy.deepcopy(FIXTURE))
 def test_ordinary_invalid_and_two_actual_solutions_are_not_swap_certificates(self):
  for wrong in [{'kind':'valid'},{'kind':'contradiction','witness':{'kind':'empty-cell','cell':0}},{'kind':'uniqueness-contradiction','witness':{'kind':'two-solutions','count':2}}]:
   with self.subTest(outcome=wrong):
    e=copy.deepcopy(FIXTURE);e['branchOutcomes'][0]=wrong
    with self.assertRaises(ValueError):p.PROOFS['unique-rectangle'](e)
 def test_all_roof_candidates_and_four_filled_swap_corners_are_required(self):
  for mode in ['missing-case','unfinished-swap','second-guess']:
   e=copy.deepcopy(FIXTURE)
   if mode=='missing-case':e['branches']=e['branches'][:-1];e['branchOutcomes']=e['branchOutcomes'][:-1]
   if mode=='unfinished-swap':e['branches'][0]=e['branches'][0][:-1]
   if mode=='second-guess':e['branches'][2].append([8,1])
   with self.subTest(mode=mode),self.assertRaises(ValueError):p.PROOFS['unique-rectangle'](e)
 def test_four_boxes_given_corners_extra_floors_and_missing_roof_pair_are_rejected(self):
  for mode in ['four-boxes','given-corner','extra-floor','missing-roof-pair']:
   e=copy.deepcopy(FIXTURE);cs=p._rectangle._b._candidates(list(map(int,e['grid'])))
   if mode=='four-boxes':e['pattern'].update(rows=[0,3],columns=[0,3],corners=[0,3,27,30],roof=0,boxes=[0,1]);cs={0:{1,6,7},3:{1,6},27:{1,6},30:{1,6}}
   if mode=='given-corner':cs.pop(8)
   if mode=='extra-floor':cs[8]=cs[8]|{7}
   if mode=='missing-roof-pair':cs[6]=cs[6]-{1}
   with self.subTest(mode=mode),self.assertRaises(ValueError):p._rectangle._rectangle(e['pattern'],cs)
 def test_integer_coordinates_and_unique_root_annotation_are_strict(self):
  for path in [('targets',0,0),('frames',0,0),('labels',0,0),('branches',0,0,0),('pattern','type'),('uniquenessPremise','solutionCount')]:
   for value in [True,1.0]:
    with self.subTest(path=path,value=value):
     e=copy.deepcopy(FIXTURE);node=e
     for k in path[:-1]:node=node[k]
     node[path[-1]]=value
     with self.assertRaises(ValueError):p.PROOFS['unique-rectangle'](e)
class RectangleWarningBinding(unittest.TestCase):
 def shell(self):
  return {'expected':{'validSlots':[0,3],'uniquenessWarnings':[{'slot':1,'cells':FIXTURE['pattern']['corners']},{'slot':2,'cells':FIXTURE['pattern']['corners']}]},'presentation':{'uniquenessPremise':copy.deepcopy(FIXTURE['uniquenessPremise']),'warningFrames':[1800,3800],'captions':[]},'frames':[{'do':'tap','at':{'part':'slot','slot':2},'time':1000},{'do':'tap','at':{'part':'cell','cell':[3,8]},'count':2,'time':1200},{'do':'tap','at':{'part':'slot','slot':1},'time':2000},{'do':'tap','at':{'part':'slot','slot':3},'time':3000},{'do':'tap','at':{'part':'cell','cell':[3,8]},'count':2,'time':3200},{'do':'tap','at':{'part':'slot','slot':1},'time':4000}]}
 def check(self,data,common):
  p._rectangle_stories.validate_story(data,FIXTURE,common,p._intermediate,p.require)
 def test_native_group_binding_delegates_generic_gestures_with_only_actual_valid_slots(self):
  from unittest.mock import Mock
  common=Mock();data=self.shell();self.check(data,common)
  common.validate_story.assert_called_once_with(data,FIXTURE,valid_slots=[0,3])
  common.validate_warning_views.assert_called_once_with(data,[0,1])
 def test_generic_invalid_missing_wrong_or_untyped_uniqueness_assertions_are_rejected(self):
  from unittest.mock import Mock
  for mode in ['missing','generic-invalid','wrong-corner','extra-slot','float-slot','float-cell','false-premise']:
   data=self.shell()
   if mode=='missing':data['expected'].pop('uniquenessWarnings')
   if mode=='generic-invalid':data['expected']['uniquenessWarnings'][0]={'slot':1,'warning':'invalid'}
   if mode=='wrong-corner':data['expected']['uniquenessWarnings'][0]['cells']=[6,8,33,34]
   if mode=='extra-slot':data['expected']['uniquenessWarnings'].append({'slot':3,'cells':FIXTURE['pattern']['corners']})
   if mode=='float-slot':data['expected']['uniquenessWarnings'][0]['slot']=1.0
   if mode=='float-cell':data['expected']['uniquenessWarnings'][0]['cells']=[6.0,8,33,35]
   if mode=='false-premise':data['presentation']['uniquenessPremise']['solutionCount']=1.0
   with self.subTest(mode=mode),self.assertRaises(ValueError):self.check(data,Mock())
 def test_warning_views_must_be_settled_active_and_unobscured(self):
  from unittest.mock import Mock
  for mode in ['missing','too-early','after-board-switch','float-time','caption-covered']:
   data=self.shell()
   if mode=='missing':data['presentation']['warningFrames']=[]
   if mode=='too-early':data['presentation']['warningFrames'][0]=1600
   if mode=='after-board-switch':data['presentation']['warningFrames'][0]=2000
   if mode=='float-time':data['presentation']['warningFrames'][0]=1800.0
   if mode=='caption-covered':data['presentation']['captions']=[{'start':1700,'end':1900}]
   with self.subTest(mode=mode),self.assertRaises(ValueError):p._stories.validate_warning_views(data,[0,1])
class RectanglePublishedFlow(unittest.TestCase):
 def test_real_story_integrates_diagnostic_states_without_weakening_gesture_setup(self):
  import json
  folder=ROOT/'learn/unique-rectangle';e=json.loads((folder/'examples.json').read_text())[0];data=json.loads((folder/'example-1.json').read_text())
  def check(story):p._rectangle_stories.validate_story(story,e,p._stories,p._intermediate,p.require)
  check(data)
  for mode in ['all-slots-valid','hidden-corner-setup','note-position-double-tap']:
   changed=copy.deepcopy(data)
   if mode=='all-slots-valid':changed['expected']['validSlots']=list(range(len(e['branches'])+1))
   if mode=='hidden-corner-setup':changed['setup']=[{'fill':[0,6,1]}]
   if mode=='note-position-double-tap':next(f for f in changed['frames'] if f['do']=='tap' and f.get('count')==2)['at']['note']=1
   with self.subTest(mode=mode),self.assertRaises(ValueError):check(changed)
if __name__=='__main__':unittest.main()
