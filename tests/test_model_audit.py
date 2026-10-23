import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np,pandas as pd,pytest
from model_audit import eligible_frame,calendar_hac_ols,model_matrix,dominant_episode_variant


def make_data(n=35, spaced=False):
    # Synthetic measurements and labels only, unrelated to private data.
    dates=pd.date_range('2025-01-01',periods=2*n if spaced else n,freq='D')[::2 if spaced else 1]
    t=np.arange(n)
    return pd.DataFrame({'night':dates.strftime('%Y-%m-%d'),'total_min':360+2*t+20*np.sin(t),
                         'start_hour':22+(t%5)*.3,'rem_min':65+3*np.sin(t)+t*.4,
                         'deep_min':40+3*np.cos(t),'split60':(t%7==0),
                         'devices':'demoWatch','eligible_architecture':True,'special':False})


def test_calendar_gap_does_not_create_false_neighbors():
    f=make_data(spaced=True)
    r=calendar_hac_ols(f,'rem_min','naive',lag_days=1)
    assert r['observed_calendar_lag_pairs']==0
    r2=calendar_hac_ols(make_data(),'rem_min','naive',lag_days=1)
    assert r2['observed_calendar_lag_pairs']==34


def test_rank_deficiency_explicitly_refused():
    f=make_data()
    f['start_hour']=f.total_min/60
    with pytest.raises(ValueError,match='Rank deficient'):
        calendar_hac_ols(f,'rem_min','naive')


def test_duplicate_window_refused():
    f=make_data()
    f.loc[0,'night']=f.loc[1,'night']
    with pytest.raises(ValueError,match='only one'):
        eligible_frame(f)


def test_no_missing_automatic_imputation():
    f=make_data();f.loc[5,'rem_min']=np.nan
    with pytest.raises(ValueError,match='Missing'):
        eligible_frame(f)


def test_positive_duration_enforced():
    f=make_data();f.loc[6,'total_min']=0
    with pytest.raises(ValueError,match='positive'):
        eligible_frame(f)


def test_hac_returns_full_rank_and_interval():
    r=calendar_hac_ols(make_data(),'rem_min','naive',lag_days=7)
    assert r['rank']==r['n_features']
    assert r['n']==35
    low,high=r['coefficients']['start_hour']['ci95']
    assert np.isfinite(low) and np.isfinite(high) and low<=high


def test_dominant_episode_proxy_not_night_total():
    f=make_data()
    e=pd.DataFrame({'night':f.night,'primary_sleep_min':f.total_min-30,
                    'primary_rem_min':f.rem_min-15,'primary_deep_min':f.deep_min,
                    'primary_start_hour_local':22.5,'n_episodes':2})
    d=dominant_episode_variant(f,e)
    assert np.allclose(d.total_min,f.total_min-30)
    assert np.allclose(d.start_hour,22.5)
    assert np.allclose(f.total_min,make_data().total_min)


def test_dominant_episode_midnight_rollover():
    f=make_data()
    e=pd.DataFrame({'night':f.night,'primary_sleep_min':f.total_min,
                    'primary_rem_min':f.rem_min,'primary_deep_min':f.deep_min,
                    'primary_start_hour_local':1.5,'n_episodes':1})
    d=dominant_episode_variant(f,e)
    assert set(d.start_hour)=={25.5}


def test_month_dummy_and_split_removal():
    f=make_data()
    x=model_matrix(eligible_frame(f),'naive',omit_split=True,include_month=True)
    assert 'split60' not in x.columns
    assert 'month_2' in x.columns


def test_negative_lag_rejected():
    with pytest.raises(ValueError,match='nonnegative'):
        calendar_hac_ols(make_data(),'rem_min','naive',lag_days=-1)


def test_algorithm_cutpoint_is_configurable_not_embedded():
    f=eligible_frame(make_data(50))
    baseline=model_matrix(f,'adjusted')
    assert 'algorithm_era_after_cutpoint' not in baseline
    adjusted=model_matrix(f,'adjusted',algorithm_cutpoint='2025-01-20')
    assert 'algorithm_era_after_cutpoint' in adjusted
    assert set(adjusted['algorithm_era_after_cutpoint'])=={0.,1.}
