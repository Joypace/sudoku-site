"""Global BUG parity and real forced crowded traces are separate obligations."""
from pathlib import Path
import copy,importlib.util,unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('bug_lesson',ROOT/'tools/validate_lessons.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
FIXTURE={'slug': 'bug-plus-one', 'grid': '502408000603507000748103590156374829389215060427986153861732945974651000235849671', 'solutionCount': 1, 'initialStatus': 'dilemma', 'initialSingles': 0, 'pattern': {'cell': 17, 'digit': 2, 'pair': [4, 8], 'cells': [1, 4, 6, 7, 8, 10, 13, 15, 16, 17, 22, 26, 42, 44, 69, 70, 71], 'eliminations': [[17, 4], [17, 8]]}, 'targets': [[17, 4], [17, 8]], 'branches': [[[17, 4], [16, 8], [7, 1], [6, 3]], [[17, 2]], [[17, 8], [16, 1], [7, 3], [6, 7]]], 'branchOutcomes': [{'kind': 'uniqueness-contradiction', 'witness': {'kind': 'bug-complement', 'cell': 17, 'digit': 2}}, {'kind': 'valid'}, {'kind': 'uniqueness-contradiction', 'witness': {'kind': 'bug-complement', 'cell': 17, 'digit': 2}}], 'frames': [[0, 0, 9, 9]], 'labels': [[0, 1, 1], [0, 1, 9], [0, 4, 6], [0, 4, 9], [0, 6, 3], [0, 6, 7], [0, 7, 1], [0, 7, 3], [0, 8, 6], [0, 8, 7], [1, 1, 1], [1, 1, 9], [1, 4, 2], [1, 4, 9], [1, 6, 4], [1, 6, 2], [1, 7, 1], [1, 7, 8], [1, 8, 4], [1, 8, 2], [1, 8, 8], [2, 4, 2], [2, 4, 6], [2, 8, 2], [2, 8, 6], [4, 6, 4], [4, 6, 7], [4, 8, 4], [4, 8, 7], [7, 6, 3], [7, 6, 2], [7, 7, 3], [7, 7, 8], [7, 8, 2], [7, 8, 8]], 'uniquenessPremise': {'kind': 'unique-root', 'solutionCount': 1}, 'sourceFamily': 'fc3f519aed79e01a', 'origin': 'original Sudoku Let’s Try practice puzzle; digit-relabelled original family', 'originalGrid': '502000000000007000008103000006000809000205000000080053060700040970600000000840601', 'completedForcedMoves': 40, 'digitRelabeling': {'permutation': [1, 5, 3, 4, 2, 6, 7, 8, 9], 'sourceGridSHA256': '6f26bd41be580e0b405665ce26dbd26ae05c01b8bc98615130a8319b59e25096', 'sourceGrid': '205408000603207000748103290126374859389512060457986123861735942974621000532849671', 'sourceOriginalGrid': '205000000000007000008103000006000809000502000000080023060700040970600000000840601', 'sourceCompletedForcedMoves': 40, 'sourceOriginalGridSHA256': '0237afe93aedd09fd820650cdcc486e598cc552499da23bd17ddb0677dd7c2f0'}, 'nativeWarnings': [{'kind': 'crowded', 'constraints': [[0, 4, 6], [1, 4, 6], [2, 6, 1], [2, 8, 6], [3, 5, 6]]}, {'kind': 'valid'}, {'kind': 'crowded', 'constraints': [[0, 4, 8], [1, 4, 3], [2, 6, 3], [3, 5, 3]]}]}
class BugProof(unittest.TestCase):
 def test_global_two_home_condition_and_visible_forced_traces(self):
  p.PROOFS['bug-plus-one'](copy.deepcopy(FIXTURE))
 def test_root_unique_is_checked_once_not_bad_trial_completions(self):
  with patch.object(p,'unique_solution',wraps=p.unique_solution) as count:p.PROOFS['bug-plus-one'](copy.deepcopy(FIXTURE))
  count.assert_called_once_with(FIXTURE['grid'])
  with patch.object(p,'unique_solution',side_effect=ValueError('not unique')):
   with self.assertRaisesRegex(ValueError,'not unique'):p.PROOFS['bug-plus-one'](copy.deepcopy(FIXTURE))
 def test_two_notes_per_cell_alone_does_not_prove_bug(self):
  g=list(map(int,FIXTURE['grid']));cs=p._bug._b._candidates(g);cs[13]=frozenset({4,9})
  with self.assertRaisesRegex(ValueError,'exactly two homes'):p._bug._bug(FIXTURE['pattern'],g,cs)
 def test_native_warning_cannot_be_generic_uniqueness_incomplete_or_retyped(self):
  for mode in ['generic','uniqueness','missing-set','float-id','wrong-global-witness']:
   e=copy.deepcopy(FIXTURE)
   if mode=='generic':e['nativeWarnings'][0]={'kind':'invalid'}
   if mode=='uniqueness':e['nativeWarnings'][0]['kind']='uniqueness'
   if mode=='missing-set':e['nativeWarnings'][0]['constraints']=e['nativeWarnings'][0]['constraints'][:-1]
   if mode=='float-id':e['nativeWarnings'][0]['constraints'][0][0]=0.0
   if mode=='wrong-global-witness':e['branchOutcomes'][0]['witness']={'kind':'two-solutions','count':2}
   with self.subTest(mode=mode),self.assertRaises(ValueError):p.PROOFS['bug-plus-one'](e)
 def test_second_guesses_and_continuing_past_first_warning_are_rejected(self):
  e=copy.deepcopy(FIXTURE);e['branches'][0][1]=[69,2]
  with self.assertRaisesRegex(ValueError,'Only the founding move'):p.PROOFS['bug-plus-one'](e)
  e=copy.deepcopy(FIXTURE);e['branches'][0].append([0,1])
  with self.assertRaisesRegex(ValueError,'Stop at the first crowded warning'):p.PROOFS['bug-plus-one'](e)
 def test_full_roof_candidates_targets_and_starting_notes_are_required(self):
  for mode in ['missing-case','missing-target','missing-label','wrong-count']:
   e=copy.deepcopy(FIXTURE)
   if mode=='missing-case':e['branches']=e['branches'][:-1];e['branchOutcomes']=e['branchOutcomes'][:-1];e['nativeWarnings']=e['nativeWarnings'][:-1]
   if mode=='missing-target':e['targets']=e['targets'][:-1]
   if mode=='missing-label':e['labels']=e['labels'][:-1]
   if mode=='wrong-count':e['uniquenessPremise']['solutionCount']=True
   with self.subTest(mode=mode),self.assertRaises(ValueError):p.PROOFS['bug-plus-one'](e)
class BugWarningBinding(unittest.TestCase):
 def shell(self):
  warnings=[{'slot':n,'constraints':w['constraints']} for n,w in enumerate(FIXTURE['nativeWarnings'],1) if w['kind']=='crowded']
  frames=[]
  for k in range(3):frames.extend([{'do':'tap','at':{'part':'slot','slot':k+2},'time':1000+k*2000},{'do':'tap','at':{'part':'cell','cell':[0,6]},'count':2,'time':1200+k*2000},{'do':'tap','at':{'part':'slot','slot':1},'time':2000+k*2000}])
  return copy.deepcopy({'expected':{'validSlots':[0,2],'crowdedWarnings':warnings},'presentation':{'uniquenessPremise':FIXTURE['uniquenessPremise'],'warningFrames':[1800,5800],'captions':[]},'frames':frames})
 def check(self,data,common):p._bug_stories.validate_story(data,FIXTURE,common,p._intermediate,p.require)
 def test_crowded_contract_delegates_the_same_generic_gestures_and_warning_windows(self):
  from unittest.mock import Mock
  data=self.shell();common=Mock();self.check(data,common);common.validate_story.assert_called_once_with(data,FIXTURE,valid_slots=[0,2]);common.validate_warning_views.assert_called_once_with(data,[0,2])
 def test_wrong_warning_kind_membership_types_or_premise_is_rejected(self):
  from unittest.mock import Mock
  for mode in ['missing','generic','trimmed','float','unique','false-premise']:
   d=self.shell()
   if mode=='missing':d['expected'].pop('crowdedWarnings')
   if mode=='generic':d['expected']['crowdedWarnings'][0]={'slot':1,'warning':'invalid'}
   if mode=='trimmed':d['expected']['crowdedWarnings'][0]['constraints'].pop()
   if mode=='float':d['expected']['crowdedWarnings'][0]['constraints'][0][0]=0.0
   if mode=='unique':d['expected']['uniquenessWarnings']=[{'slot':1,'cells':[0,1,2,3]}]
   if mode=='false-premise':d['presentation']['uniquenessPremise']['solutionCount']=1.0
   with self.subTest(mode=mode),self.assertRaises(ValueError):self.check(d,Mock())
class BugPublishedFlow(unittest.TestCase):
 def test_real_story_preserves_forced_gestures_and_crowded_only_warning_contract(self):
  import json
  folder=ROOT/'learn/bug-plus-one';e=json.loads((folder/'examples.json').read_text())[0];data=json.loads((folder/'example-1.json').read_text())
  def check(story):p._bug_stories.validate_story(story,e,p._stories,p._intermediate,p.require)
  check(data)
  for mode in ['all-slots-valid','hidden-setup','note-position-tap','false-uniqueness-warning','warning-before-force']:
   changed=copy.deepcopy(data)
   if mode=='all-slots-valid':changed['expected']['validSlots']=list(range(len(e['branches'])+1))
   if mode=='hidden-setup':changed['setup']=[{'fill':[1,8,4]}]
   if mode=='note-position-tap':next(f for f in changed['frames'] if f['do']=='tap' and f.get('count')==2)['at']['note']=1
   if mode=='false-uniqueness-warning':changed['expected']['uniquenessWarnings']=[{'slot':1,'cells':[0,1,2,3]}]
   if mode=='warning-before-force':changed['presentation']['warningFrames'][0]=0
   with self.subTest(mode=mode),self.assertRaises(ValueError):check(changed)
if __name__=='__main__':unittest.main()
