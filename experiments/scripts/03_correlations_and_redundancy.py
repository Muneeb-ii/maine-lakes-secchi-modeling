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


def compute_predictor_correlations(df: pd.DataFrame) -> pd.DataFrame:
    """Compute Pearson correlations among numeric predictor variables (excluding SECCHI)."""
    numeric_df = df.select_dtypes(include=["number"])
    cols = [c for c in numeric_df.columns if c != "SECCHI"]

    if len(cols) < 2:
        return pd.DataFrame(
            columns=["var1", "var2", "corr", "abs_corr"],
        )

    corr_matrix = numeric_df[cols].corr(method="pearson")

    rows: List[dict] = []
    for i, c1 in enumerate(cols):
        for j in range(i + 1, len(cols)):
            c2 = cols[j]
            r = corr_matrix.loc[c1, c2]
            if pd.isna(r):
                continue
            rows.append(
                {
                    "var1": c1,
                    "var2": c2,
                    "corr": r,
                    "abs_corr": abs(r),
                }
            )

    pairs_df = pd.DataFrame(rows)
    if pairs_df.empty:
        return pairs_df

    return pairs_df.sort_values("abs_corr", ascending=False).reset_index(drop=True)


def main() -> None:
    data: LoadedData = load_data()
    df = data.frame

    corr_pairs = compute_predictor_correlations(df)
    n_pairs = len(corr_pairs)

    overview_text = textwrap.dedent(
        f"""
        This report examines Pearson correlations among numeric predictor variables,
        excluding the target `SECCHI`, to identify redundancy.

        Number of predictor pairs with valid correlations: **{n_pairs}**

        Strongly correlated pairs (e.g. |r| ≥ 0.7) are of particular interest, as they
        indicate potential redundancy among predictors.
        """
    ).strip()

    if corr_pairs.empty:
        top_pairs_md = "_No numeric predictor pairs with valid correlations._"
        strong_pairs_md = "_No strongly correlated predictor pairs found._"
        matrix_snippet_md = "_Correlation matrix not available (insufficient numeric predictors)._"
    else:
        # Show top N pairs by absolute correlation.
        top_pairs = corr_pairs.head(50)
        top_pairs_md = df_to_markdown_table(top_pairs)

        strong_pairs = corr_pairs[corr_pairs["abs_corr"] >= 0.7]
        if not strong_pairs.empty:
            strong_pairs_md = df_to_markdown_table(strong_pairs)
        else:
            strong_pairs_md = "_No pairs with |r| ≥ 0.7 found._"

        # Provide a small snippet of the full correlation matrix for context.
        numeric_df = df.select_dtypes(include=["number"])
        cols = [c for c in numeric_df.columns if c != "SECCHI"]
        corr_matrix = numeric_df[cols].corr(method="pearson")
        snippet_cols = cols[: min(8, len(cols))]
        corr_snippet = corr_matrix.loc[snippet_cols, snippet_cols].reset_index().rename(
            columns={"index": "variable"}
        )
        matrix_snippet_md = df_to_markdown_table(corr_snippet, round_decimals=2)

    sections = [
        ("Overview", overview_text),
        ("Top correlated predictor pairs (by |r|)", top_pairs_md),
        ("Strongly correlated predictor pairs (|r| ≥ 0.7)", strong_pairs_md),
        ("Correlation matrix snippet (predictors only)", matrix_snippet_md),
    ]

    report_path = write_markdown_report(
        filename="03_correlations_and_redundancy.md",
        title="Secchi Dataset – Correlations & Predictor Redundancy",
        sections=sections,
    )

    print(f"Wrote correlations and redundancy report to {report_path}")


if __name__ == "__main__":
    main()

