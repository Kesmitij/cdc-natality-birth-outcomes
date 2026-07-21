"""
Fixed-width parser for CDC Natality U.S. public-use microdata.

Reads line-oriented fixed-width text (optionally from a zip) and extracts
only the fields defined in layouts.NATALITY_FIELDS. Designed for streaming /
chunked processing so multi-GB annual files remain usable.
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Union

from .layouts import FIELD_BY_NAME, NATALITY_FIELDS, Field


def extract_fields(
    line: str,
    fields: Optional[Sequence[Field]] = None,
) -> Dict[str, str]:
    """
    Extract fixed-width fields from a single record line.

    Missing/short lines pad with spaces so slice access is safe.
    Values are stripped of trailing/leading whitespace but not otherwise cleaned.
    """
    if fields is None:
        fields = NATALITY_FIELDS
    # Ensure line is long enough for the rightmost field
    max_end = max(f.end for f in fields)
    if len(line) < max_end:
        line = line.ljust(max_end)
    # Drop newline/CR if present in body (defensive)
    if line.endswith("\n") or line.endswith("\r"):
        line = line.rstrip("\r\n").ljust(max_end)
    out: Dict[str, str] = {}
    for f in fields:
        out[f.name] = line[f.slice].strip()
    return out


def parse_lines(
    lines: Iterable[str],
    fields: Optional[Sequence[Field]] = None,
) -> Iterator[Dict[str, str]]:
    """Yield parsed dicts for non-empty lines."""
    for line in lines:
        if not line or not line.strip():
            continue
        yield extract_fields(line, fields)


def _find_7za() -> Optional[Path]:
    """Locate 7za.exe shipped under tools/ or on PATH."""
    root = Path(__file__).resolve().parents[2]
    candidates = [
        root / "tools" / "x64" / "7za.exe",
        root / "tools" / "7za.exe",
        root / "tools" / "arm64" / "7za.exe",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def extract_zip_if_needed(path: Union[str, Path], extract_root: Optional[Path] = None) -> Path:
    """
    CDC Natality zips often use Deflate64 (method 9), unsupported by Python zipfile.
    Extract with 7za when needed; return path to the fixed-width text file.
    """
    import subprocess

    path = Path(path)
    if path.suffix.lower() != ".zip":
        return path

    if extract_root is None:
        extract_root = path.parent / "extracted" / path.stem
    extract_root.mkdir(parents=True, exist_ok=True)

    existing = list(extract_root.glob("*.txt")) + list(extract_root.glob("*.dat"))
    existing = [p for p in existing if p.stat().st_size > 1_000_000]
    if existing:
        return max(existing, key=lambda p: p.stat().st_size)

    # Try stdlib first (works for Deflate)
    try:
        with zipfile.ZipFile(path, "r") as zf:
            names = [
                n
                for n in zf.namelist()
                if not n.endswith("/")
                and (
                    "us" in n.lower()
                    or n.lower().endswith(".txt")
                    or n.lower().endswith(".dat")
                    or "." not in Path(n).name
                )
            ]
            member = names[0] if names else zf.namelist()[0]
            zf.extract(member, path=extract_root)
            return extract_root / member
    except NotImplementedError:
        pass
    except RuntimeError:
        pass

    seven = _find_7za()
    if seven is None:
        raise RuntimeError(
            f"Cannot extract Deflate64 zip {path.name}: install 7-Zip tools under tools/x64/7za.exe"
        )
    cmd = [str(seven), "x", "-y", f"-o{extract_root}", str(path)]
    subprocess.run(cmd, check=True, capture_output=True)
    existing = list(extract_root.glob("*.txt")) + list(extract_root.glob("*.dat"))
    existing = [p for p in existing if p.stat().st_size > 1_000_000]
    if not existing:
        # any large file
        existing = [p for p in extract_root.rglob("*") if p.is_file() and p.stat().st_size > 1_000_000]
    if not existing:
        raise FileNotFoundError(f"No extracted microdata found under {extract_root}")
    return max(existing, key=lambda p: p.stat().st_size)


def open_natality_text(path: Union[str, Path]) -> io.TextIOBase:
    """
    Open a Natality data file for text reading.

    Accepts:
      - .zip (Deflate or Deflate64 via 7za extraction)
      - raw fixed-width .txt / .us / extensionless file
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)

    if path.suffix.lower() == ".zip":
        text_path = extract_zip_if_needed(path)
        return open(text_path, "r", encoding="latin-1", errors="replace")

    return open(path, "r", encoding="latin-1", errors="replace")


def iter_records(
    path: Union[str, Path],
    fields: Optional[Sequence[Field]] = None,
) -> Iterator[Dict[str, str]]:
    """Stream parsed records from a path (zip or text)."""
    with open_natality_text(path) as fh:
        yield from parse_lines(fh, fields)


def parse_to_dicts(
    path: Union[str, Path],
    fields: Optional[Sequence[Field]] = None,
    max_rows: Optional[int] = None,
) -> List[Dict[str, str]]:
    """Parse up to max_rows records into a list (for fixtures / small files)."""
    rows: List[Dict[str, str]] = []
    for i, rec in enumerate(iter_records(path, fields)):
        rows.append(rec)
        if max_rows is not None and i + 1 >= max_rows:
            break
    return rows


def build_synthetic_line(values: Dict[str, str], line_length: int = 1500) -> str:
    """
    Build a synthetic fixed-width record for unit tests.

    `values` maps field names to the exact character content to place
    (will be left-justified / truncated to field width).
    """
    buf = [" "] * line_length
    for name, val in values.items():
        if name not in FIELD_BY_NAME:
            raise KeyError(f"Unknown field: {name}")
        f = FIELD_BY_NAME[name]
        s = str(val)[: f.width].ljust(f.width)
        for i, ch in enumerate(s):
            buf[f.start - 1 + i] = ch
    return "".join(buf)
