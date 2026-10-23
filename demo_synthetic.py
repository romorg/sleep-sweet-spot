"""Safe public-facing sample: three fully fictional sleep records."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'src'))
from sleep_pipeline import analyze

D='2026-02-03 '
records=[
    {'sourceName':'demoWatch', 'sourceVersion':'test',
     'startDate':D+'22:30:00 -0600','endDate':'2026-02-04 02:00:00 -0600',
     'value':'HKCategoryValueSleepAnalysisAsleepCore',
     'metadata':[{'key':'HKTimeZone','value':'America/Mexico_City'}]},
    {'sourceName':'demoWatch', 'sourceVersion':'test',
     'startDate':'2026-02-04 02:00:00 -0600','endDate':'2026-02-04 02:15:00 -0600',
     'value':'HKCategoryValueSleepAnalysisAwake',
     'metadata':[{'key':'HKTimeZone','value':'America/Mexico_City'}]},
    {'sourceName':'demoWatch', 'sourceVersion':'test',
     'startDate':'2026-02-04 02:15:00 -0600','endDate':'2026-02-04 06:00:00 -0600',
     'value':'HKCategoryValueSleepAnalysisAsleepREM',
     'metadata':[{'key':'HKTimeZone','value':'America/Mexico_City'}]},
]
result,checks=analyze(records)
print(result[['total_min','awake_min','core_min','rem_min','coverage','start_hour']].round(2).to_string(index=False))
