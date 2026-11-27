"""Full House: one blank and eight distinct starting digits in a whole house."""
def geometry(kind, number):
    return {'row': [number, 0, 1, 9], 'column': [0, number, 9, 1],
            'box': [number//3*3, number%3*3, 3, 3]}[kind]


def validate_pattern(example, position, require):
    grid, units, candidates = position(example)
    kind, number = example['unit'], example['unitIndex']
    cell, digit = example['cell'], example['digit']
    require(kind in ['row', 'column', 'box'] and type(number) is int and number in range(9),
            'Invalid Full House unit')
    require(type(cell) is int and cell in range(81) and type(digit) is int and digit in range(1, 10),
            'Invalid Full House choice')
    unit = units[{'row': 0, 'column': 9, 'box': 18}[kind]+number]
    require([i for i in sorted(unit) if not grid[i]] == [cell],
            'Full House needs exactly one blank in the complete named unit')
    filled = [[i, grid[i]] for i in sorted(unit) if grid[i]]
    require(len(filled) == 8 and {v for _, v in filled} == set(range(1, 10))-{digit},
            'Full House needs all eight other distinct starting digits')
    witnesses = example.get('unitGivens')
    require(isinstance(witnesses, list) and all(isinstance(w, list) and len(w) == 2 and
            all(type(v) is int for v in w) for w in witnesses), 'Full House witnesses use integer cells and digits')
    require(witnesses == filled, 'Full House witnesses must list all eight starting clues')
    require(candidates.get(cell) == {digit}, 'Full House target must have its sole missing digit')


def validate_story(data, example, forced_single_animation, require):
    require(data.get('style') == 'chill', 'Full House uses the actual Chill Mode forced double tap')
    checks = data.get('expected', {})
    require(checks.get('revealFrameCount') == 1 and checks.get('revealLabelCount') == 1,
            'Full House asserts one full-house reveal and its one missing digit')
    forced_single_animation(data, example, geometry(example['unit'], example['unitIndex']), 'Full House')
