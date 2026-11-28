"""HoDoKu two-component Multi Colors certificates.

Pass canonical Site intermediate_proofs as base and advanced_proofs as advanced.
pattern={digit,components:[{cells,edges,units,colors:[class0,class1]},...],
         rule:'type1'|'type2',interaction:[aClass,bClass] (type1) or [aClass] (type2)}.
Type2 rejects a class in component0 using both classes of component1.
Exactly two COMPLETE disconnected conjugate components, not arbitrary subpaths.
validate() is raw-givens + valid exhaustive founding-cell trials only; no native,
uniqueness, hidden pruning, or four-color App rendering is claimed.
"""
import re


def _component(raw, cs, digit, edges, units, b):
    b._require(type(raw) is dict, 'Component object required')
    cells = set(b._cells(raw['cells']))
    b._require(len(cells) >= 2 and all(digit in cs.get(i, ()) for i in cells),
               'Component needs live conjugate candidates')
    graph = {}
    for a, c in edges:
        graph.setdefault(a, set()).add(c); graph.setdefault(c, set()).add(a)
    reached, pending = set(), [min(cells)]
    while pending:
        i = pending.pop()
        if i not in reached:
            reached.add(i); pending.extend(graph.get(i, set()) - reached)
    b._require(reached == cells and all(i in graph for i in cells),
               'Declare one complete connected conjugate component')
    expected = {e for e in edges if e[0] in cells}
    b._require(type(raw['edges']) is list, 'Edges list required')
    declared = [tuple(sorted(b._cells(e, 2))) for e in raw['edges']]
    b._require(len(declared) == len(set(declared)) and set(declared) == expected,
               'All actual strong edges required')
    colors = raw['colors']
    b._require(type(colors) is list and len(colors) == 2, 'Two color classes required')
    groups = [set(b._cells(c)) for c in colors]
    b._require(all(groups) and not groups[0] & groups[1] and groups[0] | groups[1] == cells,
               'Color classes must partition the component')
    b._require(all((a in groups[0]) != (c in groups[0]) for a, c in expected),
               'Conjugate component must be bipartite')
    expected_units = {(('row','column','box')[n//9], n%9) for n,e in units if e in expected}
    b._require(type(raw['units']) is list, 'Strong units list required')
    declared_units = []
    for item in raw['units']:
        b._require(type(item) is list and len(item) == 2, 'Invalid strong unit')
        kind, n = item; b._frame(kind, n); declared_units.append((kind,n))
    b._require(len(declared_units) == len(set(declared_units)) and set(declared_units) == expected_units,
               'Every actual strong unit required')
    return cells, groups, {b._frame(kind,n) for kind,n in expected_units}


def derive(p, cs, *, base, advanced):
    b=base
    b._require(type(p) is dict, 'Named pattern required')
    digit=b._integer(p['digit'],10,'color digit',1)
    raw=p['components'];b._require(type(raw) is list and len(raw)==2,'Exactly two components required')
    edges,units=advanced._conjugates(cs,digit)
    a,ac,af=_component(raw[0],cs,digit,edges,units,b)
    c,bc,cf=_component(raw[1],cs,digit,edges,units,b)
    b._require(not a & c,'Components must be distinct and disconnected')
    interaction=p['interaction']
    b._require(type(interaction) is list,'Typed interaction classes required')
    rule=p['rule']
    b._require(rule in ('type1','type2'),'Unknown Multi Colors rule')
    b._require(len(interaction)==(2 if rule=='type1' else 1),'Wrong interaction arity')
    for v in interaction:b._integer(v,2,'interaction class')
    sees=lambda x,y:any(j in b.PEERS[i] for i in x for j in y)
    if rule=='type1':
        ai,bi=interaction
        b._require(sees(ac[ai],bc[bi]),'Type1 needs actual cross-component weak link')
        targets={(i,digit) for i in cs if i not in a|c and digit in cs[i]
                 and bool(b.PEERS[i]&ac[1-ai]) and bool(b.PEERS[i]&bc[1-bi])}
    else:
        ai=interaction[0]
        b._require(all(sees(ac[ai],group) for group in bc),
                   'Type2 class must see both opposite classes of other component')
        targets={(i,digit) for i in ac[ai]}
    b._require(targets,'Multi Colors must eliminate a candidate')
    return targets,af|cf,b._labels(cs,a|c,{digit})


def simple_coloring_whole_case(p, cs, targets, *, base, advanced, all_components=None):
    """Private quality check only; theorem validity never requires minimality."""
    wanted=set(map(tuple,targets));base._require(wanted,'Nonempty targets required')
    for component in (p['components'] if all_components is None else all_components):
        for rule in ('trap','wrap'):
            for bad in ([0,1] if rule=='wrap' else [None]):
                q={'digit':p['digit'],'component':component['cells'],'edges':component['edges'],
                   'units':component['units'],'colors':component['colors'],'rule':rule}
                if bad is not None:q['badColor']=bad
                try:derived,_,_=advanced._coloring(q,cs)
                except ValueError:continue
                if wanted<=derived:return {'component':component['cells'],'rule':rule,'targets':sorted(derived)}
    return None


def validate(e, *, base, advanced):
    b=base
    try:
        b._require(type(e) is dict,'Fixture object required')
        if 'slug' in e:b._require(e['slug']=='multi-coloring','Wrong slug')
        text=e['grid'];b._require(type(text) is str and re.fullmatch(r'[0-9]{81}',text),'Invalid grid')
        grid=list(map(int,text));cs=b._candidates(grid);b._consistent(grid,cs)
        b._require(not b._forced(grid,cs),'Root must have zero ordinary singles')
        targets,frames,labels=derive(e['pattern'],cs,base=b,advanced=advanced)
        for raw in [e['targets']]+([e['pattern']['eliminations']] if 'eliminations' in e['pattern'] else []):
            b._require(type(raw) is list,'Targets list required');claimed=[b._choice(q) for q in raw]
            b._require(len(claimed)==len(set(claimed)) and set(claimed)==targets,'All and only derived targets required')
        b._appearance(e['frames'],frames,4,'Reveal frames');b._appearance(e['labels'],labels,3,'Reveal labels')
        b._branches(e,grid,cs,targets)
    except (KeyError,TypeError,IndexError,AttributeError) as error:
        raise ValueError('Malformed Multi Colors fixture') from error
