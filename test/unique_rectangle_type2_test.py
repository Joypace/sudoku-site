"""Synthetic geometry/contract tests; no discovered puzzle or native claims."""
from collections import Counter
import copy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

TOOLS=Path(__file__).resolve().parents[1]/'tools'
def load(name):
 spec=importlib.util.spec_from_file_location('ur2_test_'+name,TOOLS/(name+'.py'))
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
proof=load('unique_rectangle_type2')
b=load('intermediate_proofs');rectangle=load('unique_rectangle');common=load('intermediate_stories')


def fixture(transpose=False):
 t=(lambda i:i%9*9+i//9) if transpose else (lambda i:i)
 corners=sorted(t(i) for i in [0,1,27,28]);roofs=sorted(t(i) for i in [0,1]);floors=sorted(set(corners)-set(roofs))
 cs={i:set(range(1,10)) for i in range(81)}
 for i in floors:cs[i]={1,2}
 for i in roofs:cs[i]={1,2,3}
 p={'type':2,'rows':sorted({i//9 for i in corners}),'columns':sorted({i%9 for i in corners}),
    'boxes':sorted({i//27*3+i%9//3 for i in corners}),'corners':corners,
    'roofs':roofs,'floors':floors,'digits':[1,2],'extra':3}
 targets,frames,labels=proof.derive(p,cs,base=b,rectangle=rectangle)
 e={'slug':'unique-rectangle-type-2','grid':'0'*81,'pattern':p,'proofMode':'uniqueness-disjunction',
    'coverage':{'kind':'roof-extra-disjunction','choices':[[i,3] for i in roofs]},
    'branches':[[[i,3]] for i in roofs],'branchOutcomes':[{'kind':'valid'},{'kind':'valid'}],
    'targets':[list(q) for q in sorted(targets)],'frames':[list(q) for q in sorted(frames)],
    'labels':[list(q) for q in sorted(labels)],'uniquenessPremise':{'kind':'unique-root','solutionCount':1}}
 return e,cs


def story(e):
 frames=[];time=0
 def add(do,**kw):
  nonlocal time
  time+=100;frames.append({'do':do,'time':time,**kw})
 cell=lambda i:{'part':'cell','cell':[i//9,i%9]}
 slot=lambda n:{'part':'slot','slot':n}
 for k,branch in enumerate(e['branches']):
  if k:add('tap',at=slot(1))
  add('tap',at=slot(k+2));i,d=branch[0];r,c=divmod(d-1,3)
  add('down',at=cell(i));add('move',at={**cell(i),'offset':[1.2*(c-1),1.2*(r-1)]})
  add('ready',digit=d);add('up')
 add('tap',at=slot(1))
 for n in (2,3):add('down',at=slot(n));add('move',at=slot(1));add('up')
 for i,d in e['targets']:
  r,c=divmod(d-1,3);dx,dy=c-1,r-1;scale=1.617/(2**.5 if dx and dy else 1)
  add('down',at=cell(i),inputDelay=440);add('move',at={**cell(i),'offset':[scale*dx,scale*dy]});add('up')
 checks={'initialStatus':'dilemma','boards':3,'validSlots':[0,1,2],
         'slotFills':[[n,i//9,i%9,d] for n,branch in enumerate(e['branches'],1) for i,d in branch],
         'overlays':[[1,0],[2,0]],'fills':[[i//9,i%9,0] for i in e['pattern']['roofs']],
         'notes':[[i//9,i%9,d,False] for i,d in e['targets']]+[[i//9,i%9,3,True] for i in e['pattern']['roofs']],
         'revealFrameCount':4,'revealLabelCount':10}
 return {'grid':e['grid'],'style':'chill','setup':[],'frames':frames,'expected':checks,
         'presentation':{'duration':time+500,'choiceReveal':{'start':500,'frames':e['frames'],'labels':e['labels']},
                         'coverage':e['coverage'],'uniquenessPremise':e['uniquenessPremise']}}

class Type2(unittest.TestCase):
 def test_both_roof_orientations_full_targets_and_structural_swap(self):
  for transposed in (False,True):
   e,cs=fixture(transposed);targets,frames,labels=proof.derive(e['pattern'],cs,base=b,rectangle=rectangle)
   self.assertTrue(targets);self.assertEqual(len(frames),4);self.assertEqual(len(labels),10)
   proof.conditional_swap(e['pattern'],[0]*81,rectangle=rectangle)
   p=e['pattern'];a=[0]*81;c=[0]*81
   for row,r in enumerate(p['rows']):
    for col,k in enumerate(p['columns']):a[r*9+k]=p['digits'][(row+col)%2];c[r*9+k]=p['digits'][(row+col+1)%2]
   self.assertNotEqual(a,c)
   for unit in b.UNITS:self.assertEqual(Counter(a[i] for i in unit),Counter(c[i] for i in unit))
   # Directly enumerate the forbidden no-Z rectangle completions only;
   # these partial assignments are not full solutions of an original root.
   self.assertEqual([a[i] for i in p['corners']],[1,2,2,1])

 def test_geometry_blanks_exact_candidates_and_typed_metadata(self):
  e,cs=fixture();p=e['pattern']
  for key,val in [('type',True),('roofs',[0,28]),('roofs',[0,0]),('floors',[27,True]),
                  ('boxes',[0,1]),('corners',[0,1,27,True]),('extra',1),('digits',[1,True])]:
   q=copy.deepcopy(p);q[key]=val
   with self.subTest(key=key),self.assertRaises(ValueError):proof.derive(q,cs,base=b,rectangle=rectangle)
  for i,value in [(0,None),(0,{1,2}),(0,{1,2,3,4}),(27,{1,2,3})]:
   mask=copy.deepcopy(cs)
   if value is None:del mask[i]
   else:mask[i]=value
   with self.subTest(i=i,value=value),self.assertRaises(ValueError):proof.derive(p,mask,base=b,rectangle=rectangle)

 def test_coverage_different_founders_and_no_extra_guess_or_unavailable_fill(self):
  e,cs=fixture();targets=set(map(tuple,e['targets']))
  proof.trials(e,[0]*81,cs,targets,base=b)
  wrong=[]
  q=copy.deepcopy(e);q['coverage']['choices']=[[0,1],[0,2],[0,3]];wrong.append(q)
  q=copy.deepcopy(e);q['coverage']['choices'][0][0]=False;wrong.append(q)
  q=copy.deepcopy(e);q['coverage']['kind']='exhaustive-cell';wrong.append(q)
  q=copy.deepcopy(e);q['coverage']['extraClaim']='two-solutions';wrong.append(q)
  q=copy.deepcopy(e);q['branches'][1]=q['branches'][0];wrong.append(q)
  q=copy.deepcopy(e);q['branches'][0].append([80,2]);wrong.append(q)
  q=copy.deepcopy(e);q['branches'][0].append([1,3]);wrong.append(q)
  q=copy.deepcopy(e);q['branchOutcomes'][0]={'kind':'uniqueness-contradiction','witness':{'kind':'two-solutions','count':2}};wrong.append(q)
  for q in wrong:
   with self.subTest(q=q),self.assertRaises(ValueError):proof.trials(q,[0]*81,cs,targets,base=b)
  with patch.object(b,'_consistent',side_effect=ValueError('invalid prefix')):
   with self.assertRaisesRegex(ValueError,'invalid prefix'):proof.trials(e,[0]*81,cs,targets,base=b)

 def test_root_only_callback_targets_appearance_and_false_two_solutions(self):
  e,cs=fixture();raw=b._candidates;unique=Mock()
  # Wrapper wiring uses a synthetic initial mask; does not qualify an empty root.
  with patch.object(b,'_candidates',side_effect=lambda grid:cs if not any(grid) else raw(grid)):
   proof.validate(e,base=b,rectangle=rectangle,unique_root=unique)
   unique.assert_called_once_with(e['grid'])
   for key,value in [('targets',e['targets'][:-1]),('targets',e['targets']*2),('targets',e['targets']+[[80,3]]),
                     ('frames',e['frames'][:-1]),('labels',e['labels'][:-1]),('solutionCount',2)]:
    q=copy.deepcopy(e);q[key]=value
    with self.subTest(key=key),self.assertRaises(ValueError):proof.validate(q,base=b,rectangle=rectangle,unique_root=Mock())
   with self.assertRaisesRegex(ValueError,'root not unique'):
    proof.validate(e,base=b,rectangle=rectangle,unique_root=Mock(side_effect=ValueError('root not unique')))

 def test_story_projection_retains_actual_roof_notes_and_common_input_guards(self):
  e,_=fixture();data=story(e);before=copy.deepcopy(data)
  proof.validate_story(data,e,common=common,base=b);self.assertEqual(data,before)
  # Unchanged common validator correctly refuses the two extra retention checks.
  with self.assertRaisesRegex(ValueError,'Remove exactly'):common.validate_story(data,e)
  for mutation in ('drop-retention','false-retention','hidden-final','wrong-gesture','warning-claim','wrong-coverage'):
   q=copy.deepcopy(data)
   if mutation=='drop-retention':q['expected']['notes']=q['expected']['notes'][:-1]
   elif mutation=='false-retention':q['expected']['notes'][-1][-1]=False
   elif mutation=='hidden-final':q['final']=[{'id':'SET_FILL'}]
   elif mutation=='wrong-gesture':next(f for f in q['frames'] if f['do']=='ready')['digit']=2
   elif mutation=='warning-claim':q['expected']['uniquenessWarnings']=[{'slot':1}]
   else:q['presentation']['coverage']={'kind':'exhaustive-cell'}
   with self.subTest(mutation=mutation),self.assertRaises(ValueError):proof.validate_story(q,e,common=common,base=b)

 def test_story_note_assertions_require_exact_integer_coordinates_and_booleans(self):
  e,_=fixture();data=story(e)
  mutations=[]
  # Numerically equal values must not pass equality-based admission.
  for field in (0,1,2):
   for value in (1,1.0,True):
    if type(value) is int and value==data['expected']['notes'][-1][field]:continue
    q=copy.deepcopy(data);q['expected']['notes'][-1][field]=value;mutations.append(q)
  for index,values in ((0,(0,0.0)),(-1,(1,1.0))):
   for value in values:
    q=copy.deepcopy(data);q['expected']['notes'][index][3]=value;mutations.append(q)
  for value in ([-1,0,3,True],[9,0,3,True],[0,9,3,True],[0,0,0,True],[0,0,10,True],
                [0,0,3],(0,0,3,True)):
   q=copy.deepcopy(data);q['expected']['notes'][-1]=value;mutations.append(q)
  for q in mutations:
   with self.subTest(notes=q['expected']['notes'][-1]),self.assertRaises(ValueError):
    proof.validate_story(q,e,common=common,base=b)

 def test_presentation_premise_and_coverage_have_exact_types_and_arity(self):
  e,_=fixture();data=story(e);mutations=[]
  for value in (1.0,True,False,2):
   q=copy.deepcopy(data);q['presentation']['uniquenessPremise']['solutionCount']=value;mutations.append(q)
  for key,value in [('kind','two-solutions'),('extra','unbound')]:
   q=copy.deepcopy(data);q['presentation']['uniquenessPremise'][key]=value;mutations.append(q)
  choices=data['presentation']['coverage']['choices']
  for value in (tuple(choices),choices[:1],choices+choices[:1],
                [[0],[1,3]],[[0,3,0],[1,3]],[(0,3),[1,3]],
                [[False,3],[1,3]],[[0.0,3],[1,3]],[[0,3.0],[1,3]],[[0,True],[1,3]]):
   q=copy.deepcopy(data);q['presentation']['coverage']['choices']=value;mutations.append(q)
  for key,value in [('kind','exhaustive-cell'),('extra','unbound')]:
   q=copy.deepcopy(data);q['presentation']['coverage'][key]=value;mutations.append(q)
  for q in mutations:
   with self.subTest(presentation=q['presentation']),self.assertRaises(ValueError):
    proof.validate_story(q,e,common=common,base=b)

 def test_story_board_count_and_valid_slots_have_exact_integer_types(self):
  e,_=fixture();data=story(e)
  for key,value in [('boards',3.0),('boards',True),('boards',False),('boards',2),('boards',4),
                    ('validSlots',[False,1,2]),('validSlots',[0,True,2]),
                    ('validSlots',[0,1,2.0]),('validSlots',[0.0,1,2]),
                    ('validSlots',(0,1,2)),('validSlots',[0,1]),
                    ('validSlots',[0,1,3]),('validSlots',[0,1,1])]:
   q=copy.deepcopy(data);q['expected'][key]=value
   with self.subTest(key=key,value=value),self.assertRaises(ValueError):
    proof.validate_story(q,e,common=common,base=b)

if __name__=='__main__':unittest.main()
