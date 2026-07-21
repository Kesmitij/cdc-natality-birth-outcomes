"""Unit tests for fixed-width parser and synthetic fixtures."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from natality.layouts import FIELD_BY_NAME, NATALITY_FIELDS
from natality.parser import build_synthetic_line, extract_fields, parse_lines
from natality.variables import (
    cesarean,
    construct_record,
    education_label,
    low_birth_weight,
    low_apgar5,
    preterm,
    race_ethnicity,
    tobacco_use,
)


def test_field_slices_non_overlapping_known_core():
    """Core fields used in analysis have positive width and known starts."""
    assert FIELD_BY_NAME["MAGER"].start == 75
    assert FIELD_BY_NAME["MAGER"].end == 76
    assert FIELD_BY_NAME["DBWT"].start == 504
    assert FIELD_BY_NAME["OEGest_Comb"].start == 499
    assert FIELD_BY_NAME["OEGest_R3"].start == 503
    assert FIELD_BY_NAME["AB_NICU"].name == "AB_NICU"
    for f in NATALITY_FIELDS:
        assert f.width >= 1
        assert f.start >= 1
        assert f.end >= f.start


def test_extract_fields_from_synthetic_line():
    values = {
        "DOB_YY": "2020",
        "MAGER": "28",
        "MRACEHISP": "1",
        "MEDUC": "6",
        "OEGest_Comb": "39",
        "OEGest_R3": "2",
        "DBWT": "3400",
        "DMETH_REC": "1",
        "AB_NICU": "N",
        "APGAR5": "09",
        "CIG_REC": "N",
        "RESTATUS": "1",
        "PRECARE5": "1",
        "DPLURAL": "1",
        "PAY_REC": "2",
        "RF_PDIAB": "N",
        "RF_GDIAB": "N",
        "RF_PHYPE": "N",
        "RF_GHYPE": "N",
        "RF_EHYPE": "N",
        "LBO_REC": "1",
        "BMI": "24.5",
        "BMI_R": "2",
    }
    line = build_synthetic_line(values)
    parsed = extract_fields(line)
    assert parsed["DOB_YY"] == "2020"
    assert parsed["MAGER"] == "28"
    assert parsed["DBWT"] == "3400"
    assert parsed["OEGest_R3"] == "2"
    assert parsed["MRACEHISP"] == "1"
    assert parsed["MEDUC"] == "6"
    assert parsed["AB_NICU"] == "N"


def test_preterm_and_lbw_coding():
    term = {
        "OEGest_R3": "2",
        "OEGest_Comb": "39",
        "DBWT": "3400",
    }
    pre = {
        "OEGest_R3": "1",
        "OEGest_Comb": "34",
        "DBWT": "2100",
    }
    missing = {
        "OEGest_R3": "",
        "OEGest_Comb": "99",
        "DBWT": "9999",
    }
    assert preterm(term) == 0
    assert preterm(pre) == 1
    assert preterm(missing) is None
    assert low_birth_weight(term) == 0
    assert low_birth_weight(pre) == 1
    assert low_birth_weight(missing) is None


def test_not_stated_not_treated_as_zero():
    """Unknown codes must not enter denominators as non-events."""
    raw = {
        "DOB_YY": "2021",
        "MAGER": "99",
        "MEDUC": "9",
        "MRACEHISP": "8",
        "OEGest_R3": "",
        "OEGest_Comb": "99",
        "DBWT": "9999",
        "DMETH_REC": "9",
        "AB_NICU": "U",
        "APGAR5": "99",
        "CIG_REC": "U",
        "RESTATUS": "1",
        "PRECARE5": "5",
        "DPLURAL": "",
        "PAY_REC": "9",
        "RF_PDIAB": "U",
        "RF_GDIAB": "U",
        "RF_PHYPE": "U",
        "RF_GHYPE": "U",
        "RF_EHYPE": "U",
        "BMI": "99.9",
        "LBO_REC": "9",
    }
    rec = construct_record(raw)
    assert rec["maternal_age"] is None
    assert rec["education"] is None
    assert rec["race_eth"] is None
    assert rec["preterm"] is None
    assert rec["lbw"] is None
    assert rec["cesarean"] is None
    assert rec["nicu"] is None
    assert rec["low_apgar5"] is None
    assert rec["tobacco"] is None
    assert rec["obesity"] is None


def test_construct_healthy_term_singleton():
    raw = {
        "DOB_YY": "2019",
        "MAGER": "31",
        "MRACEHISP": "2",
        "MHISP_R": "0",
        "MEDUC": "3",
        "PRECARE5": "1",
        "PRECARE": "02",
        "CIG_REC": "N",
        "BMI": "27.0",
        "BMI_R": "3",
        "RF_PDIAB": "N",
        "RF_GDIAB": "N",
        "RF_PHYPE": "N",
        "RF_GHYPE": "N",
        "RF_EHYPE": "N",
        "PAY_REC": "1",
        "DPLURAL": "1",
        "OEGest_Comb": "38",
        "OEGest_R3": "2",
        "DBWT": "3100",
        "APGAR5": "08",
        "DMETH_REC": "2",
        "RDMETH_REC": "3",
        "LBO_REC": "1",
        "AB_NICU": "N",
        "AB_ANTI": "N",
        "IP_GON": "N",
        "IP_SYPH": "N",
        "IP_CHLAM": "N",
        "IP_HEPB": "N",
        "IP_HEPC": "N",
        "RESTATUS": "1",
    }
    rec = construct_record(raw)
    assert rec["year"] == 2019
    assert rec["maternal_age"] == 31
    assert rec["race_eth"] == "NH Black"
    assert rec["education"] == "HS / GED"
    assert rec["pnc_timing"] == "1st trimester"
    assert rec["preterm"] == 0
    assert rec["lbw"] == 0
    assert rec["cesarean"] == 1
    assert rec["low_risk_cesarean"] == 1  # nullip term singleton cesarean
    assert rec["nicu"] == 0
    assert rec["low_apgar5"] == 0
    assert rec["tobacco"] == 0
    assert rec["payment"] == "Medicaid"
    assert rec["infection"] == 0


def test_parse_lines_iterator():
    lines = [
        build_synthetic_line({"DOB_YY": "2018", "MAGER": "25", "DBWT": "3000", "OEGest_R3": "2"}),
        "",
        build_synthetic_line({"DOB_YY": "2018", "MAGER": "40", "DBWT": "1400", "OEGest_R3": "1"}),
    ]
    rows = list(parse_lines(lines))
    assert len(rows) == 2
    assert rows[0]["MAGER"] == "25"
    assert rows[1]["DBWT"] == "1400"


def test_low_apgar_and_cesarean_edges():
    assert low_apgar5({"APGAR5": "06"}) == 1
    assert low_apgar5({"APGAR5": "07"}) == 0
    assert low_apgar5({"APGAR5": "99"}) is None
    assert cesarean({"DMETH_REC": "1"}) == 0
    assert cesarean({"DMETH_REC": "2"}) == 1
    assert tobacco_use({"CIG_REC": "Y"}) == 1
    assert education_label({"MEDUC": "7"}) == "Graduate"
    assert race_ethnicity({"MRACEHISP": "7"}) == "Hispanic"


def test_fixture_file_if_present():
    fixture = ROOT / "data" / "fixtures" / "synthetic_records.txt"
    if not fixture.exists():
        pytest.skip("fixture not written yet")
    text = fixture.read_text(encoding="latin-1")
    rows = list(parse_lines(text.splitlines()))
    assert len(rows) >= 2
    recs = [construct_record(r) for r in rows]
    assert any(r["preterm"] == 1 for r in recs)
    assert any(r["preterm"] == 0 for r in recs)
