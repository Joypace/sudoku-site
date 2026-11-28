"""Hall-degeneracy mathematics only; synthetic masks do not qualify lessons."""
import copy
from itertools import combinations, product
import unittest
from unittest.mock import patch
from pathlib import Path
import importlib.util
from sashimi_jellyfish_test import fixture as v1_fixture
ROOT=Path(__file__).resolve().parents[1]
def _load(name):
 spec=importlib.util.spec_from_file_location('hall_test_'+name,ROOT/'tools'/(name+'.py'));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
b=_load('intermediate_proofs');rule=_load('sashimi_jellyfish')


def fixture(transpose=False, kind='pair'):
    t=(lambda i:i%9*9+i//9) if transpose else (lambda i:i)
    # All pair/triple body degrees >=2: no singleton masquerading as v2.
    if kind=='pair': groups=[[0,1],[27,28],[58,61],[67,70]]
    elif kind=='triple': groups=[[0,1],[28,31],[54,58],[67,70]]
    elif kind=='four': groups=[[0,1,4,7],[27,28],[54,55],[67,70]]
    elif kind=='regular': groups=[[0,1,4,7],[27,28,31,34],[54,55,58,61],[63,64,67,70]]
    elif kind=='hall-fail': groups=[[0,1],[27,28],[54,55],[67,70]]
    else: raise ValueError(kind)
    positions=[i for group in groups for i in group]+[2]
    cs={t(i):{2,7} for i in positions+[9,10,13]}
    p={'orientation':'columns' if transpose else 'rows','bases':[0,3,6,7],
       'covers':[0,1,4,7],'digit':7,'positions':[t(i) for i in positions],
       'fins':[t(2)],'finBox':0}
    return p,cs,t,[[t(i) for i in group] for group in groups]


class HallSashimi(unittest.TestCase):
    def test_previous_singleton_only_negative_is_a_valid_fin_blocked_pair(self):
        for transposed in (False, True):
            p,cs,t,_=v1_fixture(transposed,2)
            p['positions'].append(t(1));cs[t(1)]={7}
            p['finFreeReduction']={'bases':[0,3],'covers':[0,1]}
            targets,_,_=rule.derive(p,cs,base=b)
            self.assertEqual(targets,{(t(9),7),(t(10),7)})
            unit=(lambda i:i%9) if transposed else (lambda i:i//9)
            groups=[[i for i in p['positions'] if unit(i)==base] for base in p['bases']]
            placements=[q for q in product(*groups) if all(q[j] not in b.PEERS[q[i]]
                        for i in range(4) for j in range(i+1,4))]
            for fin_true in (False,True):
                branch=[q for q in placements if (t(2) in q)==fin_true]
                self.assertTrue(branch)
                for target,_ in targets:
                    self.assertTrue(all(any(i in b.PEERS[target] for i in q) for q in branch))

    def test_explicit_reduction_must_be_the_real_fin_containing_tight_subset(self):
        p,cs,_,_=fixture()
        p['finFreeReduction']={'bases':[0,3],'covers':[0,1]}
        rule.derive(p,cs,base=b)
        for value in [{'bases':[0,3],'covers':[0,4]},
                      {'bases':[3,6],'covers':[0,1]},
                      {'bases':[False,3],'covers':[0,1]},
                      {'bases':[0,0],'covers':[0,1]}]:
            q=copy.deepcopy(p);q['finFreeReduction']=value
            with self.subTest(value=value),self.assertRaises(ValueError):rule.derive(q,cs,base=b)

    def test_degree_two_cycles_and_triple_tightness_independent_placements(self):
        for transposed,kind in product((False,True),('pair','triple')):
            p,cs,t,body=fixture(transposed,kind)
            targets,frames,labels=rule.derive(p,cs,base=b)
            self.assertEqual(targets,{(t(9),7),(t(10),7)})
            self.assertEqual(len(frames),5)
            self.assertEqual(labels,{(i//9,i%9,7) for i in p['positions']})
            cross=(lambda i:i//9) if transposed else (lambda i:i%9)
            # Independent Cartesian matching enumeration, not Hall reimplementation.
            matchings=[q for q in product(*body) if len({cross(i) for i in q})==4]
            self.assertTrue(matchings)
            self.assertTrue(all(len(group)>=2 for group in body))
            if kind=='triple':
                self.assertTrue(all(len({cross(i) for group in pair for i in group})>2
                                    for pair in combinations(body,2)))
            groups=[body[0]+[t(2)],*body[1:]]
            placements=[q for q in product(*groups) if all(q[j] not in b.PEERS[q[i]]
                        for i in range(4) for j in range(i+1,4))]
            for fin_true in (False,True):
                branch=[q for q in placements if (t(2) in q)==fin_true]
                self.assertTrue(branch)
                for target,_ in targets:
                    self.assertTrue(all(any(i in b.PEERS[target] for i in q) for q in branch))

    def test_v1_profiles_still_accepted(self):
        for transposed,width in product((False,True),(2,3,4)):
            p,cs,_,_=v1_fixture(transposed,width)
            self.assertTrue(rule.derive(p,cs,base=b)[0])

    def test_regular_and_hall_deficient_bodies_rejected(self):
        for transposed in (False,True):
            p,cs,_,_=fixture(transposed,'regular')
            with self.assertRaisesRegex(ValueError,'No proper tight'):rule.derive(p,cs,base=b)
            p,cs,_,body=fixture(transposed,'hall-fail')
            cross=(lambda i:i//9) if transposed else (lambda i:i%9)
            self.assertFalse([q for q in product(*body) if len({cross(i) for i in q})==4])
            with self.assertRaisesRegex(ValueError,'Hall matching'):rule.derive(p,cs,base=b)

    def test_unaffected_nonfin_tight_subset_is_not_sufficient(self):
        for transposed in (False, True):
            p,cs,_,body=fixture(transposed,'four')
            cross=(lambda i:i//9) if transposed else (lambda i:i%9)
            self.assertEqual(len({cross(i) for group in body[1:3] for i in group}),2)
            self.assertTrue([q for q in product(*body) if len({cross(i) for i in q})==4])
            with self.assertRaisesRegex(ValueError,'containing the fin-bearing base'):
                rule.derive(p,cs,base=b)

    def test_full_geometry_targets_appearance_and_branches_not_relaxed(self):
        p,cs,_,_=fixture()
        for key,val in [('positions',p['positions'][:-1]),('fins',[0]),('bases',[0,3,6,True]),
                        ('covers',[0,1,4,4]),('digit',True),('finBox',1)]:
            q=copy.deepcopy(p);q[key]=val
            with self.subTest(key=key),self.assertRaises(ValueError):rule.derive(q,cs,base=b)
        targets,frames,labels=rule.derive(p,cs,base=b)
        e={'slug':'sashimi-jellyfish','grid':'0'*81,'pattern':p,'targets':[list(q) for q in targets],
           'frames':[list(q) for q in frames],'labels':[list(q) for q in labels],
           'branches':[[[0,2]],[[0,7]]]}
        with patch.object(b,'_candidates',return_value=cs),patch.object(b,'_consistent'),patch.object(b,'_forced',return_value=set()):
            with patch.object(b,'_branches') as branch:
                rule.validate(e,base=b);self.assertEqual(branch.call_args.args[3],targets)
            for key,val in [('targets',e['targets'][:1]),('targets',e['targets']*2),
                            ('frames',e['frames'][:-1]),('labels',e['labels'][:-1])]:
                q=copy.deepcopy(e);q[key]=val
                with self.subTest(key=key),self.assertRaises(ValueError):rule.validate(q,base=b)
            q=copy.deepcopy(e);q['branches']=q['branches'][:1]
            with self.assertRaisesRegex(ValueError,'exhaust'):rule.validate(q,base=b)
            q=copy.deepcopy(e);q['branches'][0].append([2,7])
            with self.assertRaisesRegex(ValueError,'founding fill'):rule.validate(q,base=b)
        with self.assertRaises(ValueError):rule.validate(e,base=b)

if __name__=='__main__':unittest.main()
