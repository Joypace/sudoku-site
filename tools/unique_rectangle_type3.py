"""UR3 virtual naked-pair profile, not all UR Type3 subsets.

Two floors exactly XY; two non-diagonal roofs contain XY plus nonempty extras.
The UNION of roof extras is exactly E={a,b}. One actual bivalue E partner and
both roofs lie in one declared house. Unique-root reasoning supplies a virtual
E placement in the roofs; together with the partner it reserves both E digits.

Inject canonical intermediate_proofs as base, unique_rectangle as rectangle,
and unique_rectangle_type2 as ur2 (only its structural conditional_swap).
No solution payload, branch counting, nested guesses or warning claim.
"""
from copy import deepcopy
import re


def derive(p,cs,*,base,rectangle):
    b=base
    b._require(type(p) is dict and type(p.get('type')) is int and p['type']==3
               and p.get('profile')=='virtual-naked-pair','Bounded UR3 virtual-pair profile required')
    rows=rectangle._indices(p['rows'],2,'rectangle rows');cols=rectangle._indices(p['columns'],2,'rectangle columns')
    corners=[r*9+c for r in rows for c in cols]
    b._require(b._cells(p['corners'],4)==corners and all(i in cs for i in corners),'Four originally blank corners required')
    boxes=sorted({i//27*3+i%9//3 for i in corners})
    b._require(len(boxes)==2 and rectangle._indices(p['boxes'],2,'rectangle boxes')==boxes,'Exactly two boxes required')
    roofs=b._cells(p['roofs'],2);floors=b._cells(p['floors'],2)
    b._require(roofs==sorted(roofs) and floors==sorted(floors) and not set(roofs)&set(floors)
               and set(roofs)|set(floors)==set(corners),'Roof/floor partition required')
    b._require(roofs[0]//9==roofs[1]//9 or roofs[0]%9==roofs[1]%9,'Roofs must be non-diagonal')
    pair=b._digits(p['digits'],2);extras=b._digits(p['extraDigits'],2)
    b._require(not pair&extras,'Extras must be outside XY')
    b._require(all(cs[i]==pair for i in floors) and all(pair<cs[i] for i in roofs),'Exact XY floors and expanded XY roofs required')
    actual=set().union(*(cs[i]-pair for i in roofs))
    b._require(actual==extras,'Declare exactly the complete two-digit roof-extra union')
    partner=b._integer(p['partner'],81,'real subset partner')
    unit=b._unit(p)
    b._require(partner not in corners and partner in cs and cs[partner]==extras
               and set(roofs)|{partner}<=unit,'One exact bivalue extra partner in a shared house required')
    common_units=[(n,u) for n,u in enumerate(b.UNITS) if set(roofs)|{partner}<=u]
    scope=set().union(*(u for n,u in common_units))-set(corners)-{partner}
    targets={(i,d) for i in scope for d in cs.get(i,set())&extras}
    b._require(targets,'Virtual subset must eliminate a candidate')
    frames=b._cell_frames(corners)|{b._frame(('row','column','box')[n//9],n%9) for n,u in common_units}
    labels=b._labels(cs,set(corners)|{partner})
    choices=[[i,d] for i in roofs for d in sorted(cs[i]-pair)]
    return targets,frames,labels,choices


def coverage(raw,expected,b):
    b._require(type(raw) is dict and set(raw)=={'kind','choices'} and
               raw['kind']=='roof-extras-disjunction','Explicit roof-extra disjunction required')
    choices=raw['choices'];b._require(type(choices) is list and 2<=len(choices)<=4,'Two to four explicit roof-extra choices required')
    for q in choices:b._choice(q)
    b._require(choices==expected,'Cover every different roof-extra literal exactly once')


def trials(e,grid,cs,targets,choices,*,base):
    b=base
    b._require(e.get('proofMode')=='uniqueness-roof-extras-disjunction','Wrong UR3 proof mode')
    coverage(e['coverage'],choices,b)
    branches=e['branches'];b._require(type(branches) is list and len(branches)==len(choices)
                                     and all(type(x) is list and x for x in branches),'One trial per disjunct required')
    b._require([list(b._choice(branch[0])) for branch in branches]==choices,'Founding guesses must match different roof extras')
    b._require(e.get('branchOutcomes')==[{'kind':'valid'} for _ in choices],'Initial profile permits only valid guest boards')
    for branch in branches:
        state=grid.copy();current=cs
        for n,raw in enumerate(branch):
            i,d=b._choice(raw);b._require(d in current.get(i,()),'Unavailable trial fill')
            if n:b._require((i,d) in b._forced(state,current),'Only the founding roof-extra fill may be a guess')
            state[i]=d;current=b._candidates(state);b._consistent(state,current)
        b._require(all(state[i]!=d and d not in current.get(i,()) for i,d in targets),'Every disjunct must oppose every target')


def validate(e,*,base,rectangle,ur2,unique_root):
    b=base
    try:
        b._require(type(e) is dict and e.get('slug','unique-rectangle-type-3')=='unique-rectangle-type-3','Wrong UR3 namespace')
        text=e['grid'];b._require(type(text) is str and re.fullmatch(r'[0-9]{81}',text),'Invalid original shared grid')
        grid=list(map(int,text));cs=b._candidates(grid);b._consistent(grid,cs)
        b._require(not b._forced(grid,cs),'Root must start at zero ordinary singles')
        premise=e['uniquenessPremise']
        b._require(type(premise) is dict and set(premise)=={'kind','solutionCount'} and premise['kind']=='unique-root'
                   and type(premise['solutionCount']) is int and premise['solutionCount']==1,'Typed unique-root premise required')
        if 'solutionCount' in e:b._require(type(e['solutionCount']) is int and e['solutionCount']==1,'No two original solutions claim')
        targets,frames,labels,choices=derive(e['pattern'],cs,base=b,rectangle=rectangle)
        unique_root(text)  # ONLY the original shared root; never the alternatives.
        ur2.conditional_swap(e['pattern'],grid,rectangle=rectangle)
        for raw in [e['targets']]+([e['pattern']['eliminations']] if 'eliminations' in e['pattern'] else []):
            b._require(type(raw) is list,'Targets list required');claimed=[b._choice(q) for q in raw]
            b._require(len(claimed)==len(set(claimed)) and set(claimed)==targets,'All and only all-common-house subset targets required')
        b._appearance(e['frames'],frames,4,'UR3 reveal frames');b._appearance(e['labels'],labels,3,'UR3 reveal labels')
        trials(e,grid,cs,targets,choices,base=b)
    except (KeyError,TypeError,IndexError,AttributeError) as error:
        raise ValueError('Malformed UR3 virtual-pair fixture') from error


def validate_story(data,e,*,common,base):
    """Keep common mutative binding unchanged; add actual retained-note assertions."""
    b=base;p=e['pattern'];checks=data.get('expected',{});count=len(e['branches'])
    b._require(2<=count<=4 and data.get('grid')==e['grid'] and data.get('final',[])==[],'Bounded guests and original shared root required')
    removals=[[i//9,i%9,d,False] for i,d in e['targets']]
    # All advertised initial corner/partner candidates stay written on Root.
    retained=[[r,c,d,True] for r,c,d in e['labels']]
    notes=checks.get('notes');b._require(type(notes) is list,'Actual notes list required')
    for q in notes:
        b._require(type(q) is list and len(q)==4,'Note quadruple required')
        b._integer(q[0],9,'note row');b._integer(q[1],9,'note column');b._integer(q[2],10,'note digit',1)
        b._require(type(q[3]) is bool,'Actual Boolean note flag required')
    b._require(notes==removals+retained,'Assert actual target removal and retained pattern notes')
    b._integer(checks.get('boards'),6,'board count',3)
    b._require(checks['boards']==count+1,'Exactly Root plus declared guests required')
    slots=checks.get('validSlots');b._require(type(slots) is list,'Valid slots list required')
    for slot in slots:b._integer(slot,count+1,'valid slot')
    b._require(slots==list(range(count+1)),'Every board must remain valid')
    for key in ('uniquenessWarnings','crowdedWarnings','invalidSlots'):
        b._require(checks.get(key,[])==[],'No hypothetical SDK warning assertion')
    presentation=data.get('presentation',{});premise=presentation.get('uniquenessPremise')
    b._require(type(premise) is dict and set(premise)=={'kind','solutionCount'} and premise['kind']=='unique-root'
               and type(premise['solutionCount']) is int and premise['solutionCount']==1
               and premise==e['uniquenessPremise'],'Typed displayed original uniqueness premise required')
    choices=e['coverage']['choices'];coverage(presentation.get('coverage'),choices,b)
    projected=deepcopy(data);projected['expected']['notes']=removals
    common.validate_story(projected,e,valid_slots=list(range(count+1)))
