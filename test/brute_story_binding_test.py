"""Presentation admission only; these fixtures claim no Sudoku/native proof."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    'search_input_binding', Path(__file__).resolve().parents[1] / 'tools/brute_story_binding.py')
rules = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rules)


def fixture():
    state = {'boardCount': 1, 'redo': None}
    example = {'grid': '0' * 81, 'mode': 'single-board', 'events': [
        {'op': 'guess', 'choice': [1, 1], 'checkpoint': state},
        {'op': 'inspect', 'checkpoint': state}]}
    data = {'grid': example['grid'], 'style': 'chill', 'setup': [],
            'expected': {'initialStatus': 'dilemma'}, 'frames': [
                {'do': 'down', 'at': {'part': 'cell', 'cell': [0, 1]}, 'time': 1000},
                {'do': 'move', 'at': {'part': 'cell', 'cell': [0, 1], 'offset': [-1.2, -1.2]}, 'time': 1100, 'ms': 450},
                {'do': 'ready', 'digit': 1, 'time': 1600},
                {'do': 'up', 'time': 2300}],
            'presentation': {'duration': 6000,
                'searchEventWindows': [{'start': 500, 'end': 3000}, {'start': 3600, 'end': 5000}],
                'searchCheckpoints': [{'time': 3000, 'state': state}, {'time': 5000, 'state': state}]}}
    return data, example


class SearchInputs(unittest.TestCase):
    def test_checked_choice_and_quiet_checkpoints_are_admitted(self):
        data, example = fixture()
        rules.validate_story(data, example)

    def test_checkpoint_cannot_precede_its_event_or_follow_the_next_one(self):
        for at in [900, 4000]:
            data, example = fixture()
            data['presentation']['searchCheckpoints'][0]['time'] = at
            with self.assertRaisesRegex(ValueError, 'after its event'):
                rules.validate_story(data, example)
        data, example = fixture()
        data['presentation']['searchEventWindows'][0]['end'] = 1500
        with self.assertRaises(ValueError):
            rules.validate_story(data, example)

    def test_no_different_guess_hidden_final_edit_or_extra_board(self):
        data, example = fixture()
        data['frames'][2]['digit'] = 7
        with self.assertRaises(ValueError):
            rules.validate_story(data, example)
        data, example = fixture()
        data['final'] = [{'id': 'SET_FILL'}]
        with self.assertRaisesRegex(ValueError, 'hidden'):
            rules.validate_story(data, example)
        data, example = fixture()
        # Keep source and declared runtime snapshot equal: the one-board rule
        # must still reject the additional board.
        example['events'][0]['checkpoint']['boardCount'] = 2
        with self.assertRaisesRegex(ValueError, 'exactly one board'):
            rules.validate_story(data, example)

    def test_history_requires_real_grouped_double_tap(self):
        expected = rules.actions_for({'op': 'undoDouble'})[0]
        self.assertEqual(expected['count'], 2)
        self.assertEqual([t['finger'] for t in expected['touches']], [0, 1])
        expected = rules.actions_for({'op': 'redoDouble'})[0]
        self.assertEqual([t['finger'] for t in expected['touches']], [0, 1, 2])


if __name__ == '__main__':
    unittest.main()
