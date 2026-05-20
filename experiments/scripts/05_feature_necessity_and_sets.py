from __future__ import annotations

import textwrap
from typing import Dict, List, Set, Tuple

import numpy as np
import pandas as pd

from experiment_utils import (
    LoadedData,
    df_to_markdown_table,
    load_data,
    summarize_missingness,
    write_markdown_report,
)


CORE_VARS: Set[str] = {"MIDAS", "SAMPDATE", "SECCHI"}


def compute_secchi_correlations(df: pd.DataFrame) -> Dict[str, float]:
    """Compute absolute Pearson correlations between SECCHI and each numeric predictor."""
    if "SECCHI" not in df.columns:
        return {}

    numeric_df = df.select_dtypes(include=["number"])
    if "SECCHI" not in numeric_df.columns:
        return {}

    corrs: Dict[str, float] = {}
    for col in numeric_df.columns:
        if col == "SECCHI":
            continue
        pair = numeric_df[["SECCHI", col]].dropna()
        if len(pair) < 20:
            continue
        r = pair.corr(method="pearson").iloc[0, 1]
        if pd.isna(r):
            continue
        corrs[col] = float(abs(r))
    return corrs


def compute_redundant_pairs(df: pd.DataFrame, threshold: float = 0.8) -> List[Tuple[str, str, float]]:
    """Identify highly correlated predictor pairs (excluding SECCHI) above a threshold."""
    numeric_df = df.select_dtypes(include=["number"])
    cols = [c for c in numeric_df.columns if c != "SECCHI"]
    if len(cols) < 2:
        return []

    corr_matrix = numeric_df[cols].corr(method="pearson")
    pairs: List[Tuple[str, str, float]] = []
    for i, c1 in enumerate(cols):
        for j in range(i + 1, len(cols)):
            c2 = cols[j]
            r = corr_matrix.loc[c1, c2]
            if pd.isna(r):
                continue
            if abs(r) >= threshold:
                pairs.append((c1, c2, float(r)))
    return pairs


def categorize_variables(
    df: pd.DataFrame,
    missing_summary: pd.DataFrame,
    secchi_corrs: Dict[str, float],
    redundant_pairs: List[Tuple[str, str, float]],
) -> pd.DataFrame:
    """Assign each variable to a category and attach redundancy info."""
    pct_missing_map = {
        row["column"]: float(row["pct_missing"]) for _, row in missing_summary.iterrows()
    }

    redundant_map: Dict[str, Set[str]] = {}
    for v1, v2, _ in redundant_pairs:
        redundant_map.setdefault(v1, set()).add(v2)
        redundant_map.setdefault(v2, set()).add(v1)

    rows: List[dict] = []
    all_cols = list(df.columns)

    for col in all_cols:
        pct_missing = pct_missing_map.get(col, np.nan)
        corr_strength = secchi_corrs.get(col, np.nan)
        is_core = col in CORE_VARS

        if is_core:
            category = "core_identifier_or_target"
        else:
            very_sparse = pct_missing > 70.0 if not pd.isna(pct_missing) else False
            is_numeric = not pd.isna(corr_strength)
            weak_signal = (corr_strength < 0.05) if is_numeric else False

            if not is_numeric:
                category = "categorical_or_date"
            elif (not very_sparse) and (not weak_signal):
                category = "high_value_predictor"
            elif very_sparse or weak_signal:
                category = "low_value_or_problematic"
            else:
                category = "other"

        redundant_with = sorted(redundant_map.get(col, []))
        rows.append(
            {
                "variable": col,
                "category": category,
                "pct_missing": pct_missing,
                "abs_corr_with_SECCHI": corr_strength,
                "redundant_with": ", ".join(redundant_with),
            }
        )

    result = pd.DataFrame(rows)
    result = result.sort_values(
        ["category", "abs_corr_with_SECCHI"], ascending=[True, False]
    ).reset_index(drop=True)
    return result


def derive_feature_sets(categorized: pd.DataFrame) -> Tuple[List[str], List[str]]:
    """Propose minimal and extended feature sets based on categorization."""
    core = categorized[categorized["category"] == "core_identifier_or_target"]["variable"]
    high_value = categorized[categorized["category"] == "high_value_predictor"].copy()

    high_value_sorted = high_value.sort_values(
        "abs_corr_with_SECCHI", ascending=False
    )["variable"].tolist()

    minimal_extra = high_value_sorted[: min(8, len(high_value_sorted))]

    minimal_set = list(core) + minimal_extra
    extended_set = list(core) + high_value_sorted

    # De‑duplicate while preserving order.
    def _unique(seq: List[str]) -> List[str]:
        seen: Set[str] = set()
        ordered: List[str] = []
        for item in seq:
            if item in seen:
                continue
            seen.add(item)
            ordered.append(item)
        return ordered

    return _unique(minimal_set), _unique(extended_set)


def main() -> None:
    data: LoadedData = load_data()
    df = data.frame

    missing_summary = summarize_missingness(df)
    secchi_corrs = compute_secchi_correlations(df)
    redundant_pairs = compute_redundant_pairs(df, threshold=0.8)

    categorized = categorize_variables(df, missing_summary, secchi_corrs, redundant_pairs)
    minimal_set, extended_set = derive_feature_sets(categorized)

    overview_text = textwrap.dedent(
        f"""
        This report combines missingness, redundancy, and association with `SECCHI` to
        propose variable categories and recommended feature sets for modeling.

        - **Core variables** (identifiers/target): {', '.join(sorted(CORE_VARS))}
        - **Number of high‑value predictors**: {int((categorized['category'] == 'high_value_predictor').sum())}
        - **Number of highly correlated predictor pairs (|r| ≥ 0.8)**: {len(redundant_pairs)}
        """
    ).strip()

    cat_table_md = df_to_markdown_table(
        categorized[
            [
                "variable",
                "category",
                "pct_missing",
                "abs_corr_with_SECCHI",
                "redundant_with",
            ]
        ],
        max_rows=200,
    )

    if redundant_pairs:
        redundant_df = pd.DataFrame(
            redundant_pairs, columns=["var1", "var2", "corr"]
        ).assign(abs_corr=lambda d: d["corr"].abs())
        redundant_df = redundant_df.sort_values("abs_corr", ascending=False)
        redundant_pairs_md = df_to_markdown_table(redundant_df)
    else:
        redundant_pairs_md = "_No highly correlated predictor pairs (|r| ≥ 0.8) identified._"

    minimal_set_md = "- " + "\n- ".join(f"`{v}`" for v in minimal_set) if minimal_set else "_(none)_"
    extended_set_md = "- " + "\n- ".join(f"`{v}`" for v in extended_set) if extended_set else "_(none)_"

    sections = [
        ("Overview", overview_text),
        ("Variable categories and metrics", cat_table_md),
        ("Highly correlated predictor pairs", redundant_pairs_md),
        ("Proposed minimal feature set", minimal_set_md),
        ("Proposed extended feature set", extended_set_md),
    ]

    report_path = write_markdown_report(
        filename="05_feature_necessity_and_sets.md",
        title="Secchi Dataset – Feature Necessity & Recommended Variable Sets",
        sections=sections,
    )

    print(f"Wrote feature necessity and sets report to {report_path}")


if __name__ == "__main__":
    main()

