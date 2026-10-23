"""Purely synthetic demonstration; no actual sleep observations."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'src'))
from sleep_pipeline import parse_record,sleep_window
from episodes import summarize_window_episodes,is_possible_short_daytime_episode


def fake_record(start,end,stage='AsleepCore'):
    return {'sourceName':'exampleWatchFictional','sourceVersion':'synthetic',
            'startDate':start,'endDate':end,
            'value':'HKCategoryValueSleepAnalysis'+stage,
            'metadata':[{'key':'HKTimeZone','value':'America/Mexico_City'}]}

raw=[fake_record('2026-01-01 13:00:00 -0600','2026-01-01 13:30:00 -0600'),
     fake_record('2026-01-01 23:00:00 -0600','2026-01-02 07:00:00 -0600')]
parsed=[parse_record(x) for x in raw]
row,diag=sleep_window(parsed,'2026-01-01')
result=summarize_window_episodes(row,parsed,diag,threshold_min=60)
print('SYNTHETIC EXAMPLE ONLY')
print('Noon-window total sleep (minutes):',row['total_min'])
print('Would historical architecture filter select this window?:',row['eligible_architecture'])
print('Gap-defined episodes:',result['n_episodes'])
print('Largest episode (minutes):',result['primary_sleep_min'])
print('Short daytime candidate:',result['possible_daytime_count'])
