"""Single-fin Sashimi X-Wing with a complete 1+2 degenerate body.

Pass the existing intermediate_proofs module as ``base``. derive() accepts
synthetic masks for theorem tests; validate() always reconstructs raw candidates.
Official definition: https://hodoku.sourceforge.net/en/tech_fishfs.php
The fin-free body is degenerate. This implements only the 1+2 body profile,
not all Sashimi fish, and does not modify regular finned-fish admission.
"""
import re


def derive(p, cs, *, base):
    b = base
    b._require(type(p) is dict, 'Named premises required')
    orientation = p['orientation']
    b._require(orientation in ('rows', 'columns'), 'Invalid orientation')
    bases, covers = p['bases'], p['covers']
    for values in (bases, covers):
        b._require(type(values) is list and len(values) == 2, 'Two units required')
        for value in values:
            b._integer(value, 9, 'fish unit')
        b._require(len(set(values)) == 2, 'Repeated fish unit')
    d = b._integer(p['digit'], 10, 'fish digit', 1)
    row_based = orientation == 'rows'
    unit = (lambda i: i // 9) if row_based else (lambda i: i % 9)
    cross = (lambda i: i % 9) if row_based else (lambda i: i // 9)
    positions = {i for i in cs if unit(i) in bases and d in cs[i]}
    b._require(set(b._cells(p['positions'])) == positions, 'Incomplete base positions')
    fins = {i for i in positions if cross(i) not in covers}
    b._require(len(fins) == 1 and set(b._cells(p['fins'], 1)) == fins,
               'Exactly one actual fin required')
    fin = next(iter(fins))
    body = positions - fins
    b._require({cross(i) for i in body} == set(covers), 'Incomplete covers')
    b._require(sum(unit(i) == unit(fin) for i in body) == 1,
               'Fin-bearing base needs exactly one body position')
    b._require(sum(unit(i) != unit(fin) for i in body) == 2,
               'Other base needs both cover positions')
    box = b._integer(p['finBox'], 9, 'fin box')
    b._require(fin in b.UNITS[18 + box], 'Wrong fin box')
    targets = {(i, d) for i in cs if d in cs[i] and unit(i) not in bases
               and cross(i) in covers and i in b.PEERS[fin]}
    b._require(targets, 'No eliminations')
    kind = 'row' if row_based else 'column'
    frames = {b._frame(kind, n) for n in bases} | {b._frame('box', box)}
    return targets, frames, b._labels(cs, positions, {d})


def validate(e, *, base):
    """Raw-givens, valid-exhaustive-trial profile; uniqueness/UI remain separate."""
    b = base
    try:
        b._require(type(e) is dict, 'Fixture must be an object')
        if 'slug' in e:
            b._require(e['slug'] == 'sashimi-x-wing', 'Wrong slug')
        text = e['grid']
        b._require(type(text) is str and re.fullmatch(r'[0-9]{81}', text), 'Invalid grid')
        grid = list(map(int, text))
        cs = b._candidates(grid)
        b._consistent(grid, cs)
        b._require(not b._forced(grid, cs), 'Root must have zero ordinary singles')
        targets, frames, labels = derive(e['pattern'], cs, base=b)
        for raw in [e['targets']] + ([e['pattern']['eliminations']]
                                     if 'eliminations' in e['pattern'] else []):
            b._require(type(raw) is list, 'Targets must be a list')
            claimed = [b._choice(q) for q in raw]
            b._require(len(claimed) == len(set(claimed)) and set(claimed) == targets,
                       'Targets must be all and only derived eliminations')
        b._appearance(e['frames'], frames, 4, 'Reveal frames')
        b._appearance(e['labels'], labels, 3, 'Reveal labels')
        b._branches(e, grid, cs, targets)
    except (KeyError, TypeError, IndexError, AttributeError) as error:
        raise ValueError('Malformed Sashimi fixture') from error
