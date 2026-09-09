"""Experiment 48: simple level models for longer-horizon Secchi outlooks."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from experiment_utils import CanonicalReport, df_to_markdown_table, get_dataset_artifact_path, load_data, write_canonical_report


ROOT = Path(__file__).resolve().parents[2]
REPORT_FILENAME = "48_simple_long_horizon_models.md"
REPORT_TITLE = "Experiment 48: Simple long-horizon level models"
PREDICTIONS_FILENAME = "48_simple_long_horizon_predictions.csv"
METRICS_FILENAME = "48_simple_long_horizon_metrics.csv"
PLOT_FILENAME = "48_simple_long_horizon_models.png"
DATASET_ID = "secchi-merged-2026-06-29-r1"
DEVELOPMENT_ORIGINS = tuple(range(2005, 2015))
LATER_ORIGINS = tuple(range(2015, 2020))
CALIBRATION_ORIGINS = tuple(range(1990, 2015))
DEVELOPMENT_HORIZONS = (1, 3, 5, 10)
LATER_HORIZONS = (1, 2, 3, 4, 5)
CALIBRATION_HORIZONS = (1, 2, 3, 4, 5, 10)

MODELS = (
    "Recent 3-calendar-year mean",
    "Recent 5-calendar-year mean",
    "Recent 10-calendar-year mean",
    "Last 5 observed-year mean",
    "Last 10 observed-year mean",
    "EWMA alpha 0.10",
    "EWMA alpha 0.20",
    "EWMA alpha 0.30",
    "Shrink recent/long-run 25/75",
    "Shrink recent/long-run 50/50",
    "Shrink recent/long-run 75/25",
    "Local-level state-space",
)


def _load_local_level():
    path = Path(__file__).with_name("40_forecasting_baselines.py")
    spec = importlib.util.spec_from_file_location("baseline40_for_48", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _ewma(values: np.ndarray, alpha: float) -> float:
    level = float(values[0])
    for value in values[1:]:
        level = alpha * float(value) + (1.0 - alpha) * level
    return level


def _prediction_map(history: pd.DataFrame, origin: int, horizons: tuple[int, ...], local_level) -> dict[str, list[float]]:
    history = history.sort_values("year")
    years = history["year"].to_numpy(dtype=int)
    values = history["summer_secchi"].to_numpy(dtype=float)
    recent5 = history[history["year"] >= origin - 4]["summer_secchi"]
    means = {}
    for window in (3, 5, 10):
        subset = history[history["year"] >= origin - window + 1]["summer_secchi"]
        means[f"Recent {window}-calendar-year mean"] = float(subset.mean()) if len(subset) else float(values[-1])
    means["Last 5 observed-year mean"] = float(np.mean(values[-min(5, len(values)) :]))
    means["Last 10 observed-year mean"] = float(np.mean(values[-min(10, len(values)) :]))
    for alpha in (0.10, 0.20, 0.30):
        means[f"EWMA alpha {alpha:.2f}"] = _ewma(values, alpha)
    recent_value = float(recent5.mean()) if len(recent5) else float(values[-1])
    long_run = float(np.mean(values))
    for weight in (0.25, 0.50, 0.75):
        means[f"Shrink recent/long-run {int(weight * 100)}/{int((1 - weight) * 100)}"] = weight * recent_value + (1.0 - weight) * long_run
    local, _ = local_level._local_level_forecast(years, values, [origin + h for h in horizons])
    return {name: [float(value)] * len(horizons) for name, value in means.items()} | {
        "Local-level state-space": [float(value) for value in local]
    }


def _mase_scale(values: np.ndarray) -> float:
    if len(values) < 2:
        return float("nan")
    scale = float(np.mean(np.abs(np.diff(values))))
    return scale if scale > 0 else float("nan")


def _cases(
    target: pd.DataFrame,
    origins: tuple[int, ...],
    horizons: tuple[int, ...],
    split: str,
    local_level,
) -> pd.DataFrame:
    target = target.sort_values(["MIDAS", "year"])
    by_lake = {lake: group for lake, group in target.groupby("MIDAS", sort=True)}
    lookup = target.set_index(["MIDAS", "year"])
    rows: list[dict[str, object]] = []
    for origin in origins:
        for lake, lake_target in by_lake.items():
            history = lake_target[lake_target["year"] <= origin]
            recent = history[history["year"] >= origin - 4]
            if len(history) < 2 or recent.empty:
                continue
            years = history["year"].to_numpy(dtype=int)
            values = history["summer_secchi"].to_numpy(dtype=float)
            predictions = _prediction_map(history, origin, horizons, local_level)
            scale = _mase_scale(values)
            gap = int(origin - years[-1])
            support = "Full" if len(history) >= 10 and gap <= 2 else ("Limited" if len(history) >= 2 and gap <= 4 else "Unavailable")
            for index, horizon in enumerate(horizons):
                key = (lake, origin + horizon)
                if key not in lookup.index:
                    continue
                actual = float(lookup.loc[key, "summer_secchi"])
                for model in MODELS:
                    rows.append(
                        {
                            "split": split,
                            "origin_year": origin,
                            "forecast_year": origin + horizon,
                            "horizon": horizon,
                            "MIDAS": lake,
                            "model": model,
                            "actual": actual,
                            "prediction": float(predictions[model][index]),
                            "last_value": float(values[-1]),
                            "naive_abs_error": abs(float(values[-1]) - actual),
                            "mase_scale": scale,
                            "history_years": len(history),
                            "gap_since_last": gap,
                            "support_tier": support,
                        }
                    )
    return pd.DataFrame(rows)


def _finite_width(values: np.ndarray, level: float) -> float:
    values = values[np.isfinite(values)]
    if len(values) < 19:
        return float("nan")
    rank = int(np.ceil((len(values) + 1) * level))
    return float(np.sort(values)[rank - 1]) if rank <= len(values) else float("nan")


def _calibrate(eval_frame: pd.DataFrame, calibration_frame: pd.DataFrame, horizons: tuple[int, ...]) -> pd.DataFrame:
    """Assign empirical half-widths per model, origin, and horizon.

    Shared width columns must be written only on that model's rows. Computing
    lower/upper inside the model loop reused the last model's widths.
    """
    out = eval_frame.copy()
    out["width_80"] = np.nan
    out["width_95"] = np.nan
    for model in MODELS:
        model_mask = out["model"] == model
        for level in (80, 95):
            width_column = f"width_{level}"
            for origin in sorted(out.loc[model_mask, "origin_year"].unique()):
                prior = calibration_frame[
                    (calibration_frame["model"] == model)
                    & (calibration_frame["origin_year"] < origin)
                    & (calibration_frame["forecast_year"] <= origin)
                ]
                running = 0.0
                for horizon in horizons:
                    residuals = prior[prior["horizon"] == horizon]
                    width = _finite_width(
                        np.abs(residuals["prediction"] - residuals["actual"]).to_numpy(float),
                        level / 100.0,
                    )
                    if np.isfinite(width):
                        running = max(running, width)
                        mask = model_mask & (out["origin_year"] == origin) & (out["horizon"] == horizon)
                        out.loc[mask, width_column] = running
    out["lower_80"] = (out["prediction"] - out["width_80"]).clip(lower=0)
    out["upper_80"] = out["prediction"] + out["width_80"]
    out["lower_95"] = (out["prediction"] - out["width_95"]).clip(lower=0)
    out["upper_95"] = out["prediction"] + out["width_95"]
    return out


def _metrics(frame: pd.DataFrame, split: str, support: str | None = None) -> pd.DataFrame:
    subset = frame[frame["split"] == split]
    if support is not None:
        subset = subset[subset["support_tier"] == support]
    rows = []
    for (model, horizon), group in subset.groupby(["model", "horizon"], sort=True):
        error = group["prediction"] - group["actual"]
        scale = group["mase_scale"].to_numpy(float)
        valid = np.isfinite(scale) & (scale > 0)
        lake_errors = group.assign(abs_error=np.abs(error)).groupby("MIDAS", as_index=False).agg(model_mae=("abs_error", "mean"), naive_mae=("naive_abs_error", "mean"))
        row: dict[str, object] = {
            "split": split,
            "support_tier": support or "All",
            "model": model,
            "horizon": int(horizon),
            "n_cases": len(group),
            "n_lakes": int(group["MIDAS"].nunique()),
            "MAE": float(np.mean(np.abs(error))),
            "RMSE": float(np.sqrt(np.mean(error**2))),
            "mean_bias": float(np.mean(error)),
            "MASE": float(np.mean(np.abs(error[valid] / scale[valid]))) if valid.any() else np.nan,
            "pct_lakes_beat_naive": float(np.mean(lake_errors["model_mae"] < lake_errors["naive_mae"]) * 100) if len(lake_errors) else np.nan,
        }
        for level in (80, 95):
            lo, hi = group[f"lower_{level}"], group[f"upper_{level}"]
            valid_interval = lo.notna() & hi.notna()
            row[f"n_interval_{level}"] = int(valid_interval.sum())
            row[f"coverage_{level}"] = float(np.mean((group.loc[valid_interval, "actual"] >= lo[valid_interval]) & (group.loc[valid_interval, "actual"] <= hi[valid_interval]))) if valid_interval.any() else np.nan
            row[f"width_{level}"] = float(np.mean((hi[valid_interval] - lo[valid_interval]))) if valid_interval.any() else np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    data = load_data()
    if data.dataset_id != DATASET_ID:
        raise RuntimeError(f"Expected {DATASET_ID}, got {data.dataset_id}")
    target = pd.read_csv(get_dataset_artifact_path("annual_summer_target_path"))
    target["MIDAS"] = target["MIDAS"].astype(str).str.strip()
    target["year"] = target["year"].astype(int)
    target["summer_secchi"] = pd.to_numeric(target["summer_secchi"], errors="raise")
    target = target[target["year"] <= 2024].copy()
    local_level = _load_local_level()

    development = _cases(target, DEVELOPMENT_ORIGINS, DEVELOPMENT_HORIZONS, "development", local_level)
    later = _cases(target, LATER_ORIGINS, LATER_HORIZONS, "later", local_level)
    calibration = _cases(target, CALIBRATION_ORIGINS, CALIBRATION_HORIZONS, "calibration", local_level)
    calibration = calibration[["origin_year", "forecast_year", "horizon", "MIDAS", "model", "actual", "prediction"]]

    development = _calibrate(development, calibration, DEVELOPMENT_HORIZONS)
    later = _calibrate(later, calibration, LATER_HORIZONS)
    predictions = pd.concat([development, later], ignore_index=True)
    metrics = pd.concat(
        [
            _metrics(development, "development"),
            _metrics(development, "development", "Full"),
            _metrics(later, "later"),
            _metrics(later, "later", "Full"),
        ],
        ignore_index=True,
    )
    reports = ROOT / "reports"
    predictions.to_csv(reports / PREDICTIONS_FILENAME, index=False)
    metrics.to_csv(reports / METRICS_FILENAME, index=False)

    development_full = metrics[(metrics["split"] == "development") & (metrics["support_tier"] == "Full") & (metrics["horizon"].isin([5, 10]))]
    later_full = metrics[(metrics["split"] == "later") & (metrics["support_tier"] == "Full") & (metrics["horizon"] == 5)]
    development_rank = development_full.groupby("model")["MAE"].mean().sort_values().head(5).reset_index(name="mean_MAE_h5_h10")
    later_rank = later_full.sort_values("MAE").head(8)

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5), sharey=True)
    for split, ax, title in (("development", axes[0], "2005–2014 rolling origins"), ("later", axes[1], "2015–2019 origins; 2020–2024 outcomes")):
        plot = metrics[(metrics["split"] == split) & (metrics["support_tier"] == "Full")]
        for model in ("Recent 5-calendar-year mean", "EWMA alpha 0.20", "Shrink recent/long-run 75/25", "Local-level state-space"):
            line = plot[plot["model"] == model].sort_values("horizon")
            ax.plot(line["horizon"], line["MAE"], marker="o", label=model)
        ax.set_title(title)
        ax.set_xlabel("Horizon (years)")
        ax.set_xticks(sorted(plot["horizon"].unique()))
        ax.grid(alpha=0.25)
    axes[0].set_ylabel("MAE (m)")
    axes[1].legend(fontsize=8, loc="upper left")
    fig.tight_layout()
    fig.savefig(reports / PLOT_FILENAME, dpi=150)
    plt.close(fig)

    results = (
        "### Development full-support ranking (mean MAE across 5- and 10-year horizons)\n\n"
        + df_to_markdown_table(development_rank, round_decimals=4)
        + "\n\n### Later-origin full-support results at five years\n\n"
        + df_to_markdown_table(later_rank, round_decimals=4)
        + "\n\nThe later-origin table is the most relevant historical check. "
        "Interval widths are model-specific. Experiment 49 decides whether any challenger may replace the served Trends baseline."
    )
    report = CanonicalReport(
        objective="Test a small, transparent family of level-based models for long-horizon annual summer Secchi prediction, with the existing local-level model retained as a comparator.",
        method="Evaluate fixed calendar-window means, last-observed-year means, fixed exponential smoothing, fixed shrinkage between recent and long-run lake levels, and the existing local-level state-space model. Use rolling origins 2005–2014 for development and 2015–2019 for a later-origin check against 2020–2024 outcomes. Calibrate symmetric empirical intervals from earlier outcome-matured residuals, with a separate width curve per model.",
        parameters=f"Dataset ID: `{DATASET_ID}`. Development horizons: {DEVELOPMENT_HORIZONS}; later-origin horizons: {LATER_HORIZONS}. Calendar means use observations in the preceding calendar window; observed-year means use the last N available lake-years. EWMA alphas: 0.10, 0.20, 0.30. Recent/long-run shrinkage weights: 25/75, 50/50, 75/25. Full support: at least 10 observed years and no more than a two-year gap; limited support is retained for diagnostics.",
        results=results + "\n\nArtifacts: `" + PREDICTIONS_FILENAME + "`, `" + METRICS_FILENAME + "`, and `" + PLOT_FILENAME + "`.",
        next_step="Experiment 49 is the predefined replacement test. Point metrics here may rank a challenger ahead of local-level; that is not a license to swap the served Trends model until Experiment 49's independent-outcome gate can be evaluated.",
    )
    write_canonical_report(REPORT_FILENAME, REPORT_TITLE, report)
    print(f"Wrote {REPORT_FILENAME}, {PREDICTIONS_FILENAME}, {METRICS_FILENAME}, and {PLOT_FILENAME}")


if __name__ == "__main__":
    main()
