"""Independent placement enumeration, synthetic masks only; no lesson eligibility."""
import copy
from itertools import combinations, product
import unittest
from unittest.mock import patch
from pathlib import Path
import importlib.util
ROOT=Path(__file__).resolve().parents[1]
def _load(name):
 spec=importlib.util.spec_from_file_location('jellyfish_test_'+name,ROOT/'tools'/(name+'.py'));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
b=_load('intermediate_proofs')
rule=_load('sashimi_jellyfish')


def fixture(transpose=False, width=2):
    t = (lambda i: i % 9 * 9 + i // 9) if transpose else (lambda i: i)
    groups = [[0,2], [27,28,31,34][:width],
              [55,58,54,61][:width], [67,70,63,64][:width]]
    positions = [i for group in groups for i in group]
    cs = {t(i): {2,7} for i in positions + [9,10,13]}
    p = {'orientation':'columns' if transpose else 'rows','bases':[0,3,6,7],
         'covers':[0,1,4,7],'digit':7,'positions':[t(i) for i in positions],
         'fins':[t(2)],'finBox':0}
    return p,cs,t,[[t(i) for i in group] for group in groups]


class Jellyfish(unittest.TestCase):
    def test_theorem_both_orientations_all_nonfin_body_sizes(self):
        for transposed,width in product((False,True),(2,3,4)):
            p,cs,t,groups=fixture(transposed,width)
            targets,frames,labels=rule.derive(p,cs,base=b)
            self.assertEqual(targets,{(t(9),7),(t(10),7)})
            self.assertEqual(len(frames),5)
            self.assertEqual(labels,{(i//9,i%9,7) for i in p['positions']})
            placements=[q for q in product(*groups) if all(q[j] not in b.PEERS[q[i]]
                        for i in range(4) for j in range(i+1,4))]
            self.assertTrue(placements)
            for fin_true in (True,False):
                conditional=[q for q in placements if (t(2) in q)==fin_true]
                self.assertTrue(conditional)
                for target,_ in targets:
                    self.assertTrue(all(any(i in b.PEERS[target] for i in q) for q in conditional))
            # Fixtures themselves have no unconditional ordinary 2/3-fish
            # within the declared bases: include the ACTUAL fin, never prune it.
            cross=(lambda i:i//9) if transposed else (lambda i:i%9)
            for size in (2,3):
                for subset in combinations(groups,size):
                    self.assertGreater(len({cross(i) for group in subset for i in group}),size)

    def test_false_and_incomplete_geometry(self):
        p,cs,_,_=fixture()
        variants=[('bases',[0,3,6]),('bases',[0,3,6,6]),('bases',[0,3,6,True]),
                  ('covers',[0,1,4]),('covers',[0,1,4,4]),('covers',[0,1,4,False]),
                  ('fins',[0]),('fins',[2,3]),('finBox',1),('digit',True),
                  ('positions',p['positions'][:-1]),('positions',p['positions']+[9]),
                  ('positions',p['positions']+[0]),('orientation','diagonal')]
        for key,value in variants:
            q=copy.deepcopy(p);q[key]=value
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):rule.derive(q,cs,base=b)
        # Adding body cell 1 is now the explicitly tested fin-blocked pair
        # reduction, not malformed geometry; see the Hall-profile regression.
        for remove,add in [([],[3]),([28],[]),([70],[64])]:
            q=copy.deepcopy(p);mask=copy.deepcopy(cs)
            for i in remove:del mask[i];q['positions'].remove(i)
            for i in add:mask[i]={7};q['positions'].append(i)
            with self.subTest(remove=remove,add=add),self.assertRaises(ValueError):rule.derive(q,mask,base=b)
        with self.assertRaisesRegex(ValueError,'No eliminations'):
            rule.derive(p,{i:ds for i,ds in cs.items() if i not in (9,10)},base=b)

    def test_wrapper_appearance_all_targets_and_real_branch_rejections(self):
        p,cs,_,_=fixture();targets,frames,labels=rule.derive(p,cs,base=b)
        e={'slug':'sashimi-jellyfish','grid':'0'*81,'pattern':p,
           'targets':[list(q) for q in sorted(targets)],'frames':[list(q) for q in sorted(frames)],
           'labels':[list(q) for q in sorted(labels)],'branches':[[[0,2]],[[0,7]]]}
        # Synthetic mask injection tests delegation only; raw-grid check below
        # cannot qualify this empty-grid fixture as an actual lesson.
        with patch.object(b,'_candidates',return_value=cs),patch.object(b,'_consistent'),patch.object(b,'_forced',return_value=set()):
            with patch.object(b,'_branches') as branch:
                rule.validate(e,base=b);self.assertEqual(branch.call_args.args[3],targets)
            for key,value in [('targets',e['targets'][:1]),('targets',e['targets']*2),
                              ('targets',e['targets']+[[13,7]]),('frames',e['frames'][:-1]),
                              ('labels',e['labels'][:-1]),('slug','sashimi-swordfish')]:
                q=copy.deepcopy(e);q[key]=value
                with self.subTest(key=key),self.assertRaises(ValueError):rule.validate(q,base=b)
            q=copy.deepcopy(e);q['pattern']['eliminations']=[[9,7]]
            with self.assertRaises(ValueError):rule.validate(q,base=b)
            q=copy.deepcopy(e);q['branches']=q['branches'][:1]
            with self.assertRaisesRegex(ValueError,'exhaust'):rule.validate(q,base=b)
            q=copy.deepcopy(e);q['branches'][0].append([2,7])
            with self.assertRaisesRegex(ValueError,'founding fill'):rule.validate(q,base=b)
            with patch.object(b,'_forced',return_value={(0,2)}):
                with self.assertRaisesRegex(ValueError,'zero ordinary singles'):rule.validate(e,base=b)
        with self.assertRaises(ValueError):rule.validate(e,base=b)

if __name__=='__main__':unittest.main()
