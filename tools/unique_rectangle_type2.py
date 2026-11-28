"""UR Type2: unique-root roof-Z disjunction, not one-cell exhaustion.

Dependencies are injected canonical Site modules: intermediate_proofs (base),
unique_rectangle (rectangle), and unique_root(text), which MUST raise unless
that ORIGINAL raw root has exactly one solution. No answer payload is used.
"""
from copy import deepcopy
import re


def derive(p, cs, *, base, rectangle):
    b=base
    b._require(type(p) is dict and type(p.get('type')) is int and p['type']==2,'UR Type2 required')
    rows=rectangle._indices(p['rows'],2,'rectangle rows')
    cols=rectangle._indices(p['columns'],2,'rectangle columns')
    corners=[r*9+c for r in rows for c in cols]
    b._require(b._cells(p['corners'],4)==corners and all(i in cs for i in corners),'Four original blank rectangle corners required')
    boxes=sorted({i//27*3+i%9//3 for i in corners})
    b._require(len(boxes)==2 and rectangle._indices(p['boxes'],2,'rectangle boxes')==boxes,'Exactly two rectangle boxes required')
    pair=b._digits(p['digits'],2);z=b._integer(p['extra'],10,'roof extra',1)
    b._require(z not in pair,'Roof extra must differ from swap pair')
    roofs=b._cells(p['roofs'],2);floors=b._cells(p['floors'],2)
    b._require(roofs==sorted(roofs) and floors==sorted(floors) and set(roofs)|set(floors)==set(corners)
               and not set(roofs)&set(floors),'Roofs and floors must partition the rectangle')
    b._require(roofs[0]//9==roofs[1]//9 or roofs[0]%9==roofs[1]%9,'Type2 roofs must be non-diagonal')
    b._require(all(cs[i]==pair for i in floors) and all(cs[i]==pair|{z} for i in roofs),'Floors exactly XY and roofs exactly XYZ required')
    targets=b._common(cs,roofs,z,excluded=corners)
    b._require(targets,'Roof disjunction must eliminate a candidate')
    return targets,b._cell_frames(corners),b._labels(cs,corners)


def conditional_swap(p, grid, *, rectangle):
    """Structural conditional completion bijection; these are NOT two solutions."""
    for flip in (0,1):
        hypothetical=grid.copy()
        for r,row in enumerate(p['rows']):
            for c,col in enumerate(p['columns']):
                hypothetical[row*9+col]=p['digits'][(r+c+flip)%2]
        rectangle._rectangle_swap(p,hypothetical)


def trials(e, grid, cs, targets, *, base):
    b=base;p=e['pattern'];z=p['extra'];branches=e['branches']
    expected=[[i,z] for i in p['roofs']]
    coverage=e['coverage']
    b._require(type(coverage) is dict and set(coverage)=={'kind','choices'}
               and coverage['kind']=='roof-extra-disjunction','Explicit roof-Z disjunction required')
    b._require(type(coverage['choices']) is list,'Coverage choices list required')
    choices=[list(b._choice(q)) for q in coverage['choices']]
    b._require(choices==expected,'Cover both different roof-Z choices, not roof values')
    b._require(e.get('proofMode')=='uniqueness-disjunction','Uniqueness disjunction proof mode required')
    b._require(type(branches) is list and len(branches)==2 and all(type(x) is list and x for x in branches),'Exactly two roof alternatives required')
    b._require([list(b._choice(branch[0])) for branch in branches]==expected,'Each different roof must found its Z trial')
    b._require(e.get('branchOutcomes')==[{'kind':'valid'},{'kind':'valid'}],'No local-invalid, uniqueness-warning or two-solution claim')
    for branch in branches:
        state=grid.copy();current=cs
        for n,raw in enumerate(branch):
            i,d=b._choice(raw);b._require(d in current.get(i,()),'Trial choice unavailable')
            if n:b._require((i,d) in b._forced(state,current),'Only the founding roof-Z fill may be a guess')
            state[i]=d;current=b._candidates(state);b._consistent(state,current)
        b._require(all(state[i]!=d and d not in current.get(i,()) for i,d in targets),'Every alternative must oppose every target')


def validate(e, *, base, rectangle, unique_root):
    b=base
    try:
        b._require(type(e) is dict and e.get('slug','unique-rectangle-type-2')=='unique-rectangle-type-2','Wrong UR2 namespace')
        text=e['grid'];b._require(type(text) is str and re.fullmatch(r'[0-9]{81}',text),'Invalid original grid')
        grid=list(map(int,text));cs=b._candidates(grid);b._consistent(grid,cs)
        b._require(not b._forced(grid,cs),'Root must have zero ordinary singles')
        premise=e['uniquenessPremise']
        b._require(type(premise) is dict and set(premise)=={'kind','solutionCount'} and premise['kind']=='unique-root'
                   and type(premise['solutionCount']) is int and premise['solutionCount']==1,'Explicit unique original root required')
        if 'solutionCount' in e:b._require(type(e['solutionCount']) is int and e['solutionCount']==1,'No two actual original solutions claim')
        targets,frames,labels=derive(e['pattern'],cs,base=b,rectangle=rectangle)
        unique_root(text)  # Exactly one call, on the unmodified ORIGINAL root.
        conditional_swap(e['pattern'],grid,rectangle=rectangle)
        for raw in [e['targets']]+([e['pattern']['eliminations']] if 'eliminations' in e['pattern'] else []):
            b._require(type(raw) is list,'Targets list required');claimed=[b._choice(q) for q in raw]
            b._require(len(claimed)==len(set(claimed)) and set(claimed)==targets,'All and only common roof-Z targets required')
        b._appearance(e['frames'],frames,4,'Rectangle reveal frames');b._appearance(e['labels'],labels,3,'Rectangle reveal labels')
        trials(e,grid,cs,targets,base=b)
    except (KeyError,TypeError,IndexError,AttributeError) as error:
        raise ValueError('Malformed UR Type2 certificate') from error


def validate_story(data,e,*,common,base):
    """Project ONLY note expectations for unchanged common physical-input binding."""
    b=base;p=e['pattern'];checks=data.get('expected',{})
    b._require(data.get('grid')==e['grid'],'Story must use the original shared root')
    removals=[[i//9,i%9,d,False] for i,d in e['targets']]
    retention=[[i//9,i%9,p['extra'],True] for i in p['roofs']]
    notes=checks.get('notes')
    b._require(type(notes) is list,'Actual note assertions must be a list')
    for note in notes:
        b._require(type(note) is list and len(note)==4,'Actual note assertion needs four fields')
        b._integer(note[0],9,'note row');b._integer(note[1],9,'note column')
        b._integer(note[2],10,'note digit',1)
        b._require(type(note[3]) is bool,'Note state must be an actual boolean')
    b._require(notes==removals+retention,'Assert actual target removals AND both retained roof-Z notes')
    b._integer(checks.get('boards'),4,'board count',3)
    slots=checks.get('validSlots')
    b._require(type(slots) is list and len(slots)==3,'Exactly three valid slots required')
    for slot in slots:b._integer(slot,3,'valid board slot')
    b._require(slots==[0,1,2],'Root and both roof-Z guests must be valid')
    b._require(data.get('final',[])==[],'No hidden final edits')
    for key in ('uniquenessWarnings','crowdedWarnings','invalidSlots'):
        b._require(checks.get(key,[])==[],'UR2 alternatives do not claim warning boards')
    presentation=data.get('presentation',{})
    premise=presentation.get('uniquenessPremise')
    b._require(type(premise) is dict and set(premise)=={'kind','solutionCount'} and
               premise['kind']=='unique-root' and type(premise['solutionCount']) is int and
               premise['solutionCount']==1,'Presentation needs a typed unique-root premise')
    coverage=presentation.get('coverage')
    b._require(type(coverage) is dict and set(coverage)=={'kind','choices'} and
               coverage['kind']=='roof-extra-disjunction','Presentation needs exact disjunction coverage')
    choices=coverage['choices']
    b._require(type(choices) is list and len(choices)==2,'Presentation must cover exactly two roof choices')
    for q in choices:b._choice(q)
    b._require(premise==e['uniquenessPremise'] and coverage==e['coverage'],
               'Show the unique-root disjunction premise')
    b._require(len(e['frames'])==4 and len(e['labels'])==10,'Reveal four corners and ten actual candidates')
    projected=deepcopy(data);projected['expected']['notes']=removals
    common.validate_story(projected,e,valid_slots=[0,1,2])
