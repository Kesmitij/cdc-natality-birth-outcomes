"""
Descriptive trends, disparity tables, and multivariable logistic regression
for CDC Natality analysis-ready tables.

Descriptives are vectorized (groupby agg). Logistic models use complete-case
analysis; large datasets may use documented outcome-stratified samples.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

import numpy as np
import pandas as pd

LOG = logging.getLogger(__name__)

PRIMARY_OUTCOMES = [
    "preterm",
    "lbw",
    "vlbw",
    "cesarean",
    "nicu",
    "low_apgar5",
    "infection",
    "ab_anti",
]

STRATIFIERS = [
    "year",
    "age_group",
    "education",
    "race_eth",
    "pnc_timing",
    "tobacco",
    "obesity",
    "diabetes",
    "hypertension",
    "multiple",
    "payment",
]


def load_analysis_frames(
    paths: Sequence[Union[str, Path]],
) -> pd.DataFrame:
    """Load one or more parquet/CSV analysis tables and concatenate."""
    frames = []
    for p in paths:
        p = Path(p)
        if not p.exists():
            LOG.warning("Missing analysis file: %s", p)
            continue
        if p.suffix.lower() == ".parquet":
            frames.append(pd.read_parquet(p))
        elif p.suffix.lower() == ".csv":
            frames.append(pd.read_csv(p, na_values=["", "NA", "nan"]))
        else:
            LOG.warning("Unsupported file type: %s", p)
    if not frames:
        raise FileNotFoundError("No analysis frames loaded")
    df = pd.concat(frames, ignore_index=True)
    for col in PRIMARY_OUTCOMES + [
        "tobacco",
        "obesity",
        "diabetes",
        "hypertension",
        "multiple",
        "education_ord",
        "maternal_age",
        "gest_weeks",
        "bw_g",
        "us_resident",
        "low_risk_cesarean",
    ]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    return df


def outcome_rate(series: pd.Series) -> Dict[str, Any]:
    s = series.dropna()
    if len(s) == 0:
        return {"n": 0, "events": 0, "rate_per_100": np.nan}
    events = int((s == 1).sum())
    n = int(len(s))
    return {"n": n, "events": events, "rate_per_100": 100.0 * events / n}


def yearly_trends(df: pd.DataFrame, outcomes: Sequence[str] = PRIMARY_OUTCOMES) -> pd.DataFrame:
    """Vectorized yearly rates."""
    rows = []
    years = sorted([int(y) for y in df["year"].dropna().unique()])
    for year in years:
        g = df.loc[df["year"] == year]
        row: Dict[str, Any] = {"year": year, "n_births": int(len(g))}
        for oc in outcomes:
            if oc not in g.columns:
                continue
            s = g[oc]
            n = int(s.notna().sum())
            events = int((s == 1).sum())
            row[f"{oc}_n"] = n
            row[f"{oc}_events"] = events
            row[f"{oc}_rate"] = (100.0 * events / n) if n else np.nan
        if "low_risk_cesarean" in g.columns:
            s = g["low_risk_cesarean"]
            n = int(s.notna().sum())
            events = int((s == 1).sum())
            row["low_risk_cesarean_n"] = n
            row["low_risk_cesarean_events"] = events
            row["low_risk_cesarean_rate"] = (100.0 * events / n) if n else np.nan
        rows.append(row)
    return pd.DataFrame(rows).sort_values("year")


def stratified_rates(
    df: pd.DataFrame,
    outcome: str,
    by: str,
) -> pd.DataFrame:
    """Fast complete-case rates by stratifier level."""
    if outcome not in df.columns or by not in df.columns:
        return pd.DataFrame(columns=["outcome", "stratifier", "level", "n", "events", "rate_per_100"])
    sub = df[[by, outcome]].copy()
    sub[by] = sub[by].where(sub[by].notna(), other="Missing")
    # drop missing outcomes only
    sub = sub.dropna(subset=[outcome])
    if sub.empty:
        return pd.DataFrame(columns=["outcome", "stratifier", "level", "n", "events", "rate_per_100"])
    grp = sub.groupby(by, dropna=False)[outcome]
    n = grp.size()
    events = grp.sum()  # 0/1
    out = pd.DataFrame(
        {
            "outcome": outcome,
            "stratifier": by,
            "level": n.index.astype(str),
            "n": n.values.astype(int),
            "events": events.values.astype(int),
            "rate_per_100": 100.0 * events.values / n.values,
        }
    )
    return out.sort_values("rate_per_100", ascending=False)


def disparity_table(
    df: pd.DataFrame,
    outcome: str,
    group_col: str = "race_eth",
    ref_level: str = "NH White",
) -> pd.DataFrame:
    base = stratified_rates(df, outcome, group_col)
    ref = base.loc[base["level"] == ref_level, "rate_per_100"]
    ref_rate = float(ref.iloc[0]) if len(ref) else np.nan
    base["ref_level"] = ref_level
    base["ref_rate_per_100"] = ref_rate
    base["risk_ratio"] = base["rate_per_100"] / ref_rate if ref_rate and ref_rate > 0 else np.nan
    base["rate_diff_pp"] = base["rate_per_100"] - ref_rate
    return base


def black_white_gap_by_year(df: pd.DataFrame, outcome: str = "preterm") -> pd.DataFrame:
    sub = df.loc[df["race_eth"].isin(["NH White", "NH Black"]), ["year", "race_eth", outcome]].dropna(
        subset=[outcome]
    )
    if sub.empty:
        return pd.DataFrame()
    # pivot rates
    rows = []
    for year, g in sub.groupby("year", sort=True):
        w = g.loc[g["race_eth"] == "NH White", outcome]
        b = g.loc[g["race_eth"] == "NH Black", outcome]
        wr = 100.0 * (w == 1).sum() / len(w) if len(w) else np.nan
        br = 100.0 * (b == 1).sum() / len(b) if len(b) else np.nan
        rows.append(
            {
                "year": int(year),
                "outcome": outcome,
                "white_rate": wr,
                "black_rate": br,
                "white_n": int(len(w)),
                "black_n": int(len(b)),
                "rate_ratio": (br / wr) if wr and wr > 0 else np.nan,
                "rate_diff_pp": br - wr if wr == wr else np.nan,
            }
        )
    return pd.DataFrame(rows)


def education_gradient(df: pd.DataFrame, outcome: str = "preterm") -> pd.DataFrame:
    order = ["Less than HS", "HS / GED", "Some college", "Associate", "Bachelor's", "Graduate"]
    tab = stratified_rates(df, outcome, "education")
    tab["education_order"] = tab["level"].apply(lambda x: order.index(x) if x in order else 99)
    return tab.sort_values("education_order")


def pnc_gradient(df: pd.DataFrame, outcome: str = "preterm") -> pd.DataFrame:
    order = ["1st trimester", "2nd trimester", "3rd trimester", "No PNC"]
    tab = stratified_rates(df, outcome, "pnc_timing")
    tab["pnc_order"] = tab["level"].apply(lambda x: order.index(x) if x in order else 99)
    return tab.sort_values("pnc_order")


def fit_logistic(
    df: pd.DataFrame,
    outcome: str,
    predictors: Optional[List[str]] = None,
    max_iter: int = 100,
) -> Dict[str, Any]:
    """Multivariable logistic regression (statsmodels), complete-case."""
    import statsmodels.api as sm

    if predictors is None:
        predictors = [
            "maternal_age",
            "race_eth",
            "education",
            "pnc_timing",
            "tobacco",
            "obesity",
            "diabetes",
            "hypertension",
            "multiple",
            "payment",
            "year",
        ]

    use_cols = [outcome] + [p for p in predictors if p in df.columns]
    d = df[use_cols].dropna()
    n_total = len(df)
    n_model = len(d)
    if n_model < 500:
        return {
            "outcome": outcome,
            "error": f"Insufficient complete cases: {n_model}",
            "n_model": n_model,
            "n_total": n_total,
        }

    y = d[outcome].astype(int)
    parts = []
    ref_notes = {}

    if "maternal_age" in d.columns:
        parts.append(d[["maternal_age"]].astype(float))
    if "year" in d.columns:
        yr = d[["year"]].astype(float)
        yr = yr.rename(columns={"year": "year_c"})
        yr["year_c"] = yr["year_c"] - yr["year_c"].mean()
        parts.append(yr)

    for b in ("tobacco", "obesity", "diabetes", "hypertension", "multiple"):
        if b in d.columns:
            parts.append(d[[b]].astype(float))

    cat_refs = {
        "race_eth": "NH White",
        "education": "HS / GED",
        "pnc_timing": "1st trimester",
        "payment": "Private",
    }
    for col, ref in cat_refs.items():
        if col not in d.columns:
            continue
        cats = sorted([c for c in d[col].dropna().unique() if c != ref])
        s = pd.Categorical(d[col], categories=[ref] + cats)
        dum = pd.get_dummies(s, prefix=col, drop_first=True, dtype=float)
        dum.index = d.index
        parts.append(dum)
        ref_notes[col] = ref

    if not parts:
        return {"outcome": outcome, "error": "No predictors", "n_model": n_model}

    X = pd.concat(parts, axis=1)
    X = sm.add_constant(X, has_constant="add")
    X = X.loc[y.index]

    try:
        res = sm.Logit(y, X).fit(disp=False, maxiter=max_iter, method="newton")
    except Exception as e:
        try:
            res = sm.Logit(y, X).fit(disp=False, maxiter=max_iter, method="bfgs")
        except Exception as e2:
            return {
                "outcome": outcome,
                "error": f"{e} | fallback: {e2}",
                "n_model": n_model,
                "n_total": n_total,
            }

    params = res.params
    conf = res.conf_int()
    conf.columns = ["ci_low", "ci_high"]
    table = pd.DataFrame(
        {
            "term": params.index,
            "coef": params.values,
            "or": np.exp(params.values),
            "ci_low": np.exp(conf["ci_low"].values),
            "ci_high": np.exp(conf["ci_high"].values),
            "pvalue": res.pvalues.values,
            "stderr": res.bse.values,
        }
    )
    return {
        "outcome": outcome,
        "n_model": n_model,
        "n_total": n_total,
        "pct_complete": 100.0 * n_model / n_total if n_total else np.nan,
        "pseudo_r2": float(res.prsquared) if hasattr(res, "prsquared") else None,
        "llf": float(res.llf),
        "aic": float(res.aic),
        "bic": float(res.bic),
        "converged": bool(res.mle_retvals.get("converged", True))
        if getattr(res, "mle_retvals", None)
        else True,
        "reference_levels": ref_notes,
        "coefficients": table.to_dict(orient="records"),
    }


def extract_key_findings(
    df: pd.DataFrame,
    trends: pd.DataFrame,
    gaps: pd.DataFrame,
    model_results: Dict[str, Any],
) -> Dict[str, Any]:
    findings: Dict[str, Any] = {}
    findings["n_births"] = int(len(df))
    findings["years"] = sorted([int(y) for y in df["year"].dropna().unique()])

    for oc in ["preterm", "lbw", "cesarean", "nicu"]:
        col = f"{oc}_rate"
        if col in trends.columns and len(trends):
            t = trends.dropna(subset=[col]).sort_values("year")
            if len(t):
                findings[f"{oc}_first_year"] = int(t.iloc[0]["year"])
                findings[f"{oc}_last_year"] = int(t.iloc[-1]["year"])
                findings[f"{oc}_rate_first"] = float(t.iloc[0][col])
                findings[f"{oc}_rate_last"] = float(t.iloc[-1][col])
                findings[f"{oc}_rate_change_pp"] = float(t.iloc[-1][col] - t.iloc[0][col])

    for oc in ["preterm", "lbw"]:
        g = gaps[gaps["outcome"] == oc].dropna(subset=["rate_ratio"]).sort_values("year") if len(gaps) else gaps
        if len(g):
            findings[f"bw_{oc}_rr_first"] = float(g.iloc[0]["rate_ratio"])
            findings[f"bw_{oc}_rr_last"] = float(g.iloc[-1]["rate_ratio"])
            findings[f"bw_{oc}_diff_first"] = float(g.iloc[0]["rate_diff_pp"])
            findings[f"bw_{oc}_diff_last"] = float(g.iloc[-1]["rate_diff_pp"])
            findings[f"bw_{oc}_black_rate_last"] = float(g.iloc[-1]["black_rate"])
            findings[f"bw_{oc}_white_rate_last"] = float(g.iloc[-1]["white_rate"])

    if "education" in df.columns and "preterm" in df.columns:
        eg = education_gradient(df, "preterm")
        eg_ok = eg[eg["level"] != "Missing"]
        if len(eg_ok):
            findings["edu_preterm"] = eg_ok[["level", "rate_per_100", "n"]].to_dict(orient="records")

    if "pnc_timing" in df.columns and "preterm" in df.columns:
        pg = pnc_gradient(df, "preterm")
        pg_ok = pg[pg["level"] != "Missing"]
        if len(pg_ok):
            findings["pnc_preterm"] = pg_ok[["level", "rate_per_100", "n"]].to_dict(orient="records")

    if "preterm" in model_results and "coefficients" in model_results["preterm"]:
        coefs = model_results["preterm"]["coefficients"]
        findings["preterm_model_ors"] = {
            c["term"]: {
                "or": c["or"],
                "ci_low": c["ci_low"],
                "ci_high": c["ci_high"],
                "pvalue": c["pvalue"],
            }
            for c in coefs
            if c["term"] != "const"
        }
        findings["preterm_model_n"] = model_results["preterm"].get("n_model")
        findings["preterm_model_complete_pct"] = model_results["preterm"].get("pct_complete")

    return findings


def run_full_analysis(
    df: pd.DataFrame,
    output_dir: Union[str, Path],
    outcomes_for_models: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Produce all descriptive tables, disparity analyses, and models."""
    output_dir = Path(output_dir)
    tables = output_dir / "tables"
    models = output_dir / "models"
    figures = output_dir / "figures"
    for d in (tables, models, figures):
        d.mkdir(parents=True, exist_ok=True)

    if outcomes_for_models is None:
        outcomes_for_models = ["preterm", "lbw", "cesarean", "nicu", "low_apgar5"]

    artifacts: Dict[str, Any] = {"tables": {}, "models": {}}

    LOG.info("Yearly trends...")
    trends = yearly_trends(df)
    trends_path = tables / "yearly_trends.csv"
    trends.to_csv(trends_path, index=False)
    artifacts["tables"]["yearly_trends"] = str(trends_path)
    LOG.info("  trends rows=%s", len(trends))

    LOG.info("Stratified rates...")
    strat_frames = []
    strat_outcomes = ["preterm", "lbw", "cesarean", "nicu", "low_apgar5", "vlbw", "infection"]
    strat_bys = [
        "race_eth",
        "education",
        "pnc_timing",
        "age_group",
        "payment",
        "tobacco",
        "obesity",
        "diabetes",
        "hypertension",
        "multiple",
    ]
    for oc in strat_outcomes:
        if oc not in df.columns:
            continue
        for by in strat_bys:
            if by not in df.columns:
                continue
            strat_frames.append(stratified_rates(df, oc, by))
    strat = pd.concat(strat_frames, ignore_index=True) if strat_frames else pd.DataFrame()
    strat_path = tables / "stratified_rates.csv"
    strat.to_csv(strat_path, index=False)
    artifacts["tables"]["stratified_rates"] = str(strat_path)
    LOG.info("  stratified rows=%s", len(strat))

    LOG.info("Black–White gaps...")
    gap_frames = []
    for oc in ["preterm", "lbw", "vlbw", "cesarean", "nicu", "low_apgar5"]:
        if oc in df.columns:
            gap_frames.append(black_white_gap_by_year(df, oc))
    gaps = pd.concat(gap_frames, ignore_index=True) if gap_frames else pd.DataFrame()
    gaps_path = tables / "black_white_gaps.csv"
    gaps.to_csv(gaps_path, index=False)
    artifacts["tables"]["black_white_gaps"] = str(gaps_path)

    for oc in ["preterm", "lbw", "nicu"]:
        if oc not in df.columns:
            continue
        education_gradient(df, oc).to_csv(tables / f"education_gradient_{oc}.csv", index=False)
        pnc_gradient(df, oc).to_csv(tables / f"pnc_gradient_{oc}.csv", index=False)

    for oc in ["preterm", "lbw", "cesarean", "nicu"]:
        if oc in df.columns:
            disparity_table(df, oc, "race_eth", "NH White").to_csv(
                tables / f"disparity_race_{oc}.csv", index=False
            )

    overall = {"n_births": int(len(df)), "years": sorted([int(y) for y in df["year"].dropna().unique()])}
    for oc in PRIMARY_OUTCOMES:
        if oc in df.columns:
            overall[oc] = outcome_rate(df[oc])
    with open(tables / "overall_summary.json", "w", encoding="utf-8") as f:
        json.dump(overall, f, indent=2)
    artifacts["tables"]["overall_summary"] = str(tables / "overall_summary.json")

    model_results: Dict[str, Any] = {}
    for oc in outcomes_for_models:
        if oc not in df.columns:
            continue
        LOG.info("Fitting logistic model for %s (n=%s)...", oc, f"{len(df):,}")
        fit_df = df
        if len(df) > 800_000:
            # Outcome-stratified sample for computational feasibility (documented)
            pos = df[df[oc] == 1]
            neg = df[df[oc] == 0]
            n_pos = min(len(pos), 150_000)
            n_neg = min(len(neg), 300_000)
            pos_s = pos.sample(n=n_pos, random_state=42) if len(pos) > n_pos else pos
            neg_s = neg.sample(n=n_neg, random_state=42) if len(neg) > n_neg else neg
            fit_df = pd.concat([pos_s, neg_s], ignore_index=True)
            LOG.info("  model sample size: %s", f"{len(fit_df):,}")
        res = fit_logistic(fit_df, oc)
        # annotate sampling
        res["sampled_for_model"] = len(df) > 800_000
        res["full_n"] = int(len(df))
        model_results[oc] = res
        with open(models / f"logit_{oc}.json", "w", encoding="utf-8") as f:
            json.dump(res, f, indent=2, default=str)
        if "coefficients" in res:
            pd.DataFrame(res["coefficients"]).to_csv(models / f"logit_{oc}_coefs.csv", index=False)
        LOG.info("  model done: %s", "ok" if "coefficients" in res else res.get("error"))

    artifacts["models"] = {k: str(models / f"logit_{k}.json") for k in model_results}

    key = extract_key_findings(df, trends, gaps, model_results)
    with open(tables / "key_findings.json", "w", encoding="utf-8") as f:
        json.dump(key, f, indent=2, default=str)
    artifacts["key_findings"] = key
    artifacts["key_findings_path"] = str(tables / "key_findings.json")
    LOG.info("Key findings years=%s n=%s", key.get("years"), key.get("n_births"))
    return artifacts
