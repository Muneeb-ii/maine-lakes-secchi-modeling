from __future__ import annotations

import textwrap
from pathlib import Path

import pandas as pd

from experiment_utils import (
    CanonicalReport,
    LoadedData,
    df_to_markdown_table,
    load_data,
    summarize_missingness,
    write_canonical_report,
)

def describe_row_missingness(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize distribution of per‑row missing values."""
    n_cols = df.shape[1]
    if n_cols == 0 or df.empty:
        return pd.DataFrame()

    missing_count = df.isna().sum(axis=1)
    missing_frac = missing_count / float(n_cols)

    summary = pd.DataFrame(
        {
            "stat": [
                "min_missing_frac",
                "p25_missing_frac",
                "median_missing_frac",
                "p75_missing_frac",
                "max_missing_frac",
            ],
            "value": [
                missing_frac.min(),
                missing_frac.quantile(0.25),
                missing_frac.median(),
                missing_frac.quantile(0.75),
                missing_frac.max(),
            ],
        }
    )
    return summary


def missingness_by_group(
    df: pd.DataFrame,
    group_col: str,
) -> pd.DataFrame:
    """Compute average non‑missing fraction per column within each group."""
    if group_col not in df.columns:
        return pd.DataFrame()

    group_sizes = df.groupby(group_col).size().to_frame("n_rows")
    completeness = df.drop(columns=[group_col]).notna().groupby(df[group_col]).mean() * 100.0

    # Join sizes and completeness, then bring the group column back as a normal column.
    combined = group_sizes.join(completeness)
    combined = combined.reset_index()  # index name becomes the grouping column (e.g. MIDAS)
    return combined


def main() -> None:
    data: LoadedData = load_data()
    df = data.frame

    col_missing = summarize_missingness(df)
    row_missing = describe_row_missingness(df)

    by_midas = missingness_by_group(df, "MIDAS")
    by_year = missingness_by_group(df, "year")
    by_season = missingness_by_group(df, "season")

    n_rows, n_cols = df.shape
    unique_lakes = df["MIDAS"].nunique()
    
    # Compute summary statistics about records per lake
    if "MIDAS" in df.columns:
        records_per_lake = df.groupby("MIDAS").size()
        lake_stats = pd.DataFrame({
            "Statistic": ["Unique Lakes", "Min Records/Lake", "Median Records/Lake", "Mean Records/Lake", "Max Records/Lake"],
            "Value": [
                unique_lakes,
                records_per_lake.min(),
                records_per_lake.median(),
                records_per_lake.mean(),
                records_per_lake.max()
            ]
        })
        lake_stats_md = df_to_markdown_table(lake_stats, round_decimals=2)
    else:
        lake_stats_md = "_MIDAS column not found._"

    overview_text = textwrap.dedent(
        f"""
        Total rows: **{n_rows}**

        Total columns: **{n_cols}**
        
        Total unique lakes (MIDAS): **{unique_lakes}**

        This report summarizes missingness patterns in the Secchi dataset:

        - Per‑variable missingness and completeness.
        - Distribution of missingness across rows.
        - Summary statistics of records per lake.
        - How completeness varies by lake (`MIDAS`), year, and season (when available).
        """
    ).strip()

    col_missing_md = df_to_markdown_table(col_missing)
    if not row_missing.empty:
        row_missing_md = df_to_markdown_table(row_missing)
    else:
        row_missing_md = "_No rows to summarize._"

    def group_section_md(name: str, table: pd.DataFrame) -> str:
        if table.empty:
            return f"No `{name}` information available in the dataset."

        # Show only summary of a few key columns to keep table readable.
        display_cols = [c for c in table.columns if c in ("MIDAS", "year", "season", "n_rows")]
        # Add a simple completeness measure: mean non-missing across all columns.
        non_missing_cols = [c for c in table.columns if c not in ("MIDAS", "year", "season", "n_rows")]
        if non_missing_cols:
            table = table.copy()
            table["mean_pct_non_missing"] = table[non_missing_cols].mean(axis=1)
            display_cols.append("mean_pct_non_missing")

        subset = table[display_cols].sort_values("n_rows", ascending=False)
        return df_to_markdown_table(subset)

    by_midas_md = group_section_md("MIDAS", by_midas)
    by_year_md = group_section_md("year", by_year)
    by_season_md = group_section_md("season", by_season)

    report = CanonicalReport(
        objective=(
            "Establish the dataset size, lake coverage, and missingness structure before feature "
            "selection or model training decisions are made."
        ),
        method=(
            "Load the canonical merged dataset, parse temporal fields, summarize per-column and "
            "per-row missingness, and compare completeness patterns across MIDAS, year, and season."
        ),
        parameters=(
            "Input dataset: `data/Merged_Dataset.csv`.\n\n"
            "Grouping dimensions evaluated: `MIDAS`, `year`, and `season` when present.\n\n"
            "No model fitting is performed in this experiment."
        ),
        results=(
            f"{overview_text}\n\n"
            "### Lake Records Summary Statistics\n\n"
            f"{lake_stats_md}\n\n"
            "### Per-variable missingness\n\n"
            f"{col_missing_md}\n\n"
            "### Per-row missingness distribution\n\n"
            f"{row_missing_md}\n\n"
            "### Missingness patterns by MIDAS\n\n"
            f"{by_midas_md}\n\n"
            "### Missingness patterns by year\n\n"
            f"{by_year_md}\n\n"
            "### Missingness patterns by season\n\n"
            f"{by_season_md}"
        ),
        next_step=(
            "Use the completeness profile to guide early feature screening, redundancy checks, "
            "and the first modeling baselines."
        ),
    )

    report_path = write_canonical_report(
        filename="01_missingness_overview.md",
        title="Secchi Dataset – Missingness & Data Quality Overview",
        report=report,
    )

    print(f"Wrote missingness report to {report_path}")

if __name__ == "__main__":
    main()

