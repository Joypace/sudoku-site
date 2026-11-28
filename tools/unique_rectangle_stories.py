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
    common.validate_warning_views(data,[k for k,o in enumerate(outcomes) if o['kind']=='uniqueness-contradiction'])
