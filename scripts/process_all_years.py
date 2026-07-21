#!/usr/bin/env python3
"""Extract (via 7za), process, and optionally cleanup each Natality year."""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from natality.parser import extract_zip_if_needed  # noqa: E402
from natality.process import process_and_save  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
LOG = logging.getLogger("process_all")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", default="2016-2024")
    ap.add_argument("--cleanup", action="store_true", help="Delete extracted text after process")
    ap.add_argument("--max-rows", type=int, default=None)
    args = ap.parse_args()

    if "-" in args.years and "," not in args.years:
        a, b = args.years.split("-", 1)
        years = list(range(int(a), int(b) + 1))
    else:
        years = [int(x) for x in args.years.split(",") if x.strip()]

    raw = ROOT / "data" / "raw"
    out = ROOT / "data" / "processed"
    out.mkdir(parents=True, exist_ok=True)
    results = []
    t0 = time.time()

    for y in years:
        zip_path = raw / f"Nat{y}us.zip"
        if not zip_path.exists():
            LOG.error("Missing %s", zip_path)
            results.append({"year": y, "error": "missing zip"})
            continue
        pq = out / f"natality_analysis_{y}.parquet"
        if pq.exists() and args.max_rows is None:
            LOG.info("SKIP year %s (parquet exists)", y)
            results.append({"year": y, "skipped": True, "parquet": str(pq)})
            continue

        LOG.info("==== Year %s ====", y)
        text = extract_zip_if_needed(zip_path, raw / "extracted" / str(y))
        LOG.info("Text file: %s (%.1f GB)", text, text.stat().st_size / 1e9)
        meta = process_and_save(text, out, year=y, max_rows=args.max_rows)
        results.append(meta)

        if args.cleanup:
            extract_dir = raw / "extracted" / str(y)
            if extract_dir.exists():
                shutil.rmtree(extract_dir, ignore_errors=True)
                LOG.info("Cleaned %s", extract_dir)

        with open(out / "process_summary.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, default=str)

    LOG.info("All done in %.1f min", (time.time() - t0) / 60)
    with open(out / "process_summary.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)


if __name__ == "__main__":
    main()
