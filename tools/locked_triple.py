"""A proper three-cell naked subset reserves its shared line and box."""
def validate_pattern(example, base, require):
    grid = list(map(int, example['grid']))
    candidates = base._candidates(grid)
    pattern = example['pattern']
    kind = pattern['unit']
    require(kind in ['row', 'column'], 'Locked Triple needs a line and box')
    line = base._unit(pattern)
    box = base._integer(pattern['boxIndex'], 9, 'box index')
    block = base.UNITS[18+box]
    cells = base._cells(pattern['cells'], 3)
    digits = base._digits(pattern['digits'], 3)
    require(set(cells) <= line & block, 'All Locked Triple cells must share both houses')
    from itertools import combinations
    require(all(len(candidates.get(a, set()) | candidates.get(b, set())) > 2
                for a, b in combinations(cells, 2)), 'Use a proper triple without a contained naked pair')
    targets = {(i, d) for i in (line | block)-set(cells) for d in digits & candidates.get(i, set())}
    claimed = [base._choice(q) for q in example['targets']]
    require(len(claimed) == len(set(claimed)) and set(claimed) == targets,
            'Locked Triple removes all and only eliminations in both houses')
    require(any(i in line-block for i, _ in targets) and any(i in block-line for i, _ in targets),
            'These teaching examples must demonstrate both houses outside the intersection')
    labels = base._labels(candidates, cells)
    frames = {base._frame(kind, pattern['unitIndex']), base._frame('box', box)}
    base._appearance(example['frames'], frames, 4, 'Locked Triple reveal frames')
    base._appearance(example['labels'], labels, 3, 'Locked Triple reveal labels')
    # Keep the existing zero-single, complete-subset and one-guess/forced-only
    # branch specification for each complete house, without duplicating it.
    for unit_kind, number, unit in [(kind, pattern['unitIndex'], line), ('box', box, block)]:
        base.validate_pattern('naked-triple', {**example, 'slug': 'naked-triple',
            'pattern': {**pattern, 'unit': unit_kind, 'unitIndex': number},
            'targets': [[i, d] for i, d in sorted(targets) if i in unit],
            'frames': [list(base._frame(unit_kind, number))]})
