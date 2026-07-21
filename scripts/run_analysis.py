#!/usr/bin/env python3
"""Run descriptive + regression analysis on processed Natality tables."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from natality.analyze import load_analysis_frames, run_full_analysis  # noqa: E402
from natality.figures import generate_all_figures  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--processed-dir",
        type=Path,
        default=ROOT / "data" / "processed",
    )
    ap.add_argument(
        "--results-dir",
        type=Path,
        default=ROOT / "results",
    )
    ap.add_argument(
        "--glob",
        type=str,
        default="natality_analysis_*.parquet",
        help="Glob under processed-dir",
    )
    ap.add_argument(
        "--sample-frac",
        type=float,
        default=None,
        help="Optional random fraction of rows for faster analysis",
    )
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    paths = sorted(args.processed_dir.glob(args.glob))
    # Fallback to sample CSVs if parquet missing
    if not paths:
        paths = sorted(args.processed_dir.glob("natality_analysis_*_sample.csv"))
    if not paths:
        # any parquet
        paths = sorted(args.processed_dir.glob("*.parquet"))
    if not paths:
        logging.error("No processed files in %s", args.processed_dir)
        sys.exit(2)

    logging.info("Loading %s files...", len(paths))
    df = load_analysis_frames(paths)
    logging.info("Loaded %s rows, years=%s", f"{len(df):,}", sorted(df["year"].dropna().unique()))

    if args.sample_frac is not None and 0 < args.sample_frac < 1:
        df = df.sample(frac=args.sample_frac, random_state=args.seed)
        logging.info("Sampled to %s rows", f"{len(df):,}")

    artifacts = run_full_analysis(df, args.results_dir)
    figs = generate_all_figures(args.results_dir)
    artifacts["figures"] = figs

    out = args.results_dir / "analysis_manifest.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(artifacts, f, indent=2, default=str)
    logging.info("Analysis complete. Manifest: %s", out)
    logging.info("Key findings: %s", json.dumps(artifacts.get("key_findings", {}), indent=2, default=str)[:2000])


if __name__ == "__main__":
    main()
