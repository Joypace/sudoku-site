"""BUG+1 follows from a verified unique root and global two-home parity.

Native ordinary-single traces are additional visible evidence. Their crowded
choice sets are verified separately from the conditional complement theorem.
"""
import importlib.util
from pathlib import Path
import re
_spec=importlib.util.spec_from_file_location('_bug_candidate_rules',Path(__file__).with_name('intermediate_proofs.py'))
_b=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_b)

def _bug(p, grid, cs):
    cell = _b._integer(p['cell'], 81, 'BUG extra cell')
    extra = _b._integer(p['digit'], 10, 'BUG extra digit', 1)
    _b._require(cell in cs and len(cs[cell]) == 3 and extra in cs[cell],
                'BUG+1 needs exactly one trivalue cell')
    _b._require(all(len(ds) == 2 for i, ds in cs.items() if i != cell),
                'Every other originally blank BUG cell must be bivalue')
    _b._require(set(_b._cells(p['cells'])) == set(cs), 'BUG proof must include every unsolved cell')
    pair = cs[cell] - {extra}
    _b._require(_b._digits(p['pair'], 2) == pair, 'Incorrect BUG residual pair')
    reduced = {i: ds - {extra} if i == cell else ds for i, ds in cs.items()}
    for unit in _b.UNITS:
        for d in _b.DIGITS - {grid[i] for i in unit}:
            _b._require(len(_b._live(reduced, unit, d)) == 2,
                        'Removing the extra candidate must leave exactly two homes for every missing unit digit')
    return {(cell, d) for d in pair}, {(0, 0, 9, 9)}, _b._labels(cs, cs)

def crowded_claims(grid,cs):
    claims={}
    for i,d in _b._forced(grid,cs):
        r,c=divmod(i,9)
        for key in [(0,r,c),(1,r,d-1),(2,c,d-1),(3,r//3*3+c//3,d-1)]:claims.setdefault(key,[]).append([i,d])
    return {k:sorted(v) for k,v in claims.items() if len(v)>1}

def crowded_constraints(grid,cs):
    return [list(k) for k in sorted(crowded_claims(grid,cs))]

def _constraint_ids(raw):
    _b._require(type(raw) is list,'Crowded constraints must be a list')
    result=[]
    for row in raw:
        _b._require(type(row) is list and len(row)==3,'Wrong constraint coordinates')
        _b._integer(row[0],4,'constraint kind');_b._integer(row[1],9,'constraint index');_b._integer(row[2],9,'constraint label')
        result.append(tuple(row))
    _b._require(len(result)==len(set(result)),'Repeated crowded constraint')
    return raw

def validate_pattern(e,unique_root):
    try:
        _b._require(type(e) is dict and e.get('slug','bug-plus-one')=='bug-plus-one','Wrong BUG technique')
        text=e['grid'];_b._require(type(text) is str and re.fullmatch(r'[0-9]{81}',text),'Invalid grid')
        grid=list(map(int,text));cs=_b._candidates(grid);_b._consistent(grid,cs)
        _b._require(not _b._forced(grid,cs),'BUG root must have zero ordinary singles')
        premise=e['uniquenessPremise'];_b._require(type(premise) is dict and set(premise)=={'kind','solutionCount'} and premise['kind']=='unique-root' and type(premise['solutionCount']) is int and premise['solutionCount']==1,'Verified unique-root premise required')
        if 'solutionCount' in e:_b._require(type(e['solutionCount']) is int and e['solutionCount']==1,'Wrong root solution-count annotation')
        unique_root(text);p=e['pattern'];targets,frames,labels=_bug(p,grid,cs)
        claimed=[_b._choice(q) for q in e['targets']];_b._require(len(claimed)==len(set(claimed)) and set(claimed)==targets,'Remove exactly the two non-extra choices')
        if 'eliminations' in p:
            recorded=[_b._choice(q) for q in p['eliminations']];_b._require(len(recorded)==len(set(recorded)) and set(recorded)==targets,'Recorded BUG eliminations differ')
        _b._appearance(e['frames'],frames,4,'BUG reveal frames');_b._appearance(e['labels'],labels,3,'BUG reveal labels')
        branches=e['branches'];outcomes=e['branchOutcomes'];warnings=e['nativeWarnings']
        _b._require(type(branches) is list and branches and all(type(b) is list and b for b in branches),'Missing visible BUG trials')
        _b._require(type(outcomes) is list and type(warnings) is list and len(branches)==len(outcomes)==len(warnings),'Missing mathematical or native outcomes')
        starts=[_b._choice(b[0]) for b in branches];_b._require(all(i==p['cell'] for i,d in starts) and len(starts)==len(set(starts)) and {d for i,d in starts}==cs[p['cell']],'Exhaust every exceptional-cell candidate')
        for branch,outcome,warning in zip(branches,outcomes,warnings):
            state=grid.copy();current=cs
            for n,raw in enumerate(branch):
                _b._require(not crowded_constraints(state,current),'Stop at the first crowded warning')
                i,d=_b._choice(raw);_b._require(d in current.get(i,()),'BUG trial fill is unavailable')
                if n:_b._require((i,d) in _b._forced(state,current),'Only the founding move may be a guess')
                state[i]=d;current=_b._candidates(state);_b._consistent(state,current)
            crowded=crowded_constraints(state,current)
            if branch[0][1]!=p['digit']:
                witness={'kind':'bug-complement','cell':p['cell'],'digit':p['digit']}
                _b._require(type(outcome) is dict and outcome=={'kind':'uniqueness-contradiction','witness':witness},'Bad pair choice uses the conditional global complement theorem')
                raw=outcome['witness'];_b._integer(raw['cell'],81,'BUG witness cell');_b._integer(raw['digit'],10,'BUG witness digit',1)
                _b._require(type(warning) is dict and set(warning)=={'kind','constraints'} and warning['kind']=='crowded','Native warning must be crowded, not an invented uniqueness group')
                _b._require(crowded and _constraint_ids(warning['constraints'])==crowded,'Declare all and only the actual crowded choice sets')
            else:
                _b._require(outcome=={'kind':'valid'} and warning=={'kind':'valid'} and not crowded,'Extra-value trial must remain ordinary valid')
                _b._require(all(state[i]!=d and d not in current.get(i,()) for i,d in targets),'Extra-value trial must exclude the full pair')
    except (KeyError,TypeError,IndexError,AttributeError) as error:
        raise ValueError('Malformed BUG+1 proof or visible trace') from error
