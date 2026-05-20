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


def compute_secchi_relationships(df: pd.DataFrame) -> pd.DataFrame:
    """Compute correlations and simple linear fits between SECCHI and each numeric predictor."""
    if "SECCHI" not in df.columns:
        return pd.DataFrame(
            columns=[
                "predictor",
                "n",
                "pearson_r",
                "spearman_r",
                "slope",
                "intercept",
                "r_squared",
            ]
        )

    numeric_df = df.select_dtypes(include=["number"])
    if "SECCHI" not in numeric_df.columns:
        return pd.DataFrame(
            columns=[
                "predictor",
                "n",
                "pearson_r",
                "spearman_r",
                "slope",
                "intercept",
                "r_squared",
            ]
        )

    predictors = [c for c in numeric_df.columns if c != "SECCHI"]
    rows: List[dict] = []

    for col in predictors:
        sub = numeric_df[["SECCHI", col]].dropna()
        n = len(sub)
        if n < 20:
            # Skip relationships with very little data.
            continue

        x = sub[col].to_numpy(dtype=float)
        y = sub["SECCHI"].to_numpy(dtype=float)

        pearson_r = float(np.corrcoef(x, y)[0, 1])
        spearman_r = float(pd.Series(x).corr(pd.Series(y), method="spearman"))

        # Simple least‑squares linear fit SECCHI ~ a * X + b
        slope, intercept = np.polyfit(x, y, deg=1)
        y_hat = slope * x + intercept
        ss_res = float(np.sum((y - y_hat) ** 2))
        ss_tot = float(np.sum((y - y.mean()) ** 2))
        r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else np.nan

        rows.append(
            {
                "predictor": col,
                "n": n,
                "pearson_r": pearson_r,
                "spearman_r": spearman_r,
                "slope": slope,
                "intercept": intercept,
                "r_squared": r_squared,
            }
        )

    rel_df = pd.DataFrame(rows)
    if rel_df.empty:
        return rel_df

    rel_df["abs_pearson_r"] = rel_df["pearson_r"].abs()
    rel_df = rel_df.sort_values("abs_pearson_r", ascending=False).reset_index(drop=True)
    return rel_df


def main() -> None:
    data: LoadedData = load_data()
    df = data.frame

    rel_df = compute_secchi_relationships(df)

    if rel_df.empty:
        overview_text = (
            "No suitable numeric predictors with at least 20 overlapping "
            "observations with `SECCHI` were found for this analysis."
        )
        ranking_md = "_No predictor–SECCHI relationships to report._"
        top_pos_md = "_No strong positive relationships found._"
        top_neg_md = "_No strong negative relationships found._"
    else:
        overview_text = textwrap.dedent(
            f"""
            This report examines relationships between `SECCHI` and each numeric predictor,
            using Pearson and Spearman correlations and simple one‑predictor linear models
            (`SECCHI ~ predictor`).

            Predictors considered: **{len(rel_df)}** (each with at least 20 overlapping observations).
            """
        ).strip()

        ranking_md = df_to_markdown_table(
            rel_df[
                [
                    "predictor",
                    "n",
                    "pearson_r",
                    "spearman_r",
                    "r_squared",
                    "slope",
                ]
            ],
            max_rows=200,
        )

        # Top positive and negative correlations based on Pearson r.
        pos = rel_df[rel_df["pearson_r"] > 0].sort_values("pearson_r", ascending=False)
        neg = rel_df[rel_df["pearson_r"] < 0].sort_values("pearson_r", ascending=True)

        if not pos.empty:
            top_pos = pos.head(15)[
                ["predictor", "pearson_r", "spearman_r", "r_squared", "n"]
            ]
            top_pos_md = df_to_markdown_table(top_pos)
        else:
            top_pos_md = "_No positive relationships detected._"

        if not neg.empty:
            top_neg = neg.head(15)[
                ["predictor", "pearson_r", "spearman_r", "r_squared", "n"]
            ]
            top_neg_md = df_to_markdown_table(top_neg)
        else:
            top_neg_md = "_No negative relationships detected._"

    sections = [
        ("Overview", overview_text),
        ("Predictor–SECCHI ranking by |Pearson r|", ranking_md),
        ("Top positive relationships (higher SECCHI with higher predictor)", top_pos_md),
        ("Top negative relationships (lower SECCHI with higher predictor)", top_neg_md),
    ]

    report_path = write_markdown_report(
        filename="04_predictor_secchi_relationships.md",
        title="Secchi Dataset – Predictor Relationships with SECCHI",
        sections=sections,
    )

    print(f"Wrote predictor–SECCHI relationships report to {report_path}")


if __name__ == "__main__":
    main()

