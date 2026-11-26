"""Named-rule mathematics, independent of fixture discovery and rendering."""

import copy
import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location(
    'intermediate_proofs', Path(__file__).resolve().parents[1] / 'tools/intermediate_proofs.py')
p = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(p)


class NamedRules(unittest.TestCase):
    def test_triples_allow_partial_memberships_and_remove_in_correct_direction(self):
        named = dict(unit='row', unitIndex=0, cells=[0, 1, 2], digits=[1, 2, 3])
        cs = {0: {1, 2}, 1: {2, 3}, 2: {1, 3}, 3: {1, 4}, 4: {3, 5}}
        targets, frames, labels = p._triples('naked-triple', named, cs)
        self.assertEqual(targets, {(3, 1), (4, 3)})
        self.assertEqual(frames, {(0, 0, 1, 9)})
        self.assertEqual(len(labels), 6)
        hidden = {0: {1, 2, 4}, 1: {2, 3, 5}, 2: {1, 3, 6}, 3: {4, 5}}
        targets, _, labels = p._triples('hidden-triple', named, hidden)
        self.assertEqual(targets, {(0, 4), (1, 5), (2, 6)})
        self.assertEqual(len(labels), 6)
        hidden[3].add(1)
        with self.assertRaises(ValueError):
            p._triples('hidden-triple', named, hidden)

    def test_swordfish_uses_all_base_candidates_and_crossing_targets(self):
        named = dict(orientation='rows', bases=[0, 3, 6], covers=[1, 4, 7],
                     digit=9, positions=[1, 4, 31, 34, 55, 61])
        cs = {i: {2, 9} for i in named['positions'] + [10, 43]}
        targets, frames, labels = p._fish(named, cs)
        self.assertEqual(targets, {(10, 9), (43, 9)})
        self.assertEqual(len(frames), 3)
        self.assertEqual(len(labels), 6)
        cs[0] = {2, 9}
        with self.assertRaises(ValueError):
            p._fish(named, cs)

    def test_xy_and_xyz_targets_have_different_visibility_requirements(self):
        named = dict(pivot=0, wings=[3, 9], digits=[1, 2], digit=3)
        cs = {0: {1, 2}, 3: {1, 3}, 9: {2, 3}, 12: {3, 4}}
        targets, _, _ = p._wings('xy-wing', named, cs)
        self.assertEqual(targets, {(12, 3)})
        xyz = dict(pivot=0, wings=[3, 1], digits=[1, 2, 3], digit=3)
        cs = {0: {1, 2, 3}, 3: {1, 3}, 1: {2, 3}, 2: {3, 4}, 12: {3, 4}}
        targets, _, _ = p._wings('xyz-wing', xyz, cs)
        self.assertEqual(targets, {(2, 3)})
        self.assertNotIn((12, 3), targets)

    def test_w_wing_includes_a_link_cell_when_it_is_also_a_target(self):
        named = dict(cells=[36, 10], digits=[1, 2], link=[0, 1],
                     unit='row', unitIndex=0)
        cs = {36: {1, 2}, 10: {1, 2}, 0: {1, 2}, 1: {1, 2}, 37: {2, 4}}
        targets, _, _ = p._w_wing(named, cs)
        self.assertIn((0, 2), targets)
        self.assertIn((37, 2), targets)
        wrong = copy.deepcopy(named)
        wrong['link'] = [0, 2]
        with self.assertRaises(ValueError):
            p._w_wing(wrong, cs)

    def test_skyscraper_and_kite_rederive_links(self):
        named = dict(links=[[0, 3], [9, 13]], digit=7, orientation='rows')
        cs = {i: {2, 7} for i in [0, 3, 9, 13, 21]}
        targets, frames, _ = p._two_links('skyscraper', named, cs)
        self.assertEqual(targets, {(21, 7)})
        self.assertEqual(frames, {(0, 0, 1, 9), (1, 0, 1, 9)})
        named = dict(links=[[0, 3], [10, 37]], digit=7)
        cs = {i: {2, 7} for i in [0, 3, 10, 37, 39]}
        targets, frames, _ = p._two_links('two-string-kite', named, cs)
        self.assertEqual(targets, {(39, 7)})
        self.assertEqual(frames, {(0, 0, 1, 9), (0, 1, 9, 1)})
        cs[46] = {2, 7}
        with self.assertRaises(ValueError):
            p._two_links('two-string-kite', named, cs)

    def test_empty_rectangle_is_a_cross_plus_an_external_conjugate(self):
        named = dict(boxIndex=4, row=3, col=5, link=[27, 63],
                     unit='column', unitIndex=0, digit=9)
        cs = {i: {2, 9} for i in [30, 31, 41, 50, 27, 63, 68]}
        targets, frames, labels = p._empty_rectangle(named, cs)
        self.assertEqual(targets, {(68, 9)})
        self.assertEqual(frames, {(3, 3, 3, 3), (0, 0, 9, 1)})
        self.assertEqual(len(labels), 6)
        cs[32] = {2, 9}
        with self.assertRaises(ValueError):
            p._empty_rectangle(named, cs)


class TrialContract(unittest.TestCase):
    def test_public_entry_point_binds_named_rule_targets_geometry_and_trials(self):
        fixture = {
            'slug': 'xy-wing',
            'grid': '581060237040710650076350041790021060150630700632075410027503186815206070060187000',
            'targets': [[41, 8]],
            'branches': [[[48, 8]], [[48, 9], [30, 8]]],
            'frames': [[0, 3, 1, 1], [3, 3, 1, 1], [5, 3, 1, 1]],
            'labels': [[0, 3, 4], [0, 3, 9], [3, 3, 4], [3, 3, 8], [5, 3, 8], [5, 3, 9]],
            'pattern': {'pivot': 3, 'wings': [30, 48], 'digits': [4, 9], 'digit': 8,
                        'eliminations': [[41, 8]]},
        }
        p.validate_pattern('xy-wing', fixture)
        for key, value in [('targets', []), ('targets', [[41, 8], [41, 8]]),
                           ('targets', [[41, 8], [0, 8]]), ('frames', [[0, 0, 1, 9]]),
                           ('labels', fixture['labels'][:-1]),
                           ('branches', fixture['branches'][:1]), ('grid', '0' * 80),
                           ('slug', 'xyz-wing')]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                changed = copy.deepcopy(fixture)
                changed[key] = value
                p.validate_pattern('xy-wing', changed)
        changed = copy.deepcopy(fixture)
        changed['pattern']['eliminations'] = []
        with self.assertRaises(ValueError):
            p.validate_pattern('xy-wing', changed)
        for slug, value in [('unknown', fixture), ('xy-wing', {}), ('xy-wing', None)]:
            with self.subTest(slug=slug, value=value), self.assertRaises(ValueError):
                p.validate_pattern(slug, value)

    def test_one_guess_then_only_singles_with_exhaustive_same_cell_choices(self):
        grid = list(map(int, '030007050008100040092000700000060030000000809003401000004002000250870600000500000'))
        cs = p._candidates(grid)
        branches = [[[65, 1], [70, 9]], [[65, 9], [70, 1]]]
        targets = {(68, 9), (71, 1)}
        p._branches({'branches': branches}, grid, cs, targets)
        for bad in [branches[:1], [branches[0], branches[0]],
                    [branches[0], [[70, 1], [65, 9]]],
                    [[[65, 1], [0, 1]], branches[1]]]:
            with self.subTest(branches=bad), self.assertRaises(ValueError):
                p._branches({'branches': bad}, grid, cs, targets)
        with self.assertRaisesRegex(ValueError, 'Every target'):
            p._branches({'branches': branches}, grid, cs, {(0, 4)})

    def test_exact_integer_and_geometry_contracts(self):
        for choice in [[True, 1], [0, True], [0.0, 1], [0, 1.0], [81, 1], [0, 0]]:
            with self.subTest(choice=choice), self.assertRaises(ValueError):
                p._choice(choice)
        expected = {(0, 0, 1, 9)}
        p._appearance([[0, 0, 1, 9]], expected, 4, 'frames')
        for raw in [[[0, 0, True, 9]], [[0, 0, 1, 9]] * 2, [[0, 0, 1, 8]]]:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                p._appearance(raw, expected, 4, 'frames')


if __name__ == '__main__':
    unittest.main()
