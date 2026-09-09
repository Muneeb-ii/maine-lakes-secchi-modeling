"""Experiment 49: predefined Trends baseline replacement test."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from experiment_utils import CanonicalReport, df_to_markdown_table, load_data, write_canonical_report


ROOT = Path(__file__).resolve().parents[2]
REPORT_FILENAME = "49_trends_replacement_protocol.md"
REPORT_TITLE = "Experiment 49: Trends Baseline Replacement Protocol"
ASSESSMENT_FILENAME = "49_trends_replacement_assessment.json"
METRICS_FILENAME = "49_trends_replacement_metrics.csv"

DATASET_ID = "secchi-merged-2026-06-29-r1"
INCUMBENT = "Local-level state-space"
CHALLENGERS = (
    "Recent 10-calendar-year mean",
    "EWMA alpha 0.20",
    "Last 10 observed-year mean",
)
CONFIRMATION_SPLIT = "later"
CONFIRMATION_HORIZON = 5
CONFIRMATION_SUPPORT = "Full"
INDEPENDENT_AFTER_YEAR = 2024
MIN_MAE_IMPROVEMENT_M = 0.02
COVERAGE_80 = (0.70, 0.90)
COVERAGE_95 = (0.85, 1.00)


def _load_predictions() -> pd.DataFrame:
    path = ROOT / "reports" / "48_simple_long_horizon_predictions.csv"
    if not path.exists():
        raise RuntimeError("Experiment 48 predictions are required. Run experiment 48 first.")
    frame = pd.read_csv(path)
    required = {
        "split",
        "horizon",
        "forecast_year",
        "support_tier",
        "model",
        "MIDAS",
        "actual",
        "prediction",
        "lower_80",
        "upper_80",
        "lower_95",
        "upper_95",
    }
    missing = required.difference(frame.columns)
    if missing:
        raise RuntimeError(f"Experiment 48 predictions are missing columns: {sorted(missing)}")
    frame["forecast_year"] = pd.to_numeric(frame["forecast_year"], errors="coerce")
    if frame["forecast_year"].isna().any():
        raise RuntimeError("Experiment 48 predictions contain invalid forecast years.")
    return frame


def _attach_region(frame: pd.DataFrame) -> pd.DataFrame:
    data = load_data()
    meta = data.frame[["MIDAS", "REGION"]].copy()
    meta["MIDAS"] = meta["MIDAS"].astype(str).str.strip()
    meta["REGION"] = meta["REGION"].fillna("Unknown").astype(str)
    meta = meta.drop_duplicates("MIDAS")
    out = frame.copy()
    out["MIDAS"] = out["MIDAS"].astype(str).str.strip()
    return out.merge(meta, on="MIDAS", how="left")


def _confirmation(frame: pd.DataFrame, *, independent: bool) -> pd.DataFrame:
    cohort = (
        frame[frame["forecast_year"] > INDEPENDENT_AFTER_YEAR]
        if independent
        else frame[frame["forecast_year"] <= INDEPENDENT_AFTER_YEAR]
    )
    return cohort[
        (cohort["split"] == CONFIRMATION_SPLIT)
        & (cohort["horizon"] == CONFIRMATION_HORIZON)
        & (cohort["support_tier"] == CONFIRMATION_SUPPORT)
        & cohort["model"].isin((INCUMBENT,) + CHALLENGERS)
    ].copy()


def _model_metrics(group: pd.DataFrame) -> dict[str, float]:
    error = group["prediction"] - group["actual"]
    lo80, hi80 = group["lower_80"], group["upper_80"]
    lo95, hi95 = group["lower_95"], group["upper_95"]
    valid80 = lo80.notna() & hi80.notna()
    valid95 = lo95.notna() & hi95.notna()
    return {
        "n_cases": int(len(group)),
        "n_lakes": int(group["MIDAS"].nunique()),
        "MAE": float(np.mean(np.abs(error))),
        "coverage_80": float(
            np.mean((group.loc[valid80, "actual"] >= lo80[valid80]) & (group.loc[valid80, "actual"] <= hi80[valid80]))
        )
        if valid80.any()
        else float("nan"),
        "coverage_95": float(
            np.mean((group.loc[valid95, "actual"] >= lo95[valid95]) & (group.loc[valid95, "actual"] <= hi95[valid95]))
        )
        if valid95.any()
        else float("nan"),
    }


def _lake_win_share(confirm: pd.DataFrame, challenger: str, incumbent_mae: pd.Series) -> float:
    part = confirm[confirm["model"] == challenger].assign(abs_error=lambda df: (df["prediction"] - df["actual"]).abs())
    lake_mae = part.groupby("MIDAS")["abs_error"].mean()
    aligned = lake_mae.align(incumbent_mae, join="inner")
    if aligned[0].empty:
        return float("nan")
    return float(np.mean(aligned[0] < aligned[1]) * 100)


def _region_mae(confirm: pd.DataFrame, model: str) -> pd.Series:
    part = confirm[confirm["model"] == model]
    return part.assign(abs_error=lambda df: (df["prediction"] - df["actual"]).abs()).groupby("REGION")["abs_error"].mean()


def _evaluate(
    dry_run: pd.DataFrame,
    latest_year: int,
    independent_confirm: pd.DataFrame,
) -> tuple[pd.DataFrame, dict]:
    # A newer source dataset is not sufficient by itself: the evaluated
    # prediction artifact must contain post-2024 outcomes. This prevents a
    # stale Experiment 48 CSV from authorizing a replacement accidentally.
    independent_available = latest_year > INDEPENDENT_AFTER_YEAR and not independent_confirm.empty
    confirm = independent_confirm if independent_available else dry_run
    incumbent_rows = confirm[confirm["model"] == INCUMBENT]
    incumbent = _model_metrics(incumbent_rows)
    incumbent_lake = incumbent_rows.assign(abs_error=lambda df: (df["prediction"] - df["actual"]).abs()).groupby("MIDAS")[
        "abs_error"
    ].mean()
    incumbent_region = _region_mae(confirm, INCUMBENT)

    rows = []
    replacement = None
    for model in (INCUMBENT,) + CHALLENGERS:
        metrics = _model_metrics(confirm[confirm["model"] == model])
        region = _region_mae(confirm, model)
        worse_regions = int((region > incumbent_region.reindex(region.index)).sum()) if model != INCUMBENT else 0
        lake_wins = 0.0 if model == INCUMBENT else _lake_win_share(confirm, model, incumbent_lake)
        mae_gain = incumbent["MAE"] - metrics["MAE"]
        coverage_ok = (
            COVERAGE_80[0] <= metrics["coverage_80"] <= COVERAGE_80[1]
            and COVERAGE_95[0] <= metrics["coverage_95"] <= COVERAGE_95[1]
        )
        mae_ok = model == INCUMBENT or mae_gain >= MIN_MAE_IMPROVEMENT_M
        lakes_ok = model == INCUMBENT or lake_wins > 50
        regions_ok = model == INCUMBENT or worse_regions <= 1
        replace_ok = bool(
            independent_available and model != INCUMBENT and coverage_ok and mae_ok and lakes_ok and regions_ok
        )
        rows.append(
            {
                "model": model,
                "role": "incumbent" if model == INCUMBENT else "challenger",
                **metrics,
                "mae_improvement_vs_incumbent": 0.0 if model == INCUMBENT else float(mae_gain),
                "pct_lakes_better_mae": lake_wins if model != INCUMBENT else np.nan,
                "regions_worse_than_incumbent": worse_regions,
                "coverage_gate": coverage_ok,
                "mae_gate": mae_ok,
                "lake_gate": lakes_ok,
                "region_gate": regions_ok,
                "independent_outcomes_gate": independent_available,
                "would_replace": replace_ok,
            }
        )
        if replace_ok and replacement is None:
            replacement = model

    assessment = {
        "dataset_id": DATASET_ID,
        "incumbent": INCUMBENT,
        "latest_observed_year": latest_year,
        "independent_outcomes_available": independent_available,
        "independent_after_year": INDEPENDENT_AFTER_YEAR,
        "confirmation": {
            "split": CONFIRMATION_SPLIT,
            "horizon_years": CONFIRMATION_HORIZON,
            "support_tier": CONFIRMATION_SUPPORT,
            "evaluation_cohort": "post-2024 outcomes" if independent_available else "2020–2024 dry run",
            "note": (
                "Post-2024 prediction rows are present and evaluated."
                if independent_available
                else "2020–2024 later-origin check is a dry run, not an independent post-2024 test."
            ),
        },
        "gates": {
            "min_mae_improvement_m": MIN_MAE_IMPROVEMENT_M,
            "coverage_80": list(COVERAGE_80),
            "coverage_95": list(COVERAGE_95),
            "majority_lakes_better_mae": True,
            "max_regions_worse_than_incumbent": 1,
            "require_independent_outcomes_after": INDEPENDENT_AFTER_YEAR,
        },
        "selected_replacement": replacement,
        "decision": (
            f"Replace the served Trends model with {replacement}."
            if replacement
            else "Keep the served local-level Trends baseline. No challenger may replace it until post-2024 outcomes exist and the remaining gates pass on that window."
        ),
    }
    return pd.DataFrame(rows), assessment


def main() -> None:
    data = load_data()
    if data.dataset_id != DATASET_ID:
        raise RuntimeError(f"Expected {DATASET_ID}, got {data.dataset_id}")
    latest_year = int(pd.to_datetime(data.frame["SAMPDATE"], errors="coerce").dt.year.max())
    predictions = _attach_region(_load_predictions())
    dry_run = _confirmation(predictions, independent=False)
    independent = _confirmation(predictions, independent=True)
    if dry_run.empty and independent.empty:
        raise RuntimeError("No Experiment 48 confirmation rows matched the replacement cohort.")
    metrics, assessment = _evaluate(dry_run, latest_year, independent)
    reports = ROOT / "reports"
    metrics.to_csv(reports / METRICS_FILENAME, index=False)
    (reports / ASSESSMENT_FILENAME).write_text(json.dumps(assessment, indent=2) + "\n", encoding="utf-8")
    report = CanonicalReport(
        objective=(
            "Freeze a replacement test for the served Trends local-level baseline, then apply it. "
            "Experiment 48 may rank a simpler level model higher on historical MAE; this experiment decides whether that is enough to swap the dashboard."
        ),
        method=(
            "Read Experiment 48's model-specific later-origin predictions. Compare the incumbent local-level model with "
            "the 10-year calendar mean, EWMA (alpha 0.20), and last-10-observed-year mean on full-support five-year cases. "
            "Gates were written before looking at post-2024 data: model-specific 80%/95% coverage in the stated bands, "
            f"MAE at least {MIN_MAE_IMPROVEMENT_M:.2f} m better than local-level, better MAE on a majority of lakes, "
            "worse MAE in at most one region, and independent outcomes after 2024. The 2020–2024 window is reported as a "
            "dry run and cannot authorize a swap."
        ),
        parameters=(
            f"Dataset ID: `{DATASET_ID}`. Incumbent: `{INCUMBENT}`. Challengers: {list(CHALLENGERS)}. "
            f"Confirmation: split `{CONFIRMATION_SPLIT}`, horizon {CONFIRMATION_HORIZON}, support `{CONFIRMATION_SUPPORT}`. "
            f"Independent outcomes required after {INDEPENDENT_AFTER_YEAR}."
        ),
        results=(
            f"### {'Independent post-2024 metrics' if assessment['independent_outcomes_available'] else 'Dry-run metrics (2020–2024 outcomes; not independent)'}\n\n"
            f"{df_to_markdown_table(metrics, round_decimals=4)}\n\n"
            f"**Independent post-2024 outcomes available:** {assessment['independent_outcomes_available']}.\n\n"
            f"**Decision:** {assessment['decision']}\n\n"
            f"Artifacts: `{METRICS_FILENAME}`, `{ASSESSMENT_FILENAME}`."
        ),
        next_step=(
            "Rerun this experiment when the processed snapshot includes summer outcomes after 2024. "
            "Until then, keep the Experiment 46 local-level outlook on the dashboard."
        ),
    )
    path = write_canonical_report(REPORT_FILENAME, REPORT_TITLE, report)
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
