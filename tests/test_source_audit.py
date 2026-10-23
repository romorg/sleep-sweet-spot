"""Synthetic device/source combinations."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from source_audit import source_class,source_inventory


def r(source,value):
    return {'sourceName':source,'value':'HKCategoryValueSleepAnalysis'+value,
            'device':'DEMO SERIAL:should-not-be-exported','metadata':[{'key':'HKTimeZone','value':'Test/City'}]}


def test_clock_in_bed_does_not_become_watch():
    assert source_class(r('Clock','InBed'))==('clock','in_bed')


def test_sleep_app_not_native_staged_watch():
    assert source_class(r('Sleep++','AsleepUnspecified'))==('sleep_plus_plus','unspecified_sleep')


def test_source_class_not_device_model():
    a=source_inventory([r('demoWatch7','AsleepREM'),r('Clock','InBed')])
    assert all('SERIAL' not in str(x) and 'Test/City' not in str(x) for x in a)
    assert a[0]['records']==1


def test_unknown_app_remains_unknown():
    assert source_class(r('Example','AsleepDeep'))==('other_or_unknown','staged_sleep')
