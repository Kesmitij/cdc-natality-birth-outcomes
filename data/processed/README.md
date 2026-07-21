# Processed analysis-ready tables

Annual parquet files (`natality_analysis_YYYY.parquet`) are produced by
`scripts/process_all_years.py` and are **gitignored** (~27 MB each, ~250 MB total).

Committed artifacts for reproduction of the paper/site live under `results/`
(tables, models, figures). Process metadata is in `process_summary.json` after a run.

## Rebuild from raw CDC zips

```bash
py -3.12 scripts/download_natality.py --years 2016-2024
py -3.12 scripts/process_all_years.py --years 2016-2024 --cleanup
```

U.S. resident record counts matched published NCHS totals exactly for 2016–2023
(see process metadata / control-total checks). 2024 kept 3,628,934 births
(provisional published total may differ slightly as NCHS revises).
