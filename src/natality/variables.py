"""
Documented construction of analysis outcomes and covariates from raw Natality fields.

Missing / "not stated" codes are mapped to pandas/polars nulls (None) — never silently
treated as valid category levels in rate numerators/denominators.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Union


def _int_or_none(x: Any) -> Optional[int]:
    if x is None:
        return None
    s = str(x).strip()
    if s == "" or s.upper() in {"U", "X", "9", "99", "999", "9999"}:
        # Note: single "9" is only unknown for some 1-digit fields; callers
        # should use field-specific parsers below. This helper is conservative
        # only for multi-digit empty-like codes when used carefully.
        try:
            return int(s)
        except ValueError:
            return None
    try:
        return int(float(s))
    except (ValueError, TypeError):
        return None


def parse_year(raw: Dict[str, str]) -> Optional[int]:
    v = _int_or_none(raw.get("DOB_YY"))
    if v is None or v < 1990 or v > 2030:
        return None
    return v


def parse_maternal_age(raw: Dict[str, str]) -> Optional[int]:
    """MAGER: 12–50 valid; 99 not stated."""
    v = _int_or_none(raw.get("MAGER"))
    if v is None or v == 99 or v < 12 or v > 50:
        return None
    return v


def age_group(age: Optional[int]) -> Optional[str]:
    if age is None:
        return None
    if age < 20:
        return "<20"
    if age < 25:
        return "20-24"
    if age < 30:
        return "25-29"
    if age < 35:
        return "30-34"
    if age < 40:
        return "35-39"
    return "40+"


def education_label(raw: Dict[str, str]) -> Optional[str]:
    """
    MEDUC (1–8; 9=unknown):
      1 = 8th grade or less
      2 = 9–12th grade, no diploma
      3 = High school graduate / GED
      4 = Some college credit, no degree
      5 = Associate degree
      6 = Bachelor's degree
      7 = Master's degree
      8 = Doctorate / Professional
      9 = Unknown
    """
    code = str(raw.get("MEDUC", "")).strip()
    mapping = {
        "1": "Less than HS",
        "2": "Less than HS",
        "3": "HS / GED",
        "4": "Some college",
        "5": "Associate",
        "6": "Bachelor's",
        "7": "Graduate",
        "8": "Graduate",
    }
    return mapping.get(code)  # 9 / blank -> None


def education_ordinal(raw: Dict[str, str]) -> Optional[int]:
    """Collapsed education 1–4 for models: <HS, HS, Some coll/AA, BA+."""
    code = str(raw.get("MEDUC", "")).strip()
    mapping = {
        "1": 1,
        "2": 1,
        "3": 2,
        "4": 3,
        "5": 3,
        "6": 4,
        "7": 4,
        "8": 4,
    }
    return mapping.get(code)


def race_ethnicity(raw: Dict[str, str]) -> Optional[str]:
    """
    Single-race / Hispanic categories using MRACEHISP when present, else MHISP_R + MRACE6.

    MRACEHISP (common coding):
      1 = Non-Hispanic White
      2 = Non-Hispanic Black
      3 = Non-Hispanic AIAN
      4 = Non-Hispanic Asian
      5 = Non-Hispanic NHOPI
      6 = Non-Hispanic more than one race
      7 = Hispanic
      8 = Origin unknown or not stated
      9 = etc. (treat as missing)
    """
    mrh = str(raw.get("MRACEHISP", "")).strip()
    mapping = {
        "1": "NH White",
        "2": "NH Black",
        "3": "NH AIAN",
        "4": "NH Asian",
        "5": "NH NHOPI",
        "6": "NH Multiracial",
        "7": "Hispanic",
    }
    if mrh in mapping:
        return mapping[mrh]

    # Fallback: Hispanic origin + bridged race
    hisp = str(raw.get("MHISP_R", "")).strip()
    # MHISP_R: 0=Non-Hispanic, 1=Mexican, 2=PR, 3=Cuban, 4=Central/SA, 5=Other/unk Hisp, 9=unk
    if hisp in {"1", "2", "3", "4", "5"}:
        return "Hispanic"
    race6 = str(raw.get("MRACE6", "")).strip()
    rmap = {
        "1": "NH White",
        "2": "NH Black",
        "3": "NH AIAN",
        "4": "NH Asian",
        "5": "NH NHOPI",  # sometimes combined
        "6": "NH Multiracial",
    }
    # If non-Hispanic (0) or unknown Hispanic, use race
    if hisp in {"0", "9", ""}:
        return rmap.get(race6)
    return rmap.get(race6)


def hispanic_origin(raw: Dict[str, str]) -> Optional[str]:
    hisp = str(raw.get("MHISP_R", "")).strip()
    if hisp == "0":
        return "Non-Hispanic"
    if hisp in {"1", "2", "3", "4", "5"}:
        return "Hispanic"
    return None


def prenatal_care_timing(raw: Dict[str, str]) -> Optional[str]:
    """
    PRECARE5 when available:
      1 = 1st–3rd month
      2 = 4th–6th month
      3 = 7th–final month
      4 = No prenatal care
      5 = Unknown / not stated
    Else derive from PRECARE (00=none, 01–10 months, 99=unknown).
    """
    pc5 = str(raw.get("PRECARE5", "")).strip()
    if pc5 == "1":
        return "1st trimester"
    if pc5 == "2":
        return "2nd trimester"
    if pc5 == "3":
        return "3rd trimester"
    if pc5 == "4":
        return "No PNC"
    if pc5 == "5":
        return None

    pc = str(raw.get("PRECARE", "")).strip()
    if pc in {"99", "", " "}:
        return None
    if pc in {"00", "0"}:
        return "No PNC"
    try:
        m = int(pc)
    except ValueError:
        return None
    if 1 <= m <= 3:
        return "1st trimester"
    if 4 <= m <= 6:
        return "2nd trimester"
    if 7 <= m <= 10:
        return "3rd trimester"
    return None


def tobacco_use(raw: Dict[str, str]) -> Optional[int]:
    """1 if smoked during pregnancy, 0 if not, None if unknown. CIG_REC Y/N/U."""
    v = str(raw.get("CIG_REC", "")).strip().upper()
    if v == "Y":
        return 1
    if v == "N":
        return 0
    return None


def bmi_value(raw: Dict[str, str]) -> Optional[float]:
    """Pre-pregnancy BMI; 99.9 = unknown."""
    s = str(raw.get("BMI", "")).strip()
    if not s or s in {"99.9", "999", "99.90"}:
        return None
    try:
        v = float(s)
    except ValueError:
        return None
    if v < 10 or v > 90:
        return None
    return v


def obesity(raw: Dict[str, str]) -> Optional[int]:
    """BMI >= 30 -> 1; known BMI < 30 -> 0; else None."""
    b = bmi_value(raw)
    if b is None:
        # try BMI_R: 1 underweight 2 normal 3 overweight 4 obesity I 5 II 6 III 9 unk
        br = str(raw.get("BMI_R", "")).strip()
        if br in {"4", "5", "6"}:
            return 1
        if br in {"1", "2", "3"}:
            return 0
        return None
    return 1 if b >= 30 else 0


def yn_flag(raw: Dict[str, str], field: str) -> Optional[int]:
    """Y/N/U style flags -> 1/0/None."""
    v = str(raw.get(field, "")).strip().upper()
    if v == "Y":
        return 1
    if v == "N":
        return 0
    return None


def any_diabetes(raw: Dict[str, str]) -> Optional[int]:
    p = yn_flag(raw, "RF_PDIAB")
    g = yn_flag(raw, "RF_GDIAB")
    if p is None and g is None:
        return None
    if p == 1 or g == 1:
        return 1
    if p == 0 and g == 0:
        return 0
    # one known zero and other missing -> still known if the known is 1 handled above
    if p == 0 and g is None:
        return None
    if g == 0 and p is None:
        return None
    return 0 if (p or 0) == 0 and (g or 0) == 0 else None


def any_hypertension(raw: Dict[str, str]) -> Optional[int]:
    flags = [yn_flag(raw, f) for f in ("RF_PHYPE", "RF_GHYPE", "RF_EHYPE")]
    if all(f is None for f in flags):
        return None
    if any(f == 1 for f in flags):
        return 1
    if all(f == 0 for f in flags if f is not None) and None not in flags:
        return 0
    # If any is 0 and none is 1, but some missing — treat as incomplete
    if any(f == 1 for f in flags):
        return 1
    if all(f != 1 for f in flags) and any(f == 0 for f in flags):
        # partial zeros without positives: require all present for a firm 0
        if None in flags:
            return None
        return 0
    return None


def plurality_multi(raw: Dict[str, str]) -> Optional[int]:
    """1 if twin+, 0 if singleton, None if unknown. DPLURAL: 1 single, 2 twin, 3 triplet+."""
    v = str(raw.get("DPLURAL", "")).strip()
    if v == "1":
        return 0
    if v in {"2", "3", "4", "5"}:
        return 1
    return None


def payment_source(raw: Dict[str, str]) -> Optional[str]:
    """
    PAY_REC:
      1 = Medicaid
      2 = Private insurance
      3 = Self-pay
      4 = Other
      9 = Unknown
    """
    code = str(raw.get("PAY_REC", "")).strip()
    mapping = {
        "1": "Medicaid",
        "2": "Private",
        "3": "Self-pay",
        "4": "Other",
    }
    if code in mapping:
        return mapping[code]
    # Fall back to PAY
    pay = str(raw.get("PAY", "")).strip()
    paymap = {
        "1": "Medicaid",
        "2": "Private",
        "3": "Self-pay",
        "4": "Other",
        "5": "Other",
        "6": "Other",
        "8": "Other",
    }
    return paymap.get(pay)


# --- Outcomes ---


def gestational_weeks(raw: Dict[str, str]) -> Optional[int]:
    """Obstetric estimate combined (weeks). 99 = not stated."""
    v = _int_or_none(raw.get("OEGest_Comb"))
    if v is None or v == 99 or v < 17 or v > 47:
        return None
    return v


def preterm(raw: Dict[str, str]) -> Optional[int]:
    """
    Preterm <37 weeks using obstetric estimate.
    OEGest_R3 (NCHS standard): 1 = under 37 weeks; 2 = 37 weeks and over; 3 = not stated.
    Falls back to OEGest_Comb weeks when recode missing.
    """
    r3 = str(raw.get("OEGest_R3", "")).strip()
    if r3 == "1":
        return 1
    if r3 == "2":
        return 0
    if r3 == "3":
        return None
    w = gestational_weeks(raw)
    if w is None:
        return None
    return 1 if w < 37 else 0


def birth_weight_g(raw: Dict[str, str]) -> Optional[int]:
    v = _int_or_none(raw.get("DBWT"))
    if v is None or v == 9999 or v < 227 or v > 8165:
        # NCHS edits typically 227–8165 g; 9999 not stated
        if v == 9999 or v is None:
            return None
        if v < 227 or v > 8165:
            return None
    return v


def low_birth_weight(raw: Dict[str, str]) -> Optional[int]:
    w = birth_weight_g(raw)
    if w is None:
        return None
    return 1 if w < 2500 else 0


def very_low_birth_weight(raw: Dict[str, str]) -> Optional[int]:
    w = birth_weight_g(raw)
    if w is None:
        return None
    return 1 if w < 1500 else 0


def cesarean(raw: Dict[str, str]) -> Optional[int]:
    """
    DMETH_REC: 1 = vaginal, 2 = cesarean, 9 = unknown.
    RDMETH_REC detail also accepted: 3,4,5,6 often cesarean pathways.
    """
    d = str(raw.get("DMETH_REC", "")).strip()
    if d == "1":
        return 0
    if d == "2":
        return 1
    rd = str(raw.get("RDMETH_REC", "")).strip()
    # RDMETH_REC: 1 vaginal, 2 vaginal after prior C, 3 primary C, 4 repeat C, 5 vacuum, 6 forceps, 9 unk
    if rd in {"1", "2", "5", "6"}:
        return 0
    if rd in {"3", "4"}:
        return 1
    return None


def low_risk_cesarean(raw: Dict[str, str]) -> Optional[int]:
    """
    NTSV-style approximation available in public-use files:
    Nulliparous (LBO_REC == 1), term (OE >= 37), singleton, vertex-not fully available —
    public files lack full presentation detail consistently; we use:
      - singleton
      - term (not preterm)
      - first live birth (LBO_REC == 1)
      - cesarean among this group
    Returns None if not in the low-risk denominator; 0/1 if cesarean among low-risk.
    """
    multi = plurality_multi(raw)
    pt = preterm(raw)
    lbo = str(raw.get("LBO_REC", "")).strip()
    cs = cesarean(raw)
    if multi is None or pt is None or cs is None:
        return None
    if multi != 0:  # not singleton
        return None
    if pt != 0:  # not term
        return None
    if lbo != "1":  # not first live birth
        return None
    return cs


def nicu(raw: Dict[str, str]) -> Optional[int]:
    return yn_flag(raw, "AB_NICU")


def low_apgar5(raw: Dict[str, str]) -> Optional[int]:
    """5-minute Apgar < 7; 99 unknown."""
    v = _int_or_none(raw.get("APGAR5"))
    if v is None or v == 99 or v > 10:
        return None
    return 1 if v < 7 else 0


def antibiotics_sepsis(raw: Dict[str, str]) -> Optional[int]:
    return yn_flag(raw, "AB_ANTI")


def any_infection(raw: Dict[str, str]) -> Optional[int]:
    flags = [
        yn_flag(raw, f)
        for f in ("IP_GON", "IP_SYPH", "IP_CHLAM", "IP_HEPB", "IP_HEPC")
    ]
    if all(f is None for f in flags):
        return None
    if any(f == 1 for f in flags):
        return 1
    if all(f == 0 for f in flags):
        return 0
    if any(f == 1 for f in flags):
        return 1
    # mixed missing/zero without positive
    if None in flags and not any(f == 1 for f in flags):
        return None
    return 0


def is_us_resident(raw: Dict[str, str]) -> bool:
    """RESTATUS 1–3 are U.S. residents; 4 = foreign residents (exclude for U.S. totals)."""
    r = str(raw.get("RESTATUS", "")).strip()
    return r in {"1", "2", "3", ""}  # blank treated as keep for older quirks


def construct_record(raw: Dict[str, str]) -> Dict[str, Any]:
    """
    Build a single analysis-ready record from raw fixed-width fields.
    All missing/"not stated" -> None.
    """
    age = parse_maternal_age(raw)
    return {
        "year": parse_year(raw),
        "maternal_age": age,
        "age_group": age_group(age),
        "education": education_label(raw),
        "education_ord": education_ordinal(raw),
        "race_eth": race_ethnicity(raw),
        "hispanic": hispanic_origin(raw),
        "pnc_timing": prenatal_care_timing(raw),
        "tobacco": tobacco_use(raw),
        "bmi": bmi_value(raw),
        "obesity": obesity(raw),
        "diabetes": any_diabetes(raw),
        "hypertension": any_hypertension(raw),
        "multiple": plurality_multi(raw),
        "payment": payment_source(raw),
        "gest_weeks": gestational_weeks(raw),
        "preterm": preterm(raw),
        "bw_g": birth_weight_g(raw),
        "lbw": low_birth_weight(raw),
        "vlbw": very_low_birth_weight(raw),
        "cesarean": cesarean(raw),
        "low_risk_cesarean": low_risk_cesarean(raw),
        "nicu": nicu(raw),
        "low_apgar5": low_apgar5(raw),
        "ab_anti": antibiotics_sepsis(raw),
        "infection": any_infection(raw),
        "us_resident": 1 if is_us_resident(raw) else 0,
    }
