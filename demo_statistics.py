"""Entirely synthetic demonstration, no sensitive data or real findings."""
from pathlib import Path
import sys
import numpy as np,pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parent/'src'))
from model_audit import calendar_hac_ols
rng=np.random.default_rng(20261022)
n=240
start=22.7+rng.normal(0,1.2,n)
hours=7.5-.45*(start-23)+rng.normal(0,.55,n)
total=60*np.maximum(hours,3)
rem=12.5*hours+rng.normal(0,12,n)
deep=45+0.8*hours+rng.normal(0,6,n)
f=pd.DataFrame({'night':pd.date_range('2024-01-01',periods=n).strftime('%Y-%m-%d'),
                'total_min':total,'start_hour':start,'rem_min':rem,
                'deep_min':deep,'split60':rng.random(n)>.92,
                'devices':'synthetic'})
for outcome in ('rem_min','deep_min'):
    m=calendar_hac_ols(f,outcome,'naive')
    print('SYNTHETIC',outcome,'N=',m['n'])
    for term in ('sleep_hours','start_hour'):
        d=m['coefficients'][term];print(' ',term,round(d['estimate'],2),[round(x,2) for x in d['ci95']])
print('Synthetic demonstration only. No findings from an individual.')
