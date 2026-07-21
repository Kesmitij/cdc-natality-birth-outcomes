#!/usr/bin/env python3
"""Download CDC Natality U.S. public-use zips and record checksums."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.request
from pathlib import Path

# Allow running without install
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from natality.layouts import NCHS_US_BIRTH_TOTALS, data_url, userguide_url  # noqa: E402


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, dest: Path, force: bool = False) -> dict:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and not force and dest.stat().st_size > 1_000_000:
        print(f"SKIP (exists): {dest.name} ({dest.stat().st_size:,} bytes)")
        return {
            "url": url,
            "path": str(dest),
            "bytes": dest.stat().st_size,
            "sha256": sha256_file(dest),
            "skipped": True,
        }

    print(f"Downloading {url}")
    t0 = time.time()
    tmp = dest.with_suffix(dest.suffix + ".part")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "cdc-natality-research/1.0"})
        with urllib.request.urlopen(req, timeout=600) as resp, open(tmp, "wb") as out:
            total = 0
            while True:
                block = resp.read(1024 * 1024)
                if not block:
                    break
                out.write(block)
                total += len(block)
                if total % (50 * 1024 * 1024) < 1024 * 1024:
                    print(f"  ... {total / 1e6:.0f} MB")
        tmp.replace(dest)
    except Exception as e:
        if tmp.exists():
            tmp.unlink(missing_ok=True)
        print(f"FAIL {url}: {e}")
        return {"url": url, "path": str(dest), "error": str(e)}

    elapsed = time.time() - t0
    digest = sha256_file(dest)
    print(f"OK {dest.name}: {dest.stat().st_size:,} bytes in {elapsed:.0f}s sha256={digest[:16]}...")
    return {
        "url": url,
        "path": str(dest),
        "bytes": dest.stat().st_size,
        "sha256": digest,
        "elapsed_sec": elapsed,
        "skipped": False,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--years",
        type=str,
        default="2016-2023",
        help="Years e.g. 2016-2023 or 2020,2021,2022",
    )
    ap.add_argument(
        "--outdir",
        type=Path,
        default=ROOT / "data" / "raw",
    )
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--guides", action="store_true", help="Also download user guides")
    args = ap.parse_args()

    if "-" in args.years and "," not in args.years:
        a, b = args.years.split("-", 1)
        years = list(range(int(a), int(b) + 1))
    else:
        years = [int(x) for x in args.years.split(",") if x.strip()]

    manifest = {
        "source_portal": "https://www.cdc.gov/nchs/data_access/VitalStatsOnline.htm",
        "ftp_base": "https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Datasets/DVS/natality",
        "years_requested": years,
        "nchs_control_totals": {str(y): NCHS_US_BIRTH_TOTALS.get(y) for y in years},
        "files": [],
        "guides": [],
    }

    for y in years:
        url = data_url(y)
        dest = args.outdir / f"Nat{y}us.zip"
        info = download(url, dest, force=args.force)
        info["year"] = y
        manifest["files"].append(info)

    if args.guides:
        gdir = ROOT / "docs" / "userguides"
        for y in years:
            url = userguide_url(y)
            dest = gdir / f"UserGuide{y}.pdf"
            info = download(url, dest, force=args.force)
            info["year"] = y
            manifest["guides"].append(info)

    out_json = args.outdir / "download_manifest.json"
    args.outdir.mkdir(parents=True, exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"Wrote {out_json}")

    # Exit non-zero if all failed
    ok = [f for f in manifest["files"] if "error" not in f]
    if not ok:
        sys.exit(2)


if __name__ == "__main__":
    main()
