"""Statistical diagnostics for longitudinal Watch-derived sleep summaries.

Observational, single-participant descriptive models. Calendar-day HAC uses
actual differences between observed dates rather than treating successive
observations as exactly one day apart. Not causal, not diagnostic.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

OUTCOMES = ('rem_min', 'deep_min', 'rem_pct', 'deep_pct')


def eligible_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Caller supplies an episode-augmented architecture cohort.

    Do not conflate missing daytime functioning labels with zero outcomes.
    """
    q = df.copy()
    if 'eligible_architecture' in q.columns:
        q=q[q.eligible_architecture & ~q.special]
    q['date']=pd.to_datetime(q['night']).dt.normalize()
    q=q.sort_values('date').reset_index(drop=True)
    if q['date'].duplicated().any():
        raise ValueError('A model may contain only one analytical window per date')
    if q[['total_min','rem_min','deep_min','start_hour']].isna().any().any():
        raise ValueError('Missing core measurements: do not silently impute')
    if (q['total_min']<=0).any():
        raise ValueError('Sleep duration must be positive')
    q['rem_pct']=100*q.rem_min/q.total_min
    q['deep_pct']=100*q.deep_min/q.total_min
    return q


def model_matrix(frame: pd.DataFrame, adjustment: str='adjusted', omit_split: bool=False,
                 include_month: bool=False, algorithm_cutpoint: str | None=None) -> pd.DataFrame:
    if adjustment not in ('naive','adjusted'):
        raise ValueError('Unknown adjustment')
    X=pd.DataFrame(index=frame.index)
    X['sleep_hours']=frame.total_min.astype(float)/60
    X['start_hour']=frame.start_hour.astype(float)
    if not omit_split:
        X['split60']=frame.split60.astype(float)
    if adjustment=='adjusted':
        if algorithm_cutpoint is not None:
            X['algorithm_era_after_cutpoint']=(frame.date>=pd.Timestamp(algorithm_cutpoint)).astype(float)
        X=pd.concat([X, pd.get_dummies(frame.date.dt.year.astype(str),prefix='year',drop_first=True,dtype=float),
                     pd.get_dummies(frame.devices.astype(str),prefix='device',drop_first=True,dtype=float)],axis=1)
    if include_month:
        X=pd.concat([X,pd.get_dummies(frame.date.dt.month.astype(str),prefix='month',drop_first=True,dtype=float)],axis=1)
    X.insert(0,'intercept',1.0)
    return X


def calendar_hac_ols(frame: pd.DataFrame,outcome: str,adjustment: str='adjusted',
                     lag_days: int=7, omit_split: bool=False, include_month: bool=False,
                     algorithm_cutpoint: str | None=None) -> dict:
    """OLS with Bartlett calendar-day HAC SE and large-sample 95% Wald intervals.

    Uses all date pairs at distances 1..lag_days, not previous N observed rows.
    Do not use this for dependent variable = subjective next-day quality.
    """
    if lag_days<0:
        raise ValueError('lag_days must be nonnegative')
    if frame.empty:
        raise ValueError('Empty sample')
    if outcome not in OUTCOMES:
        raise ValueError('Unknown outcome')
    q=eligible_frame(frame)
    X=model_matrix(q,adjustment,omit_split,include_month,algorithm_cutpoint)
    a=X.to_numpy(dtype=float)
    if np.linalg.matrix_rank(a)<a.shape[1]:
        raise ValueError('Rank deficient design: drop collinear covariates; do not use pseudo-inverse')
    if len(q)<=a.shape[1]+1:
        raise ValueError('Too few observations for model')
    y=q[outcome].to_numpy(dtype=float)
    beta=np.linalg.lstsq(a,y,rcond=None)[0]
    residual=y-a@beta
    xtx_inv=np.linalg.inv(a.T@a)
    scores=a*residual[:,None]
    meat=scores.T@scores
    days=(q.date-q.date.min()).dt.days.to_numpy(dtype=int)
    # Efficient lag pairing; unique date per window is guaranteed by eligible_frame.
    indices={int(day):i for i,day in enumerate(days)}
    matched_pairs=0
    for gap in range(1,lag_days+1):
        weight=1-gap/(lag_days+1)
        for i,day in enumerate(days):
            j=indices.get(int(day)+gap)
            if j is not None:
                cross=np.outer(scores[j],scores[i])
                meat+=weight*(cross+cross.T)
                matched_pairs+=1
    vcov=xtx_inv@meat@xtx_inv
    std=np.sqrt(np.maximum(0,np.diag(vcov)))
    r2=1-np.sum(residual**2)/np.sum((y-y.mean())**2) if np.sum((y-y.mean())**2)>0 else float('nan')
    # Standardized regressor condition number: interpret as a diagnostic only.
    z=a[:,1:];stdx=z.std(axis=0,ddof=0)
    centered=(z-z.mean(axis=0))/np.where(stdx==0,1,stdx)
    rank_condition=float(np.linalg.cond(centered)) if z.shape[1]>0 else 1.0
    coefficients={key:{'estimate':float(b),'se_calendar_hac':float(s),
                     'ci95':[float(b-1.96*s),float(b+1.96*s)]}
                  for key,b,s in zip(X.columns,beta,std)}
    return dict(n=len(q),outcome=outcome,adjustment=adjustment,features=list(X.columns),
                rank=int(np.linalg.matrix_rank(a)),n_features=len(X.columns),
                condition_standardized=float(rank_condition),r2=float(r2),
                lag_days=lag_days,observed_calendar_lag_pairs=int(matched_pairs),
                coefficients=coefficients)


def simple_spearman(frame: pd.DataFrame) -> dict:
    q=eligible_frame(frame)
    cols=('rem_min','deep_min','rem_pct','deep_pct','total_min')
    return {'n':len(q),'rho_start':{k:float(spearmanr(q.start_hour,q[k]).statistic) for k in cols},
            'rho_total':{k:float(spearmanr(q.total_min,q[k]).statistic) for k in cols}}


def dominant_episode_variant(frame: pd.DataFrame, episodes: pd.DataFrame) -> pd.DataFrame:
    """A sensitivity proxy only. NOT a validated substitute for overnight sleep."""
    q=eligible_frame(frame)
    if episodes['night'].duplicated().any():
        raise ValueError('Duplicate night in episode summary')
    e=episodes[['night','primary_sleep_min','primary_rem_min','primary_deep_min',
                'primary_start_hour_local','n_episodes']].copy()
    q=q.merge(e,on='night',validate='one_to_one')
    for key,other in [('total_min','primary_sleep_min'),('rem_min','primary_rem_min'),
                      ('deep_min','primary_deep_min')]:q[key]=q[other]
    # v0.3 stores dominant episode start as an ordinary civil hour (0-24).
    q['start_hour']=q.primary_start_hour_local.where(q.primary_start_hour_local>=12,
                                                    q.primary_start_hour_local+24)
    return q


def model_comparison(frame: pd.DataFrame,episodes: pd.DataFrame,
                     algorithm_cutpoint: str | None=None) -> dict:
    q=eligible_frame(frame)
    d=dominant_episode_variant(q,episodes)
    nonsplit=q[~q.split60].copy()
    regular=q[q.start_hour.between(20,29,inclusive='left')].copy()
    # Measurement/software-era comparisons are optional and must be justified
    # by this dataset's own provenance, not a participant-specific date.
    era1=era2=None
    specs={'naive':(q,'naive',False,False),
           'adjusted':(q,'adjusted',False,False),
           'adjusted_month':(q,'adjusted',False,True),
           'adjusted_no_split_windows':(nonsplit,'adjusted',True,False),
           'adjusted_regular_start':(regular,'adjusted',False,False),
           'adjusted_dominant_episode_proxy':(d,'adjusted',False,False)}
    if algorithm_cutpoint is not None:
        cutoff=pd.Timestamp(algorithm_cutpoint)
        era1=q[q.date<cutoff].copy()
        era2=q[q.date>=cutoff].copy()
        if len(era1)<20 or len(era2)<20:
            raise ValueError('Algorithm cutpoint leaves too few windows in an era')
        specs['pre_update']=(era1,'naive',False,False)
        specs['post_update']=(era2,'naive',False,False)
    results={}
    for name,(f,adjustment,omit_split,include_month) in specs.items():
        results[name]={outcome:calendar_hac_ols(f,outcome,adjustment,
                                                 omit_split=omit_split,include_month=include_month,
                                                 algorithm_cutpoint=algorithm_cutpoint)
                       for outcome in OUTCOMES}
    return {'algorithm_cutpoint':algorithm_cutpoint,'models':results,
            'spearman_full':simple_spearman(q),
            'spearman_pre_update':simple_spearman(era1) if era1 is not None else None,
            'spearman_post_update':simple_spearman(era2) if era2 is not None else None,
            'episode_sensitivity_n_affected':int((q.merge(episodes[['night','primary_sleep_min']],on='night')
                                                   .eval('total_min - primary_sleep_min > 0.00001')).sum())}
