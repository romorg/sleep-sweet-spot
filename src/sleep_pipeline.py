"""Sleep Sweet Spot 0.2: timezone-aware, interval-based, single-participant exploratory pipeline.

Input: private Apple Health SleepAnalysis JSON. No health records embedded in code.
Outputs are private until separately reviewed for publication.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from typing import Any
import json
import pandas as pd

STAGE_PREFIX = 'HKCategoryValueSleepAnalysis'
SLEEP_STAGES = {'AsleepCore','AsleepDeep','AsleepREM','AsleepUnspecified'}
RECOGNIZED = SLEEP_STAGES | {'Awake'}


def timezone_of(record: dict) -> str | None:
    for entry in record.get('metadata') or []:
        if entry.get('key') == 'HKTimeZone':
            return entry.get('value') or None
    return None


def parse_record(record: dict, watch_source_substring: str = 'Watch') -> dict | None:
    """UTC for elapsed times; IANA metadata for civil times; exclude non-Watch/InBed."""
    source = record.get('sourceName','')
    stage = record.get('value','').removeprefix(STAGE_PREFIX)
    if watch_source_substring not in source or stage not in RECOGNIZED:
        return None
    start = datetime.strptime(record['startDate'], '%Y-%m-%d %H:%M:%S %z')
    end = datetime.strptime(record['endDate'], '%Y-%m-%d %H:%M:%S %z')
    if end <= start:
        return None
    tz = timezone_of(record)
    if tz is None:
        raise ValueError('Missing HKTimeZone in Watch record; explicit review required')
    try:
        tzinfo = ZoneInfo(tz)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f'Invalid timezone {tz}') from exc
    start_utc = start.timestamp()
    end_utc = end.timestamp()
    local = start.astimezone(tzinfo)
    raw_local = start.replace(tzinfo=None)
    return {'s':start_utc, 'e':end_utc, 'stage':stage, 'source':source,
            'version':str(record.get('sourceVersion','')), 'tz':tz,
            'local':local, 'export_wall':raw_local,
            'local_night':(local - timedelta(hours=12)).date().isoformat(),
            'export_night':(raw_local - timedelta(hours=12)).date().isoformat()}


def sweep(records: list[dict]) -> tuple[list[tuple[float,float,str]], float]:
    """Return disjoint labeled segments and conflicting time in seconds.

    Detailed stages override simultaneous AsleepUnspecified. Overlapping
    different detailed states (including Awake) are flagged as conflicts.
    """
    events: dict[float,list[tuple[str,int]]] = defaultdict(list)
    for r in records:
        events[r['s']].append((r['stage'],1))
        events[r['e']].append((r['stage'],-1))
    stamps = sorted(events)
    active: dict[str,int] = {}
    segments: list[tuple[float,float,str]] = []
    conflict = 0.0
    for i,t in enumerate(stamps[:-1]):
        for stage,delta in events[t]:
            active[stage] = active.get(stage,0) + delta
        detailed = [stage for stage,n in active.items() if n>0 and stage!='AsleepUnspecified']
        if len(detailed)>1:
            conflict += stamps[i+1] - t
        chosen = detailed[0] if len(detailed)==1 else (
            'AsleepUnspecified' if not detailed and active.get('AsleepUnspecified',0)>0 else None)
        if chosen is not None and t<stamps[i+1]:
            if segments and segments[-1][1] == t and segments[-1][2] == chosen:
                segments[-1] = (segments[-1][0],stamps[i+1],chosen)
            else:
                segments.append((t,stamps[i+1],chosen))
    return segments, conflict


def union(intervals: list[tuple[float,float]]) -> list[tuple[float,float]]:
    result=[]
    for a,b in sorted(intervals):
        if result and a <= result[-1][1]:
            result[-1]=(result[-1][0],max(result[-1][1],b))
        else:
            result.append((a,b))
    return result


def hour_axis(timestamp: float, tz: str) -> float:
    civil=datetime.fromtimestamp(timestamp,timezone.utc).astimezone(ZoneInfo(tz))
    h=civil.hour + civil.minute/60 + civil.second/3600
    return h if h>=12 else h+24


def recorded_minutes(segments, stage: str, low: float, high: float) -> float:
    return sum(max(0,min(high,b)-max(low,a)) for a,b,s in segments if s==stage)/60


def sleep_window(records: list[dict], night: str, special_nights: frozenset[str] | None = None) -> tuple[dict|None,dict]:
    """Process a noon-to-noon window. Not necessarily one physiological night.

    Returns a row and the interval diagnostics needed for event classification.
    """
    segments,conflict_s = sweep(records)
    sleep=[(a,b,s) for a,b,s in segments if s in SLEEP_STAGES]
    if not sleep:
        return None,{}
    first,last=sleep[0][0],sleep[-1][1]
    stage_min={s:recorded_minutes(segments,s,first,last) for s in SLEEP_STAGES}
    total=sum(stage_min.values())
    span=(last-first)/60
    awake=recorded_minutes(segments,'Awake',first,last)
    sleep_merged=union([(a,b) for a,b,_ in sleep])
    sleep_record_first=min((r for r in records if r['stage'] in SLEEP_STAGES and r['s']<=first<r['e']),
                           key=lambda x:x['s'], default=None)
    sleep_record_last=max((r for r in records if r['stage'] in SLEEP_STAGES and r['s']<last<=r['e']),
                          key=lambda x:x['e'],default=None)
    tz_start=sleep_record_first['tz'] if sleep_record_first else records[0]['tz']
    tz_finish=sleep_record_last['tz'] if sleep_record_last else records[-1]['tz']
    gaps=[]
    for i,((a,b),(c,d)) in enumerate(zip(sleep_merged,sleep_merged[1:])):
        before=sum(y-x for x,y in sleep_merged[:i+1])/60
        after=sum(y-x for x,y in sleep_merged[i+1:])/60
        gaps.append({'a':b,'b':c,'gap_min':(c-b)/60,'before_min':before,'after_min':after,
                     'awake_min':recorded_minutes(segments,'Awake',b,c)})
    qualifying=[g for g in gaps if g['before_min']>=60 and g['after_min']>=60]
    flagged_tzs=sorted({r['tz'] for r in records})
    local_first=datetime.fromtimestamp(first,timezone.utc).astimezone(ZoneInfo(tz_start))
    local_last=datetime.fromtimestamp(last,timezone.utc).astimezone(ZoneInfo(tz_finish))
    row={'night':night, 'wake_date':local_last.date().isoformat(),
         'total_min':total,'span_min':span,'awake_min':awake,
         'unmeasured_min':max(0,span-total-awake),
         'coverage':(total-stage_min['AsleepUnspecified'])/total,
         'start_hour':hour_axis(first,tz_start),'finish_hour':hour_axis(last,tz_finish),
         'tz_start':tz_start,'tz_finish':tz_finish,'timezone_mixed':len(flagged_tzs)>1,
         'tz_count':len(flagged_tzs),'conflict_min':conflict_s/60,
         'devices':'|'.join(sorted(set(r['source'] for r in records))),
         'versions':'|'.join(sorted(set(r['version'] for r in records))),
         'episode_count_gap60':1+sum(g['gap_min']>=60 for g in gaps),
         'split60':any(g['gap_min']>=60 for g in qualifying),
         'split90':any(g['gap_min']>=90 for g in qualifying),
         'split120':any(g['gap_min']>=120 for g in qualifying),
         'max_qualifying_gap_min':max((g['gap_min'] for g in qualifying),default=0),
         'first_sleep_utc':datetime.fromtimestamp(first,timezone.utc).isoformat(),
         'last_sleep_utc':datetime.fromtimestamp(last,timezone.utc).isoformat(),
         'special': night in (special_nights or frozenset())}
    for stage,key in [('AsleepCore','core'),('AsleepDeep','deep'),('AsleepREM','rem'),('AsleepUnspecified','unspecified')]:
        row[key+'_min']=stage_min[stage]
        row[key+'_pct']=100*stage_min[stage]/total
    row['eligible_architecture']=row['coverage']>=.95 and total>=180 and span<=960 and row['conflict_min']==0
    row['eligible_morning']=row['eligible_architecture'] and 20<=row['start_hour']<29
    return row,{'sleep':sleep,'gaps':gaps,'segments':segments,'first':first,'last':last,'tz_start':tz_start,'tz_finish':tz_finish}


def classify_morning(window: dict, diag: dict, threshold_min: int=15) -> dict:
    """Nonclinical observed 05:00-07:00 awakening / further Watch-recorded sleep."""
    tz=diag['tz_start']
    selected=None
    for g in diag['gaps']:
        at=hour_axis(g['a'],tz)
        resume=hour_axis(g['b'],tz)
        if (5<=at<7 or 29<=at<31) and g['before_min']>=60 and g['gap_min']>=threshold_min \
                and g['awake_min']>=.9*g['gap_min'] and g['after_min']>=15 and (resume<12 or 24<=resume<36):
            selected=g
            break
    finish=window['finish_hour']
    is_final=(5<=finish<7 or 29<=finish<31)
    name='additional' if selected else ('final' if is_final else 'other')
    return {'group':name,'event_gap_min':selected['gap_min'] if selected else None,
            'additional_sleep_min':selected['after_min'] if selected else None}


def analyze(records: list[dict], watch_source_substring: str = 'Watch', special_nights: frozenset[str] | None = None):
    data=[]
    for r in records:
        rr=parse_record(r,watch_source_substring)
        if rr is not None:data.append(rr)
    # Validated input here: source keeps exact rows, duplicate interval-stage repeats collapsed.
    seen=set();grouped=defaultdict(list);deduped=0
    for r in data:
        key=(r['s'],r['e'],r['stage'])
        if key in seen:
            deduped+=1
            continue
        seen.add(key)
        grouped[r['local_night']].append(r)
    rows=[]
    for night,g in sorted(grouped.items()):
        row,diag=sleep_window(g,night,special_nights)
        if row is not None:
            if row['eligible_morning']:
                row.update({f'morning_{k}':v for k,v in classify_morning(row,diag).items()})
            rows.append(row)
    return pd.DataFrame(rows),{'watch_records':len(data),'duplicates_removed':deduped,
                               'local_reassigned_records':sum(r['export_night']!=r['local_night'] for r in data),
                               'watch_shifted_wall_time':sum(r['local'].replace(tzinfo=None)!=r['export_wall'] for r in data)}
