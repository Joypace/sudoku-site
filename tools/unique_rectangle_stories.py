"""Bind conditional swaps to exact native uniqueness-only warning groups."""
def validate_story(data,e,common,base,require):
    corners=e['pattern']['corners'];outcomes=e['branchOutcomes'];checks=data.get('expected',{})
    good=[0]+[n for n,o in enumerate(outcomes,1) if o['kind']=='valid']
    expected=[{'slot':n,'cells':corners} for n,o in enumerate(outcomes,1) if o['kind']=='uniqueness-contradiction']
    declared=checks.get('uniquenessWarnings')
    require(type(declared) is list,'Exact uniqueness groups must be checked by the native exporter')
    for group in declared:
        require(type(group) is dict and set(group)=={'slot','cells'},'Wrong uniqueness warning assertion')
        base._integer(group['slot'],len(outcomes)+1,'uniqueness warning slot',1);base._cells(group['cells'],4)
    require(declared==expected,'Assert only the intended four-corner group for each rejected trial')
    base._cells(checks.get('validSlots'))
    presentation=data.get('presentation',{});premise=presentation.get('uniquenessPremise')
    require(type(premise) is dict and premise==e['uniquenessPremise'] and type(premise.get('solutionCount')) is int,'Explain the verified unique-root premise explicitly')
    common.validate_story(data,e,valid_slots=good)
    times=presentation.get('warningFrames')
    require(type(times) is list and len(times)==len(expected) and all(type(t) is int for t in times),'Record one actual warning view per rejected trial')
    frames=data['frames'];warning=0
    for k,outcome in enumerate(outcomes):
        if outcome['kind']!='uniqueness-contradiction':continue
        start=next(i for i,f in enumerate(frames) if f['do']=='tap' and f.get('at')=={'part':'slot','slot':k+2})
        end=next(i for i in range(start+1,len(frames)) if frames[i]['do']=='tap' and frames[i].get('at')=={'part':'slot','slot':1})
        fills=[f for f in frames[start:end] if f['do']=='tap' and f.get('count')==2]
        t=times[warning];warning+=1
        require(fills and fills[-1]['time']+500<=t<frames[end]['time'],'Warning view must follow the completed swap and precede leaving that board')
        require(not any(c['start']<=t<=c['end']+200 for c in presentation.get('captions',[])),'Warning proof view must be unobscured by captions')
