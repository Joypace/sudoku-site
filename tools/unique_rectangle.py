"""Type 1 rectangle exclusion is conditional on an actually unique root.

A trial filling the four original-blank corners with the swap pair could not
extend to the unique solution: any completion would have a swapped partner.
Native uniqueness warnings are verified separately, never inferred here.
"""
from collections import Counter
import importlib.util
from pathlib import Path
import re
_spec=importlib.util.spec_from_file_location('_rectangle_candidate_rules',Path(__file__).with_name('intermediate_proofs.py'))
_b=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_b)

def _indices(raw, count, name):
    _b._require(type(raw) is list and len(raw) == count, f'Wrong {name} count')
    for n in raw:
        _b._integer(n, 9, name)
    _b._require(len(set(raw)) == count and raw == sorted(raw), f'Invalid {name}')
    return raw

def _rectangle(p, cs):
    _b._require(type(p['type']) is int and p['type'] == 1, 'Only Unique Rectangle Type 1 is supported')
    rows = _indices(p['rows'], 2, 'rectangle rows')
    cols = _indices(p['columns'], 2, 'rectangle columns')
    corners = [r * 9 + c for r in rows for c in cols]
    _b._require(_b._cells(p['corners'], 4) == corners and all(i in cs for i in corners),
                'All four rectangle corners must be originally blank')
    boxes = sorted({i // 27 * 3 + i % 9 // 3 for i in corners})
    _b._require(len(boxes) == 2 and _indices(p['boxes'], 2, 'rectangle boxes') == boxes,
                'A uniqueness rectangle must occupy exactly two boxes')
    pair = _b._digits(p['digits'], 2)
    roof = _b._integer(p['roof'], 81, 'rectangle roof')
    _b._require(roof in corners and all(cs[i] == pair for i in corners if i != roof),
                'The three non-roof corners must have exactly the swap pair')
    _b._require(pair < cs[roof], 'The roof must contain the swap pair and extra candidates')
    extras = cs[roof] - pair
    _b._require(_b._digits(p['extras'], len(extras)) == extras, 'Incorrect roof extra candidates')
    return {(roof, d) for d in pair}, _b._cell_frames(corners), _b._labels(cs, corners)

def _rectangle_swap(p, grid):
    corners, pair = p['corners'], set(p['digits'])
    _b._require(all(grid[i] in pair for i in corners), 'Rejected rectangle trial must fill all four swap corners')
    swapped = grid.copy()
    x, y = p['digits']
    for i in corners:
        swapped[i] = y if grid[i] == x else x
    # Every affected row, column and box must retain exactly its contributions;
    # all other cells (and every original given) remain fixed. Therefore ANY
    # completion extending the bad trial would have a distinct swapped partner.
    for unit in _b.UNITS:
        affected = set(corners) & unit
        if affected:
            _b._require(len(affected) == 2 and
                        Counter(grid[i] for i in affected) == Counter(swapped[i] for i in affected),
                        'Corner exchange does not preserve every affected unit')

def _trials(e,grid,cs,targets):
    p=e['pattern'];branches=e['branches'];outcomes=e['branchOutcomes']
    _b._require(type(branches) is list and branches and all(type(b) is list and b for b in branches),'Missing exhaustive rectangle trials')
    _b._require(type(outcomes) is list and len(outcomes)==len(branches),'Missing rectangle outcomes')
    starts=[_b._choice(b[0]) for b in branches]
    _b._require(all(i==p['roof'] for i,d in starts) and len(starts)==len(set(starts)) and {d for i,d in starts}==cs[p['roof']],'Trials must exhaust all roof candidates')
    for branch,outcome in zip(branches,outcomes):
        state=grid.copy();current=cs
        for n,raw in enumerate(branch):
            i,d=_b._choice(raw)
            _b._require(i in p['corners'] and d in current.get(i,()),'Rectangle fill is outside the named corners or unavailable')
            if n:_b._require((i,d) in _b._forced(state,current),'Only the founding move may be a guess')
            state[i]=d;current=_b._candidates(state);_b._consistent(state,current)
        if branch[0][1] in p['digits']:
            _rectangle_swap(p,state)
            _b._require(type(outcome) is dict and set(outcome)=={'kind','witness'},'Missing structural uniqueness witness')
            witness=outcome['witness'];_b._require(type(witness) is dict and set(witness)=={'kind','corners','digits'},'Invalid structural swap witness')
            _b._cells(witness['corners'],4);_b._digits(witness['digits'],2)
            _b._require(outcome=={'kind':'uniqueness-contradiction','witness':{'kind':'rectangle-digit-swap','corners':p['corners'],'digits':p['digits']}},'Use the conditional corner swap, not a local contradiction or two actual root solutions')
        else:
            _b._require(outcome=={'kind':'valid'},'Extra-candidate trials remain ordinary valid trials')
            _b._require(all(state[i]!=d and d not in current.get(i,()) for i,d in targets),'Extra-candidate trial must exclude the complete roof pair')

def validate_pattern(e,unique_root):
    """unique_root must raise unless this original root has exactly one solution."""
    try:
        _b._require(type(e) is dict and e.get('slug','unique-rectangle')=='unique-rectangle','Wrong uniqueness technique')
        text=e['grid'];_b._require(type(text) is str and re.fullmatch(r'[0-9]{81}',text),'Invalid grid')
        grid=list(map(int,text));cs=_b._candidates(grid);_b._consistent(grid,cs)
        _b._require(not _b._forced(grid,cs),'Rectangle root must have zero ordinary singles')
        premise=e['uniquenessPremise']
        _b._require(type(premise) is dict and set(premise)=={'kind','solutionCount'} and premise['kind']=='unique-root' and type(premise['solutionCount']) is int and premise['solutionCount']==1,'Explicit unique-root precondition required')
        if 'solutionCount' in e:_b._require(type(e['solutionCount']) is int and e['solutionCount']==1,'Wrong root solution-count annotation')
        unique_root(text)
        p=e['pattern'];_b._require(type(p) is dict,'Missing rectangle premises')
        targets,frames,labels=_rectangle(p,cs);claimed=[_b._choice(q) for q in e['targets']]
        _b._require(len(claimed)==len(set(claimed)) and set(claimed)==targets,'Remove all and only the roof swap pair')
        if 'eliminations' in p:
            recorded=[_b._choice(q) for q in p['eliminations']]
            _b._require(len(recorded)==len(set(recorded)) and set(recorded)==targets,'Recorded rectangle eliminations differ')
        _b._appearance(e['frames'],frames,4,'Rectangle reveal frames');_b._appearance(e['labels'],labels,3,'Rectangle reveal labels')
        _trials(e,grid,cs,targets)
    except (KeyError,TypeError,IndexError,AttributeError) as error:
        raise ValueError('Malformed Type 1 rectangle fixture') from error
