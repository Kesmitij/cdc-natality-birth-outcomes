#!/usr/bin/env python3
"""Process downloaded CDC Natality zips into analysis-ready parquet files."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from natality.process import process_and_save  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=str, default="2016-2023")
    ap.add_argument("--raw-dir", type=Path, default=ROOT / "data" / "raw")
    ap.add_argument("--out-dir", type=Path, default=ROOT / "data" / "processed")
    ap.add_argument(
        "--max-rows",
        type=int,
        default=None,
        help="Optional cap on raw rows per year (for smoke tests)",
    )
    args = ap.parse_args()

    if "-" in args.years and "," not in args.years:
        a, b = args.years.split("-", 1)
        years = list(range(int(a), int(b) + 1))
    else:
        years = [int(x) for x in args.years.split(",") if x.strip()]

    results = []
    for y in years:
        # Accept zip or extracted text
        candidates = [
            args.raw_dir / f"Nat{y}us.zip",
            args.raw_dir / f"Nat{y}us.txt",
            args.raw_dir / f"nat{y}us.dat",
            args.raw_dir / f"Nat{y}PublicUS.c20250514.r20250715.txt",  # late naming variants
        ]
        # Also glob
        found = None
        for c in candidates:
            if c.exists():
                found = c
                break
        if found is None:
            matches = list(args.raw_dir.glob(f"*{y}*us*"))
            matches = [m for m in matches if m.suffix.lower() in {".zip", ".txt", ".dat", ""}]
            if matches:
                found = matches[0]
        if found is None:
            logging.error("No raw file for year %s in %s", y, args.raw_dir)
            results.append({"year": y, "error": "file not found"})
            continue
        logging.info("Processing year %s from %s", y, found)
        meta = process_and_save(
            found,
            args.out_dir,
            year=y,
            max_rows=args.max_rows,
        )
        results.append(meta)

    summary_path = args.out_dir / "process_summary.json"
    args.out_dir.mkdir(parents=True, exist_ok=True)
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    logging.info("Wrote %s", summary_path)

    ok = [r for r in results if "error" not in r]
    if not ok:
        sys.exit(2)


if __name__ == "__main__":
    main()
