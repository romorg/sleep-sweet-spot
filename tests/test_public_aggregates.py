"""Validate curated public tables, distinct from protected pipeline data."""
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]


def test_public_onset_group_count():
    a=pd.read_csv(ROOT/'data/public_onset_counts.csv')
    assert list(a.start_band)==['20:00–21:59','22:00–23:59','00:00–01:59','02:00–04:59']
    assert len(a)==4
    assert a.n.sum()==2058


def test_public_onset_threshold_nesting():
    a=pd.read_csv(ROOT/'data/public_onset_counts.csv')
    assert (a.n_sleep_at_least_7h<=a.n_sleep_at_least_5h).all()
    assert (a.n_sleep_at_least_5h<=a.n).all()
    assert (a.n_sleep_at_least_7h>=0).all()


def test_public_transition_matrix_totals():
    a=pd.read_csv(ROOT/'data/public_next_night_matrix.csv')
    assert a.shape==(5,6)
    assert a.iloc[:,1:].to_numpy().sum()==1933
    assert list(a.iloc[:,1:].sum(axis=1))==[236,337,556,487,317]


def test_stage_counts_ordered():
    a=pd.read_csv(ROOT/'data/public_stage_summary.csv').iloc[0]
    assert a.eligible_windows==1381
    assert 0<=a.split_gap_120m<=a.split_gap_90m<=a.split_gap_60m<=a.eligible_windows
    assert a.split_gap_60m==105


def test_no_identifying_columns():
    for name in ['public_onset_counts.csv','public_next_night_matrix.csv','public_stage_summary.csv']:
        a=pd.read_csv(ROOT/'data'/name)
        disallowed=('night','date','utc','timezone','location','city','note','name','source','device','patient','event')
        for col in a.columns:
            assert not any(word in col.casefold() for word in disallowed),f'Unexpected column {col} in {name}'


def test_actual_next_duration_count():
    a=pd.read_csv(ROOT/'data/public_next_night_matrix.csv')
    assert a.next_at_least_8h.sum()==302
