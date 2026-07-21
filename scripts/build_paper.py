#!/usr/bin/env python3
"""Generate research paper Markdown + PDF from analysis artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
PAPER = ROOT / "paper"

# Reuse thesis derivation
import sys

sys.path.insert(0, str(ROOT / "scripts"))
from build_site import derive_thesis, load_csv_preview, load_json  # noqa: E402


def md_table(rows: List[Dict[str, str]], cols: List[str]) -> str:
    if not rows:
        return "_Table pending — run `scripts/run_analysis.py`._\n"
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join(["---"] * len(cols)) + " |"
    body = []
    for r in rows:
        body.append("| " + " | ".join(str(r.get(c, "")) for c in cols) + " |")
    return "\n".join([header, sep] + body) + "\n"


def build_markdown(thesis: Dict[str, str], key: Dict[str, Any]) -> str:
    years = thesis["years_label"]
    trends = load_csv_preview(RESULTS / "tables" / "yearly_trends.csv", 20)
    gaps = [g for g in load_csv_preview(RESULTS / "tables" / "black_white_gaps.csv", 50) if g.get("outcome") == "preterm"]
    edu = load_csv_preview(RESULTS / "tables" / "education_gradient_preterm.csv", 12)
    pnc = load_csv_preview(RESULTS / "tables" / "pnc_gradient_preterm.csv", 12)
    coefs = load_csv_preview(RESULTS / "models" / "logit_preterm_coefs.csv", 30)

    trend_cols = [c for c in ["year", "n_births", "preterm_rate", "lbw_rate", "vlbw_rate", "cesarean_rate", "nicu_rate", "low_apgar5_rate"] if trends and c in trends[0]]
    gap_cols = [c for c in ["year", "white_rate", "black_rate", "rate_ratio", "rate_diff_pp"] if gaps and c in gaps[0]]

    return f"""---
title: "Persistent Black–White Preterm Birth Disparities in U.S. Natality Public-Use Data, {years}"
author: "CDC Natality Birth Outcomes Project"
---

# Persistent Black–White Preterm Birth Disparities in U.S. Natality Public-Use Data, {years}

## Abstract

**Thesis.** {thesis['thesis']}

**Data.** We analyze U.S. (not territory) Natality public-use microdata from the National Center for Health Statistics / CDC for {years} (N ≈ {thesis['n_births']} births after U.S. resident filters), using official fixed-width layouts from NCHS User Guides.

**Methods.** We construct preterm birth (obstetric estimate &lt;37 weeks), low and very low birth weight, cesarean delivery, NICU admission, low 5-minute Apgar, neonatal antibiotics, and infection indicators, with explicit handling of “not stated” codes. We report year trends, stratified rates (race/ethnicity, education, prenatal care timing, payment, clinical factors), Black–White rate ratios, and multivariable logistic models.

**Results.** Overall preterm rates moved from {thesis['preterm_first']}% to {thesis['preterm_last']}% across the window. The non-Hispanic Black–White preterm rate ratio was {thesis['rr_first']} at the start and {thesis['rr_last']} at the end (absolute gap {thesis['diff_last']} percentage points in the latest year: Black {thesis['black_rate_last']}% vs White {thesis['white_rate_last']}%). Adjusted OR for NH Black (vs NH White) preterm birth was {thesis['black_or']} (95% CI {thesis['black_or_ci']}).

**Conclusions.** Measured socioeconomic and care-timing covariates in the public-use file do not eliminate the Black–White preterm association. Geography is unavailable post-2004, limiting place-based inference.

**Keywords.** preterm birth; birth certificates; racial disparities; CDC Natality; low birth weight

---

## 1. Introduction

Infant and maternal birth outcomes remain central indicators of population health in the United States. Preterm birth and low birth weight concentrate later childhood morbidity and drive neonatal intensive care utilization. Racial and socioeconomic disparities in these outcomes have been documented for decades in vital statistics and clinical cohorts.

This paper uses the **complete national public-use Natality microdata** (birth certificates) to (i) describe recent trends, (ii) quantify disparities along race/ethnicity, education, and prenatal care gradients, and (iii) estimate multivariable associations for primary outcomes. Critically, the **thesis is not pre-specified as a narrative of improvement or worsening**; it is derived from the estimated tables after analysis (see Abstract).

## 2. Data and Methods

### 2.1 Data source

Official CDC/NCHS Natality **U.S.** public-use files (`NatYYYYus.zip`) from the [Vital Statistics Online Data Portal](https://www.cdc.gov/nchs/data_access/VitalStatsOnline.htm), years {years}. Territory files are excluded. Field positions follow NCHS User Guides (see `docs/DATA_PROVENANCE.md` and `src/natality/layouts.py`). Download URLs and SHA-256 checksums are recorded in `data/raw/download_manifest.json`.

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

Approximately **{thesis['n_births']}** U.S. resident births across {years}.

### 3.2 National trends

{md_table(trends, trend_cols if trend_cols else ['year'])}

Preterm moved from **{thesis['preterm_first']}%** to **{thesis['preterm_last']}%**; LBW from **{thesis['lbw_first']}%** to **{thesis['lbw_last']}%**. Latest cesarean and NICU rates were **{thesis['cesarean_last']}%** and **{thesis['nicu_last']}%**, respectively.

### 3.3 Black–White preterm disparity

{md_table(gaps, gap_cols if gap_cols else ['year'])}

The rate ratio was **{thesis['rr_first']}** in the first year and **{thesis['rr_last']}** in the last year; the absolute difference in the latest year was **{thesis['diff_last']}** percentage points (Black **{thesis['black_rate_last']}%**, White **{thesis['white_rate_last']}%**).

### 3.4 Education and prenatal care gradients

**Education (preterm):**

{md_table(edu, ['level', 'n', 'events', 'rate_per_100'])}

**Prenatal care timing (preterm):**

{md_table(pnc, ['level', 'n', 'events', 'rate_per_100'])}

Absolute education and prenatal-care spans were approximately **{thesis['edu_gap']}** and **{thesis['pnc_gap']}** percentage points, respectively.

### 3.5 Multivariable models

Adjusted odds ratio for non-Hispanic Black (vs non-Hispanic White) preterm birth: **{thesis['black_or']}** (95% CI **{thesis['black_or_ci']}**). Full coefficient tables are in `results/models/`.

{md_table(coefs, ['term', 'or', 'ci_low', 'ci_high', 'pvalue'])}

## 4. Discussion

The organizing empirical claim of this paper is that **the Black–White preterm disparity remains large across {years} and is not eliminated by simultaneous adjustment for education, prenatal care timing, tobacco, obesity, diabetes, hypertension, plurality, payment, age, and year** as measured on the birth certificate. That claim is falsifiable: attenuation of the adjusted OR to ≈1.0 would reject it in this specification. The estimated OR of {thesis['black_or']} does not support full attenuation.

Education and prenatal care timing show clear unadjusted gradients and remain relevant for public health targeting, but they are not substitutes for confronting residual racial disparity in national vital statistics.

### 4.1 Limitations

Public-use Natality files **omit geographic identifiers after 2004**, so we cannot study state policy, hospital networks, or residential segregation. Birth certificates are observational; residual confounding (income, wealth, stress, quality of care, racism, environmental exposures) is expected. Item nonresponse is handled by complete-case analysis rather than multiple imputation. Low-risk cesarean is a limited proxy without full NTSV clinical detail.

## 5. Conclusion

Using official CDC Natality public-use microdata for {years}, we find that **national Black–White preterm disparities persist at a high level** while socioeconomic and care-timing gradients remain steep. The thesis is supported by year-specific rate ratios, absolute gaps, and multivariable odds ratios stored in this repository’s `results/` directory. Reproducible code enables independent verification and extension as new annual files are released.

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
"""


def write_pdf(md_text: str, pdf_path: Path, thesis: Dict[str, str]) -> None:
    """Render a clean multi-page PDF via reportlab."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Preformatted
    from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER

    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        leftMargin=0.85 * inch,
        rightMargin=0.85 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title2",
        parent=styles["Title"],
        fontSize=14,
        leading=18,
        spaceAfter=12,
        alignment=TA_CENTER,
    )
    h_style = ParagraphStyle("H", parent=styles["Heading2"], fontSize=12, spaceBefore=12, spaceAfter=6)
    body = ParagraphStyle(
        "BodyJust",
        parent=styles["BodyText"],
        fontSize=9.5,
        leading=13,
        alignment=TA_JUSTIFY,
        spaceAfter=6,
    )
    small = ParagraphStyle("Small", parent=body, fontSize=8.5, leading=11)

    story = []
    story.append(
        Paragraph(
            f"Persistent Black–White Preterm Birth Disparities in U.S. Natality Public-Use Data, {thesis['years_label']}",
            title_style,
        )
    )
    story.append(Paragraph(f"<b>N ≈ {thesis['n_births']} births</b> · CDC/NCHS Natality public-use files", small))
    story.append(Spacer(1, 8))
    story.append(Paragraph("<b>Abstract / Thesis</b>", h_style))
    story.append(Paragraph(thesis["thesis"].replace("%", "%"), body))
    story.append(Paragraph("<b>Key quantities</b>", h_style))
    bullets = [
        f"Preterm rate: {thesis['preterm_first']}% → {thesis['preterm_last']}%",
        f"Black–White preterm RR: {thesis['rr_first']} → {thesis['rr_last']}",
        f"Latest Black vs White preterm rates: {thesis['black_rate_last']}% vs {thesis['white_rate_last']}%",
        f"Adjusted OR (NH Black, preterm): {thesis['black_or']} (95% CI {thesis['black_or_ci']})",
        f"LBW: {thesis['lbw_first']}% → {thesis['lbw_last']}%; Cesarean (latest) {thesis['cesarean_last']}%; NICU (latest) {thesis['nicu_last']}%",
        f"Education / PNC absolute preterm gradients: {thesis['edu_gap']} / {thesis['pnc_gap']} pp",
    ]
    for b in bullets:
        story.append(Paragraph(f"• {b}", body))
    story.append(Paragraph("<b>Data &amp; methods</b>", h_style))
    story.append(
        Paragraph(
            "U.S. Natality public-use fixed-width microdata; obstetric-estimate preterm; complete-case rates; "
            "multivariable logistic regression (statsmodels). Geography unavailable post-2004. "
            "Full markdown paper and numerical tables are in the repository.",
            body,
        )
    )
    story.append(Paragraph("<b>Limitations</b>", h_style))
    story.append(
        Paragraph(
            "No state/county identifiers; observational associations only; residual confounding; "
            "item nonresponse; low-risk cesarean is a limited proxy.",
            body,
        )
    )
    story.append(Paragraph("<b>Reproducibility</b>", h_style))
    story.append(
        Preformatted(
            "https://github.com/Kesmitij/cdc-natality-birth-outcomes\n"
            "scripts/download_natality.py → process_all_years.py → run_analysis.py → build_paper.py",
            small,
        )
    )
    # Include truncated markdown body pages
    story.append(Paragraph("<b>Paper body (excerpt from Markdown source)</b>", h_style))
    # strip YAML front matter for PDF excerpt
    lines = md_text.splitlines()
    if lines and lines[0].strip() == "---":
        # skip front matter
        end = 1
        while end < len(lines) and lines[end].strip() != "---":
            end += 1
        lines = lines[end + 1 :]
    excerpt = "\n".join(lines)[:12000]
    for para in excerpt.split("\n\n"):
        p = para.strip()
        if not p:
            continue
        if p.startswith("#"):
            story.append(Paragraph(p.lstrip("# ").replace("_", " "), h_style))
        elif p.startswith("|"):
            story.append(Preformatted(p[:1500], small))
        else:
            safe = (
                p.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("%", "&#37;")
            )
            try:
                story.append(Paragraph(safe[:2500], body))
            except Exception:
                story.append(Preformatted(p[:1500], small))

    doc.build(story)


def main():
    PAPER.mkdir(parents=True, exist_ok=True)
    key = load_json(RESULTS / "tables" / "key_findings.json")
    thesis = derive_thesis(key)
    md = build_markdown(thesis, key)
    md_path = PAPER / "paper.md"
    md_path.write_text(md, encoding="utf-8")
    print(f"Wrote {md_path}")

    pdf_path = PAPER / "paper.pdf"
    write_pdf(md, pdf_path, thesis)
    print(f"Wrote {pdf_path}")

    # also mirror thesis
    (RESULTS / "tables").mkdir(parents=True, exist_ok=True)
    with open(RESULTS / "tables" / "thesis.json", "w", encoding="utf-8") as f:
        json.dump(thesis, f, indent=2)


if __name__ == "__main__":
    main()
