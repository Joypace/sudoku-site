"""Named advanced rules, derived from givens rather than detector output.

Indices are zero-based, digits are 1–9. The fixture and exhaustive trial schema
matches intermediate_proofs. Uniqueness and native Core validity are separate
gates; this module does not infer either from local candidate consistency.
"""

from collections import defaultdict
from itertools import combinations
import importlib.util
from pathlib import Path
import re


_spec = importlib.util.spec_from_file_location(
    '_advanced_candidate_rules', Path(__file__).with_name('intermediate_proofs.py'))
_b = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_b)

SLUGS = ('naked-quadruple', 'hidden-quadruple', 'jellyfish', 'finned-x-wing',
         'finned-swordfish', 'finned-jellyfish', 'simple-coloring', 'remote-pairs')


def _quadruple(slug, p, cs):
    unit = _b._unit(p)
    cells = _b._cells(p['cells'], 4)
    digits = _b._digits(p['digits'], 4)
    _b._require(all(i in unit and i in cs for i in cells), 'Quadruple outside its unit')
    if slug == 'naked-quadruple':
        _b._require(set().union(*(cs[i] for i in cells)) == digits,
                    'Naked Quadruple needs exactly four combined candidates')
        targets = {(i, d) for i in unit - set(cells) for d in cs.get(i, set()) & digits}
        labels = _b._labels(cs, cells)
    else:
        places = [_b._live(cs, unit, d) for d in digits]
        _b._require(all(places) and set().union(*places) == set(cells),
                    'Hidden Quadruple digits must occur only in its four cells')
        targets = {(i, d) for i in cells for d in cs[i] - digits}
        labels = _b._labels(cs, cells, digits)
    return targets, {_b._frame(p['unit'], p['unitIndex'])}, labels


def _fish(slug, p, cs):
    size = {'jellyfish': 4, 'finned-x-wing': 2,
            'finned-swordfish': 3, 'finned-jellyfish': 4}[slug]
    orientation = p['orientation']
    _b._require(orientation in ('rows', 'columns'), 'Invalid fish orientation')
    row_based = orientation == 'rows'
    base = (lambda i: i // 9) if row_based else (lambda i: i % 9)
    cross = (lambda i: i % 9) if row_based else (lambda i: i // 9)
    bases, covers = p['bases'], p['covers']
    for group in (bases, covers):
        _b._require(type(group) is list and len(group) == size, 'Wrong fish size')
        for i in group:
            _b._integer(i, 9, 'fish unit')
        _b._require(len(set(group)) == size, 'Repeated fish unit')
    digit = _b._integer(p['digit'], 10, 'fish digit', 1)
    positions = {i for i in cs if base(i) in bases and digit in cs[i]}
    _b._require(set(_b._cells(p['positions'])) == positions,
                'Fish must declare every candidate in every base unit')
    fins = {i for i in positions if cross(i) not in covers}
    body = positions - fins
    _b._require({cross(i) for i in body} == set(covers), 'Incorrect fish cover units')
    for i in bases:
        _b._require(2 <= sum(base(j) == i for j in body) <= size,
                    'Basic fish body needs at least two positions in every base')
    targets = {(i, digit) for i in cs if base(i) not in bases
               and cross(i) in covers and digit in cs[i]}
    kind = 'row' if row_based else 'column'
    frames = {_b._frame(kind, n) for n in bases}
    if slug == 'jellyfish':
        _b._require(not fins, 'Jellyfish bases must be contained by its covers')
    else:
        declared = set(_b._cells(p['fins']))
        _b._require(fins and declared == fins and len({base(i) for i in fins}) == 1,
                    'Finned fish must declare all fins in one base')
        box = _b._integer(p['finBox'], 9, 'fin box')
        _b._require(fins <= _b.UNITS[18 + box], 'All fins must share the declared box')
        # These slugs teach regular finned fish. A body reducible to a smaller
        # fish belongs to the separately catalogued sashimi variants.
        for n in range(1, size):
            for subset in combinations(bases, n):
                covered = {cross(i) for i in body if base(i) in subset}
                _b._require(len(covered) > n, 'Degenerate fin-free body is Sashimi, not regular finned fish')
        targets = {(i, d) for i, d in targets if all(i in _b.PEERS[f] for f in fins)}
        frames.add(_b._frame('box', box))
    return targets, frames, _b._labels(cs, positions, {digit})


def _conjugates(cs, digit):
    edges = set()
    units = []
    for index, unit in enumerate(_b.UNITS):
        live = _b._live(cs, unit, digit)
        if len(live) == 2:
            edge = tuple(sorted(live))
            edges.add(edge)
            units.append((index, edge))
    return edges, units


def _coloring(p, cs):
    digit = _b._integer(p['digit'], 10, 'color digit', 1)
    cells = set(_b._cells(p['component']))
    _b._require(len(cells) >= 2 and all(digit in cs.get(i, ()) for i in cells),
                'Color component needs live digit candidates')
    all_edges, all_units = _conjugates(cs, digit)
    graph = defaultdict(set)
    for a, b in all_edges:
        graph[a].add(b)
        graph[b].add(a)
    reached = set()
    pending = [min(cells)]
    while pending:
        i = pending.pop()
        if i not in reached:
            reached.add(i)
            pending.extend(graph[i] - reached)
    _b._require(reached == cells, 'Coloring must include the entire connected strong-link component')
    edges = {edge for edge in all_edges if edge[0] in cells}
    declared_edges = []
    _b._require(type(p['edges']) is list, 'Color edges must be a list')
    for edge in p['edges']:
        _b._cells(edge, 2)
        declared_edges.append(tuple(sorted(edge)))
    _b._require(len(declared_edges) == len(set(declared_edges)) and
                set(declared_edges) == edges, 'Incomplete or false conjugate edges')
    colors = p['colors']
    _b._require(type(colors) is list and len(colors) == 2, 'Coloring needs two classes')
    groups = [set(_b._cells(color)) for color in colors]
    _b._require(all(groups) and not groups[0] & groups[1] and
                groups[0] | groups[1] == cells, 'Color classes must partition the component')
    _b._require(all((a in groups[0]) != (b in groups[0]) for a, b in edges),
                'Conjugate endpoints must have opposite colors')
    frame_units = set()
    for index, edge in all_units:
        if edge in edges:
            kind = ('row', 'column', 'box')[index // 9]
            frame_units.add((kind, index % 9))
    raw_units = p['units']
    _b._require(type(raw_units) is list, 'Color units must be a list')
    declared_units = []
    for item in raw_units:
        _b._require(type(item) is list and len(item) == 2, 'Invalid color unit')
        kind, n = item
        _b._frame(kind, n)
        declared_units.append((kind, n))
    _b._require(len(declared_units) == len(set(declared_units)) and
                set(declared_units) == frame_units, 'Coloring must show every conjugate unit')
    rule = p['rule']
    if rule == 'trap':
        targets = {(i, digit) for i in cs if i not in cells and digit in cs[i]
                   and all(_b.PEERS[i] & group for group in groups)}
    elif rule == 'wrap':
        bad = _b._integer(p['badColor'], 2, 'bad color')
        _b._require(any(_b.PEERS[i] & (groups[bad] - {i}) for i in groups[bad]),
                    'Color Wrap needs two same-color cells sharing a unit')
        targets = {(i, digit) for i in groups[bad]}
    else:
        raise ValueError('Unknown simple-coloring rule')
    return targets, {_b._frame(kind, n) for kind, n in frame_units}, _b._labels(cs, cells, {digit})


def _remote_pairs(p, cs):
    cells = _b._cells(p['cells'])
    digits = _b._digits(p['digits'], 2)
    _b._require(len(cells) >= 4 and len(cells) % 2 == 0,
                'Remote Pairs needs an even path of at least four cells')
    _b._require(all(cs.get(i) == digits for i in cells), 'Remote Pair cells must share one bivalue set')
    _b._require(all(b in _b.PEERS[a] for a, b in zip(cells, cells[1:])),
                'Every consecutive Remote Pair cell must see the next')
    _b._require(cells[-1] not in _b.PEERS[cells[0]], 'Remote Pair endpoints must not see each other')
    # Consecutive bivalue cells alternate the two digits, so an even path has
    # opposite endpoint values. Extra peer edges do not change that implication.
    targets = set().union(*(_b._common(cs, [cells[0], cells[-1]], d) for d in digits))
    return targets, _b._cell_frames(cells), _b._labels(cs, cells)


def _local_issues(grid, cs):
    """Concrete Sudoku contradictions, without completion search or solutions."""
    issues = [{'kind': 'empty-cell', 'cell': i} for i, ds in cs.items() if not ds]
    for index, unit in enumerate(_b.UNITS):
        kind, n = ('row', 'column', 'box')[index // 9], index % 9
        for d in _b.DIGITS:
            filled = sum(grid[i] == d for i in unit)
            if filled > 1:
                issues.append({'kind': 'duplicate', 'unit': kind, 'unitIndex': n, 'digit': d})
            elif not filled and not _b._live(cs, unit, d):
                issues.append({'kind': 'missing-digit', 'unit': kind, 'unitIndex': n, 'digit': d})
    return issues


def _witness(raw, issues):
    _b._require(type(raw) is dict, 'A contradictory trial needs a concrete witness')
    if raw.get('kind') == 'empty-cell':
        _b._integer(raw['cell'], 81, 'empty cell')
        _b._require(set(raw) == {'kind', 'cell'}, 'Invalid empty-cell witness')
    else:
        _b._require(raw.get('kind') in ('missing-digit', 'duplicate'),
                    'Unsupported contradiction witness')
        _b._unit(raw)
        _b._integer(raw['digit'], 10, 'contradiction digit', 1)
        _b._require(set(raw) == {'kind', 'unit', 'unitIndex', 'digit'},
                    'Invalid unit contradiction witness')
    _b._require(raw in issues, 'Declared contradiction is not present in the trial')


def _trials(e, grid, cs, targets):
    branches = e['branches']
    _b._require(type(branches) is list and branches and
                all(type(b) is list and b for b in branches), 'Missing exhaustive trials')
    outcomes = e.get('branchOutcomes', [{'kind': 'valid'} for _ in branches])
    _b._require(type(outcomes) is list and len(outcomes) == len(branches),
                'Each trial needs exactly one declared outcome')
    starts = [_b._choice(b[0]) for b in branches]
    root = starts[0][0]
    _b._require(all(i == root for i, d in starts) and len(starts) == len(set(starts))
                and {d for i, d in starts} == cs.get(root, set()),
                'Trials must exhaust every original candidate of one founding cell')
    valid = 0
    for branch, outcome in zip(branches, outcomes):
        _b._require(type(outcome) is dict and outcome.get('kind') in ('valid', 'contradiction'),
                    'Unknown trial outcome')
        state, current, issues = grid.copy(), cs, []
        for n, choice in enumerate(branch):
            _b._require(not issues, 'A trial must stop at its first local contradiction')
            i, d = _b._choice(choice)
            _b._require(d in current.get(i, ()), 'Trial fill is not available')
            if n:
                _b._require((i, d) in _b._forced(state, current),
                            'Only the founding move may be a guess')
            state[i] = d
            current = _b._candidates(state)
            issues = _local_issues(state, current)
        if outcome['kind'] == 'contradiction':
            _b._require(set(outcome) == {'kind', 'witness'}, 'Invalid contradiction outcome')
            _witness(outcome['witness'], issues)
        else:
            _b._require(set(outcome) == {'kind'} and not issues,
                        'Valid trial has an unexplained contradiction')
            valid += 1
            for i, d in targets:
                _b._require(state[i] != d and d not in current.get(i, ()),
                            'A valid trial must exclude every target')
    _b._require(valid, 'At least one exhaustive trial must remain locally consistent')


def validate_pattern(slug, e):
    """Validate named premises, complete eliminations, native reveal and trials."""
    try:
        _b._require(slug in SLUGS and type(e) is dict, 'Unknown advanced technique or fixture')
        if 'slug' in e:
            _b._require(e['slug'] == slug, 'Fixture slug mismatch')
        text = e['grid']
        _b._require(type(text) is str and re.fullmatch(r'[0-9]{81}', text), 'Invalid grid')
        grid = list(map(int, text))
        cs = _b._candidates(grid)
        _b._consistent(grid, cs)
        _b._require(not _b._forced(grid, cs), 'Advanced root must have zero singles')
        p = e['pattern']
        _b._require(type(p) is dict, 'Named premises required')
        if slug.endswith('quadruple'):
            targets, frames, labels = _quadruple(slug, p, cs)
        elif slug in ('jellyfish', 'finned-x-wing', 'finned-swordfish', 'finned-jellyfish'):
            targets, frames, labels = _fish(slug, p, cs)
        elif slug == 'simple-coloring':
            targets, frames, labels = _coloring(p, cs)
        else:
            targets, frames, labels = _remote_pairs(p, cs)
        _b._require(targets, 'Pattern must eliminate a candidate')
        claimed = [_b._choice(t) for t in e['targets']]
        _b._require(len(claimed) == len(set(claimed)) and set(claimed) == targets,
                    'Targets must be all and only named-rule eliminations')
        if 'eliminations' in p:
            recorded = [_b._choice(t) for t in p['eliminations']]
            _b._require(len(recorded) == len(set(recorded)) and set(recorded) == targets,
                        'Recorded eliminations differ from derived targets')
        _b._appearance(e['frames'], frames, 4, 'Reveal frames')
        _b._appearance(e['labels'], labels, 3, 'Reveal labels')
        _trials(e, grid, cs, targets)
    except (KeyError, TypeError, IndexError, AttributeError) as error:
        raise ValueError('Malformed advanced pattern fixture') from error
