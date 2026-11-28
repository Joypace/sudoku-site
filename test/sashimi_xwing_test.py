"""Synthetic masks test the theorem, not original-puzzle/native eligibility."""
import copy
import importlib.util
from itertools import product
from pathlib import Path
import unittest
from unittest.mock import patch


ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('sashimi_rule',ROOT/'tools/sashimi_xwing.py');rule=importlib.util.module_from_spec(spec);spec.loader.exec_module(rule)
spec=importlib.util.spec_from_file_location('sashimi_base',ROOT/'tools/intermediate_proofs.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)


def fixture(transpose=False):
    # r1c1 body singleton + r1c3 fin; r4c1/c2 other base.
    # r2c1/c2 are targets; r2c4 is deliberately not a cover.
    transform = (lambda i: i % 9 * 9 + i // 9) if transpose else (lambda i: i)
    cs = {transform(i): {2, 7} for i in [0, 2, 27, 28, 9, 10, 12]}
    p = {'orientation': 'columns' if transpose else 'rows', 'bases': [0, 3],
         'covers': [0, 1], 'digit': 7,
         'positions': [transform(i) for i in [0, 2, 27, 28]],
         'fins': [transform(2)], 'finBox': 0}
    return p, cs


class Sashimi(unittest.TestCase):
    def test_both_orientations_complete_targets_and_independent_assignment_theorem(self):
        for transpose in (False, True):
            p, cs = fixture(transpose)
            targets, frames, labels = rule.derive(p, cs, base=b)
            t = (lambda i: i % 9 * 9 + i // 9) if transpose else (lambda i: i)
            self.assertEqual(targets, {(t(9), 7), (t(10), 7)})
            self.assertEqual(len(frames), 3)
            self.assertEqual(labels, {(i // 9, i % 9, 7) for i in p['positions']})
            groups = [[t(0), t(2)], [t(27), t(28)]]
            # Independently enumerate all legal base placements, including fin.
            placements = [q for q in product(*groups) if q[1] not in b.PEERS[q[0]]]
            self.assertTrue(placements)
            self.assertTrue(any(t(2) in q for q in placements))
            self.assertTrue(any(t(2) not in q for q in placements))
            for target, _ in targets:
                self.assertTrue(all(any(i in b.PEERS[target] for i in q) for q in placements))

    def test_incomplete_or_false_geometry(self):
        p, cs = fixture()
        variants = []
        def add(key, value):
            q = copy.deepcopy(p); q[key] = value; variants.append(q)
        add('positions', [0, 2, 27]); add('positions', [0, 2, 27, 28, 9])
        add('positions', [0, 2, 27, 27]); add('fins', [0]); add('fins', [2, 3])
        add('bases', [0, 0]); add('bases', [False, 3]); add('covers', [0, 2])
        add('digit', True); add('finBox', 1); add('orientation', 'diagonal')
        for q in variants:
            with self.subTest(q=q), self.assertRaises(ValueError): rule.derive(q, cs, base=b)
        for extra in [1, 3]:  # regular body, or second fin, respectively
            changed = copy.deepcopy(cs); changed[extra] = {7}
            q = copy.deepcopy(p); q['positions'].append(extra)
            with self.subTest(extra=extra), self.assertRaises(ValueError): rule.derive(q, changed, base=b)
        changed = {i: ds for i, ds in cs.items() if i not in (9, 10)}
        with self.assertRaisesRegex(ValueError, 'No eliminations'): rule.derive(p, changed, base=b)

    def test_wrapper_completeness_appearance_and_branch_delegation(self):
        p, cs = fixture(); targets, frames, labels = rule.derive(p, cs, base=b)
        e = {'slug': 'sashimi-x-wing', 'grid': '0' * 81, 'pattern': p,
             'targets': [list(q) for q in sorted(targets)],
             'frames': [list(q) for q in sorted(frames)],
             'labels': [list(q) for q in sorted(labels)], 'branches': [[[0, 2]], [[0, 7]]]}
        # Only wrapper wiring uses a synthetic root; never claims raw qualification.
        with patch.object(b, '_candidates', return_value=cs), patch.object(b, '_consistent'), patch.object(b, '_forced', return_value=set()):
            with patch.object(b, '_branches') as branches:
                rule.validate(e, base=b)
                self.assertEqual(branches.call_args.args[0], e)
                self.assertEqual(branches.call_args.args[3], targets)
            for key, value in [('targets', e['targets'][:1]), ('targets', e['targets'] * 2),
                               ('targets', e['targets'] + [[12, 7]]), ('frames', e['frames'][:1]),
                               ('labels', e['labels'][:1])]:
                bad = copy.deepcopy(e); bad[key] = value
                with self.subTest(key=key, value=value), self.assertRaises(ValueError): rule.validate(bad, base=b)
            bad = copy.deepcopy(e); bad['pattern']['eliminations'] = [[9, 7]]
            with self.assertRaises(ValueError): rule.validate(bad, base=b)
            bad = copy.deepcopy(e); bad['branches'] = [[[0, 7]]]
            with self.assertRaisesRegex(ValueError, 'exhaust'): rule.validate(bad, base=b)
            bad = copy.deepcopy(e); bad['branches'][0].append([2, 7])
            with self.assertRaisesRegex(ValueError, 'founding fill'): rule.validate(bad, base=b)
            with patch.object(b, '_forced', return_value={(0, 2)}):
                with self.assertRaisesRegex(ValueError, 'zero ordinary singles'): rule.validate(e, base=b)
        # Actual unmocked raw grid cannot borrow the synthetic candidate mask.
        with self.assertRaises(ValueError): rule.validate(e, base=b)

if __name__ == '__main__': unittest.main()
