"""Finite raw-candidate search certificates; no solver, answer oracle or UI claims.

validate(example): {grid:81 digits, tree:node}. A node has steps and end.
Steps: forced fill, atomic wave (all fills forced before the wave), or exclude
with a rejected proof under that assumption. Waves stop at their boundary.
Ends: open, solved, exact contradiction witness, or exhaustive decision children.
Decision digits supply the ONE explicit guess for their child. An exclusion's
proof likewise begins after its explicit choice assumption. Rejected means
local contradiction OR every alternative rejected, never just one child.
UI snapshots, history cues and Lightning provenance need separate native binding.
"""
import re
from collections import defaultdict

UNITS = [set(range(r*9,r*9+9)) for r in range(9)] + [
    {r*9+c for r in range(9)} for c in range(9)] + [
    {(br*3+r)*9+bc*3+c for r in range(3) for c in range(3)}
    for br in range(3) for bc in range(3)]
PEERS = [set.union(*(u for u in UNITS if i in u))-{i} for i in range(81)]
DIGITS = set(range(1,10))

def require(ok, message):
    if not ok: raise ValueError(message)

def integer(v, lo, hi):
    require(type(v) is int and lo <= v < hi, 'Invalid integer coordinate')
    return v

def choice(q):
    require(type(q) is list and len(q)==2,'Invalid choice')
    return integer(q[0],0,81),integer(q[1],1,10)

def candidates(grid, removed=frozenset()):
    return {i:DIGITS-{grid[j] for j in PEERS[i]}-{d for j,d in removed if j==i}
            for i,v in enumerate(grid) if not v}

def forced(grid, cs):
    found={(i,next(iter(ds))) for i,ds in cs.items() if len(ds)==1}
    for u in UNITS:
        for d in DIGITS-{grid[i] for i in u}:
            homes=[i for i in u if d in cs.get(i,set())]
            if len(homes)==1: found.add((homes[0],d))
    return found

def contradictions(grid, cs):
    result=[]
    for n,u in enumerate(UNITS):
        for d in DIGITS:
            cells=sorted(i for i in u if grid[i]==d)
            if len(cells)>1: result.append({'kind':'duplicate','unit':n,'digit':d,'cells':cells})
        for d in DIGITS-{grid[i] for i in u}:
            if not any(d in cs.get(i,set()) for i in u):
                result.append({'kind':'missing-digit','unit':n,'digit':d})
    result.extend({'kind':'empty-cell','cell':i} for i,s in cs.items() if not s)
    claims=defaultdict(set)
    for i,d in forced(grid,cs):
        r,c=divmod(i,9)
        for k in [(0,r,c),(1,r,d-1),(2,c,d-1),(3,r//3*3+c//3,d-1)]:claims[k].add((i,d))
    crowded=[list(k) for k,v in sorted(claims.items()) if len(v)>1]
    if crowded: result.append({'kind':'crowded','constraints':crowded})
    return result

def _typed_witness(w):
    require(type(w) is dict,'Missing contradiction witness')
    kind=w.get('kind')
    if kind=='empty-cell':
        require(set(w)=={'kind','cell'},'Invalid witness fields');integer(w['cell'],0,81)
    elif kind in ('missing-digit','duplicate'):
        require(set(w)==({'kind','unit','digit','cells'} if kind=='duplicate' else {'kind','unit','digit'}),'Invalid witness fields')
        integer(w['unit'],0,27);integer(w['digit'],1,10)
        if kind=='duplicate':
            require(type(w['cells']) is list,'Invalid duplicate cells')
            for i in w['cells']:integer(i,0,81)
    elif kind=='crowded':
        require(set(w)=={'kind','constraints'} and type(w['constraints']) is list,'Invalid crowded witness')
        for row in w['constraints']:
            require(type(row) is list and len(row)==3,'Invalid constraint')
            integer(row[0],0,4);integer(row[1],0,9);integer(row[2],0,9)
    else: raise ValueError('Unsupported contradiction witness')

class _Audit:
    def __init__(self, max_nodes, max_steps):
        self.nodes=0;self.steps=0;self.max_nodes=max_nodes;self.max_steps=max_steps
    def node(self,node,grid,removed,depth=0):
        self.nodes+=1
        require(self.nodes<=self.max_nodes and depth<=81,'Certificate node/depth budget exceeded')
        require(type(node) is dict and set(node)=={'steps','end'} and type(node['steps']) is list,'Malformed node')
        grid=grid.copy();removed=set(removed)
        for step in node['steps']:
            self.steps+=1;require(self.steps<=self.max_steps,'Certificate step budget exceeded')
            cs=candidates(grid,removed)
            require(not contradictions(grid,cs),'Stop at first contradiction')
            require(type(step) is dict,'Invalid step')
            if step.get('do')=='wave':
                require(set(step)=={'do','fills'} and type(step['fills']) is list and step['fills'],'Invalid atomic wave')
                fills=[choice(q) for q in step['fills']]
                require(len({i for i,d in fills})==len(fills),'Wave cells must be distinct')
                proved=forced(grid,cs)
                require(all(q in proved for q in fills),'Every wave fill must be forced in the SAME pre-wave state')
                self.steps+=len(fills)-1
                require(self.steps<=self.max_steps,'Certificate step budget exceeded')
                for i,d in fills:grid[i]=d
                continue
            i,d=choice(step['choice'])
            require(d in cs.get(i,set()),'Choice unavailable in contextual state')
            if step.get('do')=='fill':
                require(set(step)=={'do','choice'} and (i,d) in forced(grid,cs),'Every non-guess fill must be forced')
                grid[i]=d
            elif step.get('do')=='exclude':
                require(set(step)=={'do','choice','proof'},'Invalid exclusion')
                assumed=grid.copy();assumed[i]=d
                require(self.node(step['proof'],assumed,removed,depth+1)=='rejected','Exclusion needs rejected assumption subtree')
                removed.add((i,d))
            else: raise ValueError('Unsupported step')
        cs=candidates(grid,removed);bad=contradictions(grid,cs);end=node['end']
        require(type(end) is dict,'Invalid node end');kind=end.get('kind')
        if bad:
            require(kind=='contradiction' and set(end)=={'kind','witness'},'Must declare first contradiction')
            _typed_witness(end['witness']);require(end['witness'] in bad,'False or incomplete contradiction witness')
            return 'rejected'
        if kind in ('open','solved'):
            require(set(end)=={'kind'},'Unexpected end fields')
            if kind=='solved':require(not cs,'Solved claim must fill every cell')
            return kind
        require(kind=='decision' and set(end)=={'kind','cell','children'},'Expected finite decision or honest open end')
        require(not forced(grid,cs),'Decision must be Dilemma with zero singles')
        i=integer(end['cell'],0,81);require(i in cs,'Decision cell must be blank')
        children=end['children'];require(type(children) is list and children,'Missing alternatives')
        for child in children:
            require(type(child) is dict and set(child)=={'digit','node'},'Malformed alternative');integer(child['digit'],1,10)
        digits=[ch['digit'] for ch in children]
        require(len(set(digits))==len(digits) and set(digits)==cs[i],'Exhaust every contextual candidate exactly once')
        results=[]
        for ch in children:
            assumed=grid.copy();assumed[i]=ch['digit']
            results.append(self.node(ch['node'],assumed,removed,depth+1))
        return 'rejected' if all(r=='rejected' for r in results) else 'solved' if 'solved' in results else 'open'

def validate(example, *, max_nodes=512, max_steps=4096):
    """Return certified outcome/counts. No uniqueness or native diagnostic inference."""
    try:
        require(type(example) is dict,'Expected example')
        text=example['grid'];require(type(text) is str and re.fullmatch('[0-9]{81}',text),'Expected 81 givens')
        integer(max_nodes,1,10001);integer(max_steps,1,100001)
        grid=list(map(int,text));cs=candidates(grid)
        require(not contradictions(grid,cs) and not forced(grid,cs),'Root must be consistent Dilemma with zero singles')
        audit=_Audit(max_nodes,max_steps);outcome=audit.node(example['tree'],grid,set())
        return {'outcome':outcome,'nodes':audit.nodes,'steps':audit.steps}
    except (KeyError,TypeError,IndexError,AttributeError,RecursionError) as exc:
        raise ValueError('Malformed finite search certificate') from exc
