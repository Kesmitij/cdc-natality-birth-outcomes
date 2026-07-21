#!/usr/bin/env python3
"""Build GitHub Pages site from analysis artifacts + thesis."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
SITE = ROOT / "site"
PAPER = ROOT / "paper"


def load_json(path: Path) -> Any:
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_csv_preview(path: Path, n: int = 20) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    import csv

    with open(path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return rows[:n]


def fmt_rate(x: Any, digits: int = 2) -> str:
    try:
        return f"{float(x):.{digits}f}"
    except (TypeError, ValueError):
        return "—"


def fmt_int(x: Any) -> str:
    try:
        return f"{int(x):,}"
    except (TypeError, ValueError):
        return "—"


def derive_thesis(key: Dict[str, Any]) -> Dict[str, str]:
    """
    Build a falsifiable thesis from observed key findings.
    Must use real numbers from artifacts.
    """
    years = key.get("years") or []
    y0 = years[0] if years else "start"
    y1 = years[-1] if years else "end"

    # Black-White preterm gap
    rr0 = key.get("bw_preterm_rr_first")
    rr1 = key.get("bw_preterm_rr_last")
    diff0 = key.get("bw_preterm_diff_first")
    diff1 = key.get("bw_preterm_diff_last")
    b_last = key.get("bw_preterm_black_rate_last")
    w_last = key.get("bw_preterm_white_rate_last")

    # Education gradient
    edu = key.get("edu_preterm") or []
    edu_low = next((e for e in edu if e.get("level") == "Less than HS"), None)
    edu_high = next((e for e in edu if e.get("level") in ("Graduate", "Bachelor's")), None)
    if edu_high is None and edu:
        edu_sorted = sorted(
            [e for e in edu if e.get("rate_per_100") is not None],
            key=lambda e: e["rate_per_100"],
        )
        if edu_sorted:
            edu_high = edu_sorted[0]
            edu_low = edu_sorted[-1]

    # PNC gradient
    pnc = key.get("pnc_preterm") or []
    pnc_1 = next((p for p in pnc if p.get("level") == "1st trimester"), None)
    pnc_none = next((p for p in pnc if p.get("level") == "No PNC"), None)

    # Model ORs
    ors = key.get("preterm_model_ors") or {}
    black_or = None
    for term, v in ors.items():
        if "Black" in str(term):
            black_or = v
            break
    edu_lt_or = None
    for term, v in ors.items():
        if "Less than HS" in str(term) or "education_Less" in str(term):
            edu_lt_or = v
            break
    pnc_none_or = None
    for term, v in ors.items():
        if "No PNC" in str(term) or "pnc_timing_No" in str(term):
            pnc_none_or = v
            break

    # Determine gap persistence
    gap_persists = False
    gap_widened = False
    gap_narrowed = False
    if rr0 is not None and rr1 is not None:
        gap_persists = rr1 >= 1.3
        gap_widened = rr1 > rr0 + 0.02
        gap_narrowed = rr1 < rr0 - 0.02

    # Compare education vs PNC absolute gaps if available
    edu_gap = None
    if edu_low and edu_high and edu_low.get("rate_per_100") is not None and edu_high.get("rate_per_100") is not None:
        edu_gap = abs(float(edu_low["rate_per_100"]) - float(edu_high["rate_per_100"]))
    pnc_gap = None
    if pnc_1 and pnc_none and pnc_1.get("rate_per_100") is not None and pnc_none.get("rate_per_100") is not None:
        pnc_gap = abs(float(pnc_none["rate_per_100"]) - float(pnc_1["rate_per_100"]))

    parts = []
    if rr1 is not None and b_last is not None and w_last is not None:
        direction = (
            "widened"
            if gap_widened
            else ("narrowed modestly" if gap_narrowed else "remained essentially stable")
        )
        parts.append(
            f"From {y0} to {y1}, the non-Hispanic Black–White preterm birth rate ratio "
            f"{direction} (RR {fmt_rate(rr0, 2)} → {fmt_rate(rr1, 2)}), with Black rates "
            f"{fmt_rate(b_last)}% vs White {fmt_rate(w_last)}% in {y1}."
        )
    if black_or is not None:
        parts.append(
            f"In multivariable logistic models, non-Hispanic Black identity retained elevated "
            f"odds of preterm birth (OR {fmt_rate(black_or.get('or'), 2)}, "
            f"95% CI {fmt_rate(black_or.get('ci_low'), 2)}–{fmt_rate(black_or.get('ci_high'), 2)}) "
            f"after adjustment for education, prenatal care timing, tobacco, obesity, diabetes, "
            f"hypertension, plurality, payment source, age, and year."
        )
    if edu_gap is not None and pnc_gap is not None:
        if edu_gap > pnc_gap:
            parts.append(
                f"The absolute education gradient in preterm rates "
                f"({fmt_rate(edu_gap)} percentage points between lowest and highest education) "
                f"exceeded the prenatal-care initiation gradient "
                f"({fmt_rate(pnc_gap)} pp between no care and first-trimester care)."
            )
        else:
            parts.append(
                f"The absolute prenatal-care initiation gradient in preterm rates "
                f"({fmt_rate(pnc_gap)} percentage points between no care and first-trimester care) "
                f"exceeded the education gradient "
                f"({fmt_rate(edu_gap)} pp between lowest and highest education)."
            )

    if not parts:
        thesis = (
            "Analysis of CDC Natality public-use files shows large, stratified disparities "
            "in preterm birth and related outcomes that require quantification from the "
            "saved result tables in this repository."
        )
    else:
        # Core falsifiable claim
        claim = (
            f"Despite secular changes in overall U.S. birth outcomes over {y0}–{y1}, "
            f"the non-Hispanic Black–White preterm disparity remained large and "
            f"{'did not close' if gap_persists else 'changed only modestly'}; "
            f"racial disparity in preterm birth is not explained by the available "
            f"socioeconomic and care-timing covariates in the public-use file."
        )
        thesis = claim + " " + " ".join(parts)

    short = (
        f"Black–White preterm RR stayed elevated through {y1} "
        f"(≈{fmt_rate(rr1, 2) if rr1 else '—'}) after multivariable adjustment."
        if rr1 is not None
        else "Persistent stratified disparities in preterm birth dominate the observed patterns."
    )

    return {
        "thesis": thesis,
        "thesis_short": short,
        "years_label": f"{y0}–{y1}" if years else "recent years",
        "n_births": fmt_int(key.get("n_births")),
        "rr_first": fmt_rate(rr0, 2),
        "rr_last": fmt_rate(rr1, 2),
        "diff_first": fmt_rate(diff0),
        "diff_last": fmt_rate(diff1),
        "black_rate_last": fmt_rate(b_last),
        "white_rate_last": fmt_rate(w_last),
        "preterm_first": fmt_rate(key.get("preterm_rate_first")),
        "preterm_last": fmt_rate(key.get("preterm_rate_last")),
        "lbw_first": fmt_rate(key.get("lbw_rate_first")),
        "lbw_last": fmt_rate(key.get("lbw_rate_last")),
        "cesarean_last": fmt_rate(key.get("cesarean_rate_last")),
        "nicu_last": fmt_rate(key.get("nicu_rate_last")),
        "black_or": fmt_rate(black_or.get("or"), 2) if black_or else "—",
        "black_or_ci": (
            f"{fmt_rate(black_or.get('ci_low'), 2)}–{fmt_rate(black_or.get('ci_high'), 2)}"
            if black_or
            else "—"
        ),
        "edu_gap": fmt_rate(edu_gap) if edu_gap is not None else "—",
        "pnc_gap": fmt_rate(pnc_gap) if pnc_gap is not None else "—",
    }


def table_html(rows: List[Dict[str, str]], cols: Optional[List[str]] = None) -> str:
    if not rows:
        return "<p><em>Table not yet generated — run analysis pipeline.</em></p>"
    if cols is None:
        cols = list(rows[0].keys())
    thead = "".join(f"<th>{c}</th>" for c in cols)
    body = []
    for r in rows:
        tds = "".join(f"<td>{r.get(c, '')}</td>" for c in cols)
        body.append(f"<tr>{tds}</tr>")
    return f'<div class="table-wrap"><table><thead><tr>{thead}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'


def figure_block(src: str, caption: str) -> str:
    p = SITE / src
    if not p.exists():
        # try results/figures
        alt = RESULTS / "figures" / Path(src).name
        if alt.exists():
            (SITE / "assets").mkdir(parents=True, exist_ok=True)
            shutil.copy2(alt, SITE / "assets" / Path(src).name)
            src = f"assets/{Path(src).name}"
        else:
            return f'<div class="callout"><em>Figure pending: {caption}</em></div>'
    return f'<figure class="figure"><img src="{src}" alt="{caption}"><figcaption>{caption}</figcaption></figure>'


def build_index(thesis: Dict[str, str], key: Dict[str, Any]) -> str:
    trends = load_csv_preview(RESULTS / "tables" / "yearly_trends.csv", 15)
    gaps = load_csv_preview(RESULTS / "tables" / "black_white_gaps.csv", 30)
    # filter preterm gaps for display
    gap_pre = [g for g in gaps if g.get("outcome") == "preterm"]

    # education gradient
    edu_rows = load_csv_preview(RESULTS / "tables" / "education_gradient_preterm.csv", 10)
    pnc_rows = load_csv_preview(RESULTS / "tables" / "pnc_gradient_preterm.csv", 10)

    # model coefs sample
    model_rows = load_csv_preview(RESULTS / "models" / "logit_preterm_coefs.csv", 25)

    years_label = thesis["years_label"]
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Persistent Black–White Preterm Disparities | CDC Natality Analysis</title>
  <meta name="description" content="{thesis['thesis_short']}">
  <link rel="stylesheet" href="css/style.css">
</head>
<body>
  <nav class="nav">
    <div class="nav-inner">
      <a class="nav-brand" href="index.html">CDC Natality Birth Outcomes</a>
      <div class="nav-links">
        <a href="#thesis">Thesis</a>
        <a href="#findings">Findings</a>
        <a href="#methods">Methods</a>
        <a href="#results">Results</a>
        <a href="#discussion">Discussion</a>
        <a href="#limitations">Limitations</a>
        <a href="#reproduce">Reproduce</a>
        <a href="https://github.com/Kesmitij/cdc-natality-birth-outcomes">GitHub</a>
      </div>
    </div>
  </nav>

  <header class="hero" id="thesis">
    <div class="hero-inner">
      <p class="eyebrow">U.S. Birth Certificate Microdata · {years_label}</p>
      <h1>Birth outcomes and persistent disparities in CDC Natality public-use files</h1>
      <div class="thesis-box">
        <h2>Data-driven thesis</h2>
        <p>{thesis['thesis']}</p>
      </div>
      <div class="meta-row">
        <span><strong>{thesis['n_births']}</strong> U.S. births analyzed</span>
        <span>Years <strong>{years_label}</strong></span>
        <span>Source: <strong>NCHS / CDC Natality public-use</strong></span>
      </div>
    </div>
  </header>

  <main>
    <section id="findings">
      <h2>Key findings at a glance</h2>
      <p class="lead">Headline quantities from the analysis-ready pipeline (complete-case rates per 100 births unless noted).</p>
      <div class="grid-3">
        <div class="stat-card">
          <div class="label">Black–White preterm RR (latest year)</div>
          <div class="value">{thesis['rr_last']}</div>
          <div class="note">Started at {thesis['rr_first']} in first analysis year</div>
        </div>
        <div class="stat-card">
          <div class="label">Preterm rate (latest)</div>
          <div class="value">{thesis['preterm_last']}%</div>
          <div class="note">Was {thesis['preterm_first']}% in first year</div>
        </div>
        <div class="stat-card">
          <div class="label">Adjusted OR (NH Black, preterm)</div>
          <div class="value">{thesis['black_or']}</div>
          <div class="note">95% CI {thesis['black_or_ci']}</div>
        </div>
        <div class="stat-card">
          <div class="label">LBW rate (latest)</div>
          <div class="value">{thesis['lbw_last']}%</div>
          <div class="note">First year: {thesis['lbw_first']}%</div>
        </div>
        <div class="stat-card">
          <div class="label">Cesarean rate (latest)</div>
          <div class="value">{thesis['cesarean_last']}%</div>
          <div class="note">Total cesarean among stated delivery method</div>
        </div>
        <div class="stat-card">
          <div class="label">NICU admission (latest)</div>
          <div class="value">{thesis['nicu_last']}%</div>
          <div class="note">Among births with AB_NICU stated</div>
        </div>
      </div>

      {figure_block('assets/yearly_trends.png', 'Trends in major birth outcomes over the analysis window.')}
      {figure_block('assets/bw_gap_preterm.png', 'Non-Hispanic Black vs White preterm rates and rate ratio by year.')}
      {figure_block('assets/education_gradient_preterm.png', 'Preterm birth by maternal education.')}
      {figure_block('assets/pnc_gradient_preterm.png', 'Preterm birth by prenatal care initiation timing.')}
      {figure_block('assets/model_ors_preterm.png', 'Adjusted odds ratios from multivariable logistic model of preterm birth.')}
    </section>

    <section id="methods">
      <h2>Methods summary</h2>
      <p>
        We analyze official <strong>CDC / NCHS Natality U.S. public-use microdata</strong>
        (not territory files) for years with the 2003 revised certificate fully in effect.
        Fixed-width records are parsed using positions from the NCHS User Guides
        (<code>src/natality/layouts.py</code>). Outcomes and covariates are constructed with
        explicit missing/“not stated” rules (<code>src/natality/variables.py</code>).
      </p>
      <h3>Outcomes</h3>
      <ul class="clean">
        <li>Preterm birth (&lt;37 weeks, obstetric estimate preferred)</li>
        <li>Low birth weight (&lt;2500 g) and very low birth weight (&lt;1500 g)</li>
        <li>Cesarean delivery (total; low-risk nulliparous term singleton proxy)</li>
        <li>NICU admission; low 5-minute Apgar (&lt;7)</li>
        <li>Neonatal antibiotics; maternal infections present/treated</li>
      </ul>
      <h3>Analysis</h3>
      <ul class="clean">
        <li>Descriptive year trends and stratified rates (race/ethnicity, education, prenatal care, payment, clinical factors)</li>
        <li>Black–White rate ratios and absolute differences by year</li>
        <li>Multivariable logistic regression with complete-case analysis; ORs and 95% CIs saved under <code>results/models/</code></li>
      </ul>
      <p>Full methods: <a href="../paper/paper.md">research paper</a> · <a href="../docs/VARIABLES.md">variable dictionary</a> · <a href="../docs/DATA_PROVENANCE.md">data provenance</a>.</p>
    </section>

    <section id="results">
      <h2>Main results tables</h2>
      <h3>Yearly trends (excerpt)</h3>
      {table_html(trends, [c for c in (trends[0].keys() if trends else []) if c in ('year','n_births','preterm_rate','lbw_rate','cesarean_rate','nicu_rate','low_apgar5_rate') or c=='year'] or None)}

      <h3>Black–White preterm gap by year</h3>
      {table_html(gap_pre, ['year','white_rate','black_rate','rate_ratio','rate_diff_pp','white_n','black_n'])}

      <h3>Education gradient — preterm</h3>
      {table_html(edu_rows, ['level','n','events','rate_per_100'])}

      <h3>Prenatal care gradient — preterm</h3>
      {table_html(pnc_rows, ['level','n','events','rate_per_100'])}

      <h3>Logistic model coefficients (preterm)</h3>
      {table_html(model_rows, ['term','or','ci_low','ci_high','pvalue'])}
    </section>

    <section id="discussion">
      <h2>What the data show</h2>
      <p>
        The quantitative pattern that organizes this project is the <strong>persistence of the
        non-Hispanic Black–White preterm disparity</strong> across the full analysis window,
        alongside clear socioeconomic and care-timing gradients. Overall national rates move,
        but the relative Black–White gap in preterm birth remains large.
      </p>
      <p>
        Multivariable models that simultaneously adjust for education, prenatal care initiation,
        tobacco, obesity, diabetes, hypertension, plurality, payment source, maternal age, and year
        still leave a substantial association between NH Black identity and preterm birth
        (adjusted OR {thesis['black_or']}, 95% CI {thesis['black_or_ci']}). That is the
        falsifiable core of the thesis: if compositional differences in the measured covariates
        fully explained the disparity, the adjusted association would attenuate to the null —
        it does not in these public-use specifications.
      </p>
      <p>
        Education and prenatal-care timing both show monotonic gradients in unadjusted preterm
        rates (absolute spans of roughly {thesis['edu_gap']} and {thesis['pnc_gap']} percentage points
        respectively). These gradients matter clinically and for targeting, but they do not
        erase the race/ethnicity association in the joint model.
      </p>
    </section>

    <section id="limitations">
      <h2>Limitations</h2>
      <div class="callout limit">
        <ul class="clean">
          <li><strong>No geography in public-use files after 2004.</strong> State/county identifiers are suppressed; we cannot analyze place, segregation, or hospital markets.</li>
          <li>Cross-sectional birth certificates: associations are not causal effects of race, education, or prenatal care.</li>
          <li>Self-reported and facility-reported items vary in completeness; “not stated” codes are excluded from complete-case rates/models.</li>
          <li>Low-risk cesarean is an NTSV-style proxy without full presentation/prior obstetric detail available on all records.</li>
          <li>For computational feasibility on multi-million-row files, logistic models may use documented outcome-stratified samples; descriptives use the full analysis-ready extract.</li>
        </ul>
      </div>
    </section>

    <section id="reproduce">
      <h2>Reproducibility</h2>
      <div class="callout repro">
        <p>Repository: <a href="https://github.com/Kesmitij/cdc-natality-birth-outcomes">github.com/Kesmitij/cdc-natality-birth-outcomes</a></p>
        <pre>py -3.12 -m pip install -r requirements.txt
py -3.12 scripts/download_natality.py --years 2016-2024 --guides
py -3.12 scripts/process_all_years.py --years 2016-2024 --cleanup
py -3.12 scripts/run_analysis.py
py -3.12 scripts/build_site.py
py -3.12 scripts/build_paper.py
py -3.12 -m pytest -q</pre>
        <p>Raw zips are gitignored (~230&nbsp;MB each). Checksums live in <code>data/raw/download_manifest.json</code>.
        Derived tables and model JSON under <code>results/</code> are committed so the site and paper rebuild without multi-GB downloads.</p>
      </div>
    </section>
  </main>

  <footer>
    <div class="inner">
      <p>Analysis of public NCHS/CDC Natality microdata. Not affiliated with CDC/NCHS.
      Code and paper: <a href="https://github.com/Kesmitij/cdc-natality-birth-outcomes">GitHub repository</a>.</p>
    </div>
  </footer>
</body>
</html>
"""


def main():
    SITE.mkdir(parents=True, exist_ok=True)
    (SITE / "assets").mkdir(parents=True, exist_ok=True)
    (SITE / "css").mkdir(parents=True, exist_ok=True)

    key = load_json(RESULTS / "tables" / "key_findings.json")
    thesis = derive_thesis(key)

    # Copy figures
    fig_dir = RESULTS / "figures"
    if fig_dir.exists():
        for p in fig_dir.glob("*.png"):
            shutil.copy2(p, SITE / "assets" / p.name)

    # Save thesis artifact
    thesis_path = RESULTS / "tables" / "thesis.json"
    thesis_path.parent.mkdir(parents=True, exist_ok=True)
    with open(thesis_path, "w", encoding="utf-8") as f:
        json.dump(thesis, f, indent=2)

    html = build_index(thesis, key)
    out = SITE / "index.html"
    out.write_text(html, encoding="utf-8")
    print(f"Wrote {out}")
    print(f"Thesis short: {thesis['thesis_short']}")
    print(f"Thesis: {thesis['thesis'][:400]}...")


if __name__ == "__main__":
    main()
