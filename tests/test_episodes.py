"""Strictly synthetic scenarios; no private health measurements are in tests."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from sleep_pipeline import parse_record,sleep_window
from episodes import reconstruct_episodes,summarize_window_episodes,is_possible_short_daytime_episode


def rec(start,end,stage='AsleepCore',tz='America/Mexico_City'):
    return {'sourceName':'demoWatch','sourceVersion':'0',
            'startDate':start,'endDate':end,
            'value':'HKCategoryValueSleepAnalysis'+stage,
            'metadata':[{'key':'HKTimeZone','value':tz}]}


def sample(*records):
    r=[parse_record(x) for x in records]
    row,diag=sleep_window(r,'2026-01-01')
    return r,row,diag


def test_30_min_gap_sensitivity_versus_60():
    r,row,diag=sample(rec('2026-01-01 23:00:00 -0600','2026-01-02 01:00:00 -0600'),
                      rec('2026-01-02 01:45:00 -0600','2026-01-02 03:45:00 -0600'))
    assert len(reconstruct_episodes(r,diag,30))==2
    assert len(reconstruct_episodes(r,diag,60))==1
    assert summarize_window_episodes(row,r,diag,30)['secondary_sleep_min']==120
    assert summarize_window_episodes(row,r,diag,60)['secondary_sleep_min']==0


def test_explicit_awake_and_unmeasured_differ_even_across_gap():
    r,row,diag=sample(rec('2026-01-01 22:00:00 -0600','2026-01-02 00:00:00 -0600'),
                      rec('2026-01-02 00:00:00 -0600','2026-01-02 00:45:00 -0600','Awake'),
                      rec('2026-01-02 01:15:00 -0600','2026-01-02 03:15:00 -0600'))
    episodes=reconstruct_episodes(r,diag,60)
    assert len(episodes)==2
    assert episodes[0]['awake_min']==0
    assert episodes[1]['awake_min']==0
    assert row['awake_min']==45
    assert row['unmeasured_min']==30


def test_short_afternoon_episode_is_candidate_not_confirmed_nap():
    r,row,diag=sample(rec('2026-01-01 16:00:00 -0600','2026-01-01 16:30:00 -0600'),
                      rec('2026-01-01 23:00:00 -0600','2026-01-02 05:00:00 -0600'))
    s=summarize_window_episodes(row,r,diag,60)
    assert s['possible_daytime_count']==1
    assert s['possible_daytime_before_primary']==1
    assert s['primary_sleep_min']==360
    assert s['secondary_sleep_min']==30
    assert s['primary_share_pct']<100


def test_morning_return_after_7_not_assumed_nap():
    r,row,diag=sample(rec('2026-01-01 23:00:00 -0600','2026-01-02 05:00:00 -0600'),
                      rec('2026-01-02 06:30:00 -0600','2026-01-02 07:20:00 -0600'))
    s=summarize_window_episodes(row,r,diag,60)
    assert s['n_episodes']==2
    assert s['possible_daytime_count']==0
    assert s['secondary_sleep_min']==50


def test_secondary_after_9_is_only_daytime_candidate():
    r,row,diag=sample(rec('2026-01-01 23:00:00 -0600','2026-01-02 05:00:00 -0600'),
                      rec('2026-01-02 10:15:00 -0600','2026-01-02 10:40:00 -0600'))
    s=summarize_window_episodes(row,r,diag,60)
    assert s['possible_daytime_count']==1
    assert s['possible_daytime_after_primary']==1


def test_stage_overlap_does_not_double_count_episode():
    r,row,diag=sample(rec('2026-01-01 22:00:00 -0600','2026-01-02 04:00:00 -0600','AsleepUnspecified'),
                      rec('2026-01-02 00:00:00 -0600','2026-01-02 01:00:00 -0600','AsleepDeep'))
    s=summarize_window_episodes(row,r,diag,60)
    assert s['primary_sleep_min']==360
    assert s['primary_deep_min']==60
    assert s['n_episodes']==1


def test_two_sustained_episodes_are_not_a_nap_classification():
    r,row,diag=sample(rec('2026-01-01 23:00:00 -0600','2026-01-02 02:00:00 -0600'),
                      rec('2026-01-02 04:00:00 -0600','2026-01-02 07:00:00 -0600'))
    s=summarize_window_episodes(row,r,diag,60)
    assert s['n_substantial_episodes_60']==2
    assert s['possible_daytime_count']==0
    assert s['secondary_sleep_min']==180


def test_end_and_start_durations_across_dst_from_utc():
    r,row,diag=sample(rec('2022-04-02 22:00:00 -0600','2022-04-03 02:00:00 -0600',tz='America/Mexico_City'))
    s=summarize_window_episodes(row,r,diag,60)
    assert s['primary_sleep_min']==240
    assert s['n_episodes']==1


def test_invalid_threshold_explicit_error():
    r,row,diag=sample(rec('2026-01-01 23:00:00 -0600','2026-01-02 03:00:00 -0600'))
    import pytest
    with pytest.raises(ValueError,match='threshold_min'):
        reconstruct_episodes(r,diag,0)


def test_daytime_candidate_may_be_in_ineligible_noon_window():
    # Afternoon sleep at 13:00, night begins at 23:00 and ends at 07:00.
    # Combined span is 18h and fails the 16h architecture filter, yet the
    # first short episode must remain discoverable from the broader dataset.
    r,row,diag=sample(rec('2026-01-01 13:00:00 -0600','2026-01-01 13:30:00 -0600'),
                      rec('2026-01-01 23:00:00 -0600','2026-01-02 07:00:00 -0600'))
    assert not row['eligible_architecture']
    eps=reconstruct_episodes(r,diag,60)
    assert len(eps)==2
    assert is_possible_short_daytime_episode(eps[0])
    assert not is_possible_short_daytime_episode(eps[1])
