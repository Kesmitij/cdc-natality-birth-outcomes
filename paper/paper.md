---
title: "Persistent Black–White Preterm Birth Disparities in U.S. Natality Public-Use Data, 2016–2024"
author: "CDC Natality Birth Outcomes Project"
---

# Persistent Black–White Preterm Birth Disparities in U.S. Natality Public-Use Data, 2016–2024

## Abstract

**Thesis.** Despite secular changes in overall U.S. birth outcomes over 2016–2024, the non-Hispanic Black–White preterm disparity remained large and did not close; racial disparity in preterm birth is not explained by the available socioeconomic and care-timing covariates in the public-use file. From 2016 to 2024, the non-Hispanic Black–White preterm birth rate ratio widened (RR 1.52 → 1.56), with Black rates 14.86% vs White 9.51% in 2024. In multivariable logistic models, non-Hispanic Black identity retained elevated odds of preterm birth (OR 1.49, 95% CI 1.46–1.53) after adjustment for education, prenatal care timing, tobacco, obesity, diabetes, hypertension, plurality, payment source, age, and year. The absolute prenatal-care initiation gradient in preterm rates (15.09 percentage points between no care and first-trimester care) exceeded the education gradient (2.96 pp between lowest and highest education).

**Data.** We analyze U.S. (not territory) Natality public-use microdata from the National Center for Health Statistics / CDC for 2016–2024 (N ≈ 33,511,275 births after U.S. resident filters), using official fixed-width layouts from NCHS User Guides.

**Methods.** We construct preterm birth (obstetric estimate &lt;37 weeks), low and very low birth weight, cesarean delivery, NICU admission, low 5-minute Apgar, neonatal antibiotics, and infection indicators, with explicit handling of “not stated” codes. We report year trends, stratified rates (race/ethnicity, education, prenatal care timing, payment, clinical factors), Black–White rate ratios, and multivariable logistic models.

**Results.** Overall preterm rates moved from 9.85% to 10.41% across the window. The non-Hispanic Black–White preterm rate ratio was 1.52 at the start and 1.56 at the end (absolute gap 5.35 percentage points in the latest year: Black 14.86% vs White 9.51%). Adjusted OR for NH Black (vs NH White) preterm birth was 1.49 (95% CI 1.46–1.53).

**Conclusions.** Measured socioeconomic and care-timing covariates in the public-use file do not eliminate the Black–White preterm association. Geography is unavailable post-2004, limiting place-based inference.

**Keywords.** preterm birth; birth certificates; racial disparities; CDC Natality; low birth weight

---

## 1. Introduction

Infant and maternal birth outcomes remain central indicators of population health in the United States. Preterm birth and low birth weight concentrate later childhood morbidity and drive neonatal intensive care utilization. Racial and socioeconomic disparities in these outcomes have been documented for decades in vital statistics and clinical cohorts.

This paper uses the **complete national public-use Natality microdata** (birth certificates) to (i) describe recent trends, (ii) quantify disparities along race/ethnicity, education, and prenatal care gradients, and (iii) estimate multivariable associations for primary outcomes. Critically, the **thesis is not pre-specified as a narrative of improvement or worsening**; it is derived from the estimated tables after analysis (see Abstract).

## 2. Data and Methods

### 2.1 Data source

Official CDC/NCHS Natality **U.S.** public-use files (`NatYYYYus.zip`) from the [Vital Statistics Online Data Portal](https://www.cdc.gov/nchs/data_access/VitalStatsOnline.htm), years 2016–2024. Territory files are excluded. Field positions follow NCHS User Guides (see `docs/DATA_PROVENANCE.md` and `src/natality/layouts.py`). Download URLs and SHA-256 checksums are recorded in `data/raw/download_manifest.json`.

### 2.2 Sample

Births to U.S. residents (`RESTATUS` 1–3). Foreign residents are excluded. Annual counts are checked against published NCHS U.S. totals (2% relative tolerance) in process metadata.

### 2.3 Outcomes and covariates

Documented in `docs/VARIABLES.md`. Primary outcomes: preterm (OE &lt;37 weeks), LBW (&lt;2500 g), VLBW (&lt;1500 g), cesarean, NICU, low Apgar5, infection composite, neonatal antibiotics. Stratifiers: maternal age, education, race/ethnicity (single-race / Hispanic categories via `MRACEHISP`), prenatal care initiation, tobacco, obesity, diabetes, hypertension, plurality, payment source, year.

Missing and “not stated” codes are set to null and excluded from complete-case denominators; they are never coded as event-absent.

### 2.4 Statistical analysis

1. **Descriptive trends:** annual complete-case rates per 100 births.
2. **Disparities:** rates by race/ethnicity; Black–White rate ratios and absolute differences by year; education and prenatal care gradients.
3. **Multivariable logistic regression** for primary outcomes with maternal age, race/ethnicity (ref: NH White), education (ref: HS/GED), prenatal care timing (ref: first trimester), tobacco, obesity, diabetes, hypertension, plurality, payment (ref: private), and centered year. Complete-case on model variables. When the stacked microdata exceed ~1.5M rows, models use documented outcome-stratified samples for computational feasibility; descriptives use the full extract.

Software: Python 3.12, pandas/polars, statsmodels, matplotlib. All scripts are in the public repository.

## 3. Results

### 3.1 Cohort

Approximately **33,511,275** U.S. resident births across 2016–2024.

### 3.2 National trends

| year | n_births | preterm_rate | lbw_rate | vlbw_rate | cesarean_rate | nicu_rate | low_apgar5_rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2016 | 3945875 | 9.847197952730061 | 8.165690141745596 | 1.3982493846662456 | 31.916267855222824 | 8.739217866209444 | 2.0192587111290026 |
| 2017 | 3855500 | 9.933862670758298 | 8.27704517951729 | 1.4051921636299356 | 31.98098589045529 | 8.980345102942108 | 2.012524317546542 |
| 2018 | 3791712 | 10.022603685997458 | 8.281082564836174 | 1.3769867873035648 | 31.876581724081888 | 9.154775285496097 | 1.9964424608554192 |
| 2019 | 3747540 | 10.228232154043086 | 8.313451955622414 | 1.381804719819481 | 31.677132731633613 | 9.3289681166109 | 2.0678962159602103 |
| 2020 | 3613647 | 10.093324350092725 | 8.242348373016643 | 1.3384219549280327 | 31.805661541324113 | 9.339335429449978 | 2.1023559726363015 |
| 2021 | 3664292 | 10.48750443831426 | 8.520495028491153 | 1.3808123058399147 | 32.079113978501674 | 9.615074490690098 | 2.182946540577053 |
| 2022 | 3667758 | 10.383055027070299 | 8.603218539345464 | 1.3608228406272922 | 32.143429151583796 | 9.494780848067116 | 2.1908952043154097 |
| 2023 | 3596017 | 10.405315337252583 | 8.579300003172746 | 1.3590485324379882 | 32.334204190131004 | 9.800965765821987 | 2.2446893149035407 |
| 2024 | 3628934 | 10.407129083727114 | 8.52098806902815 | 1.3274623056470032 | 32.37914296988612 | 9.881636596105833 | 2.266793656666712 |


Preterm moved from **9.85%** to **10.41%**; LBW from **8.17%** to **8.52%**. Latest cesarean and NICU rates were **32.38%** and **9.88%**, respectively.

### 3.3 Black–White preterm disparity

| year | white_rate | black_rate | rate_ratio | rate_diff_pp |
| --- | --- | --- | --- | --- |
| 2016 | 9.065912675869507 | 13.761502127160481 | 1.517938967555809 | 4.695589451290974 |
| 2017 | 9.080284792601551 | 13.917757658193771 | 1.5327446193685141 | 4.83747286559222 |
| 2018 | 9.113171040151755 | 14.124197294712392 | 1.5498663673141366 | 5.011026254560637 |
| 2019 | 9.283260417876548 | 14.389270294625376 | 1.5500233373736139 | 5.1060098767488284 |
| 2020 | 9.122401971517752 | 14.349626430705843 | 1.573009660778893 | 5.227224459188092 |
| 2021 | 9.52160730643351 | 14.743568887213181 | 1.548432781643003 | 5.221961580779672 |
| 2022 | 9.45876777302094 | 14.57871665571266 | 1.5412913188645196 | 5.11994888269172 |
| 2023 | 9.46838153162179 | 14.648030516057846 | 1.547046923187184 | 5.1796489844360565 |
| 2024 | 9.505900956195532 | 14.857628701685169 | 1.5629900595589115 | 5.351727745489637 |


The rate ratio was **1.52** in the first year and **1.56** in the last year; the absolute difference in the latest year was **5.35** percentage points (Black **14.86%**, White **9.51%**).

### 3.4 Education and prenatal care gradients

**Education (preterm):**

| level | n | events | rate_per_100 |
| --- | --- | --- | --- |
| Less than HS | 3996122 | 458223 | 11.466691957853138 |
| HS / GED | 8645337 | 962277 | 11.13058981969124 |
| Some college | 6276233 | 678645 | 10.812935083831336 |
| Associate | 2757497 | 286839 | 10.402150936156957 |
| Bachelor's | 7042824 | 599281 | 8.509100894754718 |
| Graduate | 4268722 | 364657 | 8.542533339018094 |
| Missing | 498174 | 63980 | 12.842902279123358 |


**Prenatal care timing (preterm):**

| level | n | events | rate_per_100 |
| --- | --- | --- | --- |
| 1st trimester | 25263841 | 2492341 | 9.8652497060918 |
| 2nd trimester | 5363779 | 517516 | 9.648346809217903 |
| 3rd trimester | 1480045 | 115500 | 7.803816775841275 |
| No PNC | 633524 | 158092 | 24.95438215442509 |
| Missing | 743720 | 130453 | 17.54060667993331 |


Absolute education and prenatal-care spans were approximately **2.96** and **15.09** percentage points, respectively.

### 3.5 Multivariable models

Adjusted odds ratio for non-Hispanic Black (vs non-Hispanic White) preterm birth: **1.49** (95% CI **1.46–1.53**). Full coefficient tables are in `results/models/`.

| term | or | ci_low | ci_high | pvalue |
| --- | --- | --- | --- | --- |
| const | 0.18319384285589163 | 0.17571989564304738 | 0.1909856817151881 | 0.0 |
| maternal_age | 1.0169131208020064 | 1.0155631453276652 | 1.0182648907819771 | 3.475265905380662e-135 |
| year_c | 1.0032060730561678 | 1.0004391710654854 | 1.0059806274327696 | 0.023113474394255863 |
| tobacco | 1.4742604574093432 | 1.430284535865435 | 1.5195884747266044 | 2.8569661226882513e-139 |
| obesity | 1.0153002709725705 | 0.9993622807870648 | 1.031492442785737 | 0.05997975657159842 |
| diabetes | 1.4727319336171718 | 1.4387032180003345 | 1.5075655084099975 | 4.3554978663672045e-231 |
| hypertension | 2.995692694351295 | 2.938719745669368 | 3.053770177375532 | 0.0 |
| multiple | 18.451895564690226 | 17.825659667082565 | 19.10013184863852 | 0.0 |
| race_eth_Hispanic | 1.0969261501657819 | 1.0762992829606013 | 1.117948323451191 | 1.277670065930206e-21 |
| race_eth_NH AIAN | 1.134487846972185 | 1.0478560497811915 | 1.228281952655942 | 0.0018496404087551491 |
| race_eth_NH Asian | 1.1240640494673841 | 1.0892612276888218 | 1.1599788509740052 | 3.1428964162714795e-13 |
| race_eth_NH Black | 1.4936593076895015 | 1.46276147474016 | 1.5252097939233678 | 9.6727448009108e-310 |
| race_eth_NH Multiracial | 1.1249881685730931 | 1.0732781817999961 | 1.1791895157198722 | 9.316528760390463e-07 |
| race_eth_NH NHOPI | 1.2375963738124511 | 1.0812325685799011 | 1.4165729270303076 | 0.00197956846995132 |
| education_Associate | 0.8775470784840054 | 0.8527353968285726 | 0.9030806951603837 | 4.402596207844744e-19 |
| education_Bachelor's | 0.7380636037599883 | 0.7204759192752369 | 0.7560806247947334 | 1.652472370802525e-134 |
| education_Graduate | 0.719446169293765 | 0.699048599803487 | 0.740438920351144 | 1.6563932556464594e-111 |
| education_Less than HS | 1.081879423956919 | 1.0560128218482663 | 1.1083796179034777 | 1.840804009833029e-10 |
| education_Some college | 0.9440322216402811 | 0.9243563445796659 | 0.9641269200140994 | 8.347825054898836e-08 |
| pnc_timing_2nd trimester | 0.9012901605832392 | 0.8835979908535543 | 0.9193365783680172 | 9.168916512537413e-25 |
| pnc_timing_3rd trimester | 0.7573099163326055 | 0.7295339924638801 | 0.786143367273038 | 3.7197260114318556e-48 |
| pnc_timing_No PNC | 3.10110348338152 | 2.96878939578063 | 3.2393145934530962 | 0.0 |
| payment_Medicaid | 1.090196892171569 | 1.0706039206680655 | 1.1101484318858985 | 1.0284250842244869e-20 |
| payment_Other | 1.0441437579605444 | 1.0038723856424236 | 1.0860306577616197 | 0.031353594690605675 |
| payment_Self-pay | 0.8319292401594963 | 0.7990809627379892 | 0.8661278304777882 | 3.4780927206355504e-19 |


## 4. Discussion

The organizing empirical claim of this paper is that **the Black–White preterm disparity remains large across 2016–2024 and is not eliminated by simultaneous adjustment for education, prenatal care timing, tobacco, obesity, diabetes, hypertension, plurality, payment, age, and year** as measured on the birth certificate. That claim is falsifiable: attenuation of the adjusted OR to ≈1.0 would reject it in this specification. The estimated OR of 1.49 does not support full attenuation.

Education and prenatal care timing show clear unadjusted gradients and remain relevant for public health targeting, but they are not substitutes for confronting residual racial disparity in national vital statistics.

### 4.1 Limitations

Public-use Natality files **omit geographic identifiers after 2004**, so we cannot study state policy, hospital networks, or residential segregation. Birth certificates are observational; residual confounding (income, wealth, stress, quality of care, racism, environmental exposures) is expected. Item nonresponse is handled by complete-case analysis rather than multiple imputation. Low-risk cesarean is a limited proxy without full NTSV clinical detail.

## 5. Conclusion

Using official CDC Natality public-use microdata for 2016–2024, we find that **national Black–White preterm disparities persist at a high level** while socioeconomic and care-timing gradients remain steep. The thesis is supported by year-specific rate ratios, absolute gaps, and multivariable odds ratios stored in this repository’s `results/` directory. Reproducible code enables independent verification and extension as new annual files are released.

## References

1. National Center for Health Statistics. Natality public-use data files. CDC Vital Statistics Online. https://www.cdc.gov/nchs/data_access/VitalStatsOnline.htm
2. NCHS User Guides to the Natality Public Use File (2016–2024). https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Dataset_Documentation/DVS/natality/
3. Martin JA, Hamilton BE, Osterman MJK. Births in the United States (annual NCHS data briefs / NVSR reports).

## Reproducibility

```
py -3.12 -m pip install -r requirements.txt
py -3.12 scripts/download_natality.py --years 2016-2024 --guides
py -3.12 scripts/process_all_years.py --years 2016-2024 --cleanup
py -3.12 scripts/run_analysis.py
py -3.12 scripts/build_site.py
py -3.12 scripts/build_paper.py
```

Repository: https://github.com/Kesmitij/cdc-natality-birth-outcomes
