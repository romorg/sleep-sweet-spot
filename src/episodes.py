"""Gap-defined episodes for the Sleep Sweet Spot v0.3 audit.

An *episode* is a contiguous series of recorded sleep intervals separated by
less than the selected gap threshold. It is not a clinical sleep period.

A noon-to-noon window is retained as the historical comparison unit. A longest
sleep episode is a sensitivity metric and is NOT automatically a replacement
for the total time in that window. Possible daytime episodes are leads for
review, not confirmed naps or independently observed behaviour.
"""
from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Any

from sleep_pipeline import SLEEP_STAGES, recorded_minutes, union

THRESHOLDS = (30, 60, 90, 120, 180)


def is_possible_short_daytime_episode(episode: dict) -> bool:
    """Pure *screening flag*, not a clinical or self-reported nap label."""
    return (9 <= episode['start_hour_local'] < 20
            and 15 <= episode['sleep_min'] <= 180)


def _episode_timezone(records: list[dict[str, Any]], timestamp: float) -> str:
    candidates = [r for r in records
                  if r['stage'] in SLEEP_STAGES and r['s'] <= timestamp < r['e']]
    if not candidates:
        raise ValueError('Episode start must be inside a recorded sleep interval')
    return min(candidates,key=lambda r:(r['s'],r['e'],r['tz']))['tz']


def _civil_hour(timestamp: float, tz: str) -> float:
    t = datetime.fromtimestamp(timestamp, timezone.utc).astimezone(ZoneInfo(tz))
    return t.hour+t.minute/60+t.second/3600


def reconstruct_episodes(records: list[dict], diag: dict, threshold_min: int = 60) -> list[dict]:
    """Split sleep intervals by *elapsed gaps*, not by explicit Awake alone.

    Each episode's staged sleep is measured from the disjoint interval sweep,
    not raw potentially overlapping records. Ties select the earlier episode.
    """
    if threshold_min <= 0:
        raise ValueError('threshold_min must be positive')
    sleep_intervals = union([(a,b) for a,b,s in diag['segments'] if s in SLEEP_STAGES])
    if not sleep_intervals:
        return []
    groups: list[list[tuple[float,float]]] = [[sleep_intervals[0]]]
    for previous, current in zip(sleep_intervals, sleep_intervals[1:]):
        if (current[0]-previous[1])/60 >= threshold_min:
            groups.append([current])
        else:
            groups[-1].append(current)
    episodes=[]
    for i, ranges in enumerate(groups):
        first=ranges[0][0]
        last=ranges[-1][1]
        tz=_episode_timezone(records,first)
        stage_min={s:recorded_minutes(diag['segments'],s,first,last) for s in SLEEP_STAGES}
        total=sum(stage_min.values())
        awake=recorded_minutes(diag['segments'],'Awake',first,last)
        span=(last-first)/60
        episodes.append({
            'episode_index':i,
            'start_utc':datetime.fromtimestamp(first,timezone.utc).isoformat(),
            'end_utc':datetime.fromtimestamp(last,timezone.utc).isoformat(),
            'start_hour_local':_civil_hour(first,tz),
            'end_hour_local':_civil_hour(last,tz),
            'tz_start':tz,
            'sleep_min':total,
            'span_min':span,
            'awake_min':awake,
            'unmeasured_min':max(0.0,span-total-awake),
            'core_min':stage_min['AsleepCore'],
            'deep_min':stage_min['AsleepDeep'],
            'rem_min':stage_min['AsleepREM'],
            'unspecified_min':stage_min['AsleepUnspecified']})
    return episodes


def summarize_window_episodes(window: dict, records: list[dict], diag: dict,
                              threshold_min: int=60) -> dict:
    episodes=reconstruct_episodes(records,diag,threshold_min)
    if not episodes:
        raise ValueError('Expected at least one sleep episode')
    # Dominant means the most recorded sleep; it does not mean physiological main sleep.
    longest=max(episodes,key=lambda e:e['sleep_min'])
    nonprimary=[e for e in episodes if e is not longest]
    # An observed, short secondary episode beginning in daytime is a possible
    # nap/extra sleep, NEVER a confirmation of napping or a next-day outcome.
    possible_daytime=[e for e in nonprimary
                      if is_possible_short_daytime_episode(e)
                      and longest['sleep_min']>=180]
    earlier_later={
        'before_primary':sum(e['episode_index']<longest['episode_index'] for e in possible_daytime),
        'after_primary':sum(e['episode_index']>longest['episode_index'] for e in possible_daytime)}
    # Boundaries remain explicit: the following afternoon belongs to the next
    # noon-to-noon window and cannot be assigned to this prior night here.
    return {
        'night':window['night'], 'threshold_min':threshold_min,
        'n_episodes':len(episodes),
        'n_substantial_episodes_60':sum(e['sleep_min']>=60 for e in episodes),
        'primary_sleep_min':longest['sleep_min'],
        'primary_start_hour_local':longest['start_hour_local'],
        'primary_episode_index':longest['episode_index'],
        'primary_deep_min':longest['deep_min'],
        'primary_rem_min':longest['rem_min'],
        'secondary_sleep_min':sum(e['sleep_min'] for e in nonprimary),
        'secondary_15_count':sum(e['sleep_min']>=15 for e in nonprimary),
        'secondary_30_count':sum(e['sleep_min']>=30 for e in nonprimary),
        'secondary_60_count':sum(e['sleep_min']>=60 for e in nonprimary),
        'possible_daytime_count':len(possible_daytime),
        'possible_daytime_before_primary':earlier_later['before_primary'],
        'possible_daytime_after_primary':earlier_later['after_primary'],
        'primary_share_pct':100*longest['sleep_min']/window['total_min'],
        'max_episode_diff_from_window_min':window['total_min']-longest['sleep_min'],
        'episode_records':episodes}
