# CDC Natality Birth Outcomes

**Reproducible analysis of U.S. birth outcomes and disparities using official CDC/NCHS Natality public-use microdata (2016–2024), with a data-driven thesis, research paper, and GitHub Pages site.**

[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-site-blue)](https://kesmitij.github.io/cdc-natality-birth-outcomes/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Thesis (data-driven)

The project’s public-facing claim is **not** written before the numbers exist. After processing the microdata and estimating trends, disparities, and multivariable models, the thesis is generated from `results/tables/key_findings.json` and published on the site and in `paper/paper.md`.

Open the site homepage or `results/tables/thesis.json` for the current statement supported by the saved estimates (Black–White preterm rate ratios, absolute gaps, adjusted odds ratios, education and prenatal-care gradients).

## Repository layout

```
src/natality/          # layouts, fixed-width parser, variable construction, process, analyze, figures
scripts/               # download, process, analyze, build site/paper
tests/                 # unit tests (parser fixtures + analysis on constructed inputs)
data/raw/              # gitignored zips + download_manifest.json
data/processed/        # analysis-ready parquet (large; often gitignored)
data/fixtures/         # synthetic fixed-width records for tests
results/               # tables, models, figures (committed)
paper/                 # paper.md + paper.pdf
site/                  # GitHub Pages static site
docs/                  # DATA_PROVENANCE.md, VARIABLES.md, user guides
```

## Quick start (reproduce)

```bash
# Python 3.10+
py -3.12 -m pip install -r requirements.txt

# 1) Download U.S. Natality zips (~230 MB each) + user guides
py -3.12 scripts/download_natality.py --years 2016-2024 --guides

# 2) Extract (7-Zip handles Deflate64) + process to parquet
#    tools/x64/7za.exe is included for Windows Deflate64 extraction
py -3.12 scripts/process_all_years.py --years 2016-2024 --cleanup

# 3) Descriptives + logistic models + figures
py -3.12 scripts/run_analysis.py

# 4) Site + paper from artifacts
py -3.12 scripts/build_site.py
py -3.12 scripts/build_paper.py

# 5) Tests
py -3.12 -m pytest -q
```

**Note on zips:** Recent CDC Natality archives often use **Deflate64** compression, which Python’s `zipfile` and PowerShell `Expand-Archive` cannot open. The pipeline extracts with `tools/x64/7za.exe` (7-Zip).

## Data provenance

| Item | Value |
|------|--------|
| Portal | https://www.cdc.gov/nchs/data_access/VitalStatsOnline.htm |
| Files | `NatYYYYus.zip` (U.S. only, not `*ps` territories) |
| Years | 2016–2024 (or the contiguous set successfully processed) |
| Layouts | NCHS User Guides → `src/natality/layouts.py` |
| Checksums | `data/raw/download_manifest.json` |

See [docs/DATA_PROVENANCE.md](docs/DATA_PROVENANCE.md) and [docs/VARIABLES.md](docs/VARIABLES.md).

## GitHub Pages

Static site in `site/`. Enable Pages: **Settings → Pages → Deploy from branch → `/site` folder** (or copy `site/` to `/docs` and select `/docs`).  
Live URL pattern: `https://kesmitij.github.io/cdc-natality-birth-outcomes/`

## License

MIT for code. **Natality microdata remain subject to NCHS terms of use**; we redistribute only derived summaries and documentation, not the multi-GB raw files.
