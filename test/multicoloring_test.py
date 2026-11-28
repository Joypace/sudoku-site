"""Canonical graph derivation over synthetic masks, never fake lesson givens."""
import copy
import importlib.util
from itertools import product
from pathlib import Path
import unittest
from unittest.mock import patch

SITE=Path(__file__).resolve().parents[2]/'sudoku-site/tools'
def load(name):
 spec=importlib.util.spec_from_file_location('multi_test_'+name,SITE/(name+'.py'))
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
b=load('intermediate_proofs');advanced=load('advanced_proofs');m=load('multicoloring')


def fixture(kind='type1'):
 cs={i:set(range(1,10)) for i in range(81)}
 for i in b.UNITS[0]:
  if i not in (0,4):cs[i].remove(7)
 if kind=='type1':
  for i in b.UNITS[1]:
   if i not in (9,14):cs[i].remove(7)
  seeds=[0,9]
 else:
  for i in b.UNITS[19]:
   if i not in (4,13):cs[i].discard(7)
  for i in b.UNITS[3]:
   if i not in (27,31):cs[i].discard(7)
  seeds=[0,27]
 edges,units=advanced._conjugates(cs,7);graph={}
 for a,c in edges:graph.setdefault(a,set()).add(c);graph.setdefault(c,set()).add(a)
 components=[]
 for seed in seeds:
  colors={seed:0};pending=[seed]
  while pending:
   for c in graph[pending.pop()]:
    if c not in colors:
     # recover predecessor color from its already-colored neighbour
     parent=next(i for i in graph[c] if i in colors)
     colors[c]=1-colors[parent];pending.append(c)
  cells=set(colors);actual={e for e in edges if e[0] in cells}
  components.append({'cells':sorted(cells),'edges':[list(e) for e in sorted(actual)],
    'units':[[('row','column','box')[n//9],n%9] for n,e in units if e in actual],
    'colors':[[i for i in sorted(cells) if colors[i]==k] for k in (0,1)]})
 return {'digit':7,'components':components,'rule':kind,'interaction':[0,0] if kind=='type1' else [0]},cs


def derive(p,cs):return m.derive(p,cs,base=b,advanced=advanced)

class MultiColors(unittest.TestCase):
 def test_type1_four_truth_assignments_and_all_outside_targets(self):
  p,cs=fixture();targets,frames,labels=derive(p,cs)
  self.assertTrue(targets);self.assertTrue(frames);self.assertEqual(len(labels),4)
  components=p['components'];accepted=[]
  for a,c in product((0,1),repeat=2):
   true=components[0]['colors'][a]+components[1]['colors'][c]
   legal=not any(j in b.PEERS[i] for i in true for j in true if i!=j)
   if legal:accepted.append((a,c))
   if (a,c)==(0,0):self.assertFalse(legal)
   if legal:
    for target,_ in targets:self.assertTrue(any(i in b.PEERS[target] for i in true))
  self.assertTrue(accepted)
  self.assertIsNone(m.simple_coloring_whole_case(p,cs,targets,base=b,advanced=advanced))

 def test_type2_four_truth_assignments_different_members_link_to_each_side(self):
  p,cs=fixture('type2');targets,_,_=derive(p,cs)
  self.assertEqual(targets,{(0,7),(13,7)})
  a,c=p['components'];self.assertEqual(a['colors'][0],[0,13])
  self.assertTrue(27 in b.PEERS[0]);self.assertTrue(31 in b.PEERS[13])
  self.assertFalse(any(all(bool(b.PEERS[i]&set(side)) for side in c['colors']) for i in a['colors'][0]))
  legal_count=0
  for ai,ci in product((0,1),repeat=2):
   true=a['colors'][ai]+c['colors'][ci]
   legal=not any(j in b.PEERS[i] for i in true for j in true if i!=j)
   if legal:legal_count+=1;self.assertEqual(ai,1)
   if ai==0:self.assertFalse(legal)
  self.assertGreater(legal_count,0)

 def test_false_links_types_completeness_and_disconnectedness(self):
  for kind in ('type1','type2'):
   p,cs=fixture(kind)
   changes=[]
   q=copy.deepcopy(p);q['interaction']=[0,1] if kind=='type1' else [1];changes.append(q)
   q=copy.deepcopy(p);q['interaction']=[True,0] if kind=='type1' else [0.0];changes.append(q)
   q=copy.deepcopy(p);q['components'][0]['edges']=[];changes.append(q)
   q=copy.deepcopy(p);q['components'][0]['edges'].append([0,80]);changes.append(q)
   q=copy.deepcopy(p);q['components'][0]['units']=[];changes.append(q)
   q=copy.deepcopy(p);q['components'][0]['cells']=q['components'][0]['cells'][:-1];changes.append(q)
   q=copy.deepcopy(p);q['components'][1]=copy.deepcopy(q['components'][0]);changes.append(q)
   q=copy.deepcopy(p);q['components'][0]['colors'][0].append(q['components'][0]['colors'][1][0]);changes.append(q)
   q=copy.deepcopy(p);q['components'][0]['cells'][0]=True;changes.append(q)
   q=copy.deepcopy(p);q['components'][0]['units'][0][1]=True;changes.append(q)
   for q in changes:
    with self.subTest(kind=kind,q=q),self.assertRaises(ValueError):derive(q,cs)
  p,cs=fixture()
  for i in b.UNITS[9]:
   if i not in (0,9):cs[i].discard(7)
  with self.assertRaisesRegex(ValueError,'complete connected'):derive(p,cs)

 def test_quality_is_whole_case_only_and_separate_from_theorem(self):
  p,cs=fixture('type2');a=p['components'][0]
  # Derive a real one-component trap from the complete canonical graph.
  traps={(i,7) for i in cs if 7 in cs[i] and i not in a['cells'] and all(b.PEERS[i]&set(side) for side in a['colors'])}
  self.assertTrue(traps)
  witness=m.simple_coloring_whole_case(p,cs,traps,base=b,advanced=advanced)
  self.assertIsNotNone(witness)
  extra=next((i,7) for i in cs if 7 in cs[i] and (i,7) not in traps and i not in a['cells'])
  self.assertIsNone(m.simple_coloring_whole_case(p,cs,traps|{extra},base=b,advanced=advanced))

 def test_quality_sees_an_unselected_complete_root_component(self):
  p,cs=fixture()
  for i in b.UNITS[6]:
   if i not in (54,55):cs[i].discard(7)
  wanted={(65,7)}  # r8c3 sees both ends of the third row7 component.
  self.assertIsNone(m.simple_coloring_whole_case(p,cs,wanted,base=b,advanced=advanced))
  third={'cells':[54,55],'edges':[[54,55]],'units':[['row',6]],'colors':[[54],[55]]}
  all_components=[*p['components'],third]
  witness=m.simple_coloring_whole_case(p,cs,wanted,base=b,advanced=advanced,all_components=all_components)
  self.assertIsNotNone(witness)
  self.assertEqual(set(witness['component']),{54,55})

 def test_wrapper_targets_appearance_and_exhaustive_trials(self):
  p,cs=fixture();targets,frames,labels=derive(p,cs)
  e={'slug':'multi-coloring','grid':'0'*81,'pattern':p,'targets':[list(q) for q in targets],
     'frames':[list(q) for q in frames],'labels':[list(q) for q in labels],'branches':[[[0,7]]]}
  with patch.object(b,'_candidates',return_value=cs),patch.object(b,'_consistent'),patch.object(b,'_forced',return_value=set()):
   with patch.object(b,'_branches') as branch:
    m.validate(e,base=b,advanced=advanced);self.assertEqual(branch.call_args.args[3],targets)
   for key,value in [('targets',e['targets'][:-1]),('targets',e['targets']*2),('targets',e['targets']+[[80,7]]),('frames',[]),('labels',[])]:
    q=copy.deepcopy(e);q[key]=value
    with self.subTest(key=key),self.assertRaises(ValueError):m.validate(q,base=b,advanced=advanced)
   with self.assertRaisesRegex(ValueError,'exhaust'):m.validate(e,base=b,advanced=advanced)
  with self.assertRaises(ValueError):m.validate(e,base=b,advanced=advanced)

if __name__=='__main__':unittest.main()
