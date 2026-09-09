from __future__ import annotations

import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pygam import LinearGAM, f, l, s, te

from experiment_utils import CanonicalReport, df_to_markdown_table, write_canonical_report
from forecasting_common import BACKTEST_ORIGINS, HORIZONS, build_evaluation_rows, build_training_examples, load_target_and_metadata


REPORT_FILENAME = "43_trend_shape_challenger.md"
REPORT_TITLE = "Experiment 43: Hierarchical GAM Trend-Shape Challenger"
PLOT_FILENAME = "43_trend_shape_challenger.png"
PREDICTIONS_FILENAME = "43_spline_predictions.csv"
SMOOTH_FEATURES = ["origin_year", "last_value", "recent_mean_5", "recent_slope", "history_years", "gap_since_last"]
LINEAR_FEATURES = ["lag_2", "lag_3", "all_history_slope", "history_mean", "history_std", "history_span", "latest_bottom_hit_rate", "latest_n_stations", "latest_n_readings", "latest_n_summer_dates", "LATITUDE", "LONGITUDE", "AREA_ACRES", "DEPTH_MEAN_FEET", "DEPTH_MAX_FEET", "VOLUME_ACREFEET", "ELEVATION_FEET"]
CATEGORICAL_FEATURES = ["REGION", "MIDAS"]
MODEL_FEATURES = SMOOTH_FEATURES + LINEAR_FEATURES + CATEGORICAL_FEATURES
MAX_TRAIN_ROWS = 8000


def _encode(frame: pd.DataFrame, category_maps: dict[str, dict[str, int]] | None = None) -> tuple[np.ndarray, dict[str, dict[str, int]]]:
    result = frame[MODEL_FEATURES].copy()
    # Imputation parameters are fit on the training origin and reused for the
    # evaluation lake-years.  Computing medians on the evaluation batch would
    # leak information about the held-out cohort into the forecast.
    maps = category_maps or {}
    numeric_medians = maps.get("__numeric_medians__")
    if numeric_medians is None:
        numeric_medians = {}
        for column in SMOOTH_FEATURES + LINEAR_FEATURES:
            values = pd.to_numeric(result[column], errors="coerce")
            median = values.median()
            numeric_medians[column] = float(median) if pd.notna(median) else 0.0
        maps["__numeric_medians__"] = numeric_medians
    for column in SMOOTH_FEATURES + LINEAR_FEATURES:
        result[column] = pd.to_numeric(result[column], errors="coerce")
        result[column] = result[column].fillna(numeric_medians[column]).fillna(0.0)
    for column in CATEGORICAL_FEATURES:
        values = result[column].fillna("Unknown").astype(str)
        if column not in maps:
            maps[column] = {value: index for index, value in enumerate(sorted(values.unique()))}
        # PyGAM factor terms require prediction codes within the training
        # domain. Unseen levels are temporarily mapped to zero and their
        # fitted factor contribution is removed after prediction below.
        result[column] = values.map(maps[column]).fillna(0).astype(float)
    return result.to_numpy(dtype=float), maps


def _make_terms() -> object:
    terms = s(0, n_splines=6, spline_order=3)
    for index in range(1, len(SMOOTH_FEATURES)):
        terms += s(index, n_splines=6, spline_order=3)
    for index in range(len(SMOOTH_FEATURES), len(SMOOTH_FEATURES) + len(LINEAR_FEATURES)):
        terms += l(index)
    categorical_start = len(SMOOTH_FEATURES) + len(LINEAR_FEATURES)
    terms += f(categorical_start) + f(categorical_start + 1)
    # A tensor interaction between current level and recent slope allows the
    # smooth challenger to represent nonlinear trend shapes.
    terms += te(1, 3, n_splines=[5, 5])
    return terms


def _predict_with_neutral_unseen_factors(model: LinearGAM, x: np.ndarray, unseen: dict[str, np.ndarray]) -> np.ndarray:
    """Predict while assigning unseen factor levels a neutral effect.

    Mapping an unseen MIDAS to code zero makes it inherit an arbitrary lake's
    factor coefficient.  Subtracting the fitted partial dependence for that
    factor leaves the shared smooth/linear prediction for unseen levels.
    """
    predictions = np.asarray(model.predict(x), dtype=float)
    categorical_start = len(SMOOTH_FEATURES) + len(LINEAR_FEATURES)
    for offset, column in enumerate(CATEGORICAL_FEATURES):
        mask = unseen[column]
        if not np.any(mask):
            continue
        term_index = categorical_start + offset
        factor_effect = np.asarray(model.partial_dependence(term=term_index, X=x), dtype=float).reshape(-1)
        predictions[mask] -= factor_effect[mask]
    return predictions


def _make_plot(summary: pd.DataFrame, reports_dir: Path) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    axes[0].plot(summary["horizon"], summary["MAE"], marker="o", color="#9467bd")
    axes[0].set_title("Hierarchical GAM point accuracy")
    axes[0].set_ylabel("MAE (meters)")
    axes[1].plot(summary["horizon"], summary["MASE"], marker="o", color="#8c564b", label="MASE")
    axes[1].axhline(1.0, linestyle="--", color="#d62728", alpha=0.6, label="Naive scale")
    axes[1].set_title("Scaled error")
    axes[1].set_ylabel("MASE")
    for axis in axes:
        axis.set_xticks(HORIZONS)
        axis.set_xlabel("Forecast horizon (years)")
        axis.grid(alpha=0.25)
    axes[1].legend()
    fig.suptitle(REPORT_TITLE)
    fig.tight_layout()
    path = reports_dir / PLOT_FILENAME
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def _summary(result: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for horizon, group in result.groupby("horizon", sort=True):
        actual = group["actual"].to_numpy(dtype=float)
        prediction = group["prediction"].to_numpy(dtype=float)
        errors = prediction - actual
        scales = group["mase_scale"].to_numpy(dtype=float)
        valid = np.isfinite(scales) & (scales > 0)
        lake_compare = group.assign(abs_error=np.abs(errors)).groupby("MIDAS").agg(model_mae=("abs_error", "mean"), naive_mae=("naive_abs_error", "mean"))
        rows.append({"horizon": int(horizon), "n_forecasts": len(group), "n_lakes": int(group["MIDAS"].nunique()), "MAE": float(np.mean(np.abs(errors))), "RMSE": float(np.sqrt(np.mean(errors**2))), "mean_bias": float(np.mean(errors)), "MASE": float(np.mean(np.abs(errors[valid] / scales[valid]))) if valid.any() else np.nan, "pct_lakes_beat_naive": float(np.mean(lake_compare["model_mae"] < lake_compare["naive_mae"]) * 100)})
    return pd.DataFrame(rows)


def main() -> None:
    target, metadata, dataset_id = load_target_and_metadata()
    target_by_lake = {lake_id: group.sort_values("year") for lake_id, group in target.groupby("MIDAS", sort=True)}
    metadata_lookup = metadata.set_index("MIDAS").to_dict(orient="index")
    training_by_horizon = {horizon: build_training_examples(target_by_lake, metadata_lookup, max(BACKTEST_ORIGINS), horizon) for horizon in HORIZONS}
    rows = []
    diagnostics = []
    for origin in BACKTEST_ORIGINS:
        for horizon in HORIZONS:
            train = training_by_horizon[horizon]
            train = train[(train["origin_year"] + horizon) <= origin].copy()
            if len(train) > MAX_TRAIN_ROWS:
                train = train.sort_values("origin_year").tail(MAX_TRAIN_ROWS).copy()
            evaluation = build_evaluation_rows(target_by_lake, metadata_lookup, origin, horizon)
            if train.empty or evaluation.empty:
                continue
            x_train, maps = _encode(train)
            x_evaluation, _ = _encode(evaluation, maps)
            unseen = {
                column: ~evaluation[column].fillna("Unknown").astype(str).isin(maps[column])
                for column in CATEGORICAL_FEATURES
            }
            model = LinearGAM(_make_terms(), fit_intercept=True, max_iter=200, tol=0.01, verbose=False)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                model.fit(x_train, train["actual"].to_numpy(dtype=float))
            predictions = np.maximum(_predict_with_neutral_unseen_factors(model, x_evaluation, unseen), 0.0)
            for index, row in evaluation.reset_index(drop=True).iterrows():
                rows.append({"origin_year": origin, "forecast_year": origin + horizon, "horizon": horizon, "MIDAS": row["MIDAS"], "actual": row["actual"], "prediction": predictions[index], "naive_abs_error": row["naive_abs_error"], "mase_scale": row["mase_scale"], "history_years": row["history_years"], "gap_since_last": row["gap_since_last"], "REGION": row["REGION"], "n_stations": row["n_stations"], "bottom_hit_rate": row["bottom_hit_rate"]})
            diagnostics.append({"origin_year": origin, "horizon": horizon, "n_train": len(train), "n_evaluation": len(evaluation), "gcv": float(model.statistics_.get("GCV", np.nan)), "edof": float(np.sum(model.statistics_.get("edof", np.array([np.nan]))))})
    result = pd.DataFrame(rows)
    if result.empty:
        raise RuntimeError("No hierarchical GAM rolling-origin predictions were generated.")
    summary = _summary(result)
    reports_dir = ROOT = Path(__file__).resolve().parents[2] / "reports"
    plot_path = _make_plot(summary, reports_dir)
    output_path = reports_dir / PREDICTIONS_FILENAME
    result.to_csv(output_path, index=False)
    diagnostics_frame = pd.DataFrame(diagnostics)
    report = CanonicalReport(
        objective="Test whether a hierarchical GAM trend shape improves direct Secchi forecasting beyond persistence, recent means, the Bayesian state-space model, and the global CatBoost challenger.",
        method=f"Use the same station-balanced annual summer target and expanding-window origins {BACKTEST_ORIGINS[0]}–{BACKTEST_ORIGINS[-1]}. For each horizon and origin, fit a PyGAM LinearGAM with shared nonlinear smooths, region and lake factor effects, and neutral zero contribution for unseen factor levels, using only examples available by the origin. Forecasts are evaluated against exact future lake-years.",
        parameters=f"Dataset ID: `{dataset_id}`. Horizons: `{HORIZONS}`.\n\nSmooth terms: origin year, latest value, recent mean, recent slope, history length, and monitoring gap. Linear support terms: lagged values, long-run slope, variability, station/readings support, geography, and morphometry. Factor terms: region and MIDAS lake effect; trophic classification is excluded because its source is not temporally versioned. Unseen region/lake levels are encoded for PyGAM compatibility, then their factor partial dependence is removed so they receive a neutral factor contribution. A tensor interaction links latest value and recent slope.\n\nPyGAM settings: six cubic splines per smooth term, max 200 iterations, tolerance 0.01; latest `{MAX_TRAIN_ROWS}` eligible historical examples per rolling fit when necessary. This is a hierarchical GAM-style factor-pooling challenger; PyGAM does not expose a full Bayesian GAMM random-effect posterior.",
        results=f"### Accuracy by Horizon\n\n{df_to_markdown_table(summary, round_decimals=4)}\n\n![Hierarchical GAM trend-shape challenger accuracy]({plot_path.name})\n\n### Fit Diagnostics\n\n{df_to_markdown_table(diagnostics_frame, round_decimals=4)}\n\nPredictions are persisted at `{output_path.relative_to(reports_dir.parent)}` for Experiment 45.",
        next_step="Use the rolling-origin residuals from the direct CatBoost challenger to calibrate prediction intervals and define support tiers in Experiment 44. The GAM challenger remains a candidate only if its nonlinear shape improves long-horizon error without unstable extrapolation.",
    )
    path = write_canonical_report(REPORT_FILENAME, REPORT_TITLE, report)
    print(f"Wrote report to {path}")


if __name__ == "__main__":
    main()
