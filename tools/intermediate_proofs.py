"""Independent ordinary-candidate proofs for intermediate lesson fixtures.

Cells and unit indices are zero-based; digits are 1–9. Targets are
``[cell, digit]`` pairs. Branches are lists of those pairs: one exhaustive
founding-cell choice followed exclusively by naked or hidden singles.
Uniqueness and native Core/UI behavior remain separate admission gates.
"""

import re


UNITS = (
    [frozenset(range(r * 9, r * 9 + 9)) for r in range(9)]
    + [frozenset(range(c, 81, 9)) for c in range(9)]
    + [frozenset((r + a) * 9 + c + b for a in range(3) for b in range(3))
       for r in (0, 3, 6) for c in (0, 3, 6)]
)
PEERS = [frozenset().union(*(u for u in UNITS if i in u)) - {i}
         for i in range(81)]
DIGITS = frozenset(range(1, 10))


def _require(ok, reason):
    if not ok:
        raise ValueError(reason)


def _integer(value, upper, name, lower=0):
    _require(type(value) is int and lower <= value < upper, f'Invalid {name}')
    return value


def _cells(values, count=None):
    _require(type(values) is list, 'Cells must be a list')
    for i in values:
        _integer(i, 81, 'cell')
    _require(len(set(values)) == len(values), 'Repeated cell')
    if count is not None:
        _require(len(values) == count, 'Wrong cell count')
    return values


def _digits(values, count):
    _require(type(values) is list and len(values) == count, 'Wrong digit count')
    for d in values:
        _integer(d, 10, 'digit', 1)
    _require(len(set(values)) == count, 'Repeated digit')
    return set(values)


def _choice(value):
    _require(type(value) is list and len(value) == 2, 'Invalid choice')
    return (_integer(value[0], 81, 'choice cell'),
            _integer(value[1], 10, 'choice digit', 1))


def _candidates(grid):
    return {i: DIGITS - {grid[j] for j in PEERS[i]}
            for i, d in enumerate(grid) if not d}


def _consistent(grid, cs):
    _require(all(cs.values()), 'Empty candidate cell')
    for u in UNITS:
        filled = [grid[i] for i in u if grid[i]]
        _require(len(filled) == len(set(filled)), 'Conflicting fills')
        for d in DIGITS - set(filled):
            _require(any(d in cs.get(i, ()) for i in u), 'Digit has no home')


def _forced(grid, cs):
    result = {(i, next(iter(ds))) for i, ds in cs.items() if len(ds) == 1}
    for u in UNITS:
        for d in DIGITS - {grid[i] for i in u}:
            cells = [i for i in u if d in cs.get(i, ())]
            if len(cells) == 1:
                result.add((cells[0], d))
    return result


def _unit(e):
    kind = e['unit']
    _require(kind in ('row', 'column', 'box'), 'Invalid unit kind')
    n = _integer(e['unitIndex'], 9, 'unit index')
    return UNITS[{'row': 0, 'column': 9, 'box': 18}[kind] + n]


def _live(cs, unit, digit):
    return {i for i in unit if digit in cs.get(i, ())}


def _common(cs, cells, digit, excluded=()):
    seen = set.intersection(*(set(PEERS[i]) for i in cells))
    return {(i, digit) for i in seen - set(excluded) if digit in cs.get(i, ())}


def _link(cs, cells, digit):
    _cells(cells, 2)
    _require(any(_live(cs, u, digit) == set(cells) for u in UNITS),
             'Link must be the only two digit positions in a unit')


def _branches(e, grid, cs, targets):
    raw = e['branches']
    _require(type(raw) is list and raw, 'Missing exhaustive branches')
    _require(all(type(b) is list and b for b in raw), 'Empty branch')
    starts = [_choice(b[0]) for b in raw]
    root = starts[0][0]
    _require(all(i == root for i, _ in starts), 'Trials need one founding cell')
    _require(len(starts) == len(set(starts)) and
             {d for _, d in starts} == cs.get(root, set()),
             'Trials must exhaust every original founding-cell candidate')
    for branch in raw:
        state = grid.copy()
        current = cs
        for n, raw_choice in enumerate(branch):
            i, d = _choice(raw_choice)
            _require(d in current.get(i, ()), 'Trial fill is not available')
            if n:
                _require((i, d) in _forced(state, current),
                         'Only the founding fill may be a guess')
            state[i] = d
            current = _candidates(state)
            _consistent(state, current)
        for i, d in targets:
            _require(state[i] != d and d not in current.get(i, ()),
                     'Every target must be excluded in every trial')


def _frame(kind, n):
    _integer(n, 9, 'frame unit index')
    if kind == 'row':
        return (n, 0, 1, 9)
    if kind == 'column':
        return (0, n, 9, 1)
    _require(kind == 'box', 'Invalid frame unit')
    return (n // 3 * 3, n % 3 * 3, 3, 3)


def _cell_frames(cells):
    return {(i // 9, i % 9, 1, 1) for i in cells}


def _labels(cs, cells, digits=None):
    return {(i // 9, i % 9, d) for i in cells
            for d in cs.get(i, ()) if digits is None or d in digits}


def _triples(slug, p, cs):
    u = _unit(p)
    cells = _cells(p['cells'], 3)
    ds = _digits(p['digits'], 3)
    _require(all(i in u and i in cs for i in cells), 'Triple outside its unit')
    if slug == 'naked-triple':
        _require(set().union(*(cs[i] for i in cells)) == ds,
                 'Naked Triple must contain exactly three digits')
        targets = {(i, d) for i in u - set(cells) for d in ds & cs.get(i, set())}
        labels = _labels(cs, cells)
    else:
        locations = [_live(cs, u, d) for d in ds]
        _require(all(locations) and set().union(*locations) == set(cells),
                 'Hidden Triple digits must occur only in its three cells')
        targets = {(i, d) for i in cells for d in cs[i] - ds}
        labels = _labels(cs, cells, ds)
    return targets, {_frame(p['unit'], p['unitIndex'])}, labels


def _fish(p, cs):
    orientation = p['orientation']
    _require(orientation in ('rows', 'columns'), 'Invalid fish orientation')
    bases, covers = p['bases'], p['covers']
    for values in (bases, covers):
        _require(type(values) is list and len(values) == 3, 'Fish needs three units')
        for n in values:
            _integer(n, 9, 'fish unit')
        _require(len(set(values)) == 3, 'Repeated fish unit')
    d = _integer(p['digit'], 10, 'fish digit', 1)
    row_based = orientation == 'rows'
    base = (lambda i: i // 9) if row_based else (lambda i: i % 9)
    cross = (lambda i: i % 9) if row_based else (lambda i: i // 9)
    positions = {i for i in cs if base(i) in bases and d in cs[i]}
    for n in bases:
        _require(2 <= sum(base(i) == n for i in positions) <= 3,
                 'Each Swordfish base needs two or three positions')
    _require({cross(i) for i in positions} == set(covers), 'Wrong fish covers')
    _require(set(_cells(p['positions'])) == positions, 'Incomplete fish positions')
    targets = {(i, d) for i in cs if base(i) not in bases
               and cross(i) in covers and d in cs[i]}
    kind = 'row' if row_based else 'column'
    return targets, {_frame(kind, n) for n in bases}, _labels(cs, positions, {d})


def _wings(slug, p, cs):
    pivot = _integer(p['pivot'], 81, 'pivot')
    wings = _cells(p['wings'], 2)
    _require(pivot not in wings and all(i in PEERS[pivot] for i in wings),
             'Both distinct wings must see the pivot')
    d = _integer(p['digit'], 10, 'wing elimination digit', 1)
    expected_size = 2 if slug == 'xy-wing' else 3
    ds = _digits(p['digits'], expected_size)
    _require(cs.get(pivot) == ds, 'Wrong pivot candidates')
    if slug == 'xy-wing':
        _require(d not in ds, 'XY-Wing target digit must differ from pivot digits')
    else:
        _require(d in ds, 'XYZ-Wing pivot must contain the target digit')
    others = ds if slug == 'xy-wing' else ds - {d}
    wing_sets = [cs.get(i, set()) for i in wings]
    _require(all(len(s) == 2 and d in s for s in wing_sets) and
             {frozenset(s - {d}) for s in wing_sets} ==
             {frozenset({v}) for v in others}, 'Wrong wing candidate sets')
    seeing = wings if slug == 'xy-wing' else [pivot, *wings]
    cells = [pivot, *wings]
    return _common(cs, seeing, d, cells), _cell_frames(cells), _labels(cs, cells)


def _w_wing(p, cs):
    cells = _cells(p['cells'], 2)
    ds = p['digits']
    _digits(ds, 2)
    x, y = ds
    _require(all(cs.get(i) == set(ds) for i in cells), 'W-Wing needs equal bivalue cells')
    _require(cells[1] not in PEERS[cells[0]], 'W-Wing cells must not see each other')
    link = _cells(p['link'], 2)
    _require(len(set(cells + link)) == 4, 'W-Wing needs four distinct cells')
    _require(_live(cs, _unit(p), x) == set(link), 'Wrong W-Wing conjugate unit')
    _require(link[0] in PEERS[cells[0]] and link[1] in PEERS[cells[1]],
             'W-Wing link must connect the corresponding bivalue cells')
    labels = _labels(cs, cells) | _labels(cs, link, {x})
    frames = _cell_frames(cells) | {_frame(p['unit'], p['unitIndex'])}
    return _common(cs, cells, y), frames, labels


def _two_links(slug, p, cs):
    d = _integer(p['digit'], 10, 'link digit', 1)
    links = p['links']
    _require(type(links) is list and len(links) == 2, 'Two conjugate links required')
    for link in links:
        _cells(link, 2)
    (a, b), (c, f) = links
    _require(len({a, b, c, f}) == 4, 'Links need four distinct cells')
    if slug == 'skyscraper':
        orientation = p['orientation']
        _require(orientation in ('rows', 'columns'), 'Invalid Skyscraper orientation')
        kind = 'row' if orientation == 'rows' else 'column'
        base = (lambda i: i // 9) if kind == 'row' else (lambda i: i % 9)
        cross = (lambda i: i % 9) if kind == 'row' else (lambda i: i // 9)
        _require(base(a) == base(b) and base(c) == base(f) and base(a) != base(c),
                 'Skyscraper links must use distinct parallel units')
        _require(cross(a) == cross(c) and cross(b) != cross(f),
                 'Skyscraper needs one aligned base and distinct roofs')
        frames = {_frame(kind, base(a)), _frame(kind, base(c))}
        for link in links:
            u = UNITS[(0 if kind == 'row' else 9) + base(link[0])]
            _require(_live(cs, u, d) == set(link), 'Incomplete Skyscraper base')
    else:
        row_link = next((link for link in links if link[0] // 9 == link[1] // 9), None)
        col_link = next((link for link in links if link[0] % 9 == link[1] % 9), None)
        _require(row_link is not None and col_link is not None and row_link != col_link,
                 'Kite needs one row link and one column link')
        _require(a // 27 == c // 27 and a % 9 // 3 == c % 9 // 3,
                 'Kite connectors must share a box')
        r, col = row_link[0] // 9, col_link[0] % 9
        _require(_live(cs, UNITS[r], d) == set(row_link) and
                 _live(cs, UNITS[9 + col], d) == set(col_link), 'Incomplete kite strings')
        frames = {_frame('row', r), _frame('column', col)}
    return _common(cs, [b, f], d), frames, _labels(cs, [a, b, c, f], {d})


def _turbot(p, cs):
    d = _integer(p['digit'], 10, 'Turbot digit', 1)
    links, units = p['links'], p['units']
    _require(type(links) is list and len(links) == 2 and
             type(units) is list and len(units) == 2, 'Turbot needs two declared strong links')
    for link in links:
        _cells(link, 2)
    (a, b), (c, f) = links
    _require(len({a, b, c, f}) == 4, 'Turbot needs four distinct candidates')
    frames = set()
    for unit, link in zip(units, links):
        _require(_live(cs, _unit(unit), d) == set(link), 'Incomplete Turbot conjugate unit')
        frames.add(_frame(unit['unit'], unit['unitIndex']))
    bridge = p['bridge']
    _require({a, c} <= _unit(bridge), 'Turbot connectors must share the declared weak-link unit')
    frames.add(_frame(bridge['unit'], bridge['unitIndex']))
    return _common(cs, [b, f], d), frames, _labels(cs, [a, b, c, f], {d})


def _empty_rectangle(p, cs):
    box = _integer(p['boxIndex'], 9, 'ER box')
    r = _integer(p['row'], 9, 'ER row')
    c = _integer(p['col'], 9, 'ER column')
    d = _integer(p['digit'], 10, 'ER digit', 1)
    u = UNITS[18 + box]
    _require(r // 3 == box // 3 and c // 3 == box % 3, 'ER cross outside box')
    live = _live(cs, u, d)
    _require(len(live) >= 3 and r * 9 + c not in live,
             'Teaching ER needs at least three positions and an empty intersection')
    row_arm = {i for i in live if i // 9 == r}
    col_arm = {i for i in live if i % 9 == c}
    _require(row_arm and col_arm and row_arm | col_arm == live,
             'ER candidates must lie on both arms of the cross')
    a, b = _cells(p['link'], 2)
    _require(a not in u and b not in u, 'ER conjugate link must be outside the box')
    kind = p['unit']
    _require(kind in ('row', 'column'), 'ER link must be a row or column')
    _require(_live(cs, _unit(p), d) == {a, b}, 'Wrong ER conjugate link')
    if kind == 'column':
        _require(a // 9 == r, 'ER link must meet its row arm')
        remaining = col_arm
    else:
        _require(a % 9 == c, 'ER link must meet its column arm')
        remaining = row_arm
    targets = _common(cs, [b, *remaining], d)
    frames = {_frame('box', box), _frame(kind, p['unitIndex'])}
    return targets, frames, _labels(cs, live | {a, b}, {d})


def _appearance(raw, expected, width, name):
    _require(type(raw) is list, f'Missing {name}')
    for item in raw:
        _require(type(item) is list and len(item) == width and
                 all(type(v) is int for v in item), f'Invalid {name}')
    items = [tuple(item) for item in raw]
    _require(len(items) == len(set(items)) and set(items) == expected,
             f'{name} must match independently derived pattern geometry')


def validate_pattern(slug, e):
    """Raise ValueError for an invalid premise, display, target or trial proof."""
    try:
        _require(type(e) is dict, 'Pattern fixture must be an object')
        if 'slug' in e:
            _require(e['slug'] == slug, 'Fixture slug mismatch')
        text = e['grid']
        _require(type(text) is str and re.fullmatch(r'[0-9]{81}', text), 'Invalid grid')
        grid = list(map(int, text))
        cs = _candidates(grid)
        _consistent(grid, cs)
        _require(not _forced(grid, cs), 'Intermediate root must have zero singles')
        p = e['pattern']
        _require(type(p) is dict, 'Named pattern premises required')
        if slug in ('naked-triple', 'hidden-triple'):
            targets, frames, labels = _triples(slug, p, cs)
        elif slug == 'swordfish':
            targets, frames, labels = _fish(p, cs)
        elif slug in ('xy-wing', 'xyz-wing'):
            targets, frames, labels = _wings(slug, p, cs)
        elif slug == 'w-wing':
            targets, frames, labels = _w_wing(p, cs)
        elif slug in ('skyscraper', 'two-string-kite'):
            targets, frames, labels = _two_links(slug, p, cs)
        elif slug == 'turbot-fish':
            targets, frames, labels = _turbot(p, cs)
        elif slug == 'empty-rectangle':
            targets, frames, labels = _empty_rectangle(p, cs)
        else:
            raise ValueError('Unknown intermediate technique')
        _require(targets, 'Pattern must eliminate at least one candidate')
        claimed = [_choice(t) for t in e['targets']]
        _require(len(claimed) == len(set(claimed)) and set(claimed) == targets,
                 'Targets must be all and only named-pattern eliminations')
        if 'eliminations' in p:
            extra = [_choice(t) for t in p['eliminations']]
            _require(len(extra) == len(set(extra)) and set(extra) == targets,
                     'Pattern elimination record differs from derived targets')
        _appearance(e['frames'], frames, 4, 'Reveal frames')
        _appearance(e['labels'], labels, 3, 'Reveal labels')
        _branches(e, grid, cs, targets)
    except (KeyError, TypeError, IndexError, AttributeError) as error:
        raise ValueError('Malformed intermediate pattern fixture') from error
