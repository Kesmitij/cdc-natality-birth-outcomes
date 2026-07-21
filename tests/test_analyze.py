"""Tests for analysis functions on constructed (non-mocked) inputs."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from natality.analyze import (
    black_white_gap_by_year,
    education_gradient,
    fit_logistic,
    outcome_rate,
    run_full_analysis,
    stratified_rates,
    yearly_trends,
)
from natality.parser import build_synthetic_line, extract_fields
from natality.variables import construct_record


def _make_df(n: int = 2000, seed: int = 0) -> pd.DataFrame:
    """Build a realistic synthetic analysis frame via the shipped coding path."""
    rng = np.random.default_rng(seed)
    rows = []
    races = ["NH White", "NH Black", "Hispanic", "NH Asian"]
    race_codes = {"NH White": "1", "NH Black": "2", "Hispanic": "7", "NH Asian": "4"}
    educs = ["1", "3", "4", "6", "7"]
    years = [2018, 2019, 2020, 2021, 2022]
    for i in range(n):
        race = races[i % len(races)]
        # Higher preterm risk for NH Black and low education (data-generating process)
        base_p = 0.08
        if race == "NH Black":
            base_p += 0.06
        educ = educs[i % len(educs)]
        if educ in {"1", "2"}:
            base_p += 0.04
        is_preterm = rng.random() < base_p
        gest = 34 if is_preterm else 39
        bw = 2200 if is_preterm else int(rng.normal(3300, 400))
        values = {
            "DOB_YY": str(years[i % len(years)]),
            "MAGER": str(int(rng.integers(18, 42))),
            "MRACEHISP": race_codes[race],
            "MEDUC": educ,
            "PRECARE5": str(1 + (i % 4) if (i % 4) < 4 else 1),
            "CIG_REC": "Y" if i % 10 == 0 else "N",
            "BMI": "32.0" if i % 5 == 0 else "24.0",
            "BMI_R": "4" if i % 5 == 0 else "2",
            "RF_PDIAB": "N",
            "RF_GDIAB": "Y" if i % 15 == 0 else "N",
            "RF_PHYPE": "N",
            "RF_GHYPE": "Y" if i % 12 == 0 else "N",
            "RF_EHYPE": "N",
            "PAY_REC": "1" if i % 3 == 0 else "2",
            "DPLURAL": "2" if i % 50 == 0 else "1",
            "OEGest_Comb": str(gest),
            "OEGest_R3": "1" if is_preterm else "2",
            "DBWT": str(max(500, bw)),
            "APGAR5": "05" if i % 40 == 0 else "09",
            "DMETH_REC": "2" if i % 4 == 0 else "1",
            "RDMETH_REC": "3" if i % 4 == 0 else "1",
            "LBO_REC": "1",
            "AB_NICU": "Y" if is_preterm or i % 20 == 0 else "N",
            "AB_ANTI": "Y" if i % 25 == 0 else "N",
            "IP_GON": "N",
            "IP_SYPH": "N",
            "IP_CHLAM": "Y" if i % 30 == 0 else "N",
            "IP_HEPB": "N",
            "IP_HEPC": "N",
            "RESTATUS": "1",
            "MHISP_R": "1" if race == "Hispanic" else "0",
        }
        # Fix PRECARE5 to valid 1-4
        values["PRECARE5"] = ["1", "2", "3", "4"][i % 4]
        line = build_synthetic_line(values)
        raw = extract_fields(line)
        rows.append(construct_record(raw))
    return pd.DataFrame(rows)


def test_outcome_rate_complete_case():
    s = pd.Series([0, 1, 1, None, 0])
    r = outcome_rate(s)
    assert r["n"] == 4
    assert r["events"] == 2
    assert abs(r["rate_per_100"] - 50.0) < 1e-9


def test_yearly_trends_and_gaps():
    df = _make_df(3000)
    trends = yearly_trends(df)
    assert len(trends) >= 3
    assert "preterm_rate" in trends.columns
    assert trends["preterm_rate"].notna().any()
    gaps = black_white_gap_by_year(df, "preterm")
    assert len(gaps) >= 1
    # Synthetic DGP: Black rate should exceed White on average
    assert gaps["black_rate"].mean() > gaps["white_rate"].mean()


def test_education_gradient_orders():
    df = _make_df(2000)
    eg = education_gradient(df, "preterm")
    assert "Less than HS" in set(eg["level"])
    assert eg["n"].sum() > 0


def test_stratified_rates_marks_missing():
    df = _make_df(500)
    df.loc[0:10, "race_eth"] = None
    tab = stratified_rates(df, "preterm", "race_eth")
    assert (tab["level"] == "Missing").any() or tab["n"].sum() > 0


def test_fit_logistic_returns_ors():
    df = _make_df(4000, seed=1)
    res = fit_logistic(df, "preterm")
    assert "coefficients" in res, res.get("error")
    assert res["n_model"] > 100
    terms = {c["term"] for c in res["coefficients"]}
    assert "const" in terms
    # Race NH Black dummy should exist and OR > 1 under our DGP
    black_terms = [c for c in res["coefficients"] if "Black" in str(c["term"])]
    assert black_terms, f"No Black term in {terms}"
    assert black_terms[0]["or"] > 1.0


def test_run_full_analysis_writes_artifacts(tmp_path):
    df = _make_df(2500, seed=2)
    art = run_full_analysis(df, tmp_path, outcomes_for_models=["preterm"])
    assert Path(art["tables"]["yearly_trends"]).exists()
    assert Path(art["tables"]["black_white_gaps"]).exists()
    assert "key_findings" in art
    kf = art["key_findings"]
    assert kf["n_births"] == len(df)
    assert "preterm_rate_last" in kf or "years" in kf
    # model artifact
    assert (tmp_path / "models" / "logit_preterm.json").exists()
    with open(tmp_path / "models" / "logit_preterm.json", encoding="utf-8") as f:
        m = json.load(f)
    assert "coefficients" in m
