# Raw CDC Natality public-use files

This directory holds **U.S.** Natality fixed-width microdata zips from NCHS
(not territory files). Files are large (~220–240 MB compressed per year) and are
**gitignored**.

## Download

```bash
py -3.12 scripts/download_natality.py --years 2016-2023 --guides
```

Official portal: https://www.cdc.gov/nchs/data_access/VitalStatsOnline.htm

FTP pattern:
`https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Datasets/DVS/natality/NatYYYYus.zip`

User guides:
`https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Dataset_Documentation/DVS/natality/UserGuideYYYY.pdf`

After download, `download_manifest.json` records URLs, byte sizes, and SHA-256
checksums for integrity.
