from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import copy,unittest
import brute_stories as s
from brute_force_test import GRID,OPEN

WAVES=[[[6,4],[7,6],[10,6]],[[5,7],[18,4],[25,7],[31,6],[34,3],[53,6],[60,8],[62,4]]]
def direct():return {'grid':GRID,'events':[{'op':'guess','choice':[1,1]},{'op':'lightning','stages':[{'fills':copy.deepcopy(v)} for v in WAVES]},{'op':'undoDouble'},{'op':'strike','choice':[1,1]}]}
def certified_direct():
 e=direct()
 proof={'steps':[{'do':'wave','fills':copy.deepcopy(v)} for v in WAVES],
        'end':{'kind':'contradiction','witness':{'kind':'crowded','constraints':[[0,4,2]]}}}
 e['events'][-1]['proof']=copy.deepcopy(proof)
 e['tree']={'steps':[{'do':'exclude','choice':[1,1],'proof':proof}],'end':{'kind':'open'}}
 return e
class VisibleBinding(unittest.TestCase):
 def test_direct_events_project_to_same_context_proof(self):
  e=certified_direct();result=s.validate_events(e)
  self.assertEqual(result['strikes'],[{'slot':0,'choice':[1,1]}])
  self.assertIn([1,1],result['boards'][0]['removed'])
 def test_different_visible_target_cannot_borrow_certificate(self):
  e=certified_direct();e['events'][-1]['choice']=[1,7]
  with self.assertRaises(ValueError):s.validate_events(e)
 def test_open_child_cannot_certify_strike_or_fabricate_checkpoint(self):
  e=certified_direct();e['events'][-1]['proof']=copy.deepcopy(OPEN)
  with self.assertRaises(ValueError):s.validate_events(e)
  e=certified_direct();e['events'][0]['after']={'grid':GRID,'removed':[],'status':'dilemma','redoCue':None}
  with self.assertRaises(ValueError):s.validate_events(e)
 def test_doubleundo_redo_and_new_effect_truncate_history(self):
  e=direct();e['events']=e['events'][:3]
  e['events'][-1]['after']={'grid':GRID,'removed':[],'status':'dilemma','redoCue':{'kind':'disc','choice':[1,1]}}
  e['events'] += [{'op':'redoDouble'},{'op':'undoDouble'},{'op':'guess','choice':[1,6]},{'op':'redoDouble'}]
  with self.assertRaisesRegex(ValueError,'unavailable'):s.validate_events(e)
  e['events'].pop();result=s.validate_events(e);self.assertIsNone(result['boards'][0]['redoCue'])
 def test_copy_slot_isolation_and_no_wave_past_warning(self):
  e=direct();e['events']=[{'op':'copy','source':0,'slot':1}]+e['events'][:2]
  result=s.validate_events(e);self.assertEqual(result['boards'][0]['grid'],GRID);self.assertEqual(result['boards'][1]['status'],'invalid')
  e['events'].append({'op':'wave','fills':[[9,5]]})
  with self.assertRaisesRegex(ValueError,'first warning'):s.validate_events(e)
 def test_guess_dilemma_and_preproved_wave_contract(self):
  e=direct();e['events'][1]['stages'][0]['fills'].append([31,6])
  with self.assertRaisesRegex(ValueError,'SAME pre-wave'):s.validate_events(e)
  e=direct();e['events'].insert(1,{'op':'guess','choice':[7,6]})
  with self.assertRaisesRegex(ValueError,'Dilemma'):s.validate_events(e)

class ReplayBoundaries(unittest.TestCase):
 def test_slot_six_and_float_slots_rejected(self):
  for slot in [6,True,1.0]:
   e={'grid':GRID,'events':[{'op':'copy','source':0,'slot':slot}]}
   with self.subTest(slot=slot),self.assertRaises(ValueError):s.validate_events(e)
 def test_declared_lightning_status_cannot_override_ordinary_proof(self):
  e=direct();e['events'][1]['stages'][0]['status']='solved'
  with self.assertRaisesRegex(ValueError,'stage status'):s.validate_events(e)
 def test_all_published_checkpoints_and_ring_disc_sequence(self):
  import json
  from pathlib import Path
  cases=json.loads((Path(__file__).resolve().parents[1]/'learn/brute-force/examples.json').read_text())
  for case in cases:
   with self.subTest(family=case['sourceFamily']):
    s.validate_events(case)
    events=[e for e in case['events'] if e['op']!='inspect']
    rings=[k for k,e in enumerate(events) if e.get('checkpoint',{}).get('redo') is not None and e['checkpoint']['redo']['kind']=='ring']
    if 'ring' in case['requireCues']:self.assertTrue(rings)
    for k in rings:
     if events[k]['op']=='undoDouble':
      self.assertEqual(events[k+1]['op'],'undoDouble')
      self.assertEqual(events[k+1]['checkpoint']['redo']['kind'],'disc')
 def test_cue_or_note_mask_tamper_cannot_borrow_tree(self):
  import json
  from pathlib import Path
  case=json.loads((Path(__file__).resolve().parents[1]/'learn/brute-force/examples.json').read_text())[2]
  for mode in ['cue','notes','choice']:
   e=copy.deepcopy(case)
   if mode=='cue':next(x for x in e['events'] if x['checkpoint'].get('redo'))['checkpoint']['redo']['kind']='ring'
   if mode=='notes':e['events'][-1]['checkpoint']['boards'][0]['notes'][0]=False
   if mode=='choice':e['events'][-1]['choice']=[20,3]
   with self.subTest(mode=mode),self.assertRaises(ValueError):s.validate_events(e)


class MultiBoardCheckpoints(unittest.TestCase):
 def point(self,slots=1,active=0,overlay=False):
  rows=[]
  for slot in range(slots):
   rows.append({'slot':slot,'fills':[int(c)-1 for c in GRID],'notes':[True]*729,'status':'dilemma','valid':True,'singles':0,
    'warnings':{'starving':0,'crowded':0,'uniqueness':0,'conflict':0,'warningCells':0,'conflictGroups':0},'crowdedConstraints':[],'starvingConstraints':[],'uniquenessGroups':[],
    'host':0 if overlay and slot==1 else None,'overlays':[1] if overlay and slot==0 else []})
  return {'boards':rows,'boardCount':slots,'canUndo':slots>1,'canRedo':False,'redo':None,'displaySlot':active}
 def test_new_allboard_format_copy_global_history_not_local_cursor(self):
  e={'grid':GRID,'events':[{'op':'inspect','checkpoint':self.point()},{'op':'copy','source':0,'slot':1,'checkpoint':self.point(2,1)}]}
  s.validate_events(e)
  e['events'] += [{'op':'select','slot':0},{'op':'overlay','source':1,'target':0,'checkpoint':self.point(2,0,True)}]
  s.validate_events(e)
 def test_all_other_board_values_and_overlay_memberships_must_match(self):
  for mode in ['other-board','mask','display','host','overlays','count','missing-board','global-single-history']:
   e={'grid':GRID,'events':[{'op':'copy','source':0,'slot':1,'checkpoint':self.point(2,1)}]};c=e['events'][0]['checkpoint']
   if mode=='other-board':c['boards'][0]['fills'][0]=4
   if mode=='mask':c['boards'][0]['notes'][0]=False
   if mode=='display':c['displaySlot']=0
   if mode=='host':c['boards'][1]['host']=0
   if mode=='overlays':c['boards'][0]['overlays']=[1]
   if mode=='count':c['boardCount']=1
   if mode=='missing-board':c['boards'].pop()
   if mode=='global-single-history':e={'grid':GRID,'events':[{'op':'inspect','checkpoint':self.point()}]};e['events'][0]['checkpoint']['canUndo']=True
   with self.subTest(mode=mode),self.assertRaises(ValueError):s.validate_events(e)
 def test_copies_cannot_use_unmodelled_global_history_or_edit_guest(self):
  e={'grid':GRID,'events':[{'op':'copy','source':0,'slot':1},{'op':'undoDouble'}]}
  with self.assertRaisesRegex(ValueError,'Copied-board'):s.validate_events(e)
  e['events']=[{'op':'copy','source':0,'slot':1},{'op':'overlay','source':1,'target':0},{'op':'select','slot':1}]
  with self.assertRaisesRegex(ValueError,'non-guest'):s.validate_events(e)

if __name__=='__main__':unittest.main()
