#!/usr/bin/env python3
"""Complete remaining logistic models + key findings + figures from existing tables."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from natality.analyze import (  # noqa: E402
    education_gradient,
    extract_key_findings,
    fit_logistic,
    load_analysis_frames,
    pnc_gradient,
)
from natality.figures import generate_all_figures  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
LOG = logging.getLogger("finish")


def main():
    results = ROOT / "results"
    models_dir = results / "models"
    tables = results / "tables"
    models_dir.mkdir(parents=True, exist_ok=True)

    paths = sorted((ROOT / "data" / "processed").glob("natality_analysis_*.parquet"))
    LOG.info("Loading %s parquets...", len(paths))
    df = load_analysis_frames(paths)
    LOG.info("Loaded %s rows", f"{len(df):,}")

    outcomes = ["preterm", "lbw", "cesarean", "nicu", "low_apgar5"]
    model_results = {}

    for oc in outcomes:
        out_json = models_dir / f"logit_{oc}.json"
        if out_json.exists():
            LOG.info("SKIP model %s (exists)", oc)
            with open(out_json, encoding="utf-8") as f:
                model_results[oc] = json.load(f)
            continue
        LOG.info("Fitting %s...", oc)
        fit_df = df
        if len(df) > 800_000:
            pos = df[df[oc] == 1]
            neg = df[df[oc] == 0]
            n_pos = min(len(pos), 150_000)
            n_neg = min(len(neg), 300_000)
            pos_s = pos.sample(n=n_pos, random_state=42) if len(pos) > n_pos else pos
            neg_s = neg.sample(n=n_neg, random_state=42) if len(neg) > n_neg else neg
            fit_df = pd.concat([pos_s, neg_s], ignore_index=True)
            LOG.info("  sample %s", f"{len(fit_df):,}")
        res = fit_logistic(fit_df, oc)
        res["sampled_for_model"] = len(df) > 800_000
        res["full_n"] = int(len(df))
        model_results[oc] = res
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(res, f, indent=2, default=str)
        if "coefficients" in res:
            pd.DataFrame(res["coefficients"]).to_csv(
                models_dir / f"logit_{oc}_coefs.csv", index=False
            )
        LOG.info("  done: %s", "ok" if "coefficients" in res else res.get("error"))

    trends = pd.read_csv(tables / "yearly_trends.csv")
    gaps = pd.read_csv(tables / "black_white_gaps.csv")
    key = extract_key_findings(df, trends, gaps, model_results)
    with open(tables / "key_findings.json", "w", encoding="utf-8") as f:
        json.dump(key, f, indent=2, default=str)
    LOG.info("key findings: %s", json.dumps({k: key[k] for k in list(key)[:20]}, default=str)[:1500])

    figs = generate_all_figures(results)
    LOG.info("figures: %s", figs)

    manifest = {
        "n_births": int(len(df)),
        "years": key.get("years"),
        "models": {k: str(models_dir / f"logit_{k}.json") for k in model_results},
        "figures": figs,
        "key_findings": key,
    }
    with open(results / "analysis_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, default=str)
    LOG.info("Wrote analysis_manifest.json")


if __name__ == "__main__":
    main()
