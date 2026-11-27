"""A naked pair shared by a complete line and box reserves both houses."""
def validate_pattern(example, advanced_position, naked_pair, require):
    grid, units, candidates = advanced_position(example)
    kind, number, box = example['unit'], example['unitIndex'], example['boxIndex']
    require(kind in ['row', 'column'] and type(number) is int and number in range(9) and
            type(box) is int and box in range(9), 'Locked Pair needs a line and box')
    line = units[(0 if kind == 'row' else 9)+number]
    block = units[18+box]
    pair, digits = example['pair'], example['digits']
    require(isinstance(pair, list) and isinstance(digits, list) and
            all(type(v) is int for v in pair+digits), 'Locked Pair cells and digits use integers')
    require(len(pair) == 2 and all(type(i) is int and i in line & block for i in pair),
            'Both Locked Pair cells must belong to both named houses')
    targets = {(i, d) for i in (line | block)-set(pair) for d in digits if d in candidates.get(i, set())}
    claimed = example['targets']
    require(all(isinstance(q, list) and len(q) == 2 and all(type(v) is int for v in q) for q in claimed),
            'Locked Pair targets use integer cells and digits')
    require(len(claimed) == len({tuple(q) for q in claimed}) and {tuple(q) for q in claimed} == targets,
            'Locked Pair must remove all and only eliminations in both houses')
    require(any(i in line-block for i, _ in targets) and any(i in block-line for i, _ in targets),
            'These teaching examples must demonstrate both houses outside their intersection')
    branches = example['branches']
    require(isinstance(branches, list) and all(isinstance(b, list) and
            all(isinstance(q, list) and len(q) == 2 and all(type(v) is int for v in q) for q in b)
            for b in branches), 'Locked Pair native trial coordinates use integers')
    for unit_kind, unit_number, cells in [(kind, number, line), ('box', box, block)]:
        naked_pair({**example, 'unit': unit_kind, 'unitIndex': unit_number,
                    'targets': [[i, d] for i, d in sorted(targets) if i in cells]})
    geometry = [number, 0, 1, 9] if kind == 'row' else [0, number, 9, 1]
    for name, width in [('frames', 4), ('labels', 3)]:
        vectors = example.get(name)
        require(isinstance(vectors, list) and all(isinstance(v, list) and len(v) == width and
                all(type(n) is int for n in v) for v in vectors),
                'Locked Pair native reveal coordinates use integers')
    require(example.get('frames') == [geometry, [box//3*3, box%3*3, 3, 3]] and
            example.get('labels') == [[i//9, i%9, d] for i in pair for d in digits],
            'Locked Pair reveals the complete line and box with all four pair labels')
