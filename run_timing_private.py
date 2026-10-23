"""Generate private timing aggregates from an AUTHORIZED sleep-only JSON export.

All output files are explicitly private and gitignored, including aggregate
statistics. Never publish results automatically from this script.
"""
from argparse import ArgumentParser
from pathlib import Path
from datetime import date
import json
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent/'src'))
from sleep_pipeline import analyze
from timing_analysis import (valid_windows, band_aggregates, adjacent_pairs,
                             three_night_sequences, transition_counts)
from source_audit import source_inventory
from timing_models import calendar_adjusted_timing


def main():
    p=ArgumentParser()
    p.add_argument('--json',type=Path,required=True,help='Private sleep-only JSON; never full Health export')
    p.add_argument('--output',type=Path,default=Path(__file__).resolve().parent/'outputs')
    p.add_argument('--watch-source-substring',default='Watch')
    p.add_argument('--exclude-dates-file',type=Path,help='PRIVATE exclusion IDs, one per line')
    p.add_argument('--reject-noon-crossing',action='store_true',help='Sensitivity run')
    args=p.parse_args()
    if not args.json.is_file():raise FileNotFoundError(args.json)
    if args.output.resolve()==Path(__file__).resolve().parent:
        raise ValueError('Refusing to write derived health data into repository root')
    records=json.loads(args.json.read_text())
    if not isinstance(records,list):raise ValueError('Expected sleep-only list of record objects')
    exclusions=frozenset(args.exclude_dates_file.read_text().splitlines()) if args.exclude_dates_file else frozenset()
    windows,info=analyze(records,args.watch_source_substring,special_nights=exclusions)
    cohort=valid_windows(windows,reject_noon_crossing=args.reject_noon_crossing)
    pairs=adjacent_pairs(cohort)
    threes=three_night_sequences(cohort)
    out=args.output
    out.mkdir(parents=True,exist_ok=True)
    band_aggregates(cohort).to_csv(out/'PRIVATE_onset_counts.csv',index=False)
    transition_counts(pairs).to_csv(out/'PRIVATE_transitions.csv')
    # Only counts plus software/source categories; no source labels or identifiers.
    (out/'PRIVATE_summary.json').write_text(json.dumps({
        'raw_intervals':len(records),'reconstructed_windows':len(windows),
        'timing_cohort':len(cohort),'consecutive_pairs':len(pairs),
        'complete_triads':len(threes),
        'triads_below_5h_first':int((threes['first']<300).sum()),
        'noon_crossing_candidate_count':int(cohort.crosses_noon_boundary.sum()),
        'pair_source_change_count':int(pairs.source_changed.sum()),
        'pair_timezone_change_count':int(pairs.timezone_changed.sum()),
        'source_inventory':source_inventory(records),
        'timing_models':{name:calendar_adjusted_timing(cohort,name) for name in ('total_min','finish_hour')},
        'input_diagnostics':info,'private_only':True,
    },indent=2))
    print(f'PRIVATE RESULTS ONLY. Cohort={len(cohort)}, adjacent pairs={len(pairs)}; outputs in {out}')

if __name__=='__main__':main()
