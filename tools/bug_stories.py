"""Keep the BUG theorem separate from actual crowded-constraint warnings."""
def validate_story(data,e,common,base,require):
    checks=data.get('expected',{});outcomes=e['branchOutcomes'];warnings=e['nativeWarnings']
    good=[0]+[n for n,o in enumerate(outcomes,1) if o['kind']=='valid']
    expected=[{'slot':n,'constraints':w['constraints']} for n,w in enumerate(warnings,1) if w['kind']=='crowded']
    declared=checks.get('crowdedWarnings');require(type(declared) is list and declared==expected,'Assert exact actual crowded choice sets, not generic invalidity')
    for group in declared:
        require(type(group) is dict and set(group)=={'slot','constraints'},'Wrong crowded assertion')
        base._integer(group['slot'],len(outcomes)+1,'crowded slot',1)
        for row in group['constraints']:
            require(type(row) is list and len(row)==3,'Wrong crowded constraint coordinates')
            base._integer(row[0],4,'constraint kind');base._integer(row[1],9,'constraint index');base._integer(row[2],9,'constraint label')
    require(not checks.get('uniquenessWarnings'),'Do not label a crowded warning as a uniqueness warning')
    base._cells(checks.get('validSlots'));premise=data.get('presentation',{}).get('uniquenessPremise')
    require(type(premise) is dict and premise==e['uniquenessPremise'] and type(premise.get('solutionCount')) is int,'State the actual unique-root premise')
    common.validate_story(data,e,valid_slots=good)
    common.validate_warning_views(data,[k for k,o in enumerate(outcomes) if o['kind']=='uniqueness-contradiction'])
