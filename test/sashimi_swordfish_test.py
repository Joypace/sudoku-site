"""Synthetic mask proofs only; no discovered grids or native qualification."""
import copy
from itertools import product
import unittest
from unittest.mock import patch
from pathlib import Path
import importlib.util
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('sashimi_swordfish_rule',ROOT/'tools/sashimi_swordfish.py');rule=importlib.util.module_from_spec(spec);spec.loader.exec_module(rule)
spec=importlib.util.spec_from_file_location('sashimi_swordfish_base',ROOT/'tools/intermediate_proofs.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)


def fixture(transpose=False, full=False):
    t = (lambda i: i % 9 * 9 + i // 9) if transpose else (lambda i: i)
    positions = [0, 2, 27, 28, 55, 58] + ([31] if full else [])
    cs = {t(i): {2, 7} for i in positions + [9, 10, 12]}
    p = {'orientation': 'columns' if transpose else 'rows', 'bases': [0, 3, 6],
         'covers': [0, 1, 4], 'digit': 7, 'positions': [t(i) for i in positions],
         'fins': [t(2)], 'finBox': 0}
    return p, cs, t


class Swordfish(unittest.TestCase):
    def test_independent_placements_in_both_orientations_and_body_sizes(self):
        for transposed, full in product((False, True), repeat=2):
            p, cs, t = fixture(transposed, full)
            targets, frames, labels = rule.derive(p, cs, base=b)
            self.assertEqual(targets, {(t(9), 7), (t(10), 7)})
            self.assertEqual(len(frames), 4)
            self.assertEqual(labels, {(i//9, i%9, 7) for i in p['positions']})
            groups = [[t(0), t(2)], [t(27), t(28)] + ([t(31)] if full else []), [t(55), t(58)]]
            placements = [q for q in product(*groups)
                          if all(q[j] not in b.PEERS[q[i]] for i in range(3) for j in range(i+1, 3))]
            self.assertTrue(placements)
            self.assertTrue(any(t(2) in q for q in placements))
            self.assertTrue(any(t(2) not in q for q in placements))
            for target, _ in targets:
                self.assertTrue(all(any(i in b.PEERS[target] for i in q) for q in placements))

    def test_negative_geometry_and_incomplete_masks(self):
        p, cs, _ = fixture()
        for key, value in [('bases', [0,3]), ('bases', [0,3,3]), ('bases', [0,True,6]),
                           ('covers', [0,1,2]), ('covers', [0,1,1]), ('fins', [0]),
                           ('fins', [2,3]), ('finBox', 1), ('digit', True),
                           ('positions', p['positions'][:-1]),
                           ('positions', p['positions']+[9]),
                           ('positions', p['positions']+[0])]:
            bad=copy.deepcopy(p);bad[key]=value
            with self.subTest(key=key,value=value), self.assertRaises(ValueError): rule.derive(bad,cs,base=b)
        for remove, add in [([], [1]), ([], [3]), ([28], []), ([58], [54])]:
            # Extra body in fin base; second fin; singleton nonfin base;
            # absent third cover despite all bases otherwise nonempty.
            bad=copy.deepcopy(p);mask=copy.deepcopy(cs)
            for i in remove: del mask[i];bad['positions'].remove(i)
            for i in add: mask[i]={7};bad['positions'].append(i)
            with self.subTest(remove=remove,add=add), self.assertRaises(ValueError): rule.derive(bad,mask,base=b)
        with self.assertRaisesRegex(ValueError,'No eliminations'):
            rule.derive(p,{i:ds for i,ds in cs.items() if i not in (9,10)},base=b)

    def test_wrapper_complete_targets_appearance_and_actual_branch_guards(self):
        p, cs, _ = fixture();targets,frames,labels=rule.derive(p,cs,base=b)
        e={'slug':'sashimi-swordfish','grid':'0'*81,'pattern':p,
           'targets':[list(q) for q in sorted(targets)],
           'frames':[list(q) for q in sorted(frames)],'labels':[list(q) for q in sorted(labels)],
           'branches':[[[0,2]],[[0,7]]]}
        # Synthetic-root injection is limited to wrapper wiring tests.
        with patch.object(b,'_candidates',return_value=cs),patch.object(b,'_consistent'),patch.object(b,'_forced',return_value=set()):
            with patch.object(b,'_branches') as branches:
                rule.validate(e,base=b)
                self.assertEqual(branches.call_args.args[3],targets)
            for key,value in [('targets',e['targets'][:1]),('targets',e['targets']*2),
                              ('targets',e['targets']+[[12,7]]),('frames',e['frames'][:-1]),
                              ('labels',e['labels'][:-1]),('slug','sashimi-x-wing')]:
                bad=copy.deepcopy(e);bad[key]=value
                with self.subTest(key=key),self.assertRaises(ValueError): rule.validate(bad,base=b)
            bad=copy.deepcopy(e);bad['pattern']['eliminations']=[[9,7]]
            with self.assertRaises(ValueError):rule.validate(bad,base=b)
            bad=copy.deepcopy(e);bad['branches']=bad['branches'][:1]
            with self.assertRaisesRegex(ValueError,'exhaust'):rule.validate(bad,base=b)
            bad=copy.deepcopy(e);bad['branches'][0].append([2,7])
            with self.assertRaisesRegex(ValueError,'founding fill'):rule.validate(bad,base=b)
            with patch.object(b,'_forced',return_value={(0,2)}):
                with self.assertRaisesRegex(ValueError,'zero ordinary singles'):rule.validate(e,base=b)
        with self.assertRaises(ValueError):rule.validate(e,base=b)

if __name__=='__main__':unittest.main()
