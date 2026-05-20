from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Tuple

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXPERIMENTS_ROOT = PROJECT_ROOT / "experiments"
DATA_DIR = PROJECT_ROOT / "data"
REPORTS_DIR = PROJECT_ROOT / "reports"

# Canonical research inputs.
DATA_CSV = DATA_DIR / "Merged_Dataset.csv"
METADATA_CSV = DATA_DIR / "Merged_Dataset_Metadata.csv"

STANDARD_REPORT_SECTIONS = (
    "Objective",
    "Method",
    "Parameters",
    "Results",
    "Next Step",
)


@dataclass
class LoadedData:
    frame: pd.DataFrame


@dataclass(frozen=True)
class CanonicalReport:
    objective: str
    method: str
    parameters: str
    results: str
    next_step: str


def _parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Add parsed date, year, month, and simple season from SAMPDATE."""
    if "SAMPDATE" not in df.columns:
        return df

    df = df.copy()
    df["SAMPDATE"] = pd.to_datetime(df["SAMPDATE"], errors="coerce", utc=True)
    df["date"] = df["SAMPDATE"].dt.date
    df["year"] = df["SAMPDATE"].dt.year
    df["month"] = df["SAMPDATE"].dt.month

    def _season(month: float) -> str:
        if pd.isna(month):
            return "unknown"
        m = int(month)
        if m in (12, 1, 2):
            return "winter"
        if m in (3, 4, 5):
            return "spring"
        if m in (6, 7, 8):
            return "summer"
        if m in (9, 10, 11):
            return "fall"
        return "unknown"

    df["season"] = df["month"].map(_season)
    return df


def _parse_midas(df: pd.DataFrame) -> pd.DataFrame:
    """Extract STATION from MIDAS if appended, keeping MIDAS as true lake ID."""
    if "MIDAS" not in df.columns:
        return df
        
    df = df.copy()
    # If there's a dash, it means it's <MIDAS>-<STATION>
    # We carefully split into two columns.
    has_dash = df["MIDAS"].astype(str).str.contains("-", na=False)
    
    if has_dash.any():
        split_midas = df["MIDAS"].astype(str).str.split("-", expand=True)
        # Col 0 is the base MIDAS, Col 1 is the station.
        df["MIDAS"] = split_midas[0]
        
        # Only overwrite STATION if we don't already have one, or if it makes sense to align them.
        # usually they align perfectly. We'll ensure STATION exists.
        if "STATION" not in df.columns:
            df["STATION"] = split_midas[1]
            
    return df


def load_data() -> LoadedData:
    """Load the main Secchi dataset with parsed temporal fields."""
    if not DATA_CSV.exists():
        raise FileNotFoundError(f"Data CSV not found at {DATA_CSV}")

    df = pd.read_csv(DATA_CSV)
    df = _parse_midas(df)
    df = _parse_dates(df)
    return LoadedData(frame=df)


def ensure_reports_dir() -> Path:
    """Ensure that the canonical reports directory exists and return its path."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    return REPORTS_DIR


def build_canonical_report_sections(report: CanonicalReport) -> List[Tuple[str, str]]:
    """Return report sections in the canonical experiment order."""
    return [
        ("Objective", report.objective),
        ("Method", report.method),
        ("Parameters", report.parameters),
        ("Results", report.results),
        ("Next Step", report.next_step),
    ]


def df_to_markdown_table(
    df: pd.DataFrame,
    *,
    max_rows: int = 50,
    round_decimals: int | None = 3,
) -> str:
    """Render a DataFrame as a simple GitHub‑style markdown table.

    This avoids relying on optional dependencies like `tabulate`.
    """
    if df.empty:
        return "_(no rows)_"

    work = df.copy()

    if round_decimals is not None:
        num_cols = work.select_dtypes(include=["number"]).columns
        work[num_cols] = work[num_cols].round(round_decimals)

    if len(work) > max_rows:
        work = work.head(max_rows)

    cols: List[str] = [str(c) for c in work.columns]
    header = "| " + " | ".join(cols) + " |"
    separator = "| " + " | ".join("---" for _ in cols) + " |"

    rows: List[str] = []
    for _, row in work.iterrows():
        cells: List[str] = []
        for c in work.columns:
            value = row[c]
            if pd.isna(value):
                cells.append("")
            else:
                cells.append(str(value))
        rows.append("| " + " | ".join(cells) + " |")

    return "\n".join([header, separator] + rows)


def write_markdown_report(
    filename: str,
    title: str,
    sections: Iterable[Tuple[str, str]],
) -> Path:
    """Write a markdown report with a title and ordered sections.

    Args:
        filename: Name of the file to create inside the reports directory.
        title: Top‑level heading for the report.
        sections: Iterable of (heading, body_markdown) pairs.
    """
    reports_dir = ensure_reports_dir()
    path = reports_dir / filename

    lines: List[str] = [f"# {title}", ""]

    for heading, body in sections:
        lines.append(f"## {heading}")
        lines.append("")
        if body:
            lines.append(body.rstrip())
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_canonical_report(
    filename: str,
    title: str,
    report: CanonicalReport,
) -> Path:
    """Write a report using the standard section contract for experiments."""
    return write_markdown_report(
        filename=filename,
        title=title,
        sections=build_canonical_report_sections(report),
    )


def summarize_missingness(df: pd.DataFrame) -> pd.DataFrame:
    """Compute per‑column missingness and basic completeness stats."""
    total_rows = len(df)
    if total_rows == 0:
        return pd.DataFrame(
            columns=[
                "column",
                "non_missing",
                "missing",
                "pct_missing",
                "n_unique",
            ]
        )

    non_missing = df.notna().sum()
    missing = df.isna().sum()
    pct_missing = (missing / total_rows) * 100.0
    n_unique = df.nunique(dropna=True)

    summary = pd.DataFrame(
        {
            "column": df.columns,
            "non_missing": non_missing.values,
            "missing": missing.values,
            "pct_missing": pct_missing.values,
            "n_unique": n_unique.values,
        }
    )
    return summary.sort_values("pct_missing", ascending=False).reset_index(drop=True)

