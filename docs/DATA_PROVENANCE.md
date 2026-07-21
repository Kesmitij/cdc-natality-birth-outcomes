# Data provenance — CDC Natality public-use microdata

## Source

| Item | Detail |
|------|--------|
| Portal | [Vital Statistics Online Data Portal](https://www.cdc.gov/nchs/data_access/VitalStatsOnline.htm) |
| FTP data | `https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Datasets/DVS/natality/NatYYYYus.zip` |
| User guides | `https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Dataset_Documentation/DVS/natality/UserGuideYYYY.pdf` |
| Geography | **U.S. files only** (`*us.zip`), not territory (`*ps.zip`) files |
| Certificate | 2003 revised U.S. Standard Certificate of Live Birth (fully implemented in analysis window) |

## Years in this project

Preferred window: **2016–2024** (latest available through 2024).  
Exact years successfully downloaded and processed are recorded in:

- `data/raw/download_manifest.json` (URLs, byte sizes, SHA-256)
- `data/processed/process_summary.json` (record counts, control-total checks)

If disk/network limits prevent a full 2016–2024 run, the pipeline documents the contiguous recent years actually used; analysis standards still apply to those years.

## File sizes

Approximately **220–242 MB** compressed per year; ~3.6 million birth records per year.

## Fixed-width parsing

Field positions are defined in `src/natality/layouts.py`, verified against the NCHS User Guide file-layout tables (e.g., `docs/userguides/UserGuide2023.pdf`). Key fields:

| Field | Positions (1-indexed) | Role |
|-------|----------------------|------|
| DOB_YY | 9–12 | Birth year |
| MAGER | 75–76 | Maternal age |
| RESTATUS | 104 | U.S. vs foreign resident |
| MRACEHISP | 117 | Race/Hispanic origin |
| MEDUC | 124 | Maternal education |
| PRECARE / PRECARE5 | 224–225 / 227 | Prenatal care initiation |
| CIG_REC | 269 | Tobacco during pregnancy |
| BMI / BMI_R | 283–286 / 287 | Pre-pregnancy BMI |
| RF_* diabetes/HTN | 313–317 | Risk factors |
| IP_* infections | 343–347 | Infections present/treated |
| DMETH_REC | 408 | Cesarean vs vaginal |
| PAY_REC | 436 | Payment source |
| APGAR5 | 444–445 | 5-minute Apgar |
| DPLURAL | 454 | Plurality |
| OEGest_Comb / OEGest_R3 | 499–500 / 503 | Obstetric estimate GA |
| DBWT | 504–507 | Birth weight (g) |
| AB_NICU | 519 | NICU admission |
| AB_ANTI | 521 | Antibiotics (neonatal sepsis) |

## Missing / “not stated” handling

Construction rules live in `src/natality/variables.py`. Unknown codes (e.g., MAGER=99, DBWT=9999, OEGest_R3=3, MEDUC=9, Y/N/U flags = U, PRECARE5=5) are mapped to **null** and excluded from complete-case denominators for rates and from complete-case logistic models. They are **never** coded as “no” for binary outcomes.

## Control totals

Published NCHS U.S. birth counts (approx.) are in `NCHS_US_BIRTH_TOTALS` in `layouts.py`. After processing, kept U.S. resident record counts are compared with a **2% relative tolerance** and logged in process metadata.

## Reproducible fetch

```bash
py -3.12 scripts/download_natality.py --years 2016-2024 --guides
py -3.12 scripts/process_natality.py --years 2016-2024
```

Raw zips are gitignored; checksums in the download manifest support integrity verification.
