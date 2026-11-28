"""Synthetic candidate-mask theorem tests; no raw puzzle/native qualification."""
from itertools import product
import copy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock,patch

TOOLS=Path(__file__).resolve().parents[1]/'tools'
def load(name):
 spec=importlib.util.spec_from_file_location('ur3_test_'+name,TOOLS/(name+'.py'))
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
proof=load('unique_rectangle_type3')
b=load('intermediate_proofs');rectangle=load('unique_rectangle');ur2=load('unique_rectangle_type2');common=load('intermediate_stories')


def fixture(count=2):
 roofs=[0,1];floors=[27,28];pair={1,2};extras={3,4}
 roof_extras=({3},{4}) if count==2 else ({3,4},{4}) if count==3 else ({3,4},{3,4})
 cs={i:set(range(1,10)) for i in range(81)}
 for i in floors:cs[i]=pair.copy()
 for i,ds in zip(roofs,roof_extras):cs[i]=pair|ds
 cs[2]=extras.copy()
 p={'type':3,'profile':'virtual-naked-pair','rows':[0,3],'columns':[0,1],
    'boxes':[0,3],'corners':[0,1,27,28],'roofs':roofs,'floors':floors,
    'digits':[1,2],'extraDigits':[3,4],'partner':2,'unit':'row','unitIndex':0}
 targets,frames,labels,choices=proof.derive(p,cs,base=b,rectangle=rectangle)
 e={'grid':'0'*81,'slug':'unique-rectangle-type-3','pattern':p,
    'proofMode':'uniqueness-roof-extras-disjunction',
    'coverage':{'kind':'roof-extras-disjunction','choices':choices},
    'branches':[[q,[2,7-q[1]]] for q in choices],
    'branchOutcomes':[{'kind':'valid'} for q in choices],
    'targets':[list(q) for q in sorted(targets)],'frames':[list(q) for q in sorted(frames)],
    'labels':[list(q) for q in sorted(labels)],'uniquenessPremise':{'kind':'unique-root','solutionCount':1}}
 return e,cs


def after_mask(cs,state):
 return {i:ds-{state[j] for j in b.PEERS[i]} for i,ds in cs.items() if not state[i]}

def physical_story(e):
 frames=[];clock=1000
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
 add('tap',at=slot(1))
 for n in range(2,len(e['branches'])+2):
  add('down',at=slot(n));add('move',at=slot(1));add('up')
 import math
 for i,d in e['targets']:
  row,col=divmod(d-1,3);dx,dy=col-1,row-1;scale=1.617/(math.sqrt(2) if dx and dy else 1)
  add('down',at=cell(i),inputDelay=440)
  add('move',at={**cell(i),'offset':[scale*dx,scale*dy]});add('up')
 count=len(e['branches']);cells=sorted({i for branch in e['branches'] for i,d in branch})
 return {'grid':e['grid'],'style':'chill','setup':[],'frames':frames,
  'expected':{'initialStatus':'dilemma','boards':count+1,'validSlots':list(range(count+1)),
    'slotFills':[[n,i//9,i%9,d] for n,branch in enumerate(e['branches'],1) for i,d in branch],
    'overlays':[[n,0] for n in range(1,count+1)],'fills':[[i//9,i%9,0] for i in cells],
    'notes':[[i//9,i%9,d,False] for i,d in e['targets']]+[[r,c,d,True] for r,c,d in e['labels']],
    'revealFrameCount':len(e['frames']),'revealLabelCount':len(e['labels'])},
  'presentation':{'duration':clock+500,'choiceReveal':{'start':500,'frames':e['frames'],'labels':e['labels']},
    'coverage':copy.deepcopy(e['coverage']),'uniquenessPremise':copy.deepcopy(e['uniquenessPremise'])}}


class UR3Pair(unittest.TestCase):
 def test_virtual_pair_theorem_independent_assignments_and_all_houses(self):
  for count in (2,3,4):
   e,cs=fixture(count);p=e['pattern']
   targets,frames,labels,choices=proof.derive(p,cs,base=b,rectangle=rectangle)
   self.assertEqual(len(choices),count);self.assertEqual(len(labels),10+count)
   self.assertIn((0,0,1,9),frames);self.assertIn((0,0,3,3),frames)
   self.assertIn((3,3),targets);self.assertIn((9,4),targets) # row and box scope
   cells=p['corners']+[p['partner']];legal=[]
   for values in product(*(sorted(cs[i]) for i in cells)):
    assignment=dict(zip(cells,values))
    if not any(assignment[i] in {3,4} for i in p['roofs']):continue
    if any(assignment[i]==assignment[j] and j in b.PEERS[i] for i in cells for j in cells if i<j):continue
    legal.append(assignment)
   self.assertTrue(legal)
   for target,digit in targets:
    self.assertTrue(all(any(value==digit and i in b.PEERS[target] for i,value in a.items()) for a in legal))
   self.assertEqual({tuple(q) for q in choices},{(i,d) for i in p['roofs'] for d in cs[i]-{1,2}})

 def test_strict_geometry_exact_extra_union_and_real_partner(self):
  e,cs=fixture();p=e['pattern']
  for key,val in [('type',True),('profile','all-subsets'),('roofs',[0,28]),('partner',0),('partner',True),
                  ('extraDigits',[3,5]),('unitIndex',True),('unit','column'),('boxes',[0,1])]:
   q=copy.deepcopy(p);q[key]=val
   with self.subTest(key=key),self.assertRaises(ValueError):proof.derive(q,cs,base=b,rectangle=rectangle)
  for i,ds in [(2,{3,4,5}),(0,{1,2}),(27,{1,2,3})]:
   mask=copy.deepcopy(cs);mask[i]=ds
   with self.subTest(i=i),self.assertRaises(ValueError):proof.derive(p,mask,base=b,rectangle=rectangle)
  mask=copy.deepcopy(cs);del mask[0]
  with self.assertRaises(ValueError):proof.derive(p,mask,base=b,rectangle=rectangle)

 def test_disjunction_all_literals_not_same_founder_exhaustion_and_forced_partner(self):
  for count in (2,3,4):
   e,cs=fixture(count);targets=set(map(tuple,e['targets']));choices=e['coverage']['choices']
   with patch.object(b,'_candidates',side_effect=lambda state:after_mask(cs,state)):
    proof.trials(e,[0]*81,cs,targets,choices,base=b)
    for mutation in ('missing-choice','same-founder','no-partner','second-guess','invalid-outcome'):
     q=copy.deepcopy(e)
     if mutation=='missing-choice':q['coverage']['choices']=q['coverage']['choices'][:-1]
     elif mutation=='same-founder':q['branches'][-1]=q['branches'][0]
     elif mutation=='no-partner':q['branches'][0]=q['branches'][0][:1]
     elif mutation=='second-guess':q['branches'][0].insert(1,[80,6])
     else:q['branchOutcomes'][0]={'kind':'uniqueness-contradiction'}
     with self.subTest(count=count,mutation=mutation),self.assertRaises(ValueError):proof.trials(q,[0]*81,cs,targets,choices,base=b)

 def test_raw_root_callback_swap_and_full_target_appearance_contract(self):
  e,cs=fixture();unique=Mock()
  with patch.object(b,'_candidates',side_effect=lambda state:after_mask(cs,state)):
   proof.validate(e,base=b,rectangle=rectangle,ur2=ur2,unique_root=unique)
   unique.assert_called_once_with(e['grid'])
   for key,val in [('targets',e['targets'][:-1]),('targets',e['targets']*2),('labels',e['labels'][:-1]),
                   ('frames',e['frames'][:-1]),('solutionCount',2)]:
    q=copy.deepcopy(e);q[key]=val
    with self.subTest(key=key),self.assertRaises(ValueError):proof.validate(q,base=b,rectangle=rectangle,ur2=ur2,unique_root=Mock())
   with self.assertRaisesRegex(ValueError,'not unique'):
    proof.validate(e,base=b,rectangle=rectangle,ur2=ur2,unique_root=Mock(side_effect=ValueError('not unique')))

 def test_typed_coverage_metadata(self):
  e,_=fixture();expected=e['coverage']['choices']
  for raw in ({'kind':'roof-extras-disjunction','choices':tuple(expected)},
              {'kind':'roof-extras-disjunction','choices':[[False,3],[1,4]]},
              {'kind':'roof-extras-disjunction','choices':[[0,3.0],[1,4]]},
              {'kind':'same-founder','choices':expected}):
   with self.subTest(raw=raw),self.assertRaises(ValueError):proof.coverage(raw,expected,b)

 def test_valid_physical_stories_call_unchanged_common_projection(self):
  for count in (2,3,4):
   e,_=fixture(count);data=physical_story(e);original=copy.deepcopy(data)
   with patch.object(common,'validate_story',wraps=common.validate_story) as called:
    proof.validate_story(data,e,common=common,base=b)
   called.assert_called_once()
   projected=called.call_args.args[0]
   self.assertEqual(projected['expected']['notes'],[[i//9,i%9,d,False] for i,d in e['targets']])
   self.assertEqual(called.call_args.kwargs,{'valid_slots':list(range(count+1))})
   self.assertEqual(data,original)
   with self.assertRaisesRegex(ValueError,'Remove exactly'):common.validate_story(data,e)

 def test_story_missing_retention_extra_mutation_and_wrong_guest_coverage(self):
  e,_=fixture();data=physical_story(e)
  for mutation in ('missing-retained','extra-mutation','hidden-final','wrong-coverage',
                   'wrong-guests','wrong-slots','wrong-fill','wrong-guess','extra-note'):
   q=copy.deepcopy(data)
   if mutation=='missing-retained':q['expected']['notes'].pop()
   elif mutation=='extra-mutation':q['frames'].append({'do':'tap','at':{'part':'cell','cell':[8,8]},'time':q['frames'][-1]['time']+100})
   elif mutation=='hidden-final':q['final']=[{'id':'SET_FILL'}]
   elif mutation=='wrong-coverage':q['presentation']['coverage']['choices'][1]=[0,4]
   elif mutation=='wrong-guests':q['expected']['boards']=2
   elif mutation=='wrong-slots':q['expected']['validSlots']=[0,1]
   elif mutation=='wrong-fill':q['expected']['slotFills'][0][-1]=4
   elif mutation=='wrong-guess':next(f for f in q['frames'] if f['do']=='ready')['digit']=4
   else:q['expected']['notes'].append([8,8,6,False])
   with self.subTest(mutation=mutation),self.assertRaises(ValueError):proof.validate_story(q,e,common=common,base=b)

 def test_story_exact_types_for_notes_boards_slots_premise_and_coverage(self):
  e,_=fixture();data=physical_story(e);mutations=[]
  for flag in (1,1.0):
   q=copy.deepcopy(data);q['expected']['notes'][-1][3]=flag;mutations.append(q)
  for field,value in ((0,True),(0,1.0),(1,False),(2,3.0)):
   q=copy.deepcopy(data);q['expected']['notes'][-1][field]=value;mutations.append(q)
  for value in (3.0,True):
   q=copy.deepcopy(data);q['expected']['boards']=value;mutations.append(q)
  for value in ([False,1,2],[0,True,2],[0,1,2.0],(0,1,2)):
   q=copy.deepcopy(data);q['expected']['validSlots']=value;mutations.append(q)
  for value in (1.0,True):
   q=copy.deepcopy(data);q['presentation']['uniquenessPremise']['solutionCount']=value;mutations.append(q)
  for value in ([[0.0,3],[1,4]],[[False,3],[1,4]],[(0,3),[1,4]],[[0,3]],[[0,3,1],[1,4]]):
   q=copy.deepcopy(data);q['presentation']['coverage']['choices']=value;mutations.append(q)
  for q in mutations:
   with self.subTest(q=q),self.assertRaises(ValueError):proof.validate_story(q,e,common=common,base=b)

if __name__=='__main__':unittest.main()
