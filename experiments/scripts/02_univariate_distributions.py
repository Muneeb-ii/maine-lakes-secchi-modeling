from __future__ import annotations

import textwrap
from typing import List

import numpy as np
import pandas as pd

from experiment_utils import (
    LoadedData,
    df_to_markdown_table,
    load_data,
    write_markdown_report,
)


def summarize_numeric_distributions(df: pd.DataFrame) -> pd.DataFrame:
    """Compute summary statistics and simple outlier counts for numeric columns."""
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    rows: List[dict] = []

    for col in numeric_cols:
        series = df[col].dropna()
        n = len(series)
        if n == 0:
            rows.append(
                {
                    "variable": col,
                    "n": 0,
                    "mean": np.nan,
                    "std": np.nan,
                    "min": np.nan,
                    "p5": np.nan,
                    "p25": np.nan,
                    "p50": np.nan,
                    "p75": np.nan,
                    "p95": np.nan,
                    "max": np.nan,
                    "n_outliers": 0,
                    "pct_outliers": 0.0,
                }
            )
            continue

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outliers = series[(series < lower) | (series > upper)]

        rows.append(
            {
                "variable": col,
                "n": n,
                "mean": series.mean(),
                "std": series.std(),
                "min": series.min(),
                "p5": series.quantile(0.05),
                "p25": q1,
                "p50": series.median(),
                "p75": q3,
                "p95": series.quantile(0.95),
                "max": series.max(),
                "n_outliers": len(outliers),
                "pct_outliers": (len(outliers) / float(n)) * 100.0,
            }
        )

    summary_df = pd.DataFrame(rows)
    summary_df = summary_df.sort_values("variable").reset_index(drop=True)
    return summary_df


def main() -> None:
    data: LoadedData = load_data()
    df = data.frame

    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

    overview_text = textwrap.dedent(
        f"""
        This report summarizes the univariate distributions of numeric variables,
        including potential outliers based on the 1.5×IQR rule.

        Number of numeric variables: **{len(numeric_cols)}**

        Numeric variables considered:

        {', '.join(f'`{c}`' for c in numeric_cols) if numeric_cols else '_(none)_'}
        """
    ).strip()

    summary_df = summarize_numeric_distributions(df)
    summary_md = df_to_markdown_table(summary_df, max_rows=200)

    # Highlight variables with relatively high outlier fractions.
    if not summary_df.empty:
        high_outliers = summary_df[summary_df["pct_outliers"] > 5].copy()
        high_outliers = high_outliers.sort_values("pct_outliers", ascending=False)
        high_outliers_md = df_to_markdown_table(high_outliers)
    else:
        high_outliers_md = "_No numeric variables to evaluate._"

    sections = [
        ("Overview", overview_text),
        ("Per‑variable numeric summary", summary_md),
        ("Variables with notable outlier fractions", high_outliers_md),
    ]

    report_path = write_markdown_report(
        filename="02_univariate_distributions.md",
        title="Secchi Dataset – Univariate Distributions & Outlier Screening",
        sections=sections,
    )

    print(f"Wrote univariate distributions report to {report_path}")


if __name__ == "__main__":
    main()

