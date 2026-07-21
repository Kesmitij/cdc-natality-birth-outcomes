"""Generate publication-quality static figures from saved result tables."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Union

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def _style():
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.grid": True,
            "grid.alpha": 0.3,
            "font.size": 11,
            "axes.titlesize": 13,
            "axes.labelsize": 11,
            "figure.dpi": 120,
        }
    )


def fig_yearly_trends(trends_csv: Union[str, Path], out_path: Union[str, Path]) -> Path:
    _style()
    df = pd.read_csv(trends_csv)
    outcomes = [
        ("preterm_rate", "Preterm (<37w)"),
        ("lbw_rate", "Low birth weight"),
        ("cesarean_rate", "Cesarean"),
        ("nicu_rate", "NICU admission"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(10, 7), sharex=True)
    axes = axes.ravel()
    for ax, (col, title) in zip(axes, outcomes):
        if col not in df.columns:
            ax.set_visible(False)
            continue
        ax.plot(df["year"], df[col], marker="o", color="#1f4e79", lw=2)
        ax.set_title(title)
        ax.set_ylabel("Rate per 100 births")
        ax.set_xlabel("Year")
    fig.suptitle("U.S. birth outcome trends (CDC Natality public-use files)", fontweight="bold")
    fig.tight_layout()
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return out_path


def fig_black_white_gap(gaps_csv: Union[str, Path], out_path: Union[str, Path], outcome: str = "preterm") -> Path:
    _style()
    df = pd.read_csv(gaps_csv)
    df = df[df["outcome"] == outcome].sort_values("year")
    fig, ax1 = plt.subplots(figsize=(8, 5))
    ax1.plot(df["year"], df["white_rate"], marker="o", label="NH White", color="#4c78a8")
    ax1.plot(df["year"], df["black_rate"], marker="s", label="NH Black", color="#e45756")
    ax1.set_ylabel("Rate per 100 births")
    ax1.set_xlabel("Year")
    ax1.legend(loc="upper left")
    ax2 = ax1.twinx()
    ax2.plot(df["year"], df["rate_ratio"], marker="D", color="#54a24b", ls="--", label="Rate ratio")
    ax2.set_ylabel("Black / White rate ratio")
    ax2.axhline(1.0, color="gray", ls=":", lw=1)
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="best")
    ax1.set_title(f"Black–White disparity in {outcome.replace('_', ' ')}")
    fig.tight_layout()
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return out_path


def fig_education_gradient(
    edu_csv: Union[str, Path], out_path: Union[str, Path], title: str = "Preterm by maternal education"
) -> Path:
    _style()
    df = pd.read_csv(edu_csv)
    df = df[df["level"] != "Missing"].copy()
    if "education_order" in df.columns:
        df = df.sort_values("education_order")
    fig, ax = plt.subplots(figsize=(8, 5))
    colors = plt.cm.Blues(np.linspace(0.4, 0.9, len(df)))
    ax.barh(df["level"], df["rate_per_100"], color=colors)
    ax.set_xlabel("Rate per 100 births")
    ax.set_title(title)
    for i, (r, n) in enumerate(zip(df["rate_per_100"], df["n"])):
        ax.text(r + 0.05, i, f"{r:.1f} (n={int(n):,})", va="center", fontsize=9)
    fig.tight_layout()
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return out_path


def fig_pnc_gradient(pnc_csv: Union[str, Path], out_path: Union[str, Path]) -> Path:
    _style()
    df = pd.read_csv(pnc_csv)
    df = df[df["level"] != "Missing"].copy()
    if "pnc_order" in df.columns:
        df = df.sort_values("pnc_order")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(df["level"], df["rate_per_100"], color="#f58518")
    ax.set_ylabel("Preterm rate per 100")
    ax.set_title("Preterm birth by timing of prenatal care initiation")
    ax.tick_params(axis="x", rotation=15)
    fig.tight_layout()
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return out_path


def fig_model_ors(model_json: Union[str, Path], out_path: Union[str, Path], top_n: int = 15) -> Path:
    _style()
    with open(model_json, encoding="utf-8") as f:
        res = json.load(f)
    if "coefficients" not in res:
        raise ValueError(res.get("error", "No coefficients"))
    coefs = pd.DataFrame(res["coefficients"])
    coefs = coefs[coefs["term"] != "const"].copy()
    # Prefer non-year terms; sort by |log OR|
    coefs["abs_coef"] = coefs["coef"].abs()
    coefs = coefs.sort_values("abs_coef", ascending=False).head(top_n)
    coefs = coefs.sort_values("or")
    fig, ax = plt.subplots(figsize=(9, 6))
    y = np.arange(len(coefs))
    ax.errorbar(
        coefs["or"],
        y,
        xerr=[coefs["or"] - coefs["ci_low"], coefs["ci_high"] - coefs["or"]],
        fmt="o",
        color="#1f4e79",
        ecolor="#6b7c93",
        capsize=3,
    )
    ax.axvline(1.0, color="crimson", ls="--", lw=1)
    ax.set_yticks(y)
    ax.set_yticklabels(coefs["term"])
    ax.set_xlabel("Odds ratio (95% CI)")
    ax.set_title(f"Multivariable logistic model: {res.get('outcome', '')}")
    ax.set_xscale("log")
    fig.tight_layout()
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return out_path


def generate_all_figures(results_dir: Union[str, Path]) -> Dict[str, str]:
    results_dir = Path(results_dir)
    tables = results_dir / "tables"
    models = results_dir / "models"
    figures = results_dir / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    out: Dict[str, str] = {}

    trends = tables / "yearly_trends.csv"
    if trends.exists():
        p = fig_yearly_trends(trends, figures / "yearly_trends.png")
        out["yearly_trends"] = str(p)

    gaps = tables / "black_white_gaps.csv"
    if gaps.exists():
        for oc in ["preterm", "lbw", "nicu"]:
            try:
                p = fig_black_white_gap(gaps, figures / f"bw_gap_{oc}.png", outcome=oc)
                out[f"bw_gap_{oc}"] = str(p)
            except Exception:
                pass

    edu = tables / "education_gradient_preterm.csv"
    if edu.exists():
        p = fig_education_gradient(edu, figures / "education_gradient_preterm.png")
        out["education_gradient_preterm"] = str(p)

    pnc = tables / "pnc_gradient_preterm.csv"
    if pnc.exists():
        p = fig_pnc_gradient(pnc, figures / "pnc_gradient_preterm.png")
        out["pnc_gradient_preterm"] = str(p)

    logit = models / "logit_preterm.json"
    if logit.exists():
        try:
            p = fig_model_ors(logit, figures / "model_ors_preterm.png")
            out["model_ors_preterm"] = str(p)
        except Exception:
            pass

    return out
