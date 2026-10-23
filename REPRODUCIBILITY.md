# Reproducibility guide

## What is directly reproducible in public

The three `data/public_*.csv` files are **real aggregates**, not synthetic observations. `python scripts/build_figures.py` regenerates the two figures and displays consistency checks. The three tables make group counts and transitions directly inspectable. They do **not** preserve enough information for an independent original-data re-estimation of the adjusted timing models.

Run from the repository root:

```bash
python -m pip install -r requirements.txt
python -m pip install -r requirements-figures.txt
python -m pytest -q
python scripts/build_figures.py
python demo_synthetic.py
python demo_episodes.py
python demo_statistics.py
```

## Full pipeline with your own authorized sleep-only data

Input: JSON list of Apple Health **sleep-only** records with `sourceName`, `startDate`, `endDate`, `value` and relevant `HKTimeZone` metadata. Do **not** commit this file, full Health exports, or personally identifying output. Data sources and IANA timezone fields must be reviewed for your own export; absence/invalid timezone is an explicit validation failure.

```bash
python run_timing_private.py --json /private/path/sleep_only_records.json
python run_architecture_private.py --json /private/path/sleep_only_records.json
```

These scripts write participant-level or private derived data to gitignored `outputs/`. They **do not** assert your input's results will be the same as those from this one-participant historical export. The architecture runner additionally accepts an *optional analyst-justified* software measurement change date; it is not hard-coded as a universal upgrade date.

## Limitations

- No private nightly records, exact dates, source labels, diary narratives or protected health data are bundled.
- The published counts are measured aggregates; any person can recalculate proportions from them. Neither the interval processing nor regressions can be independently replicated on the original participant without consent to the source dataset.
- Synthetic unit tests cover specified edge cases, not clinical validation.
- The staged and timing cohorts have different inclusion rules and numbers. A four-window private-exclusion sensitivity variant exists, but is not part of the published main estimate.
