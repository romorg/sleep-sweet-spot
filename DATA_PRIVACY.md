# Data dictionary and privacy policy (candidate)

## Aggregate tables under review

- `data/public_onset_counts.csv`: `start_band` (broad first recorded sleep start), `n`, `n_sleep_at_least_5h`, `n_sleep_at_least_7h`, `median_recorded_sleep_minutes`. Four rows aggregating 2,058 qualifying windows.
- `data/public_next_night_matrix.csv`: five broad initial-duration bins by five next-calendar-window duration bins. Values are counts, not person-level sequences; total 1,933 pairs. No row gives a date, individual onset time, source identifier, place or diary comment.
- `data/public_stage_summary.csv`: one staged-cohort row, sample size, split counts under three thresholds and median duration/stage minutes. No individual dates or physiological records.

These are **real derived numbers from one named participant**. Aggregation reduces but does not eliminate the possibility of sensitive inference. The historical repository already includes some of these percentages; releasing precise numerators makes them verifiable but slightly more informative.

## Deliberately not included

- Apple Health XML/JSON/CSV exports and any non-sleep health measurements.
- Any per-night timestamps, precise timezones, device IDs, source names, unusual-event dates or event narratives.
- Individual-night Core/REM/Deep/Awake, pulse, HRV, supplement, medical or psychological information.
- Prospective diary values, names, personal context or retrospective concert/travel tags that were not recorded systematically.

The absence of date-level labels also means other researchers cannot calculate all the same adjusted models using the shared CSVs. That trade-off is **intentional**. If more granular data are contemplated later, review them as a separate consent and disclosure decision.

## Safe usage

The `.gitignore` file defaults to rejecting raw data and derived CSVs. **Only reviewed files with the exact `data/public_*.csv` pattern are eligible to be tracked.** Do not run the private analysis with its output directory pointed inside a version-controlled area of tracked data.
