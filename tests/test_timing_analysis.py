"""Completely fictional dates and minute counts; no participant observations."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import pandas as pd
import pytest
from timing_analysis import (valid_windows,adjacent_pairs,three_night_sequences,
                            band_aggregates,transition_counts,privacy_check_aggregates)


def data(days=(1,2,3),totals=(290,405,490)):
    return pd.DataFrame([{'night':f'2026-02-{d:02d}', 'total_min':n, 'span_min':n+10,
                          'start_hour':23.,'finish_hour':23.+(n+10)/60,
                          'eligible_architecture':True,'special':False}
                         for d,n in zip(days,totals)])


def test_true_adjacent_day_pairs_only():
    x=valid_windows(data((1,3,4),(290,405,490)))
    p=adjacent_pairs(x)
    assert len(p)==1 and p.iloc[0].duration_initial==405


def test_complete_3_night_chain_requires_both_successors():
    assert len(three_night_sequences(valid_windows(data())))==1
    assert len(three_night_sequences(valid_windows(data((1,2,4)))))==0


def test_band_threshold_inclusive_5_7():
    x=valid_windows(data((1,2,3),(299,300,420)))
    counts=band_aggregates(x)
    assert counts.iloc[0].n==3
    assert counts.iloc[0].reached_5h==2
    assert counts.iloc[0].reached_7h==1


def test_transitions_counts_do_not_include_dates():
    p=adjacent_pairs(valid_windows(data()))
    m=transition_counts(p)
    assert m.values.sum()==2
    assert list(m.index)==['3–<5 h','5–<6 h','6–<7 h','7–<8 h','≥8 h']


def test_duplicate_days_rejected():
    x=data((1,1),(290,400))
    with pytest.raises(ValueError,match='Multiple windows'):
        valid_windows(x)


def test_exclusion_of_special_night():
    x=data();x.loc[1,'special']=True
    assert len(valid_windows(x))==2


def test_early_day_sleep_excluded():
    x=data();x.loc[0,'start_hour']=12.
    assert len(valid_windows(x))==2


def test_noon_crossing_flag_and_exclusion():
    x=data((1,2),(500,490));x.loc[0,'finish_hour']=36.5
    z=valid_windows(x)
    assert z.crosses_noon_boundary.sum()==1
    assert len(valid_windows(x,reject_noon_crossing=True))==1


def test_missing_metrics_fail():
    x=data();x.loc[0,'total_min']=float('nan')
    with pytest.raises(ValueError,match='Missing timing'):
        valid_windows(x)


def test_requires_explicit_stage_coverage():
    x=data();x.loc[1,'eligible_architecture']=False
    assert len(valid_windows(x,stage_only=True))==2


def test_privacy_threshold_is_not_anonymity():
    r=privacy_check_aggregates(pd.DataFrame({'a':[1,50,30]}),threshold=20)
    assert r['small_positive_cells']==1 and r['requires_manual_approval']


def test_second_date_in_month_is_real_date_not_row_position():
    x=valid_windows(data((1,3,5),(350,350,350)))
    assert adjacent_pairs(x).empty


def test_noon_after_12_without_continuous_clock_36_is_flagged():
    x=data((1,2),(500,480));x.loc[0,'finish_hour']=12.5
    assert valid_windows(x).crosses_noon_boundary.sum()==1


def test_pair_flags_change_in_source_and_time_zone():
    x=data((1,2),(400,450));x['devices']=['demoWatchOld','demoWatchNew']
    x['tz_start']=['America/Chicago','America/New_York']
    p=adjacent_pairs(valid_windows(x))
    assert len(p)==1 and p.iloc[0].source_changed and p.iloc[0].timezone_changed


def test_noon_uses_utc_and_iana_over_wall_hour():
    x=data((1,2),(450,480))
    x['last_sleep_utc']=['2026-02-02T18:30:00+00:00','2026-02-03T11:30:00+00:00']
    x['tz_finish']=['America/Chicago','America/Chicago']
    x.loc[0,'finish_hour']=30.5   # Deliberately incorrect display hour
    # Local day-2 noon is 18:00Z. First row really crosses noon.
    assert valid_windows(x).crosses_noon_boundary.tolist()==[True,False]
