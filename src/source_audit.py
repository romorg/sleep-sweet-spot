"""Summarize measurement provenance without leaking device identifiers.

A single person may use Apple Watch throughout but Clock measurements can
originate on iPhone. app/source != device and source name != exact hardware.
"""
from collections import Counter,defaultdict

SLEEP_PREFIX='HKCategoryValueSleepAnalysis'


def source_class(raw:dict)->tuple[str,str]:
    source=(raw.get('sourceName') or '').casefold()
    value=(raw.get('value') or '').removeprefix(SLEEP_PREFIX)
    if source=='clock':app='clock'
    elif 'sleep++' in source or 'sleepplusplus' in source:app='sleep_plus_plus'
    elif 'watch' in source:app='watch_native_or_imported'
    else:app='other_or_unknown'
    if value=='InBed':measure='in_bed'
    elif value in {'AsleepREM','AsleepDeep','AsleepCore'}:measure='staged_sleep'
    elif value=='AsleepUnspecified':measure='unspecified_sleep'
    elif value=='Awake':measure='awake'
    else:measure='other'
    return app,measure


def source_inventory(records:list[dict])->list[dict]:
    """Aggregate counts with no app source strings, locations or device metadata."""
    counts=Counter()
    for r in records:
        app,measure=source_class(r)
        counts[(app,measure)]+=1
    return [{'source_class':a,'measure':m,'records':n} for (a,m),n in sorted(counts.items())]
