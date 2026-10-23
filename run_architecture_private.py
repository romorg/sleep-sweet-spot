"""Private original-data audit v0.4.

Usage: python run_v0_4.py --json /absolute/private/apple_health_sleep_records.json
Generates private output tables in gitignored outputs/. Do not commit these.
"""
from __future__ import annotations
from argparse import ArgumentParser
from collections import defaultdict
from pathlib import Path
import json,sys
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parent/'src'))
from sleep_pipeline import parse_record,sleep_window
from episodes import summarize_window_episodes
from model_audit import model_comparison


def prepare_private_cohort(records, special_nights: frozenset[str] = frozenset(), watch_source_substring: str = 'Watch'):
    grouped=defaultdict(list);seen=set();watch=0
    for raw in records:
        r=parse_record(raw,watch_source_substring)
        if r is None:continue
        watch+=1
        key=(r['s'],r['e'],r['stage'])
        if key in seen:continue
        seen.add(key)
        grouped[r['local_night']].append(r)
    windows=[];episodes=[]
    for night,group in sorted(grouped.items()):
        row,diag=sleep_window(group,night,special_nights)
        if row is None or not row['eligible_architecture'] or row['special']:continue
        windows.append(row)
        ep=summarize_window_episodes(row,group,diag,60)
        ep.pop('episode_records',None)
        episodes.append(ep)
    return pd.DataFrame(windows),pd.DataFrame(episodes),dict(raw_rows=len(records),watch_rows=watch,
                                                selected_rows=len(windows),deduplicated_rows=len(seen))


def main():
    arg=ArgumentParser()
    arg.add_argument('--json',required=True,type=Path)
    arg.add_argument('--exclude-dates-file',type=Path,help='Private newline-separated window identifiers to exclude; do not commit')
    arg.add_argument('--watch-source-substring',default='Watch',help='Source label selector, without publishing device identifiers')
    arg.add_argument('--algorithm-cutpoint',default=None,help='Optional documented measurement software-era date YYYY-MM-DD')
    arg.add_argument('--output',default=Path(__file__).resolve().parent/'outputs',type=Path)
    args=arg.parse_args()
    if not args.json.is_file():raise FileNotFoundError(args.json)
    args.output.mkdir(parents=True,exist_ok=True)
    exclusions=frozenset(args.exclude_dates_file.read_text().splitlines()) if args.exclude_dates_file else frozenset()
    windows, episodes,meta=prepare_private_cohort(json.loads(args.json.read_text()),exclusions,args.watch_source_substring)
    results=model_comparison(windows,episodes,algorithm_cutpoint=args.algorithm_cutpoint)
    results['data_audit']=meta
    # Private rows and derived statistical results are not part of the public package.
    windows.to_csv(args.output/'private_windows_v0_4.csv',index=False)
    episodes.to_csv(args.output/'private_episodes_v0_4.csv',index=False)
    (args.output/'private_models_v0_4.json').write_text(json.dumps(results,indent=2,ensure_ascii=False))
    summary={'n':len(windows),'scenario_n':{k:v['rem_min']['n'] for k,v in results['models'].items()},
             'total_vs_start_rho':results['spearman_full']['rho_start']['total_min'],
             'affected_episode_windows':results['episode_sensitivity_n_affected'],
             'private_outputs':str(args.output)}
    print(json.dumps(summary,indent=2,ensure_ascii=False))

if __name__=='__main__':main()
