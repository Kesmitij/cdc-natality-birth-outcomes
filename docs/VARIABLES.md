# Variable construction

All coding is implemented in `src/natality/variables.py` and unit-tested in `tests/test_parser.py`.

## Outcomes

| Analysis name | Definition | Source fields |
|---------------|------------|---------------|
| `preterm` | Obstetric estimate &lt; 37 weeks | `OEGest_R3` (1=&lt;37, 2=37+, 3=NS); fallback `OEGest_Comb` |
| `lbw` | Birth weight &lt; 2500 g | `DBWT` (9999 → missing) |
| `vlbw` | Birth weight &lt; 1500 g | `DBWT` |
| `cesarean` | Cesarean delivery | `DMETH_REC` 2; else `RDMETH_REC` 3/4 |
| `low_risk_cesarean` | Cesarean among nulliparous, term, singleton (NTSV-style proxy; presentation not fully available) | `LBO_REC`, `preterm`, `multiple`, `cesarean` |
| `nicu` | NICU admission | `AB_NICU` Y/N/U |
| `low_apgar5` | 5-minute Apgar &lt; 7 | `APGAR5` (99 → missing) |
| `ab_anti` | Antibiotics for suspected neonatal sepsis | `AB_ANTI` |
| `infection` | Any of gonorrhea, syphilis, chlamydia, hep B, hep C | `IP_*` |

## Covariates / stratifiers

| Name | Definition |
|------|------------|
| `year` | `DOB_YY` |
| `maternal_age` / `age_group` | `MAGER` (99 → missing); groups &lt;20, 20–24, …, 40+ |
| `education` | Collapsed from `MEDUC`: &lt;HS, HS/GED, Some college, Associate, Bachelor's, Graduate |
| `race_eth` | From `MRACEHISP`: NH White/Black/AIAN/Asian/NHOPI/Multiracial, Hispanic |
| `hispanic` | From `MHISP_R` |
| `pnc_timing` | From `PRECARE5` / `PRECARE`: 1st/2nd/3rd trimester, No PNC |
| `tobacco` | `CIG_REC` Y/N |
| `obesity` | Pre-pregnancy BMI ≥ 30 (`BMI` / `BMI_R`) |
| `diabetes` | Prepregnancy or gestational diabetes |
| `hypertension` | Prepregnancy HTN, gestational HTN, or eclampsia |
| `multiple` | Twin+ from `DPLURAL` |
| `payment` | Medicaid / Private / Self-pay / Other from `PAY_REC` |

## Inclusion

- U.S. residents: `RESTATUS` ∈ {1, 2, 3} (foreign residents excluded from analysis tables).
- Territory microdata files are never downloaded by the project scripts.

## Models

Multivariable logistic regression (statsmodels) for primary outcomes with predictors: maternal age, race/ethnicity (ref: NH White), education (ref: HS/GED), prenatal care timing (ref: 1st trimester), tobacco, obesity, diabetes, hypertension, plurality, payment (ref: Private), and centered year. **Complete-case** analysis on model variables; sample size and % complete are saved with each model JSON.
