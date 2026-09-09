from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from catboost import CatBoostRegressor
from scipy.stats import norm

from experiment_utils import CanonicalReport, df_to_markdown_table, write_canonical_report
from forecasting_common import (
    BACKTEST_ORIGINS,
    HORIZONS,
    build_evaluation_rows,
    build_training_examples,
    load_target_and_metadata,
    project_root,
    summarize_point_predictions,
)


EXPERIMENT_ID = "42"
REPORT_FILENAME = "42_direct_multihorizon_catboost.md"
REPORT_TITLE = "Experiment 42: Direct Multi-Horizon CatBoost Forecasting"
PLOT_FILENAME = "42_direct_multihorizon_catboost.png"
PREDICTIONS_FILENAME = "42_catboost_predictions.csv"
QUANTILES = (0.025, 0.10, 0.50, 0.90, 0.975)
MAX_TRAIN_ROWS = 8000
MODEL_FEATURES = [
    "origin_year",
    "last_value",
    "lag_2",
    "lag_3",
    "recent_mean_5",
    "recent_slope",
    "all_history_slope",
    "history_mean",
    "history_std",
    "history_years",
    "history_span",
    "gap_since_last",
    "latest_bottom_hit_rate",
    "latest_n_stations",
    "latest_n_readings",
    "latest_n_summer_dates",
    "LATITUDE",
    "LONGITUDE",
    "AREA_ACRES",
    "DEPTH_MEAN_FEET",
    "DEPTH_MAX_FEET",
    "VOLUME_ACREFEET",
    "ELEVATION_FEET",
    "REGION",
]
CATEGORICAL_FEATURES = ["REGION"]


def _nest_quantiles(predictions: dict[float, np.ndarray]) -> None:
    """Keep the fitted median and expand crossing bounds outward."""
    predictions[0.10] = np.minimum(predictions[0.10], predictions[0.50])
    predictions[0.025] = np.minimum(predictions[0.025], predictions[0.10])
    predictions[0.90] = np.maximum(predictions[0.90], predictions[0.50])
    predictions[0.975] = np.maximum(predictions[0.975], predictions[0.90])


def _fit_quantile_model(train: pd.DataFrame, quantile: float) -> CatBoostRegressor:
    model = CatBoostRegressor(
        iterations=100,
        depth=5,
        learning_rate=0.05,
        l2_leaf_reg=7,
        loss_function=f"Quantile:alpha={quantile}",
        random_seed=42,
        verbose=False,
        allow_writing_files=False,
        thread_count=1,
    )
    model.fit(train[MODEL_FEATURES], train["actual"], cat_features=CATEGORICAL_FEATURES)
    return model


def _interval_score(actual: np.ndarray, lower: np.ndarray, upper: np.ndarray, level: float) -> np.ndarray:
    alpha = 1.0 - level
    return (upper - lower) + (2.0 / alpha) * (lower - actual) * (actual < lower) + (2.0 / alpha) * (actual - upper) * (actual > upper)


def _pinball(actual: np.ndarray, prediction: np.ndarray, quantile: float) -> float:
    error = actual - prediction
    return float(np.mean(np.maximum(quantile * error, (quantile - 1.0) * error)))


def _summarize(result: pd.DataFrame) -> pd.DataFrame:
    point = summarize_point_predictions(result)
    rows: list[dict[str, object]] = []
    for _, record in point.iterrows():
        horizon = int(record["horizon"])
        group = result[result["horizon"] == horizon]
        actual = group["actual"].to_numpy(dtype=float)
        row = record.to_dict()
        for level, lower_column, upper_column in [
            (0.80, "q10", "q90"),
            (0.95, "q025", "q975"),
        ]:
            lower = group[lower_column].to_numpy(dtype=float)
            upper = group[upper_column].to_numpy(dtype=float)
            label = int(level * 100)
            row[f"coverage_{label}"] = float(np.mean((actual >= lower) & (actual <= upper)))
            row[f"width_{label}"] = float(np.mean(upper - lower))
            row[f"interval_score_{label}"] = float(np.mean(_interval_score(actual, lower, upper, level)))
        row["pinball_q10"] = _pinball(actual, group["q10"].to_numpy(dtype=float), 0.10)
        row["pinball_q50"] = _pinball(actual, group["q50"].to_numpy(dtype=float), 0.50)
        row["pinball_q90"] = _pinball(actual, group["q90"].to_numpy(dtype=float), 0.90)
        rows.append(row)
    return pd.DataFrame(rows)


def _make_plot(summary: pd.DataFrame, reports_dir: Path) -> Path:
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    axes[0].plot(summary["horizon"], summary["MAE"], marker="o", label="CatBoost q50")
    axes[0].set_title("Point accuracy")
    axes[0].set_ylabel("MAE (meters)")
    axes[1].plot(summary["horizon"], summary["coverage_80"] * 100, marker="o", label="Observed 80%")
    axes[1].axhline(80, linestyle="--", color="#ff7f0e", alpha=0.5, label="Nominal 80%")
    axes[1].plot(summary["horizon"], summary["coverage_95"] * 100, marker="o", label="Observed 95%")
    axes[1].axhline(95, linestyle="--", color="#d62728", alpha=0.5, label="Nominal 95%")
    axes[1].set_title("Raw quantile coverage")
    axes[1].set_ylabel("Coverage (%)")
    axes[2].plot(summary["horizon"], summary["width_80"], marker="o", label="80% width")
    axes[2].plot(summary["horizon"], summary["width_95"], marker="o", label="95% width")
    axes[2].set_title("Interval sharpness")
    axes[2].set_ylabel("Mean width (meters)")
    for axis in axes:
        axis.set_xticks(HORIZONS)
        axis.set_xlabel("Forecast horizon (years)")
        axis.grid(alpha=0.25)
    axes[1].legend(fontsize=8, loc="best")
    axes[2].legend(fontsize=8, loc="best")
    fig.suptitle("Experiment 42: Direct Multi-Horizon CatBoost")
    fig.tight_layout()
    path = reports_dir / PLOT_FILENAME
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def main() -> None:
    target, metadata, dataset_id = load_target_and_metadata()
    target_by_lake = {lake_id: group.sort_values("year") for lake_id, group in target.groupby("MIDAS", sort=True)}
    metadata_lookup = metadata.set_index("MIDAS").to_dict(orient="index")
    training_by_horizon = {
        horizon: build_training_examples(target_by_lake, metadata_lookup, max(BACKTEST_ORIGINS), horizon)
        for horizon in HORIZONS
    }
    prediction_rows: list[dict[str, object]] = []
    fit_diagnostics: list[dict[str, object]] = []
    for origin in BACKTEST_ORIGINS:
        for horizon in HORIZONS:
            train = training_by_horizon[horizon]
            train = train[(train["origin_year"] + horizon) <= origin].copy()
            if len(train) > MAX_TRAIN_ROWS:
                train = train.sort_values("origin_year").tail(MAX_TRAIN_ROWS).copy()
            evaluation = build_evaluation_rows(target_by_lake, metadata_lookup, origin, horizon)
            if train.empty or evaluation.empty:
                continue
            predictions: dict[float, np.ndarray] = {}
            for quantile in QUANTILES:
                model = _fit_quantile_model(train, quantile)
                predictions[quantile] = np.maximum(model.predict(evaluation[MODEL_FEATURES]), 0.0)
            _nest_quantiles(predictions)
            for index, row in evaluation.reset_index(drop=True).iterrows():
                prediction = {
                    "origin_year": origin,
                    "forecast_year": origin + horizon,
                    "horizon": horizon,
                    "MIDAS": row["MIDAS"],
                    "actual": row["actual"],
                    "prediction": predictions[0.50][index],
                    "q025": predictions[0.025][index],
                    "q10": predictions[0.10][index],
                    "q50": predictions[0.50][index],
                    "q90": predictions[0.90][index],
                    "q975": predictions[0.975][index],
                    "naive_abs_error": row["naive_abs_error"],
                    "mase_scale": row["mase_scale"],
                    "history_years": row["history_years"],
                    "gap_since_last": row["gap_since_last"],
                    "REGION": row["REGION"],
                    "n_stations": row["n_stations"],
                    "bottom_hit_rate": row["bottom_hit_rate"],
                }
                prediction_rows.append(prediction)
            fit_diagnostics.append({"origin_year": origin, "horizon": horizon, "n_train": len(train), "n_evaluation": len(evaluation)})

    result = pd.DataFrame(prediction_rows)
    if result.empty:
        raise RuntimeError("No CatBoost rolling-origin predictions were generated.")
    summary = _summarize(result)
    reports_dir = project_root() / "reports"
    plot_path = _make_plot(summary, reports_dir)
    predictions_path = reports_dir / PREDICTIONS_FILENAME
    result.to_csv(predictions_path, index=False)
    diagnostics = pd.DataFrame(fit_diagnostics)
    report = CanonicalReport(
        objective=(
            "Test the main global challenger to the hierarchical state-space model: direct multi-horizon CatBoost trained from lagged annual Secchi history, recent trend features, monitoring support, and static lake characteristics."
        ),
        method=(
            f"Use the station-balanced annual summer target from Experiment 39 and expanding-window origins {BACKTEST_ORIGINS[0]}–{BACKTEST_ORIGINS[-1]}. Fit one global CatBoost quantile model per horizon and quantile using only historical training examples whose labels are available by the current origin. Keep q50 point forecasts fixed and expand any crossing quantile bounds outward into nested q10–q90 and q025–q975 intervals before scoring exact future lake-years."
        ),
        parameters=(
            f"Dataset ID: `{dataset_id}`.\n\n"
            f"Horizons: `{HORIZONS}`. Quantiles: `{QUANTILES}`.\n\n"
            "Features: latest Secchi value, two lagged values, recent five-year mean and slope, full-history slope, history mean/variability, history length/span, gap since last observation, bottom-hit and monitoring-support fields, latitude/longitude, area, depth, elevation, and region. Trophic classification is excluded because its source is not temporally versioned.\n\n"
            f"CatBoost settings: 100 iterations, depth 5, learning rate 0.05, L2 regularization 7, seed 42. To keep the rolling-origin quantile suite reproducible on the project runtime, each fit uses the latest `{MAX_TRAIN_ROWS}` eligible historical examples when more are available.\n\n"
            "Runtime note: CatBoost is available in the repository runtime. Models are fit separately by horizon and quantile, then Experiment 44 calibrates their raw intervals using rolling-origin residuals."
        ),
        results=(
            "### Accuracy and Quantile Calibration\n\n"
            f"{df_to_markdown_table(summary, round_decimals=4)}\n\n"
            f"![CatBoost multi-horizon accuracy and coverage]({plot_path.name})\n\n"
            "### Fit Sizes\n\n"
            f"{df_to_markdown_table(diagnostics, round_decimals=0)}\n\n"
            f"Predictions are persisted at `{predictions_path.relative_to(project_root())}` for Experiments 44–45."
        ),
        next_step=(
            "Compare this global direct model with a nonlinear trend-shape challenger in Experiment 43, then calibrate its quantile intervals by horizon and support tier in Experiment 44."
        ),
    )
    path = write_canonical_report(REPORT_FILENAME, REPORT_TITLE, report)
    print(f"Wrote report to {path}")


if __name__ == "__main__":
    main()
