"""
Chunked processing of CDC Natality annual files into analysis-ready parquet/CSV.

Uses pure-Python streaming parse + optional Polars for writing. Designed so a
full ~3.6M record year fits in memory as a compact analysis table, or can be
written in chunks if needed.
"""

from __future__ import annotations

import csv
import hashlib
import json
import logging
import time
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Union

from .layouts import NCHS_US_BIRTH_TOTALS
from .parser import iter_records
from .variables import construct_record

LOG = logging.getLogger(__name__)

ANALYSIS_COLUMNS = [
    "year",
    "maternal_age",
    "age_group",
    "education",
    "education_ord",
    "race_eth",
    "hispanic",
    "pnc_timing",
    "tobacco",
    "bmi",
    "obesity",
    "diabetes",
    "hypertension",
    "multiple",
    "payment",
    "gest_weeks",
    "preterm",
    "bw_g",
    "lbw",
    "vlbw",
    "cesarean",
    "low_risk_cesarean",
    "nicu",
    "low_apgar5",
    "ab_anti",
    "infection",
    "us_resident",
]


def file_sha256(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            block = f.read(chunk_size)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def process_year_file(
    path: Union[str, Path],
    year: Optional[int] = None,
    max_rows: Optional[int] = None,
    us_only: bool = True,
    progress_every: int = 500_000,
) -> Dict[str, Any]:
    """
    Process one annual Natality file.

    Returns dict with keys:
      records: list of analysis dicts
      n_raw: raw lines parsed
      n_kept: after US filter
      year: inferred/forced year
      elapsed_sec
    """
    path = Path(path)
    t0 = time.time()
    records: List[Dict[str, Any]] = []
    n_raw = 0
    n_kept = 0
    year_counter: Counter = Counter()

    for raw in iter_records(path):
        n_raw += 1
        rec = construct_record(raw)
        y = rec.get("year")
        if year is not None:
            rec["year"] = year
            y = year
        if y is not None:
            year_counter[y] += 1
        if us_only and rec.get("us_resident") != 1:
            if progress_every and n_raw % progress_every == 0:
                LOG.info("... parsed %s rows (%s kept)", f"{n_raw:,}", f"{n_kept:,}")
            if max_rows is not None and n_raw >= max_rows:
                break
            continue
        records.append(rec)
        n_kept += 1
        if progress_every and n_raw % progress_every == 0:
            LOG.info("... parsed %s rows (%s kept)", f"{n_raw:,}", f"{n_kept:,}")
        if max_rows is not None and n_raw >= max_rows:
            break

    # Infer year if not forced
    inferred = year
    if inferred is None and year_counter:
        inferred = year_counter.most_common(1)[0][0]

    elapsed = time.time() - t0
    LOG.info(
        "Processed %s: raw=%s kept=%s year=%s in %.1fs",
        path.name,
        f"{n_raw:,}",
        f"{n_kept:,}",
        inferred,
        elapsed,
    )
    return {
        "records": records,
        "n_raw": n_raw,
        "n_kept": n_kept,
        "year": inferred,
        "elapsed_sec": elapsed,
        "year_counts": dict(year_counter),
    }


def write_records_csv(records: Sequence[Dict[str, Any]], path: Union[str, Path]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=ANALYSIS_COLUMNS, extrasaction="ignore")
        w.writeheader()
        for r in records:
            w.writerow({c: r.get(c, "") if r.get(c) is not None else "" for c in ANALYSIS_COLUMNS})


def write_records_parquet(records: Sequence[Dict[str, Any]], path: Union[str, Path]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        import polars as pl

        df = pl.DataFrame(records)
        # Ensure column order
        cols = [c for c in ANALYSIS_COLUMNS if c in df.columns]
        df = df.select(cols)
        df.write_parquet(path)
    except ImportError:
        try:
            import pandas as pd

            df = pd.DataFrame.from_records(list(records), columns=ANALYSIS_COLUMNS)
            df.to_parquet(path, index=False)
        except Exception as e:
            raise RuntimeError(
                "Need polars or pandas+pyarrow to write parquet; "
                f"underlying error: {e}"
            ) from e


def check_control_total(
    year: int,
    n_kept: int,
    tolerance: float = 0.02,
) -> Dict[str, Any]:
    """Compare kept US counts to published NCHS totals."""
    expected = NCHS_US_BIRTH_TOTALS.get(year)
    if expected is None:
        return {
            "year": year,
            "n_kept": n_kept,
            "expected": None,
            "rel_diff": None,
            "ok": None,
            "note": "No published control total configured",
        }
    rel = abs(n_kept - expected) / expected
    return {
        "year": year,
        "n_kept": n_kept,
        "expected": expected,
        "rel_diff": rel,
        "ok": rel <= tolerance,
        "note": "within tolerance" if rel <= tolerance else "OUTSIDE tolerance",
    }


def aggregate_year_summary(records: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Fast overall rates for one year (complete-case per outcome)."""

    def rate(key: str) -> Dict[str, Any]:
        vals = [r[key] for r in records if r.get(key) is not None]
        if not vals:
            return {"n": 0, "events": 0, "rate": None}
        events = sum(1 for v in vals if v == 1)
        return {"n": len(vals), "events": events, "rate": events / len(vals)}

    year = None
    for r in records:
        if r.get("year") is not None:
            year = r["year"]
            break
    return {
        "year": year,
        "n_records": len(records),
        "preterm": rate("preterm"),
        "lbw": rate("lbw"),
        "vlbw": rate("vlbw"),
        "cesarean": rate("cesarean"),
        "nicu": rate("nicu"),
        "low_apgar5": rate("low_apgar5"),
        "infection": rate("infection"),
        "ab_anti": rate("ab_anti"),
    }


def process_and_save(
    input_path: Union[str, Path],
    output_dir: Union[str, Path],
    year: Optional[int] = None,
    max_rows: Optional[int] = None,
    write_parquet: bool = True,
    write_csv_sample: int = 50_000,
) -> Dict[str, Any]:
    """
    Full process for one year: parse → construct → save parquet + sample CSV + summary JSON.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    result = process_year_file(input_path, year=year, max_rows=max_rows)
    y = result["year"] or year or "unknown"
    stem = f"natality_analysis_{y}"
    meta = {
        "year": y,
        "source_path": str(input_path),
        "n_raw": result["n_raw"],
        "n_kept": result["n_kept"],
        "elapsed_sec": result["elapsed_sec"],
        "max_rows": max_rows,
        "control_total": check_control_total(int(y), result["n_kept"])
        if str(y).isdigit()
        else None,
        "summary": aggregate_year_summary(result["records"]),
    }
    if Path(input_path).exists() and Path(input_path).stat().st_size < 500_000_000:
        try:
            meta["source_sha256"] = file_sha256(Path(input_path))
        except OSError:
            pass

    if write_parquet:
        pq = output_dir / f"{stem}.parquet"
        write_records_parquet(result["records"], pq)
        meta["parquet"] = str(pq)

    # Always write a CSV sample for inspection
    sample = result["records"][:write_csv_sample]
    csv_path = output_dir / f"{stem}_sample.csv"
    write_records_csv(sample, csv_path)
    meta["sample_csv"] = str(csv_path)

    summary_path = output_dir / f"{stem}_meta.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    meta["meta_path"] = str(summary_path)
    # Drop heavy records from return
    out = {k: v for k, v in result.items() if k != "records"}
    out["meta"] = meta
    out["n_records_returned"] = len(result["records"])
    return out
