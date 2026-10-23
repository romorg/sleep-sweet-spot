"""Private onset/timing regressions. All code is participant-independent.

OLS adjusts descriptively for year, calendar month and weekday. Standard
errors are clustered by observed calendar month-year and use a small-sample
cluster correction and Student t critical value (G-1 df).

The relationship is observational and must NEVER be called an intervention
or a personalized prediction of next-day energy.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from scipy.stats import t as student_t


def calendar_adjusted_timing(cohort:pd.DataFrame, outcome:str='total_min')->dict:
    if outcome not in ('total_min','finish_hour'):
        raise ValueError('Only timing outcomes are supported')
    q=cohort.copy().sort_values('date')
    if len(q)<50 or q.date.duplicated().any():
        raise ValueError('Need >=50 unique dated windows')
    q['date']=pd.to_datetime(q.date)
    q['year']=q.date.dt.year.astype(str)
    q['month']=q.date.dt.month.astype(str)
    q['weekday']=q.date.dt.weekday.astype(str)
    x=pd.concat([q[['start_hour']].reset_index(drop=True),
                 pd.get_dummies(q[['year','month','weekday']].reset_index(drop=True),
                                drop_first=True,dtype=float)],axis=1)
    x.insert(0,'intercept',1.)
    a=x.to_numpy(float)
    clusters=q.date.dt.to_period('M').astype(str).to_numpy()
    unique=np.unique(clusters)
    g=len(unique)
    if g<3:raise ValueError('Too few calendar clusters')
    n,k=a.shape
    if np.linalg.matrix_rank(a)!=k:
        raise ValueError('Rank-deficient calendar model')
    if n<=k+1:
        raise ValueError('Insufficient degrees of freedom')
    if outcome=='total_min':
        y=q.total_min.to_numpy(float)
        units='recorded sleep minutes per onset hour'
    else:
        # hour_axis() wraps time after 11:59 back to 12... after a noon
        # crossing. Put it back on the continuous night axis for this model.
        y=np.where(q.finish_hour.to_numpy(float)<20,
                   q.finish_hour.to_numpy(float)+24,
                   q.finish_hour.to_numpy(float))*60
        units='final recorded clock minutes per onset hour'
    if not np.isfinite(a).all() or not np.isfinite(y).all():
        raise ValueError('Missing or infinite observations')
    beta=np.linalg.lstsq(a,y,rcond=None)[0]
    u=y-a@beta
    xtx=np.linalg.inv(a.T@a)
    meat=np.zeros((k,k))
    for c in unique:
        score=a[clusters==c].T@u[clusters==c]
        meat+=np.outer(score,score)
    correction=(g/(g-1))*((n-1)/(n-k))
    cov=correction*xtx@meat@xtx
    se=float(np.sqrt(max(0,cov[1,1])))
    b=float(beta[1]);crit=float(student_t.ppf(.975,df=g-1))
    return {'outcome':outcome,'n':n,'calendar_month_clusters':g,
            'onset_coefficient':b,'cluster_robust_se':se,
            'cluster_ci95':[b-crit*se,b+crit*se],
            'units':units,'covariates':['year','calendar_month','weekday'],
            'causal':False}
