"""Bounded UR4: two independent uniqueness refutations, no live union.

Canonical dependencies injected: intermediate_proofs (base), unique_rectangle
(rectangle), original unique_root callback. Root count never examines trials.
Both roofs must contain XY plus1..2 actual extras; floors exactly XY. A named
house contains both roofs and has exactly those two live positions of X.
Both roof-Y candidates are targets. Core warning timing is a SEPARATE gate.
"""
import re


def derive(p,cs,*,base,rectangle):
    b=base
    b._require(type(p) is dict and type(p.get('type')) is int and p['type']==4,'UR Type4 required')
    rows=rectangle._indices(p['rows'],2,'rectangle rows');cols=rectangle._indices(p['columns'],2,'rectangle columns')
    corners=[r*9+c for r in rows for c in cols]
    b._require(b._cells(p['corners'],4)==corners and all(i in cs for i in corners),'Four originally blank corners required')
    boxes=sorted({i//27*3+i%9//3 for i in corners})
    b._require(len(boxes)==2 and rectangle._indices(p['boxes'],2,'rectangle boxes')==boxes,'Exactly two boxes required')
    roofs=b._cells(p['roofs'],2);floors=b._cells(p['floors'],2)
    b._require(roofs==sorted(roofs) and floors==sorted(floors) and not set(roofs)&set(floors)
               and set(roofs)|set(floors)==set(corners),'Exact roof/floor partition required')
    b._require(roofs[0]//9==roofs[1]//9 or roofs[0]%9==roofs[1]%9,'Non-diagonal roofs required')
    pair=b._digits(p['digits'],2);strong=b._integer(p['strongDigit'],10,'strong UR digit',1)
    b._require(strong in pair,'Strong digit must be in UR pair')
    b._require(all(cs[i]==pair for i in floors) and all(pair<cs[i] and len(cs[i])<=4 for i in roofs),'Exact XY floors and bounded expanded XY roofs required')
    unit=b._unit(p)
    b._require(set(roofs)<=unit and b._live(cs,unit,strong)==set(roofs),'Strong UR digit must occur ONLY at both roofs in its declared house')
    b._require(b._cells(p['strongPositions'],2)==roofs,'Declare the complete actual strong-unit positions')
    rejected=next(iter(pair-{strong}));targets={(i,rejected) for i in roofs}
    return targets,b._cell_frames(corners)|{b._frame(p['unit'],p['unitIndex'])},b._labels(cs,corners)


def coverage(raw,targets,b):
    expected=[list(q) for q in sorted(targets)]
    b._require(type(raw) is dict and set(raw)=={'kind','choices'} and raw['kind']=='each-target-refuted','Independent per-target refutations required')
    choices=raw['choices'];b._require(type(choices) is list and len(choices)==2,'Exactly both roof-Y targets required')
    for q in choices:b._choice(q)
    b._require(choices==expected,'Cover each different roof-Y target exactly once')
    return expected


def trials(e,grid,cs,targets,*,base,rectangle):
    b=base;p=e['pattern']
    b._require(e.get('proofMode')=='independent-uniqueness-refutations','Not a shared-valid or one-founder exhaustive proof')
    choices=coverage(e['coverage'],targets,b)
    branches=e['branches'];b._require(type(branches) is list and len(branches)==2 and all(type(x) is list and len(x)==4 for x in branches),'Each independent trial fills exactly four corners')
    b._require([list(b._choice(branch[0])) for branch in branches]==choices,'Each rejected roof-Y must found its own trial')
    witness={'kind':'rectangle-digit-swap','corners':p['corners'],'digits':p['digits']}
    b._require(e.get('branchOutcomes')==[{'kind':'uniqueness-contradiction','witness':witness} for _ in choices],'Use conditional swap witnesses, not ordinary invalidity or two actual solutions')
    for branch in branches:
        state=grid.copy();current=cs;visited=set()
        for n,raw in enumerate(branch):
            i,d=b._choice(raw)
            b._require(i in p['corners'] and i not in visited and d in current.get(i,()),'Each named corner must be available and filled exactly once')
            if n:b._require((i,d) in b._forced(state,current),'Only the rejected target assumption may be a guess')
            visited.add(i);state[i]=d;current=b._candidates(state);b._consistent(state,current)
        rectangle._rectangle_swap(p,state)
        # No all-target-opposed assertion: each board refutes ONLY its founder.


def validate(e,*,base,rectangle,unique_root):
    b=base
    try:
        b._require(type(e) is dict and e.get('slug','unique-rectangle-type-4')=='unique-rectangle-type-4','Wrong UR4 namespace')
        text=e['grid'];b._require(type(text) is str and re.fullmatch(r'[0-9]{81}',text),'Invalid original shared grid')
        grid=list(map(int,text));cs=b._candidates(grid);b._consistent(grid,cs)
        b._require(not b._forced(grid,cs),'Root must have zero ordinary singles')
        premise=e['uniquenessPremise']
        b._require(type(premise) is dict and set(premise)=={'kind','solutionCount'} and premise['kind']=='unique-root'
                   and type(premise['solutionCount']) is int and premise['solutionCount']==1,'Typed original-root uniqueness premise required')
        if 'solutionCount' in e:b._require(type(e['solutionCount']) is int and e['solutionCount']==1,'No two actual original solutions')
        targets,frames,labels=derive(e['pattern'],cs,base=b,rectangle=rectangle)
        unique_root(text)
        for raw in [e['targets']]+([e['pattern']['eliminations']] if 'eliminations' in e['pattern'] else []):
            b._require(type(raw) is list,'Targets list required');declared=[b._choice(q) for q in raw]
            b._require(len(declared)==len(set(declared)) and set(declared)==targets,'Eliminate exactly Y from BOTH roofs')
        b._appearance(e['frames'],frames,4,'UR4 reveal frames');b._appearance(e['labels'],labels,3,'UR4 reveal labels')
        trials(e,grid,cs,targets,base=b,rectangle=rectangle)
    except (KeyError,TypeError,IndexError,AttributeError) as error:
        raise ValueError('Malformed bounded UR4 fixture') from error


def validate_story(data,e,*,base,common,rectangle_stories):
    """UR4 coverage/retention additions to the unchanged owning UR1 story gate.

    Rejected guests may be overlaid for comparison. They independently refute
    their founders; this imposes no shared all-target-opposition requirement.
    """
    from copy import deepcopy
    b=base;checks=data.get('expected',{});presentation=data.get('presentation',{})
    b._require(data.get('grid')==e['grid'] and data.get('final',[])==[],
               'Keep original shared root without hidden final edits')
    coverage(presentation.get('coverage'),set(map(tuple,e['targets'])),b)
    b._integer(checks.get('boards'),4,'board count',3)
    slots=b._cells(checks.get('validSlots'),1)
    b._require(slots==[0],'Only Root is asserted valid; guests are rejected refutations')
    for key in ('crowdedWarnings','invalidSlots'):
        b._require(checks.get(key,[])==[],'Do not substitute ordinary or generic invalidity for uniqueness')
    targets=set(map(tuple,e['targets']))
    removals=[[i//9,i%9,d,False] for i,d in e['targets']]
    retained=[[r,c,d,True] for r,c,d in e['labels'] if (r*9+c,d) not in targets]
    notes=checks.get('notes');b._require(type(notes) is list,'Actual Root notes list required')
    for q in notes:
        b._require(type(q) is list and len(q)==4,'Typed note quadruple required')
        b._integer(q[0],9,'note row');b._integer(q[1],9,'note column');b._integer(q[2],10,'note digit',1)
        b._require(type(q[3]) is bool,'Actual Boolean note flag required')
    b._require(notes==removals+retained,'Remove only both roof-Y targets and retain other pattern notes')
    projected=deepcopy(data);projected['expected']['notes']=removals
    # Canonical owner calls common.validate_story(valid_slots=[0]) AND the
    # existing warning-view gate. Exact uniqueness groups, prefix completion
    # views, overlays, releases, strikes and timings keep the same contract.
    rectangle_stories.validate_story(projected,e,common,b,b._require)
