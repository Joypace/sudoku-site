"""Single-fin Hall-degenerate Sashimi Jellyfish profile.

Raw profile: four bases/covers; fin-base body 1..4; other bodies 2..4.
Every fin-free base subset must have at least as many cover neighbours;
at least one proper subset containing the fin-bearing base must be tight. Hall's condition certifies a full
base/cover matching and the fin-containing tight proper subset certifies fin-blocked degeneracy.
This broadens only the structural profile, not targets or trial admission.

A true target excludes the fin and occupies a cover: four base placements
would need three remaining covers, impossible. Full ordinary peer constraints
can only remove placements; matching alone does not certify SDK validity.

HoDoKu's primary page explicitly permits fin-free reduction to a Swordfish:
https://hodoku.sourceforge.net/en/tech_fishg.php (Sashiminess)
Independent smaller-pattern quality filtering remains the selector's job.
"""
import re
from itertools import combinations


def derive(p, cs, *, base):
    b = base
    b._require(type(p) is dict, 'Named premises required')
    orientation = p['orientation']
    b._require(orientation in ('rows', 'columns'), 'Invalid orientation')
    bases, covers = p['bases'], p['covers']
    for values in (bases, covers):
        b._require(type(values) is list and len(values) == 4, 'Four units required')
        for value in values:
            b._integer(value, 9, 'fish unit')
        b._require(len(set(values)) == 4, 'Repeated fish unit')
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
    b._require(1 <= sum(unit(i) == unit(fin) for i in body) <= 4,
               'Fin-bearing body needs one to four positions')
    for n in set(bases) - {unit(fin)}:
        b._require(2 <= sum(unit(i) == n for i in body) <= 4,
                   'Each nonfin base needs two to four body positions')
    tight = False
    reductions = []
    for size in range(1, 5):
        for subset in combinations(bases, size):
            neighbours = {cross(i) for i in body if unit(i) in subset}
            b._require(len(neighbours) >= size, 'Fin-free body violates Hall matching condition')
            if size < 4 and unit(fin) in subset and len(neighbours) == size:
                tight = True
                reductions.append({'bases': list(subset), 'covers': sorted(neighbours)})
    b._require(tight, 'No proper tight subset containing the fin-bearing base')
    if 'finFreeReduction' in p:
        chosen = p['finFreeReduction']
        b._require(type(chosen) is dict and set(chosen) == {'bases', 'covers'},
                   'Invalid declared fin-free reduction')
        for values in (chosen['bases'], chosen['covers']):
            b._require(type(values) is list and 1 <= len(values) <= 3,
                       'Reduction needs a proper subset')
            for value in values:
                b._integer(value, 9, 'reduction unit')
        b._require(chosen in reductions, 'Declared reduction is not a fin-containing tight subset')
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
            b._require(e['slug'] == 'sashimi-jellyfish', 'Wrong slug')
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
