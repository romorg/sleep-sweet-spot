"""Fictional data only; checks dimensional and causal guardrails."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import pandas as pd
import pytest
from timing_models import calendar_adjusted_timing


def synthetic(n=160):
    days=pd.date_range('2024-01-01',periods=n,freq='D')
    d=pd.DataFrame({'date':days,'start_hour':[22.+((i*13)%19)*.07 for i in range(n)]})
    d['total_min']=[390-30*(t-22)+5*(i%5) for i,t in enumerate(d.start_hour)]
    d['finish_hour']=d.start_hour+d.total_min/60
    return d


def test_full_rank_and_negative_onset_association():
    m=calendar_adjusted_timing(synthetic(),'total_min')
    assert m['onset_coefficient']<0 and m['causal'] is False
    assert m['n']==160 and m['calendar_month_clusters']>=3
    lo,hi=m['cluster_ci95'];assert lo<=m['onset_coefficient']<=hi


def test_finish_time_is_minutes_not_hours():
    m=calendar_adjusted_timing(synthetic(),'finish_hour')
    assert 0<m['onset_coefficient']<60


def test_reject_unsupported_outcome():
    with pytest.raises(ValueError,match='Only timing outcomes'):
        calendar_adjusted_timing(synthetic(),'daytime_energy')


def test_reject_duplicate_dates():
    x=synthetic();x.loc[0,'date']=x.loc[1,'date']
    with pytest.raises(ValueError,match='unique dated'):
        calendar_adjusted_timing(x)


def test_reject_no_clusters():
    x=synthetic(60)
    with pytest.raises(ValueError,match='Too few calendar clusters'):
        calendar_adjusted_timing(x)
