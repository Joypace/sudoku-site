"""CODE ONLY synthetic proof/physical-binding tests; no native warning claims."""
import copy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock,patch

TOOLS=Path(__file__).resolve().parents[1]/'tools'
def load(name):
 spec=importlib.util.spec_from_file_location('ur4_test_'+name,TOOLS/(name+'.py'))
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
proof=load('unique_rectangle_type4')
b=load('intermediate_proofs');rectangle=load('unique_rectangle');common=load('intermediate_stories');rectangle_stories=load('unique_rectangle_stories')


def fixture():
 cs={i:set(range(1,10)) for i in range(81)}
 for i in b.UNITS[0]:
  if i not in (0,1):cs[i].remove(1)
 cs[0]={1,2,3};cs[1]={1,2,4};cs[27]=cs[28]={1,2}
 p={'type':4,'rows':[0,3],'columns':[0,1],'boxes':[0,3],'corners':[0,1,27,28],
    'roofs':[0,1],'floors':[27,28],'digits':[1,2],'strongDigit':1,
    'unit':'row','unitIndex':0,'strongPositions':[0,1]}
 targets,frames,labels=proof.derive(p,cs,base=b,rectangle=rectangle)
 witness={'kind':'rectangle-digit-swap','corners':p['corners'],'digits':p['digits']}
 e={'grid':'0'*81,'slug':'unique-rectangle-type-4','pattern':p,
    'proofMode':'independent-uniqueness-refutations',
    'coverage':{'kind':'each-target-refuted','choices':[[0,2],[1,2]]},
    'branches':[[[0,2],[1,1],[27,1],[28,2]],[[1,2],[0,1],[28,1],[27,2]]],
    'branchOutcomes':[{'kind':'uniqueness-contradiction','witness':copy.deepcopy(witness)} for _ in range(2)],
    'targets':[list(q) for q in sorted(targets)],'frames':[list(q) for q in sorted(frames)],
    'labels':[list(q) for q in sorted(labels)],'uniquenessPremise':{'kind':'unique-root','solutionCount':1}}
 return e,cs


def after_mask(cs,state):return {i:ds-{state[j] for j in b.PEERS[i]} for i,ds in cs.items() if not state[i]}


def story(e):
 frames=[];clock=1000;warnings=[]
 def add(op,**fields):
  nonlocal clock
  frames.append({'do':op,'time':clock,**fields});clock+=100
 cell=lambda i:{'part':'cell','cell':[i//9,i%9]}
 slot=lambda n:{'part':'slot','slot':n}
 for k,branch in enumerate(e['branches']):
  if k:add('tap',at=slot(1))
  add('tap',at=slot(k+2));i,d=branch[0];row,col=divmod(d-1,3)
  add('down',at=cell(i));add('move',at={**cell(i),'offset':[1.2*(col-1),1.2*(row-1)]})
  add('ready',digit=d);add('up')
  for i,d in branch[1:]:add('tap',at=cell(i),count=2)
  warnings.append(clock+600);clock+=1000
 add('tap',at=slot(1))
 for n in (2,3):add('down',at=slot(n));add('move',at=slot(1));add('up')
 import math
 for i,d in e['targets']:
  row,col=divmod(d-1,3);dx,dy=col-1,row-1;scale=1.617/(math.sqrt(2) if dx and dy else 1)
  add('down',at=cell(i),inputDelay=440);add('move',at={**cell(i),'offset':[scale*dx,scale*dy]});add('up')
 rejected=set(map(tuple,e['targets']))
 return {'grid':e['grid'],'style':'chill','setup':[],'frames':frames,
  'expected':{'initialStatus':'dilemma','boards':3,'validSlots':[0],
    'slotFills':[[slot,i//9,i%9,d] for slot,branch in enumerate(e['branches'],1) for i,d in branch],
    'fills':[[i//9,i%9,0] for i in e['pattern']['corners']],'overlays':[[1,0],[2,0]],
    'uniquenessWarnings':[{'slot':n,'cells':e['pattern']['corners']} for n in (1,2)],
    'notes':[[i//9,i%9,d,False] for i,d in e['targets']]+[[r,c,d,True] for r,c,d in e['labels'] if (r*9+c,d) not in rejected],
    'revealFrameCount':len(e['frames']),'revealLabelCount':len(e['labels'])},
  'presentation':{'duration':clock+500,'warningFrames':warnings,'captions':[],
    'choiceReveal':{'start':500,'frames':e['frames'],'labels':e['labels']},
    'uniquenessPremise':copy.deepcopy(e['uniquenessPremise']),'coverage':copy.deepcopy(e['coverage'])}}

class UR4(unittest.TestCase):
 def test_exact_strong_unit_derives_both_roof_eliminations(self):
  e,cs=fixture();targets,frames,labels=proof.derive(e['pattern'],cs,base=b,rectangle=rectangle)
  self.assertEqual(targets,{(0,2),(1,2)});self.assertIn((0,0,1,9),frames);self.assertEqual(len(labels),10)
  # X is confined to roofs; Y at either roof forces X at the other.
  for roof in e['pattern']['roofs']:
   state=[0]*81;state[roof]=2;current=after_mask(cs,state)
   self.assertIn((1-roof,1),b._forced(state,current))
 def test_missing_extra_strong_position_geometry_and_types_rejected(self):
  e,cs=fixture();p=e['pattern']
  for key,val in [('strongDigit',3),('strongDigit',True),('strongPositions',[0]),
                  ('strongPositions',[False,1]),('unitIndex',0.0),('boxes',[0,1]),
                  ('roofs',[0,28]),('floors',[27,True])]:
   q=copy.deepcopy(p);q[key]=val
   with self.subTest(key=key),self.assertRaises(ValueError):proof.derive(q,cs,base=b,rectangle=rectangle)
  mask=copy.deepcopy(cs);mask[2].add(1)
  with self.assertRaisesRegex(ValueError,'ONLY'):proof.derive(p,mask,base=b,rectangle=rectangle)
  mask=copy.deepcopy(cs);mask[0]={1,2}
  with self.assertRaises(ValueError):proof.derive(p,mask,base=b,rectangle=rectangle)
 def test_independent_trials_forced_four_corner_swaps_not_same_founder(self):
  e,cs=fixture();targets=set(map(tuple,e['targets']))
  with patch.object(b,'_candidates',side_effect=lambda state:after_mask(cs,state)):
   proof.trials(e,[0]*81,cs,targets,base=b,rectangle=rectangle)
   for mutation in ('same-founder','extra-guess','missing-corner','ordinary-invalid','two-solutions','wrong-coverage'):
    q=copy.deepcopy(e)
    if mutation=='same-founder':q['branches'][1]=q['branches'][0]
    elif mutation=='extra-guess':q['branches'][0][1]=[1,4]
    elif mutation=='missing-corner':q['branches'][0].pop()
    elif mutation=='ordinary-invalid':q['branchOutcomes'][0]={'kind':'contradiction','witness':{'kind':'empty-cell','cell':1}}
    elif mutation=='two-solutions':q['branchOutcomes'][0]['witness']={'kind':'two-solutions','count':2}
    else:q['coverage']['kind']='exhaustive-cell'
    with self.subTest(mutation=mutation),self.assertRaises(ValueError):proof.trials(q,[0]*81,cs,targets,base=b,rectangle=rectangle)
 def test_root_only_callback_full_targets_and_appearance(self):
  e,cs=fixture();unique=Mock()
  with patch.object(b,'_candidates',side_effect=lambda state:after_mask(cs,state)):
   proof.validate(e,base=b,rectangle=rectangle,unique_root=unique);unique.assert_called_once_with(e['grid'])
   for key,val in [('targets',[[0,2]]),('targets',e['targets']*2),('frames',[]),('labels',[]),('solutionCount',2)]:
    q=copy.deepcopy(e);q[key]=val
    with self.subTest(key=key),self.assertRaises(ValueError):proof.validate(q,base=b,rectangle=rectangle,unique_root=Mock())
 def test_story_independent_refutations_warning_views_and_mutation_guards(self):
  e,_=fixture();data=story(e);original=copy.deepcopy(data)
  proof.validate_story(data,e,base=b,common=common,rectangle_stories=rectangle_stories);self.assertEqual(data,original)
  for mutation in ('warning-slot','ordinary-warning','all-valid','overlay','extra-input','early-warning','covered-warning','missing-retained'):
   q=copy.deepcopy(data)
   if mutation=='warning-slot':q['expected']['uniquenessWarnings'][1]['slot']=1
   elif mutation=='ordinary-warning':q['expected']['crowdedWarnings']=[{'slot':1}]
   elif mutation=='all-valid':q['expected']['validSlots']=[0,1,2]
   elif mutation=='overlay':q['expected']['overlays']=[]
   elif mutation=='extra-input':q['frames'].append({'do':'tap','at':{'part':'cell','cell':[8,8]},'time':q['frames'][-1]['time']+100})
   elif mutation=='early-warning':q['presentation']['warningFrames'][0]=1000
   elif mutation=='covered-warning':q['presentation']['captions']=[{'start':q['presentation']['warningFrames'][0]-1,'end':q['presentation']['warningFrames'][0]+1}]
   else:q['expected']['notes'].pop()
   with self.subTest(mutation=mutation),self.assertRaises(ValueError):proof.validate_story(q,e,base=b,common=common,rectangle_stories=rectangle_stories)
 def test_story_exact_numeric_types(self):
  e,_=fixture();data=story(e);bad=[]
  for key,value in [('boards',3.0),('validSlots',[False])]:
   q=copy.deepcopy(data);q['expected'][key]=value;bad.append(q)
  for field,value in ((0,True),(1,0.0),(3,1)):
   q=copy.deepcopy(data);q['expected']['notes'][-1][field]=value;bad.append(q)
  q=copy.deepcopy(data);q['presentation']['uniquenessPremise']['solutionCount']=1.0;bad.append(q)
  q=copy.deepcopy(data);q['expected']['uniquenessWarnings'][0]['slot']=True;bad.append(q)
  q=copy.deepcopy(data);q['presentation']['coverage']['choices'][0][0]=0.0;bad.append(q)
  for q in bad:
   with self.subTest(q=q),self.assertRaises(ValueError):proof.validate_story(q,e,base=b,common=common,rectangle_stories=rectangle_stories)

 def test_story_uses_owner_projection_without_changing_source_or_common_contract(self):
  e,_=fixture();data=story(e);original=copy.deepcopy(data)
  with patch.object(rectangle_stories,'validate_story',wraps=rectangle_stories.validate_story) as owner, \
       patch.object(common,'validate_story',wraps=common.validate_story) as physical, \
       patch.object(common,'validate_warning_views',wraps=common.validate_warning_views) as views:
   proof.validate_story(data,e,base=b,common=common,rectangle_stories=rectangle_stories)
  owner.assert_called_once();physical.assert_called_once();views.assert_called_once()
  self.assertEqual(physical.call_args.kwargs,{'valid_slots':[0]})
  self.assertEqual(physical.call_args.args[0]['expected']['notes'],[[i//9,i%9,d,False] for i,d in e['targets']])
  self.assertEqual(data,original)
  with self.assertRaisesRegex(ValueError,'Remove exactly'):common.validate_story(data,e,valid_slots=[0])

if __name__=='__main__':unittest.main()
