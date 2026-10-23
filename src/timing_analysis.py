"""Observed timing and next-calendar-night analysis, using PRIVATE reconstructed windows.

There is no participant data embedded in this module. Comparisons are descriptive.
The function accepts rows created by sleep_pipeline.analyze(), not raw personal data.
All outputs are private until reviewed separately for disclosure.
"""
from __future__ import annotations
from datetime import timedelta, datetime, time
from zoneinfo import ZoneInfo
import pandas as pd

ONSET_BANDS=((20.,22.,'20:00–21:59'),(22.,24.,'22:00–23:59'),
             (24.,26.,'00:00–01:59'),(26.,29.,'02:00–04:59'))
DURATION_BANDS=('3–<5 h','5–<6 h','6–<7 h','7–<8 h','≥8 h')


def valid_windows(windows:pd.DataFrame, *, stage_only=False, reject_noon_crossing=False)->pd.DataFrame:
    """Watch windows: complete first-onset 20–05h, duration 3–16h, span <=16h.

    Noon-crossing windows are flagged, not silently made into ordinary nights.
    The stage-only cohort should use eligible_architecture but differs from a
    strictly pre-registered set if exclusions have not been passed in.
    """
    required={'night','start_hour','finish_hour','total_min','span_min','special'}
    missing=required.difference(windows.columns)
    if missing:raise ValueError(f'Missing columns: {sorted(missing)}')
    x=windows.copy()
    x['date']=pd.to_datetime(x['night'],format='%Y-%m-%d',errors='raise')
    if x.date.duplicated().any():
        raise ValueError('Multiple windows on the same noon-window date: resolve before modeling')
    if x[['total_min','span_min','start_hour','finish_hour']].isna().any().any():
        raise ValueError('Missing timing or duration: do not impute')
    if (x.total_min<=0).any() or (x.span_min<=0).any():
        raise ValueError('Nonpositive timing record')
    x=x[(x.start_hour>=20)&(x.start_hour<29)&
        (x.total_min>=180)&(x.total_min<=960)&(x.span_min<=960)&
        (~x.special.astype(bool))].copy()
    if stage_only:
        if 'eligible_architecture' not in x.columns:raise ValueError('Stage coverage column missing')
        x=x[x.eligible_architecture.astype(bool)]
    # A civil time after local noon wraps from the overnight 24–36 axis back
    # to 12–20, so the simple finish_hour >= 36 check is insufficient.
    # UTC end timestamps and actual timezone are preferred when supplied.
    x['crosses_noon_boundary']=x.finish_hour.apply(lambda h: 12<=h<20 or h>=36)
    if {'last_sleep_utc','tz_finish'}.issubset(x.columns):
        def crossed_noon(row):
            if pd.isna(row.last_sleep_utc) or pd.isna(row.tz_finish):
                raise ValueError('Missing UTC finish/timezone: verify manually')
            end_utc=pd.Timestamp(row.last_sleep_utc)
            if end_utc.tzinfo is None:
                raise ValueError('UTC finish must be timezone-aware')
            zone=ZoneInfo(row.tz_finish)
            end_local=end_utc.tz_convert(zone)
            boundary=pd.Timestamp(datetime.combine(
                (row.date+timedelta(days=1)).date(),time(12),tzinfo=zone))
            return bool(end_local>=boundary)
        x['crosses_noon_boundary']=x.apply(crossed_noon,axis=1)
    x['source_mixed']=x.devices.astype(str).str.contains('\\|',regex=True) if 'devices' in x.columns else False
    x['timezone_mixed_audit']=x.timezone_mixed.astype(bool) if 'timezone_mixed' in x.columns else False
    if reject_noon_crossing:
        x=x[~x.crosses_noon_boundary]
    return x.sort_values('date').reset_index(drop=True)


def onset_band(hour:float)->str|None:
    for lo,hi,name in ONSET_BANDS:
        if lo<=hour<hi:return name
    return None


def duration_band(minutes:float)->str:
    if minutes<180:raise ValueError('Duration below cohort minimum')
    if minutes<300:return '3–<5 h'
    if minutes<360:return '5–<6 h'
    if minutes<420:return '6–<7 h'
    if minutes<480:return '7–<8 h'
    return '≥8 h'


def band_aggregates(cohort:pd.DataFrame)->pd.DataFrame:
    """Group-level real aggregates can be separately privacy-reviewed."""
    out=[]
    for lo,hi,name in ONSET_BANDS:
        sub=cohort[(cohort.start_hour>=lo)&(cohort.start_hour<hi)]
        if len(sub)==0:continue
        out.append(dict(start_band=name,n=int(len(sub)),reached_5h=int((sub.total_min>=300).sum()),
                        reached_7h=int((sub.total_min>=420).sum()),
                        median_sleep_min=float(sub.total_min.median())))
    return pd.DataFrame(out)


def adjacent_pairs(cohort:pd.DataFrame)->pd.DataFrame:
    """Only pair truly consecutive local *noon-window dates*.

    Does not imply both are comparable physiological nights, or that there is
    no travel or app-version confounding. Caller must audit source/zone changes.
    """
    if cohort.date.duplicated().any():raise ValueError('Duplicate window dates')
    idx=cohort.set_index('date')
    records=[]
    for day,row in idx.iterrows():
        next_day=day+timedelta(days=1)
        if next_day in idx.index:
            after=idx.loc[next_day]
            devices_changed=('devices' in idx.columns and str(row.devices)!=str(after.devices))
            zone_changed=('tz_start' in idx.columns and str(row.tz_start)!=str(after.tz_start))
            records.append({'start_date':day,'duration_initial':float(row.total_min),
                            'duration_next':float(after.total_min),
                            'initial_band':duration_band(row.total_min),
                            'next_band':duration_band(after.total_min),
                            'source_changed':bool(devices_changed),'timezone_changed':bool(zone_changed),
                            'noon_crossing_either':bool(row.crosses_noon_boundary or after.crosses_noon_boundary)})
    return pd.DataFrame(records,columns=['start_date','duration_initial','duration_next','initial_band','next_band',
                                        'source_changed','timezone_changed','noon_crossing_either'])


def three_night_sequences(cohort:pd.DataFrame)->pd.DataFrame:
    if cohort.date.duplicated().any():raise ValueError('Duplicate window dates')
    idx=cohort.set_index('date')
    records=[]
    for day,row in idx.iterrows():
        if day+timedelta(days=1) in idx.index and day+timedelta(days=2) in idx.index:
            records.append({'start_date':day,'first':float(row.total_min),
                            'second':float(idx.loc[day+timedelta(days=1)].total_min),
                            'third':float(idx.loc[day+timedelta(days=2)].total_min)})
    return pd.DataFrame(records,columns=['start_date','first','second','third'])


def transition_counts(pairs:pd.DataFrame)->pd.DataFrame:
    """Cross-tabs can be privacy-reviewed; never embed dates in public outputs."""
    if len(pairs)==0:
        return pd.DataFrame(0,index=DURATION_BANDS,columns=DURATION_BANDS)
    return pd.crosstab(pairs.initial_band,pairs.next_band).reindex(index=DURATION_BANDS,
                                  columns=DURATION_BANDS,fill_value=0)


def privacy_check_aggregates(frame:pd.DataFrame, *, threshold:int=20)->dict:
    """Disclosure aid, NOT an anonymity guarantee.

    Counts below threshold flag cells for review; suppression may itself reveal
    a hidden value via row totals, so this does not sanitize data on its own.
    """
    if threshold<2:raise ValueError('Threshold must be >=2')
    x=frame.select_dtypes('number').copy()
    vals=x.to_numpy().ravel()
    risky=[float(v) for v in vals if 0<v<threshold and float(v).is_integer()]
    return {'small_positive_cells':len(risky),'minimum_positive_integer':min((int(v) for v in vals if v>0 and float(v).is_integer()),default=None),
            'requires_manual_approval':True}
