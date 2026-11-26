"""Advanced-to-native-story dispatch, not another named-rule/gesture suite.

Real case/story JSON exercises production validate(). Minimal SVGs and links
provide controlled provenance so a story failure cannot be a checksum failure.
These fixtures do not qualify actual exported artwork or native behavior.
"""
import base64
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import tempfile
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('advanced_story_admission', ROOT / 'tools/validate_lessons.py')
rules = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rules)
CURRENT = ('naked-quadruple', 'jellyfish', 'finned-x-wing', 'simple-coloring', 'remote-pairs')


def fixture_link(grid):
    # Supply a valid existing share-frame contract; encoding is not under test.
    digits = grid + '0'
    body = b'SP\x01' + bytes(int(digits[n:n+2], 16) for n in range(0, 82, 2))
    frame = body + zlib.crc32(body).to_bytes(4, 'big')
    return 'https://sudoku.joypace.com/share/?p=' + base64.urlsafe_b64encode(frame).decode()


def declared_valid_story(example):
    """A controlled valid-looking declaration must not hide a failed trial."""
    branches = example['branches']
    actions = []
    cell = lambda i: {'part': 'cell', 'cell': [i//9, i%9]}
    slot = lambda n: {'part': 'slot', 'slot': n}

    def add(operation, **fields):
        actions.append({'do': operation, 'time': 500 + len(actions)*1000, **fields})

    for n, branch in enumerate(branches):
        if n:
            add('tap', at=slot(1), count=1)
        add('tap', at=slot(n+2), count=1)
        i, d = branch[0]
        r, c = divmod(d-1, 3)
        add('down', at=cell(i))
        add('move', at={**cell(i), 'offset': [1.2*(c-1), 1.2*(r-1)]})
        add('ready', digit=d)
        add('up')
        for i, d in branch[1:]:
            add('tap', at=cell(i), count=2)
    add('tap', at=slot(1), count=1)
    for n in range(2, len(branches)+2):
        add('down', at=slot(n))
        add('move', at=slot(1))
        add('up')
    for i, d in example['targets']:
        r, c = divmod(d-1, 3)
        dx, dy = c-1, r-1
        scale = 1.617 / (math.sqrt(2) if dx and dy else 1)
        add('down', at=cell(i), inputDelay=440)
        add('move', at={**cell(i), 'offset': [scale*dx, scale*dy]})
        add('up')
    touched = sorted({i for branch in branches for i, d in branch})
    return {
        'grid': example['grid'], 'style': 'chill', 'setup': [], 'frames': actions,
        'presentation': {'duration': actions[-1]['time']+1000, 'choiceReveal': {
            'start': 500, 'frames': example['frames'], 'labels': example['labels']}},
        'expected': {
            'initialStatus': 'dilemma', 'boards': len(branches)+1,
            'validSlots': list(range(len(branches)+1)),
            'slotFills': [[n, i//9, i%9, d] for n, branch in enumerate(branches, 1) for i, d in branch],
            'overlays': [[n, 0] for n in range(1, len(branches)+1)],
            'notes': [[i//9, i%9, d, False] for i, d in example['targets']],
            'fills': [[i//9, i%9, 0] for i in touched],
            'revealFrameCount': len(example['frames']), 'revealLabelCount': len(example['labels']),
        },
    }


class AdvancedNativeDispatch(unittest.TestCase):
    def fixture(self, slug, replacement=None, mutate=None):
        temp = tempfile.TemporaryDirectory(prefix='advanced-story-dispatch-')
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        learn = root / 'learn'
        folder = learn / slug
        folder.mkdir(parents=True)
        for name in ['index.html', 'learn.css', 'learn.js']:
            (learn / name).write_text('controlled fixture')
        (folder / 'index.html').write_text('controlled article fixture')
        examples = json.loads((ROOT / 'learn' / slug / 'examples.json').read_text())
        stories = [json.loads((ROOT / 'learn' / slug / f'example-{n}.json').read_text()) for n in range(1, 4)]
        if replacement is not None:
            index = next((n for n, e in enumerate(examples) if e['grid'] == replacement['grid']), 0)
            examples[index] = copy.deepcopy(replacement)
            stories[index] = declared_valid_story(examples[index])
        if mutate is not None:
            mutate(stories[0])
        for n, (example, story) in enumerate(zip(examples, stories), 1):
            stem = f'example-{n}'
            scene = folder / (stem + '.json')
            scene.write_text(json.dumps(story, indent=2)+'\n')
            digest = hashlib.sha256(scene.read_bytes()).hexdigest()
            example.update(id=stem, animation=stem+'.svg', shareURL=fixture_link(example['grid']), scenarioSHA256=digest)
            metadata = {
                'app': '1d3fa459e04d2ddbc5fcba8344fec78474af8c93',
                'content': 'b7794cfad7e427e85d4a302130dee5a98b9f4b90', 'productDirty': False,
                'story': {'sha256': digest},
            }
            (folder / (stem+'.svg')).write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" data-duration="1"><metadata>'
                + json.dumps(metadata) + '</metadata></svg>')
        (folder / 'examples.json').write_text(json.dumps(examples)+'\n')
        manifest = {'schema': 1, 'lessons': [{
            'slug': slug, 'title': slug, 'description': 'Controlled dispatch fixture',
            'published': '2026-11-26', 'examples': [{'id': f'example-{n}'} for n in range(1, 4)],
        }]}
        (learn / 'manifest.json').write_text(json.dumps(manifest)+'\n')
        return root

    def test_completed_advanced_types_reach_production_story_admission(self):
        for slug in CURRENT:
            with self.subTest(slug=slug):
                self.assertEqual(len(rules.validate(self.fixture(slug))), 12)

    def test_advanced_dispatch_binds_the_fourth_quadruple_fill(self):
        def omit_final_fill(story):
            story['expected']['slotFills'].pop()
        root = self.fixture('naked-quadruple', mutate=omit_final_fill)
        with self.assertRaisesRegex(ValueError, 'Story fills must match its proved trials'):
            rules.validate(root)

    def test_math_valid_contradiction_cannot_enter_the_valid_only_native_profile(self):
        # Reuse the owning math specification's fixture; do not duplicate its
        # RCC/color/witness assertions or copy a second version of that proof.
        spec = importlib.util.spec_from_file_location('advanced_math_fixture', ROOT / 'test/advanced_proofs_test.py')
        owner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(owner)
        wrap = owner.TrialOutcomes().fixture()
        rules._stories.validate_story(declared_valid_story(wrap), wrap)
        root = self.fixture('simple-coloring', replacement=wrap)
        with self.assertRaisesRegex(ValueError, 'Contradictory advanced trials need their separate checked native outcome contract'):
            rules.validate(root)


if __name__ == '__main__':
    unittest.main()
