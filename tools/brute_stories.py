"""Bind visible normalized events to independently replayed finite-search proofs.

Coordinates are zero-based cells and digits 1..9. example={grid,events:[...]};
every event uses op, optional slot (must be active), optional after snapshot.
Guess/forced: choice. wave: fills. lightning: stages[{fills:...}].
strike: choice, proof (a brute_force node AFTER assuming that choice).
copy: source,slot. select:slot. undoDouble/redoDouble follow ordinary effects.
inspect is inert. overlay:source,target validates existing distinct slots only.
Snapshots: {grid:81digits,removed:[[i,d],...],status:'dilemma'/'definite'/
'invalid'/'solved',redoCue:null/{kind:'disc'/'ring',choice:[i,d]}}.
No automatic connection to native pointers is claimed: the owner must bind this
normalized event list to EXACT native scenario gestures and actual checkpoints.
"""
from dataclasses import dataclass,field
import importlib.util
from pathlib import Path
_spec=importlib.util.spec_from_file_location('brute_force_rules',Path(__file__).with_name('brute_force.py'))
b=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(b)

@dataclass
class Board:
    grid:list
    removed:set=field(default_factory=set)
    history:list=field(default_factory=list)
    position:int=0
    host:int|None=None
    def state(self):return self.grid.copy(),self.removed.copy()
    def restore(self,state):self.grid,self.removed=state[0].copy(),state[1].copy()
    def effect(self,before,kind,choice):
        self.history[self.position:]=[(before,self.state(),kind,list(choice))]
        self.position+=1

def status(board):
    cs=b.candidates(board.grid,board.removed)
    if b.contradictions(board.grid,cs):return 'invalid'
    if not cs:return 'solved'
    return 'definite' if b.forced(board.grid,cs) else 'dilemma'

def snapshot(board):
    cue=None
    if board.position<len(board.history):
        _,_,kind,choice=board.history[board.position]
        cue={'kind':'ring' if kind=='strike' else 'disc','choice':choice}
    return {'grid':''.join(map(str,board.grid)),'removed':[list(q) for q in sorted(board.removed)],'status':status(board),'redoCue':cue}

def validate_exclusion(grid,removed,choice,proof,*,max_nodes=512,max_steps=4096):
    """Context may have singles; a certified assumption subtree must reject q."""
    cs=b.candidates(grid,removed);b.require(not b.contradictions(grid,cs),'Cannot exclude after contradiction')
    i,d=b.choice(choice);b.require(d in cs.get(i,set()),'Excluded choice not live in contextual state')
    assumed=grid.copy();assumed[i]=d
    audit=b._Audit(max_nodes,max_steps)
    b.require(audit.node(proof,assumed,set(removed))=='rejected','Visible strike requires rejected contextual assumption subtree')
    return audit

def _fill(board,q,*,guess=False):
    i,d=b.choice(q);cs=b.candidates(board.grid,board.removed)
    b.require(not b.contradictions(board.grid,cs),'No fill past first warning')
    b.require(d in cs.get(i,set()),'Visible fill unavailable')
    if guess:b.require(status(board)=='dilemma','Guess must occur at Dilemma')
    else:b.require((i,d) in b.forced(board.grid,cs),'Visible non-guess fill must be forced')
    before=board.state();board.grid[i]=d;board.effect(before,'fill',q)

def _wave(board,fills):
    cs=b.candidates(board.grid,board.removed)
    b.require(not b.contradictions(board.grid,cs),'No wave past first warning')
    b.require(type(fills) is list and fills,'Empty Lightning wave')
    choices=[b.choice(q) for q in fills]
    b.require(len({i for i,d in choices})==len(choices),'Wave cells must be distinct')
    proved=b.forced(board.grid,cs)
    b.require(all(q in proved for q in choices),'Wave fills must be forced in SAME pre-wave state')
    # Commit atomically. History still records each genuine native fill action;
    # intermediate history snapshots need not be independent wave boundaries.
    for q in fills:
        before=board.state();i,d=q;board.grid[i]=d;board.effect(before,'fill',q)

def _history(board,forward):
    b.require(board.position<len(board.history) if forward else board.position>0,'History action unavailable')
    while True:
        if forward:
            board.restore(board.history[board.position][1]);board.position+=1
        else:
            board.position-=1;board.restore(board.history[board.position][0])
        if status(board)=='dilemma':break
        if (forward and board.position==len(board.history)) or (not forward and board.position==0):break

def _checkpoint(board,expected):
    b.require(type(expected) is dict and set(expected)=={'grid','removed','status','redoCue'},'Checkpoint must bind complete state and redo cue')
    raw=expected['removed'];b.require(type(raw) is list,'Invalid removed choices')
    for q in raw:b.choice(q)
    cue=expected['redoCue']
    if cue is not None:
        b.require(type(cue) is dict and set(cue)=={'kind','choice'} and cue['kind'] in ['ring','disc'],'Invalid cue');b.choice(cue['choice'])
    b.require(expected==snapshot(board),'Visible checkpoint differs from proved state/history cue')

def _flat_checkpoint(board,expected,slot,count):
    b.require(type(expected) is dict,'Missing native checkpoint')
    fills=expected.get('fills');notes=expected.get('notes')
    b.require(type(fills) is list and len(fills)==81 and all(type(v) is int for v in fills),'Invalid native fills')
    b.require(fills==[v-1 if v else -1 for v in board.grid],'Native checkpoint fills differ')
    b.require(type(notes) is list and len(notes)==729 and all(type(v) is bool for v in notes),'Invalid native note mask')
    b.require(notes==[(i,d) not in board.removed for i in range(81) for d in range(1,10)],'Native checkpoint notes differ from contextual exclusions')
    b.require(expected.get('status')==status(board),'Native checkpoint status differs')
    b.require(type(expected.get('boards')) is int and expected['boards']==count,'Native board count differs')
    b.require(expected.get('canUndo') is (board.position>0) and expected.get('canRedo') is (board.position<len(board.history)),'Native history availability differs')
    cue=snapshot(board)['redoCue'];native=expected.get('redo')
    if cue is None:b.require(native is None,'Unexpected native redo cue')
    else:
        i,d=cue['choice'];action={'id':'DELETE_NOTE' if cue['kind']=='ring' else 'SET_FILL','choice':{'row':i//9,'col':i%9,'label':d-1},'slot':slot}
        b.require(type(native) is dict and native=={'kind':cue['kind'],'action':action},'Native redo ring/disc/action differs')
        a=native['action'];b.integer(a['slot'],0,6)
        b.integer(a['choice']['row'],0,9);b.integer(a['choice']['col'],0,9);b.integer(a['choice']['label'],0,9)
    if 'crowdedConstraints' in expected:
        actual=next((w['constraints'] for w in b.contradictions(board.grid,b.candidates(board.grid,board.removed)) if w['kind']=='crowded'),[])
        b.require(expected['crowdedConstraints']==actual,'Native crowded constraint memberships differ')

def _native_checkpoint(boards,expected,active,global_effect=False):
    if type(expected.get('boards')) is not list:
        b.require(len(boards)==1,'Legacy flat checkpoints cannot certify copied boards')
        return _flat_checkpoint(boards[active],expected,active,len(boards))
    rows=expected['boards']
    b.require(type(expected.get('boardCount')) is int and expected['boardCount']==len(boards),'Native occupied board count differs')
    b.require(type(expected.get('displaySlot')) is int and expected['displaySlot']==active,'Native display slot differs')
    slots=[]
    for row in rows:
        b.require(type(row) is dict,'Invalid native board snapshot');slot=b.integer(row['slot'],0,6);slots.append(slot)
        b.require(slot in boards,'Unexpected native board slot')
        board=boards[slot];cs=b.candidates(board.grid,board.removed)
        # Reuse exact fill/note/status checks, while global history is handled
        # only once below and never inferred from a copied board's local cursor.
        flat={**row,'boards':len(boards),'canUndo':board.position>0,'canRedo':board.position<len(board.history),'redo':None}
        cue=snapshot(board)['redoCue']
        if cue:
            i,d=cue['choice'];flat['redo']={'kind':cue['kind'],'action':{'id':'DELETE_NOTE' if cue['kind']=='ring' else 'SET_FILL','choice':{'row':i//9,'col':i%9,'label':d-1},'slot':slot}}
        _flat_checkpoint(board,flat,slot,len(boards))
        b.require(type(row.get('valid')) is bool and row['valid']==(status(board)!='invalid'),'Native board validity differs')
        b.require(type(row.get('singles')) is int and row['singles']==len(b.forced(board.grid,cs)),'Native single-choice count differs')
        host=row.get('host')
        if host is not None:b.integer(host,0,6)
        b.require(host==board.host,'Native overlay host differs')
        overlays=row.get('overlays');b.require(type(overlays) is list,'Missing native overlay memberships')
        for guest in overlays:b.integer(guest,0,6)
        b.require(len(overlays)==len(set(overlays)) and set(overlays)=={i for i,v in boards.items() if v.host==slot},'Native overlay memberships differ')
        starving=[]
        for i,ds in cs.items():
            if not ds:starving.append([0,i//9,i%9])
        for n,u in enumerate(b.UNITS):
            for d in b.DIGITS-{board.grid[i] for i in u}:
                if not any(d in cs.get(i,set()) for i in u):starving.append([1+n//9,n%9,d-1])
        b.require(sorted(row.get('starvingConstraints',[]))==sorted(starving),'Native starving constraints differ')
        b.require(row.get('uniquenessGroups')==[],'This ordinary search certificate cannot use native uniqueness-only rejection')
        warnings=row.get('warnings');b.require(type(warnings) is dict,'Missing native warning diagnostics')
        crowd=next((w['constraints'] for w in b.contradictions(board.grid,cs) if w['kind']=='crowded'),[])
        for name,value in [('crowded',len(crowd)),('starving',len(starving)),('uniqueness',0),('conflict',0),('warningCells',0),('conflictGroups',0)]:
            b.require(type(warnings.get(name)) is int and warnings[name]==value,'Native warning count differs: '+name)
    b.require(len(slots)==len(set(slots)) and set(slots)==set(boards),'Native snapshot must include ALL occupied boards exactly once')
    b.require(type(expected.get('canUndo')) is bool and type(expected.get('canRedo')) is bool,'Invalid global history flags')
    if len(boards)>1:
        b.require(expected['canUndo'] is global_effect and expected['canRedo'] is False and expected.get('redo') is None,'Copied flow global history flags differ')
    if len(boards)==1:
        board=boards[active];flat={**rows[0], 'boards':1,'canUndo':expected['canUndo'],'canRedo':expected['canRedo'],'redo':expected.get('redo')}
        _flat_checkpoint(board,flat,active,1)

def validate_events(example,*,max_events=2048,max_nodes=4096,max_steps=32768):
    try:
        text=example['grid'];b.require(type(text) is str and b.re.fullmatch('[0-9]{81}',text),'Expected raw givens')
        boards={0:Board(list(map(int,text)))};active=0
        b.require(status(boards[0])=='dilemma','Root must be consistent Dilemma')
        events=example['events'];b.require(type(events) is list and 0<len(events)<=max_events,'Invalid finite event list')
        nodes=steps=0;strikes=[];global_effect=False
        for event in events:
            b.require(type(event) is dict,'Invalid event');op=event['op']
            if op=='select':
                active=b.integer(event['slot'],0,6);b.require(active in boards and boards[active].host is None,'Select existing non-guest slot')
            elif op=='copy':
                source=b.integer(event['source'],0,6);slot=b.integer(event['slot'],0,6)
                b.require(source in boards and source==active and slot not in boards and boards[source].host is None,'Copy needs active source and fresh slot')
                original=boards[source];boards[slot]=Board(original.grid.copy(),original.removed.copy());active=slot
            elif op=='overlay':
                source=b.integer(event.get('source',event.get('slot')),0,6);target=b.integer(event.get('target',event.get('host',0)),0,6)
                b.require(source in boards and target in boards and source!=target and boards[target].host is None and not any(v.host==source for v in boards.values()),'Invalid overlay slots')
                boards[source].host=target;active=target
            elif op=='unstack':
                source=b.integer(event.get('source',event.get('slot')),0,6)
                b.require(source in boards and boards[source].host is not None,'Unstack needs an actual guest')
                host=event.get('host',event.get('target',boards[source].host));b.integer(host,0,6);b.require(host==boards[source].host,'Unstack host differs')
                active=boards[source].host;boards[source].host=None
            else:
                board=boards[active]
                if 'slot' in event:b.require(type(event['slot']) is int and event['slot']==active,'Event acts on wrong board')
                if op in ['guess','forced','wave','lightning','strike']:b.require(board.host is None,'Guest boards are not editable')
                if op in ['guess','forced']:_fill(board,event['choice'],guess=op=='guess')
                elif op=='wave':_wave(board,event['fills'])
                elif op=='lightning':
                    stages=event['stages'];b.require(type(stages) is list and stages,'Missing Lightning stages')
                    for stage in stages:
                        b.require(type(stage) is dict and set(stage)<= {'fills','after','status'} and 'fills' in stage,'Invalid Lightning stage')
                        _wave(board,stage['fills'])
                        if 'status' in stage:b.require(stage['status']==status(board),'Declared Lightning stage status differs')
                        if 'after' in stage:_checkpoint(board,stage['after'])
                    b.require(status(board)!='definite','Lightning must finish full forced propagation')
                elif op=='strike':
                    before=board.state();audit=validate_exclusion(board.grid,board.removed,event['choice'],event['proof'],max_nodes=max_nodes-nodes,max_steps=max_steps-steps)
                    nodes+=audit.nodes;steps+=audit.steps;b.require(nodes<=max_nodes and steps<=max_steps,'Aggregate proof budget exceeded')
                    q=b.choice(event['choice']);board.removed.add(q);board.effect(before,'strike',q);strikes.append({'slot':active,'choice':list(q)})
                elif op in ['undoDouble','redoDouble']:
                    b.require(len(boards)==1,'Copied-board flows cannot use per-board history traversal')
                    _history(board,op=='redoDouble')
                elif op=='inspect':pass
                else:raise ValueError('Unsupported visible event')
            if op in ['guess','forced','wave','lightning','strike','copy','overlay','unstack']:global_effect=True
            if 'after' in event:_checkpoint(boards[active],event['after'])
            if 'checkpoint' in event:_native_checkpoint(boards,event['checkpoint'],active,global_effect)
        if 'expectedStrikes' in example:b.require(example['expectedStrikes']==strikes,'Visible exclusions differ from declared targets')
        return {'active':active,'boards':{slot:snapshot(board) for slot,board in boards.items()},'strikes':strikes,'proofNodes':nodes,'proofSteps':steps}
    except (KeyError,TypeError,IndexError,AttributeError) as exc:
        raise ValueError('Malformed visible finite-search events') from exc
