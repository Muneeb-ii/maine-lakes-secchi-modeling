from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from experiment_utils import CanonicalReport, df_to_markdown_table, write_canonical_report
from forecasting_common import load_target_and_metadata


REPORT_FILENAME = "45_final_model_selection.md"
REPORT_TITLE = "Experiment 45: Forecast Release Decision"
CONTRACT_FILENAME = "45_forecast_artifact_contract.json"


def _passes_horizon(row: dict, horizon: int) -> bool:
    return bool(
        row[f"beats_last_h{horizon}"]
        and row[f"beats_recent_h{horizon}"]
        and row[f"mase_h{horizon}"] < 1.0
        and row[f"majority_beats_naive_h{horizon}"]
        and all(
            np.isfinite(row[f"coverage{level}_h{horizon}"])
            and abs(row[f"coverage{level}_h{horizon}"] - nominal) <= 0.10
            for level, nominal in [(80, 0.80), (95, 0.95)]
        )
    )


def _select_model(decisions: pd.DataFrame) -> tuple[str | None, int, str]:
    for horizon, gate in [(10, "all_gates"), (5, "passes_h5")]:
        passing = decisions[decisions[gate]]
        if not passing.empty:
            model = str(passing.sort_values(["mae_h5", "mae_h10", "model"]).iloc[0]["model"])
            return (
                model,
                horizon,
                f"The candidate passed the point, majority-lake, and interval gates through {horizon} years.",
            )
    return (
        None,
        0,
        "No candidate passed the five-year skill gates. A persistence baseline is not a passing forecast product under these gates, because beating the recent-mean baseline is required.",
    )


def _markdown_tables(path: Path) -> list[pd.DataFrame]:
    lines = path.read_text(encoding="utf-8").splitlines()
    tables = []
    index = 0
    while index < len(lines) - 1:
        if lines[index].startswith("|") and lines[index + 1].startswith("|") and "---" in lines[index + 1]:
            headers = [part.strip() for part in lines[index].strip("|").split("|")]
            rows = []
            index += 2
            while index < len(lines) and lines[index].startswith("|"):
                rows.append([part.strip() for part in lines[index].strip("|").split("|")])
                index += 1
            tables.append(pd.DataFrame(rows, columns=headers))
        else:
            index += 1
    return tables


def _report_accuracy(path: Path, required: set[str]) -> pd.DataFrame:
    for table in _markdown_tables(path):
        if required.issubset(table.columns):
            result = table.copy()
            for column in table.columns:
                if column not in {"model", "REGION", "history_bin"}:
                    result[column] = pd.to_numeric(result[column], errors="coerce")
            return result
    raise ValueError(f"No accuracy table found in {path}")


def _csv_summary(frame: pd.DataFrame, model_name: str, *, calibrated: bool = False) -> pd.DataFrame:
    rows = []
    if calibrated:
        frame = frame[frame["support_tier"] != "Unavailable"].copy()
        lower_columns = {80: "cal_q10", 95: "cal_q025"}
        upper_columns = {80: "cal_q90", 95: "cal_q975"}
    else:
        lower_columns = {80: "q10", 95: "q025"}
        upper_columns = {80: "q90", 95: "q975"}
    for horizon, group in frame.groupby("horizon", sort=True):
        actual = group["actual"].to_numpy(dtype=float)
        prediction = group["prediction"].to_numpy(dtype=float)
        error = prediction - actual
        scale = group["mase_scale"].to_numpy(dtype=float)
        valid = np.isfinite(scale) & (scale > 0)
        lake_compare = group.assign(abs_error=np.abs(error)).groupby("MIDAS").agg(
            model_mae=("abs_error", "mean"), naive_mae=("naive_abs_error", "mean")
        )
        row = {
            "model": model_name,
            "horizon": int(horizon),
            "MAE": float(np.mean(np.abs(error))),
            "MASE": float(np.mean(np.abs(error[valid] / scale[valid]))) if valid.any() else np.nan,
            "pct_lakes_beat_naive": float(np.mean(lake_compare["model_mae"] < lake_compare["naive_mae"]) * 100),
        }
        for level in [80, 95]:
            if lower_columns[level] not in group.columns:
                continue
            lower = group[lower_columns[level]].to_numpy(dtype=float)
            upper = group[upper_columns[level]].to_numpy(dtype=float)
            observed = np.isfinite(lower) & np.isfinite(upper)
            row[f"coverage_{level}"] = (
                float(np.mean((actual[observed] >= lower[observed]) & (actual[observed] <= upper[observed])))
                if observed.any()
                else np.nan
            )
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    target, _, dataset_id = load_target_and_metadata()
    reports_dir = Path(__file__).resolve().parents[2] / "reports"
    baseline = _report_accuracy(
        reports_dir / "40_forecasting_baselines.md", {"model", "horizon", "MAE", "MASE", "pct_lakes_beat_naive"}
    )
    bayesian = _report_accuracy(
        reports_dir / "41_hierarchical_state_space.md", {"horizon", "MAE", "MASE", "pct_lakes_beat_naive"}
    )
    bayesian["model"] = "Bayesian hierarchical state-space"
    bayesian_predictions = pd.read_csv(reports_dir / "41_state_space_predictions.csv")
    bayesian_converged = (
        "convergence_valid" in bayesian_predictions and bayesian_predictions["convergence_valid"].eq(True).all()
    )
    catboost = _csv_summary(pd.read_csv(reports_dir / "42_catboost_predictions.csv"), "Direct multi-horizon CatBoost")
    gam = _csv_summary(pd.read_csv(reports_dir / "43_spline_predictions.csv"), "Hierarchical GAM")
    calibrated = _csv_summary(
        pd.read_csv(reports_dir / "44_calibrated_predictions.csv"), "Calibrated CatBoost", calibrated=True
    )
    metrics = pd.concat([baseline, bayesian, catboost, gam, calibrated], ignore_index=True, sort=False)
    for column in ["coverage_80", "coverage_95"]:
        if column not in metrics:
            metrics[column] = np.nan
    last = baseline[baseline["model"] == "Last annual value"].set_index("horizon")
    recent = baseline[baseline["model"] == "Recent 5-year mean"].set_index("horizon")
    decision_rows = []
    for model in metrics["model"].dropna().unique():
        group = metrics[metrics["model"] == model].set_index("horizon")
        row = {"model": model}
        for horizon in [5, 10]:
            current = group.loc[horizon] if horizon in group.index else pd.Series(dtype=float)
            row[f"mae_h{horizon}"] = float(current.get("MAE", np.nan))
            row[f"mase_h{horizon}"] = float(current.get("MASE", np.nan))
            row[f"beats_last_h{horizon}"] = (
                bool(current.get("MAE", np.inf) < last.loc[horizon, "MAE"]) if horizon in last.index else False
            )
            row[f"beats_recent_h{horizon}"] = (
                bool(current.get("MAE", np.inf) < recent.loc[horizon, "MAE"]) if horizon in recent.index else False
            )
            row[f"majority_beats_naive_h{horizon}"] = bool(current.get("pct_lakes_beat_naive", 0) > 50)
            row[f"coverage80_h{horizon}"] = float(current.get("coverage_80", np.nan))
            row[f"coverage95_h{horizon}"] = float(current.get("coverage_95", np.nan))
        row["fit_valid"] = bool(bayesian_converged) if model == "Bayesian hierarchical state-space" else True
        row["passes_h5"] = bool(row["fit_valid"] and _passes_horizon(row, 5))
        row["passes_h10"] = bool(row["passes_h5"] and _passes_horizon(row, 10))
        decision_rows.append(row)
    decisions = pd.DataFrame(decision_rows)
    selected_model, selected_horizon, selection_reason = _select_model(
        decisions.rename(columns={"passes_h10": "all_gates"})
    )
    compact = decisions[
        ["model", "mae_h5", "mae_h10", "passes_h5", "passes_h10", "fit_valid"]
    ].sort_values(["passes_h5", "mae_h5"], ascending=[False, True])
    report_contract = {
        "schema_version": 1,
        "dataset_id": dataset_id,
        "target": "station-balanced annual summer Secchi depth (meters)",
        "selected_model": selected_model,
        "release_status": "withheld",
        "maximum_recommended_horizon_years": selected_horizon,
        "forecast_origin_year": int(target["year"].max()),
        "labeled_baseline_follow_on": "46",
        "limitations": [
            "These gates measure skill over last-value and recent-mean baselines, not whether a labeled persistence outlook is useful.",
            "Bayesian state-space fits in Experiment 41 did not converge and cannot pass.",
        ],
    }
    contract_path = reports_dir / CONTRACT_FILENAME
    contract_path.write_text(json.dumps(report_contract, indent=2) + "\n", encoding="utf-8")
    report = CanonicalReport(
        objective=(
            "Record the formal release decision for a skillful multi-year Secchi forecast. "
            "This experiment applies the stated gates to Experiments 40–44; it is not a new model."
        ),
        method=(
            "Read rolling-origin outputs from Experiments 40–44. A candidate may be released only if it beats "
            "last-value and recent-mean baselines at five years, has MASE below 1, improves on a majority of lakes, "
            "and has 80% and 95% interval coverage within 0.10 of nominal. Ten-year release requires the same at both "
            "horizons. Bayesian candidates also require converged fits. Missing intervals fail the interval gate."
        ),
        parameters=(
            f"Dataset ID: `{dataset_id}`. Decision horizons: 5 and 10 years. "
            "Sources: Experiment 40 baselines, 41 Bayesian state-space, 42 CatBoost, 43 GAM, 44 calibrated CatBoost."
        ),
        results=(
            "### Gate results\n\n"
            f"{df_to_markdown_table(compact, max_rows=20, round_decimals=4)}\n\n"
            f"**Selected model:** `{selected_model}`.\n\n"
            f"**Maximum recommended skillful horizon:** **{selected_horizon} years**.\n\n"
            f"**Reason:** {selection_reason}\n\n"
            "Detail tables remain in the source experiment reports. This file is the decision record only.\n\n"
            f"Artifact contract: `{contract_path.name}`."
        ),
        next_step=(
            "Do not publish a skillful forecast. Experiment 46 evaluates a clearly labeled persistence outlook "
            "under a different bar. Experiment 49 is the later replacement test for that baseline."
        ),
    )
    path = write_canonical_report(REPORT_FILENAME, REPORT_TITLE, report)
    print(f"Wrote report to {path}")


if __name__ == "__main__":
    main()
