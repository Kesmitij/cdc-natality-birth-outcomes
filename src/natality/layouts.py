"""
Fixed-width field layouts for CDC Natality U.S. public-use files (2016–2024).

Positions are 1-indexed inclusive (NCHS User Guide convention). Internally the
parser converts to 0-indexed Python slices.

Source: NCHS User Guides (verified against UserGuide2023.pdf file layout)
  https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Dataset_Documentation/DVS/natality/

Layouts are stable for revised-certificate years used here. Only fields required
for this study are retained.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class Field:
    """One fixed-width field."""

    name: str
    start: int  # 1-indexed inclusive
    end: int  # 1-indexed inclusive
    description: str = ""

    @property
    def slice(self) -> slice:
        """0-indexed Python slice into a line string."""
        return slice(self.start - 1, self.end)

    @property
    def width(self) -> int:
        return self.end - self.start + 1


# Positions verified from UserGuide2023.pdf (File layout section).
NATALITY_FIELDS: List[Field] = [
    # Identification / year
    Field("DOB_YY", 9, 12, "Birth year"),
    # Maternal age
    Field("MAGER", 75, 76, "Mother's age in years"),
    Field("MAGER9", 79, 79, "Mother's age recode 9"),
    # Residence status (1–3 U.S.; 4 foreign)
    Field("RESTATUS", 104, 104, "Residence status"),
    # Race / ethnicity
    Field("MRACE31", 105, 106, "Mother's race recode 31"),
    Field("MRACE6", 107, 107, "Mother's race recode 6"),
    Field("MRACE15", 108, 109, "Mother's race recode 15"),
    Field("MHISP_R", 115, 115, "Mother's Hispanic origin recode"),
    Field("MRACEHISP", 117, 117, "Mother's race/Hispanic origin recode"),
    # Education
    Field("MEDUC", 124, 124, "Mother's education (1–8; 9=unknown)"),
    # Birth order
    Field("LBO_REC", 179, 179, "Live birth order recode"),
    Field("TBO_REC", 182, 182, "Total birth order recode"),
    # Prenatal care
    Field("PRECARE", 224, 225, "Month prenatal care began (00=none; 99=unknown)"),
    Field("PRECARE5", 227, 227, "Month PNC began recode 5"),
    # Tobacco
    Field("CIG0_R", 261, 261, "Cigarettes before pregnancy recode"),
    Field("CIG_REC", 269, 269, "Cigarette smoking during pregnancy (Y/N/U)"),
    # BMI / weight
    Field("BMI", 283, 286, "Pre-pregnancy BMI (xx.x; 99.9=unknown)"),
    Field("BMI_R", 287, 287, "BMI recode"),
    # Diabetes / hypertension risk factors
    Field("RF_PDIAB", 313, 313, "Prepregnancy diabetes (Y/N/U)"),
    Field("RF_GDIAB", 314, 314, "Gestational diabetes (Y/N/U)"),
    Field("RF_PHYPE", 315, 315, "Prepregnancy hypertension (Y/N/U)"),
    Field("RF_GHYPE", 316, 316, "Gestational hypertension (Y/N/U)"),
    Field("RF_EHYPE", 317, 317, "Eclampsia (Y/N/U)"),
    Field("RF_PPTERM", 318, 318, "Previous preterm birth (Y/N/U)"),
    # Infections
    Field("IP_GON", 343, 343, "Gonorrhea"),
    Field("IP_SYPH", 344, 344, "Syphilis"),
    Field("IP_CHLAM", 345, 345, "Chlamydia"),
    Field("IP_HEPB", 346, 346, "Hepatitis B"),
    Field("IP_HEPC", 347, 347, "Hepatitis C"),
    # Delivery method
    Field("RDMETH_REC", 407, 407, "Delivery method recode detail"),
    Field("DMETH_REC", 408, 408, "Delivery method recode (1=vaginal, 2=C-section)"),
    # Payment
    Field("PAY", 435, 435, "Source of payment for delivery"),
    Field("PAY_REC", 436, 436, "Payment recode"),
    # Apgar
    Field("APGAR5", 444, 445, "Five-minute Apgar score (00–10; 99=unknown)"),
    Field("APGAR5R", 446, 446, "Five-minute Apgar recode"),
    # Plurality
    Field("DPLURAL", 454, 454, "Plurality recode"),
    # Sex of infant
    Field("SEX", 475, 475, "Sex of infant (M/F)"),
    # Gestational age (obstetric estimate)
    Field("OEGest_Comb", 499, 500, "Obstetric estimate of gestation (weeks)"),
    Field("OEGest_R10", 501, 502, "OE gestation recode 10"),
    Field("OEGest_R3", 503, 503, "OE gestation recode 3 (1=<37, 2=37+, 3=NS)"),
    # Birth weight
    Field("DBWT", 504, 507, "Birth weight in grams (9999=not stated)"),
    # Abnormal conditions of newborn
    Field("AB_AVEN1", 517, 517, "Assisted ventilation immediate"),
    Field("AB_AVEN6", 518, 518, "Assisted ventilation >6 hours"),
    Field("AB_NICU", 519, 519, "Admission to NICU"),
    Field("AB_SURF", 520, 520, "Surfactant"),
    Field("AB_ANTI", 521, 521, "Antibiotics for suspected neonatal sepsis"),
    Field("AB_SEIZ", 522, 522, "Seizure or serious neurologic dysfunction"),
]

FIELD_BY_NAME: Dict[str, Field] = {f.name: f for f in NATALITY_FIELDS}


def layout_as_tuples() -> List[Tuple[str, int, int]]:
    """Return [(name, start, end), ...] for documentation / tests."""
    return [(f.name, f.start, f.end) for f in NATALITY_FIELDS]


# Expected U.S. birth counts (NCHS published totals) for QA soft checks.
# Sources: NCHS NVSS birth reports / data briefs.
NCHS_US_BIRTH_TOTALS: Dict[int, int] = {
    2016: 3_945_875,
    2017: 3_855_500,
    2018: 3_791_712,
    2019: 3_747_540,
    2020: 3_613_647,
    2021: 3_664_292,
    2022: 3_667_758,
    2023: 3_596_017,
    2024: 3_622_673,
}

CDC_FTP_BASE = "https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Datasets/DVS/natality"
USERGUIDE_BASE = (
    "https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Dataset_Documentation/DVS/natality"
)


def data_url(year: int) -> str:
    return f"{CDC_FTP_BASE}/Nat{year}us.zip"


def userguide_url(year: int) -> str:
    if year in (2018, 2019):
        return f"{USERGUIDE_BASE}/UserGuide{year}-508.pdf"
    return f"{USERGUIDE_BASE}/UserGuide{year}.pdf"
