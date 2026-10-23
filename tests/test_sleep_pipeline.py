"""Synthetic, fake Apple Watch sleep records. No personal observations."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from datetime import datetime,timezone
import pytest
from sleep_pipeline import parse_record,sleep_window,sweep,union,hour_axis,classify_morning


def record(start,end,stage='AsleepCore',tz='America/Mexico_City',source='demoWatch'):
    # Instants in synthetic data use explicit UTC offsets, metadata controls civil time.
    return {'sourceName':source,'sourceVersion':'0','startDate':start,'endDate':end,
            'value':'HKCategoryValueSleepAnalysis'+stage,
            'metadata':[{'key':'HKTimeZone','value':tz}]}


def group(*recs):
    return [parse_record(r) for r in recs]


def window(*recs,night='2026-01-01'):
    return sleep_window(group(*recs),night)


def test_dedup_and_union_do_not_double_count():
    s='2026-01-01 22:00:00 -0600';e='2026-01-02 00:00:00 -0600'
    r=group(record(s,e),record(s,e))
    segments,conf=sweep(r)
    assert conf==0
    assert sum((b-a)/60 for a,b,k in segments if k=='AsleepCore')==120
    assert len(union([(a,b) for a,b,k in segments]))==1


def test_unspecified_overlapped_with_detailed():
    r=group(record('2026-01-01 22:00:00 -0600','2026-01-02 00:00:00 -0600', 'AsleepUnspecified'),
            record('2026-01-01 22:30:00 -0600','2026-01-01 23:30:00 -0600', 'AsleepREM'))
    s,c=sweep(r)
    assert c==0
    assert round(sum((b-a)/60 for a,b,k in s if k=='AsleepREM'))==60
    assert round(sum((b-a)/60 for a,b,k in s if k=='AsleepUnspecified'))==60


def test_awake_before_first_sleep_does_not_change_start():
    row,_=window(record('2026-01-01 21:30:00 -0600','2026-01-01 22:00:00 -0600','Awake'),
                 record('2026-01-01 22:00:00 -0600','2026-01-02 02:00:00 -0600'))
    assert row['start_hour']==22
    assert row['awake_min']==0
    assert row['total_min']==240


def test_observed_awake_different_from_unmeasured_gap():
    row,_=window(record('2026-01-01 22:00:00 -0600','2026-01-02 00:00:00 -0600'),
                 record('2026-01-02 00:30:00 -0600','2026-01-02 02:30:00 -0600'))
    assert row['awake_min']==0 and row['unmeasured_min']==30
    assert row['episode_count_gap60']==1
    row2,_=window(record('2026-01-01 22:00:00 -0600','2026-01-02 00:00:00 -0600'),
                  record('2026-01-02 00:00:00 -0600','2026-01-02 00:30:00 -0600','Awake'),
                  record('2026-01-02 00:30:00 -0600','2026-01-02 02:30:00 -0600'))
    assert row2['awake_min']==30 and row2['unmeasured_min']==0


def test_split60_means_sleep_on_both_sides():
    row,_=window(record('2026-01-01 22:00:00 -0600','2026-01-01 23:30:00 -0600'),
                 record('2026-01-02 00:30:00 -0600','2026-01-02 02:00:00 -0600'))
    assert row['split60'] is True
    assert row['split90'] is False
    assert row['episode_count_gap60']==2


def test_conflicting_detailed_stages_rejected():
    row,_=window(record('2026-01-01 22:00:00 -0600','2026-01-02 02:00:00 -0600'),
                 record('2026-01-01 23:00:00 -0600','2026-01-02 00:00:00 -0600','AsleepDeep'))
    assert row['conflict_min']==60
    assert row['eligible_architecture'] is False


def test_real_iana_zone_overrides_misleading_export_offset():
    # The export -0600 is frozen, while civil Mexico City was on DST in summer 2022.
    r=parse_record(record('2022-07-01 23:00:00 -0600','2022-07-02 01:00:00 -0600'))
    assert r['local'].hour==0
    assert r['local'].date().isoformat()=='2022-07-02'
    assert r['local_night']=='2022-07-01'
    assert r['export_night']=='2022-07-01'


def test_travel_timezone_and_record_night_assignment():
    r=parse_record(record('2026-06-01 22:00:00 -0600','2026-06-02 00:00:00 -0600',tz='Europe/Madrid'))
    assert r['local'].hour==6  # UTC Jun 2 04:00, Madrid 06:00
    assert r['local_night']=='2026-06-01'
    assert r['export_night']=='2026-06-01'


def test_morning_additional_requires_recorded_awake():
    row,diag=window(record('2026-01-01 23:00:00 -0600','2026-01-02 05:30:00 -0600'),
                    record('2026-01-02 05:30:00 -0600','2026-01-02 06:00:00 -0600','Awake'),
                    record('2026-01-02 06:00:00 -0600','2026-01-02 07:00:00 -0600'))
    assert row['eligible_morning']
    assert classify_morning(row,diag)['group']=='additional'
    assert classify_morning(row,diag)['additional_sleep_min']==60
    row2,diag2=window(record('2026-01-01 23:00:00 -0600','2026-01-02 05:30:00 -0600'),
                      record('2026-01-02 06:00:00 -0600','2026-01-02 07:00:00 -0600'))
    assert classify_morning(row2,diag2)['group']=='other'


def test_missing_timezone_fails_explicitly():
    r=record('2026-01-01 22:00:00 -0600','2026-01-02 02:00:00 -0600')
    r['metadata']=[]
    with pytest.raises(ValueError,match='Missing HKTimeZone'):
        parse_record(r)
