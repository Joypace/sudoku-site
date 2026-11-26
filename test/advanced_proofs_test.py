"""Advanced named-rule and concrete local-contradiction contracts."""

import copy
import importlib.util
from pathlib import Path
import unittest


SPEC = importlib.util.spec_from_file_location(
    'advanced_proofs', Path(__file__).resolve().parents[1] / 'tools/advanced_proofs.py')
p = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(p)


class AdvancedRules(unittest.TestCase):
    def test_quadruples_allow_two_note_cells_and_remove_in_opposite_directions(self):
        named = dict(unit='row', unitIndex=0, cells=[0, 1, 2, 3], digits=[1, 2, 3, 4])
        cs = {0: {1, 2}, 1: {2, 3}, 2: {3, 4}, 3: {1, 4}, 4: {1, 5}}
        targets, frames, labels = p._quadruple('naked-quadruple', named, cs)
        self.assertEqual(targets, {(4, 1)})
        self.assertEqual(frames, {(0, 0, 1, 9)})
        self.assertEqual(len(labels), 8)
        hidden = {0: {1, 2, 5}, 1: {2, 3, 6}, 2: {3, 4, 7}, 3: {1, 4, 8}, 4: {5, 6}}
        targets, _, labels = p._quadruple('hidden-quadruple', named, hidden)
        self.assertEqual(targets, {(0, 5), (1, 6), (2, 7), (3, 8)})
        self.assertEqual(len(labels), 8)
        hidden[4].add(1)
        with self.assertRaises(ValueError):
            p._quadruple('hidden-quadruple', named, hidden)

    def fish(self, size, fins):
        bases = covers = list(range(0, size * 2, 2))
        cells = [r * 9 + c for n, r in enumerate(bases)
                 for c in (covers[n], covers[(n + 1) % size])]
        named = dict(orientation='rows', bases=bases, covers=covers, digit=9,
                     positions=sorted(cells + ([1] if fins else [])))
        cs = {i: {2, 9} for i in named['positions'] + [9, 11, 72]}
        if fins:
            named.update(fins=[1], finBox=0)
        return named, cs

    def test_jellyfish_counts_all_four_base_and_cover_units(self):
        named, cs = self.fish(4, False)
        targets, frames, labels = p._fish('jellyfish', named, cs)
        self.assertEqual(targets, {(9, 9), (11, 9), (72, 9)})
        self.assertEqual(len(frames), 4)
        self.assertEqual(len(labels), 8)
        cs[1] = {2, 9}
        with self.assertRaises(ValueError):
            p._fish('jellyfish', named, cs)

    def test_each_regular_finned_size_requires_every_fin_and_target_sees_all_fins(self):
        for size, slug in [(2, 'finned-x-wing'), (3, 'finned-swordfish'), (4, 'finned-jellyfish')]:
            with self.subTest(slug=slug):
                named, cs = self.fish(size, True)
                targets, frames, labels = p._fish(slug, named, cs)
                self.assertEqual(targets, {(9, 9), (11, 9)})
                self.assertNotIn((72, 9), targets)
                self.assertIn((0, 0, 3, 3), frames)
                self.assertIn((0, 1, 9), labels)
                for key, value in [('fins', []), ('finBox', 1), ('bases', [True] + named['bases'][1:])]:
                    wrong = copy.deepcopy(named)
                    wrong[key] = value
                    with self.subTest(key=key), self.assertRaises(ValueError):
                        p._fish(slug, wrong, cs)

    def test_sashimi_body_cannot_be_mislabeled_as_regular_finned_swordfish(self):
        named = dict(orientation='rows', bases=[0, 3, 6], covers=[0, 3, 6], digit=9,
                     positions=[0, 1, 3, 27, 30, 54, 57, 60], fins=[1], finBox=0)
        cs = {i: {2, 9} for i in named['positions'] + [9]}
        with self.assertRaisesRegex(ValueError, 'Sashimi'):
            p._fish('finned-swordfish', named, cs)

    def test_simple_color_trap_uses_complete_component_edges_units_and_bipartition(self):
        named = dict(digit=7, component=[65, 67, 72, 76],
                     edges=[[65, 72], [67, 76], [72, 76]],
                     colors=[[65, 76], [67, 72]],
                     units=[['row', 8], ['column', 4], ['box', 6]], rule='trap')
        cs = {i: {2, 7} for i in [65, 66, 67, 72, 76]}
        targets, frames, labels = p._coloring(named, cs)
        self.assertEqual(targets, {(66, 7)})
        self.assertEqual(len(frames), 3)
        self.assertEqual(len(labels), 4)
        for key, value in [('component', [65, 72]), ('edges', named['edges'][:-1]),
                           ('colors', [[65, 67], [72, 76]]), ('units', named['units'][:-1]),
                           ('rule', 'unknown')]:
            wrong = copy.deepcopy(named)
            wrong[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                p._coloring(wrong, cs)

    def test_remote_pairs_alternate_identical_bivalue_cells_and_exclude_both_digits(self):
        named = dict(digits=[6, 9], cells=[50, 52, 79, 75])
        cs = {i: {6, 9} for i in named['cells']}
        cs.update({30: {2, 6}, 39: {4, 9}})
        targets, frames, labels = p._remote_pairs(named, cs)
        self.assertEqual(targets, {(30, 6), (39, 9)})
        self.assertEqual(len(frames), 4)
        self.assertEqual(len(labels), 8)
        cs[52].add(3)
        with self.assertRaises(ValueError):
            p._remote_pairs(named, cs)


class TrialOutcomes(unittest.TestCase):
    def fixture(self):
        # Assuming r6c2=3 forces r2c5=3 and leaves row 5 without any 3.
        # The other founding choice excludes the same wrap-color candidates.
        return {
            'slug': 'simple-coloring',
            'grid': '570048060906702580810596070150004037760901020200007010427869153381475296695003748',
            'targets': [[13, 3], [46, 3], [48, 3]],
            'branches': [[[46, 3], [13, 3]], [[46, 4], [10, 3], [3, 3]]],
            'frames': [[1, 0, 1, 9], [0, 1, 9, 1], [0, 3, 9, 1], [0, 3, 3, 3]],
            'labels': [[0, 3, 3], [1, 1, 3], [1, 4, 3], [5, 1, 3], [5, 3, 3]],
            'pattern': {'digit': 3, 'component': [3, 10, 13, 46, 48],
                        'edges': [[3, 13], [3, 48], [10, 13], [10, 46]],
                        'colors': [[3, 10], [13, 46, 48]],
                        'units': [['row', 1], ['column', 1], ['column', 3], ['box', 1]],
                        'rule': 'wrap', 'badColor': 1},
            'branchOutcomes': [
                {'kind': 'contradiction', 'witness': {'kind': 'missing-digit',
                 'unit': 'row', 'unitIndex': 4, 'digit': 3}}, {'kind': 'valid'}],
        }

    def test_named_wrap_and_concrete_missing_digit_are_both_required(self):
        e = self.fixture()
        p.validate_pattern('simple-coloring', e)
        for mode in ['omit-outcomes', 'false-unit', 'fake-count', 'not-forced', 'continue-after-failure',
                     'partial-targets', 'false-frame', 'false-label', 'wrong-color', 'wrong-slug']:
            changed = copy.deepcopy(e)
            if mode == 'omit-outcomes':
                del changed['branchOutcomes']
            elif mode == 'false-unit':
                changed['branchOutcomes'][0]['witness']['unitIndex'] = 0
            elif mode == 'fake-count':
                changed['branchOutcomes'][0]['witness'] = {'kind': 'no-solutions', 'count': 0}
            elif mode == 'not-forced':
                changed['branches'][0].insert(1, [47, 4])
            elif mode == 'continue-after-failure':
                changed['branches'][0].append([47, 4])
            elif mode == 'partial-targets':
                changed['targets'] = changed['targets'][:-1]
            elif mode == 'false-frame':
                changed['frames'] = [[0, 0, 9, 9]]
            elif mode == 'false-label':
                changed['labels'][0][2] = True
            elif mode == 'wrong-color':
                changed['pattern']['badColor'] = 0
            elif mode == 'wrong-slug':
                changed['slug'] = 'remote-pairs'
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                p.validate_pattern('simple-coloring', changed)

    def test_local_witnesses_reject_floats_booleans_and_invented_results(self):
        p._witness({'kind': 'empty-cell', 'cell': 0}, [{'kind': 'empty-cell', 'cell': 0}])
        p._witness({'kind': 'duplicate', 'unit': 'row', 'unitIndex': 0, 'digit': 2},
                   [{'kind': 'duplicate', 'unit': 'row', 'unitIndex': 0, 'digit': 2}])
        for witness in [{'kind': 'empty-cell', 'cell': False}, {'kind': 'empty-cell', 'cell': 0.0},
                        {'kind': 'missing-digit', 'unit': 'row', 'unitIndex': 0, 'digit': True},
                        {'kind': 'duplicate', 'unit': 'row', 'unitIndex': 0, 'digit': 2}]:
            with self.subTest(witness=witness), self.assertRaises(ValueError):
                p._witness(witness, [])


if __name__ == '__main__':
    unittest.main()
