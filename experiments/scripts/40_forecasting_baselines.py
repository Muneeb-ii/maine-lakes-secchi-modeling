from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import theilslopes

from experiment_utils import (
    CanonicalReport,
    df_to_markdown_table,
    get_dataset_artifact_path,
    load_data,
    write_canonical_report,
)


EXPERIMENT_ID = "40"
REPORT_FILENAME = "40_forecasting_baselines.md"
REPORT_TITLE = "Experiment 40: Direct Secchi Forecasting Baselines"
PLOT_FILENAME = "40_forecasting_baselines.png"
SUMMER_MONTHS = (6, 7, 8, 9)
BACKTEST_ORIGINS = tuple(range(2005, 2015))
HORIZONS = (1, 3, 5, 10)
MIN_HISTORY = 2
RECENT_WINDOW_YEARS = 5
MODEL_NAMES = (
    "Last annual value",
    "Recent 5-year mean",
    "Theil-Sen drift",
    "Local-level state-space",
)


def _load_target_and_metadata() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, str]:
    data = load_data()
    target_path = get_dataset_artifact_path("annual_summer_target_path")
    target = pd.read_csv(target_path)
    required = {"MIDAS", "year", "summer_secchi"}
    missing = required.difference(target.columns)
    if missing:
        raise ValueError(f"Annual summer target is missing columns: {sorted(missing)}")
    target = target.copy()
    target["MIDAS"] = target["MIDAS"].astype(str).str.strip()
    target["year"] = target["year"].astype(int)
    target["summer_secchi"] = pd.to_numeric(target["summer_secchi"], errors="raise")
    target = target.sort_values(["MIDAS", "year"]).reset_index(drop=True)

    metadata_columns = ["MIDAS", "REGION", "TROPHIC_CATEGORY", "LAKE_NAME"]
    metadata = data.frame[metadata_columns].copy()
    metadata["MIDAS"] = metadata["MIDAS"].astype(str).str.strip()
    metadata = metadata.drop_duplicates("MIDAS")
    raw = data.frame[["MIDAS", "STATION", "SAMPDATE", "SECCHI"]].copy()
    raw["MIDAS"] = raw["MIDAS"].astype(str).str.strip()
    raw["STATION"] = raw["STATION"].astype(str).str.strip()
    raw["SAMPDATE"] = pd.to_datetime(raw["SAMPDATE"], errors="coerce")
    raw["SECCHI"] = pd.to_numeric(raw["SECCHI"], errors="coerce")
    raw = raw.dropna(subset=["MIDAS", "STATION", "SAMPDATE", "SECCHI"])
    return target, metadata, raw, data.dataset_id


def _local_level_nll(params: np.ndarray, years: np.ndarray, values: np.ndarray) -> float:
    q, r = np.exp(params)
    level = float(values[0])
    state_variance = 0.0
    nll = 0.0
    previous_year = int(years[0])

    for year, observed in zip(years[1:], values[1:]):
        delta = max(int(year) - previous_year, 1)
        state_variance += q * delta
        innovation = float(observed) - level
        innovation_variance = state_variance + r
        if not np.isfinite(innovation_variance) or innovation_variance <= 0:
            return float("inf")
        nll += np.log(innovation_variance) + (innovation**2 / innovation_variance)
        gain = state_variance / innovation_variance
        level += gain * innovation
        state_variance = (1.0 - gain) * state_variance
        previous_year = int(year)
    return float(0.5 * nll)


def _local_level_forecast(
    years: np.ndarray,
    values: np.ndarray,
    forecast_years: list[int],
) -> tuple[np.ndarray, bool]:
    """Fit a local-level random-walk model and return point forecasts.

    The latent level evolves as level[t] = level[t-1] + process noise and the
    observed annual Secchi value is level[t] + measurement noise. Calendar gaps
    increase the process variance by the number of missing years.
    """
    if len(values) < MIN_HISTORY:
        return np.full(len(forecast_years), np.nan), True

    scale = max(float(np.var(values, ddof=1)) if len(values) > 1 else 0.0, 1e-4)
    initial = np.log([max(scale * 0.25, 1e-6), max(scale * 0.75, 1e-6)])
    bounds = [
        (np.log(max(scale * 1e-6, 1e-10)), np.log(max(scale * 1e3, 1e-3))),
        (np.log(max(scale * 1e-6, 1e-10)), np.log(max(scale * 1e3, 1e-3))),
    ]
    result = minimize(
        _local_level_nll,
        initial,
        args=(years, values),
        method="L-BFGS-B",
        bounds=bounds,
        options={"maxiter": 80, "ftol": 1e-9},
    )

    fallback = not result.success or not np.isfinite(result.fun)
    if fallback:
        q, r = max(scale * 0.25, 1e-6), max(scale * 0.75, 1e-6)
    else:
        q, r = np.exp(result.x)

    level = float(values[0])
    state_variance = 0.0
    previous_year = int(years[0])
    for year, observed in zip(years[1:], values[1:]):
        delta = max(int(year) - previous_year, 1)
        state_variance += q * delta
        innovation_variance = state_variance + r
        gain = state_variance / innovation_variance
        level += gain * (float(observed) - level)
        state_variance = (1.0 - gain) * state_variance
        previous_year = int(year)

    forecasts = []
    last_year = int(years[-1])
    for year in forecast_years:
        # The conditional mean of a random-walk level is the latest filtered
        # level; the process variance would widen prediction intervals later.
        _ = max(int(year) - last_year, 1)
        forecasts.append(max(level, 0.0))
    return np.asarray(forecasts, dtype=float), fallback


def _history_bin(n_history: int) -> str:
    if n_history < 5:
        return "2–4 years"
    if n_history < 10:
        return "5–9 years"
    if n_history < 15:
        return "10–14 years"
    return "15+ years"


def _mase_scale(values: np.ndarray) -> float:
    if len(values) < 2:
        return float("nan")
    scale = float(np.mean(np.abs(np.diff(values))))
    return scale if scale > 0 else float("nan")


def _run_backtest(
    target: pd.DataFrame,
    metadata: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, int]]:
    target_lookup = target.set_index(["MIDAS", "year"])["summer_secchi"]
    target_detail_lookup = target.set_index(["MIDAS", "year"])
    target_by_lake = {
        lake_id: group.sort_values("year")
        for lake_id, group in target.groupby("MIDAS", sort=True)
    }
    metadata_lookup = metadata.set_index("MIDAS").to_dict(orient="index")
    rows: list[dict[str, object]] = []
    diagnostics = {"local_level_fits": 0, "local_level_fallbacks": 0}

    for origin in BACKTEST_ORIGINS:
        for lake_id, lake_target in target_by_lake.items():
            history = lake_target[lake_target["year"] <= origin]
            recent = history[
                history["year"] >= origin - RECENT_WINDOW_YEARS + 1
            ]
            if len(history) < MIN_HISTORY or recent.empty:
                continue

            forecast_years = [origin + horizon for horizon in HORIZONS]
            observed_future = {
                year: target_lookup.get((lake_id, year), np.nan)
                for year in forecast_years
            }
            evaluable_years = [
                year for year in forecast_years if pd.notna(observed_future[year])
            ]
            if not evaluable_years:
                continue

            years = history["year"].to_numpy(dtype=int)
            values = history["summer_secchi"].to_numpy(dtype=float)
            last_value = float(values[-1])
            recent_mean = float(recent["summer_secchi"].mean())
            sen_slope, sen_intercept, _, _ = theilslopes(values, years)
            theil_sen = {
                year: max(float(sen_intercept + sen_slope * year), 0.0)
                for year in forecast_years
            }
            local_level, local_fallback = _local_level_forecast(
                years, values, forecast_years
            )
            diagnostics["local_level_fits"] += 1
            diagnostics["local_level_fallbacks"] += int(local_fallback)
            local_level_by_year = dict(zip(forecast_years, local_level))
            mase_scale = _mase_scale(values)
            meta = metadata_lookup.get(lake_id, {})
            history_bin = _history_bin(len(history))

            model_predictions = {
                "Last annual value": {year: last_value for year in forecast_years},
                "Recent 5-year mean": {
                    year: recent_mean for year in forecast_years
                },
                "Theil-Sen drift": theil_sen,
                "Local-level state-space": local_level_by_year,
            }
            for year in evaluable_years:
                actual = float(observed_future[year])
                horizon = year - origin
                naive_error = abs(last_value - actual)
                target_row = target_detail_lookup.loc[(lake_id, year)]
                for model_name in MODEL_NAMES:
                    prediction = float(model_predictions[model_name][year])
                    rows.append(
                        {
                            "origin_year": origin,
                            "forecast_year": year,
                            "horizon": horizon,
                            "MIDAS": lake_id,
                            "model": model_name,
                            "actual": actual,
                            "prediction": prediction,
                            "error": prediction - actual,
                            "naive_abs_error": naive_error,
                            "mase_scale": mase_scale,
                            "history_years": len(history),
                            "history_bin": history_bin,
                            "history_latest_year": int(history["year"].max()),
                            "n_stations": int(target_row.get("n_stations", 1)),
                            "bottom_hit_rate": float(
                                target_row.get("bottom_hit_rate", np.nan)
                            ),
                            "REGION": meta.get("REGION", "Unknown"),
                            "TROPHIC_CATEGORY": meta.get(
                                "TROPHIC_CATEGORY", "Unknown"
                            ),
                        }
                    )

    result = pd.DataFrame(rows)
    if result.empty:
        raise RuntimeError("No rolling-origin forecast cases were generated.")
    return result, diagnostics


def _summer_target_variants(target: pd.DataFrame, raw: pd.DataFrame) -> dict[str, pd.Series]:
    """Build the non-leaky summer sensitivity targets from the 39 panel/raw rows."""
    variants = {
        "Canonical summer station-balanced mean": target.set_index(["MIDAS", "year"])["summer_secchi"],
        # This is the median of station-year daily-duplicate means (the
        # station-year median retained by Experiment 39), followed by the
        # lake-year median across stations.
        "Summer station-year median of daily-duplicate means": target.set_index(["MIDAS", "year"])["summer_secchi_median"],
    }
    work = raw.assign(year=raw["SAMPDATE"].dt.year, month=raw["SAMPDATE"].dt.month)
    work = work[work["month"].isin(SUMMER_MONTHS)].copy()
    # One value per station/date keeps duplicate readings from overweighting a date;
    # dates then weight station-years, exposing sensitivity to station sampling effort.
    date_station = work.groupby(["MIDAS", "STATION", "SAMPDATE", "year"], as_index=False).agg(
        value=("SECCHI", "mean")
    )
    date_weighted = (
        date_station.groupby(["MIDAS", "year"], as_index=False)
        .agg(value=("value", "mean"))
        .set_index(["MIDAS", "year"])["value"]
    )
    variants["Summer date-balanced/reading-weighted mean"] = date_weighted
    return variants


def _full_year_target(raw: pd.DataFrame, origin: int) -> pd.Series:
    """Construct a full-year target with month effects frozen at the origin.

    Effects are estimated only from observations available at ``origin``.  The
    within-lake-year subtraction removes lake level before pooling month
    residuals, and effects are centered on the summer months.
    """
    work = raw.assign(year=raw["SAMPDATE"].dt.year, month=raw["SAMPDATE"].dt.month)
    # Keep only years that can contribute to this origin's history or to one
    # of the requested target years before the relatively expensive
    # date/station aggregation. This preserves the historical fit while
    # avoiding irrelevant snapshot rows.
    target_years = {origin + horizon for horizon in HORIZONS}
    work = work[(work["year"] <= origin) | work["year"].isin(target_years)].copy()
    train = work[work["year"] <= origin].copy()
    # Deduplicate repeated readings on the same lake/station/date before
    # estimating month effects so replicate readings cannot dominate a date.
    train = train.groupby(["MIDAS", "STATION", "SAMPDATE", "year", "month"], as_index=False)["SECCHI"].mean()
    ly = train.groupby(["MIDAS", "year"])["SECCHI"].transform("mean")
    train["resid"] = train["SECCHI"] - ly
    effects = train.groupby("month")["resid"].mean()
    summer_effects = effects.reindex(SUMMER_MONTHS).dropna()
    center = float(summer_effects.mean()) if not summer_effects.empty else 0.0
    effects = effects - center
    work["adjusted"] = (work["SECCHI"] - work["month"].map(effects).fillna(0.0)).clip(lower=0.0)
    date_station = work.groupby(["MIDAS", "STATION", "SAMPDATE", "year"], as_index=False).agg(
        value=("adjusted", "mean")
    )
    station_year = date_station.groupby(["MIDAS", "STATION", "year"], as_index=False).agg(value=("value", "mean"))
    return station_year.groupby(["MIDAS", "year"])["value"].mean()


def _target_sensitivity(
    target: pd.DataFrame, raw: pd.DataFrame
) -> pd.DataFrame:
    """Compare recent-5 baselines on a common eligible cohort across targets."""
    variants = _summer_target_variants(target, raw)
    rows_by_variant: dict[str, pd.DataFrame] = {}
    for name, series in variants.items():
        panel = series.rename("actual").reset_index()
        by_lake = {str(lake): group.sort_values("year") for lake, group in panel.groupby("MIDAS", sort=False)}
        rows: list[dict[str, object]] = []
        for origin in BACKTEST_ORIGINS:
            forecast_years = {origin + horizon: horizon for horizon in HORIZONS}
            for lake, lake_panel in by_lake.items():
                history = lake_panel[lake_panel["year"] <= origin].dropna(subset=["actual"])
                recent = history[history["year"] >= origin - RECENT_WINDOW_YEARS + 1]
                if len(history) < MIN_HISTORY or recent.empty:
                    continue
                for _, future in lake_panel[lake_panel["year"].isin(forecast_years)].dropna(subset=["actual"]).iterrows():
                    year = int(future["year"])
                    if year not in forecast_years:
                        continue
                    values = history["actual"].to_numpy(dtype=float)
                    scale = _mase_scale(values)
                    horizon = forecast_years[year]
                    rows.append({"key": (origin, horizon, str(lake)), "origin_year": origin, "horizon": horizon,
                                 "MIDAS": str(lake), "actual": float(future["actual"]), "prediction": float(recent["actual"].mean()),
                                 "mase_scale": scale})
        rows_by_variant[name] = pd.DataFrame(rows)

    # Full-year is origin-specific by construction; evaluate its target values
    # only after effects are frozen at each origin.
    name = "Full-year seasonally adjusted mean"
    rows = []
    for origin in BACKTEST_ORIGINS:
        series = _full_year_target(raw, origin)
        panel = series.rename("actual").reset_index()
        for lake, lake_panel in panel.groupby("MIDAS", sort=False):
            history = lake_panel[lake_panel["year"] <= origin].dropna(subset=["actual"])
            recent = history[history["year"] >= origin - RECENT_WINDOW_YEARS + 1]
            if len(history) < MIN_HISTORY or recent.empty:
                continue
            for _, future in lake_panel[lake_panel["year"].isin([origin + h for h in HORIZONS])].dropna(subset=["actual"]).iterrows():
                horizon = int(future["year"]) - origin
                rows.append({"key": (origin, horizon, str(lake)), "origin_year": origin, "horizon": horizon,
                             "MIDAS": str(lake), "actual": float(future["actual"]), "prediction": float(recent["actual"].mean()),
                             "mase_scale": _mase_scale(history["actual"].to_numpy(dtype=float))})
    rows_by_variant[name] = pd.DataFrame(rows)
    common = set.intersection(*(set(frame["key"]) for frame in rows_by_variant.values() if not frame.empty))
    out = []
    for variant, frame in rows_by_variant.items():
        frame = frame[frame["key"].isin(common)].copy()
        if frame.empty:
            continue
        frame["abs_error"] = (frame["prediction"] - frame["actual"]).abs()
        frame["abs_scaled_error"] = frame["abs_error"] / frame["mase_scale"]
        out.append(frame.groupby("horizon", as_index=False).agg(
            target=("key", lambda _: variant), n_cases=("key", "size"), n_lakes=("MIDAS", "nunique"),
            MAE=("abs_error", "mean"), MASE=("abs_scaled_error", "mean")
        ))
    return pd.concat(out, ignore_index=True)


def _summarize(result: pd.DataFrame, group_columns: list[str]) -> pd.DataFrame:
    summaries = []
    for keys, group in result.groupby(group_columns, sort=True, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        record = dict(zip(group_columns, keys))
        errors = group["error"].to_numpy(dtype=float)
        scales = group["mase_scale"].to_numpy(dtype=float)
        valid_scales = np.isfinite(scales) & (scales > 0)
        model_name = str(group["model"].iloc[0])
        record.update(
            {
                "n_forecasts": len(group),
                "n_lakes": int(group["MIDAS"].nunique()),
                "n_origins": int(group["origin_year"].nunique()),
                "MAE": float(np.mean(np.abs(errors))),
                "RMSE": float(np.sqrt(np.mean(errors**2))),
                "mean_bias": float(np.mean(errors)),
                "MASE": float(
                    np.mean(np.abs(errors[valid_scales] / scales[valid_scales]))
                )
                if valid_scales.any()
                else float("nan"),
                # Compare lake-level mean absolute error over all available
                # origins, rather than counting repeated origin rows. This
                # makes the metric match its label and avoids weighting lakes
                # with more observed origins more heavily.
                "pct_lakes_beat_naive": (
                    float(
                        (
                            group.assign(abs_error=np.abs(group["error"]))
                            .groupby("MIDAS")[["abs_error", "naive_abs_error"]]
                            .mean()
                            .eval("abs_error < naive_abs_error")
                            .mean()
                        )
                        * 100
                    )
                    if model_name != "Last annual value"
                    else float("nan")
                ),
            }
        )
        summaries.append(record)
    return pd.DataFrame(summaries)


def _make_plot(summary: pd.DataFrame, reports_dir: Path) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for model_name in MODEL_NAMES:
        subset = summary[summary["model"] == model_name].sort_values("horizon")
        axes[0].plot(subset["horizon"], subset["MAE"], marker="o", label=model_name)
        axes[1].plot(subset["horizon"], subset["RMSE"], marker="o", label=model_name)
    for axis, metric, title in zip(
        axes,
        ["MAE", "RMSE"],
        ["Rolling-origin MAE by horizon", "Rolling-origin RMSE by horizon"],
    ):
        axis.set_xticks(HORIZONS)
        axis.set_xlabel("Forecast horizon (years)")
        axis.set_ylabel(f"{metric} (meters)")
        axis.set_title(title)
        axis.grid(alpha=0.25)
    axes[1].legend(fontsize=8, loc="best")
    fig.suptitle("Experiment 40: Direct Secchi Forecasting Baselines")
    fig.tight_layout()
    path = reports_dir / PLOT_FILENAME
    fig.savefig(path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    return path


def main() -> None:
    target, metadata, raw, dataset_id = _load_target_and_metadata()
    result, diagnostics = _run_backtest(target, metadata)
    target_sensitivity = _target_sensitivity(target, raw)
    summary = _summarize(result, ["model", "horizon"])
    subgroup = _summarize(result, ["model", "horizon", "history_bin"])
    region_summary = _summarize(
        result[result["horizon"].isin([5, 10])],
        ["model", "horizon", "REGION"],
    )

    reports_dir = Path(__file__).resolve().parents[2] / "reports"
    plot_path = _make_plot(summary, reports_dir)
    coverage_result = result.assign(
        key=list(zip(result["origin_year"], result["forecast_year"], result["MIDAS"]))
    ).drop_duplicates(["key", "horizon"])
    coverage = (
        coverage_result.groupby("horizon", as_index=False)
        .agg(
            n_forecast_cases=("key", "nunique"),
            n_lakes=("MIDAS", "nunique"),
            n_origins=("origin_year", "nunique"),
            first_origin=("origin_year", "min"),
            last_origin=("origin_year", "max"),
        )
        .sort_values("horizon")
    )

    report = CanonicalReport(
        objective=(
            "Benchmark direct annual summer Secchi forecasting baselines before fitting the "
            "hierarchical state-space and global multi-horizon CatBoost candidates. The experiment "
            "tests whether simple persistence, recent-level, robust-drift, or local-level dynamics "
            "provide useful forecasts at horizons 1, 3, 5, and 10 years."
        ),
        method=(
            "Use the persisted station-balanced annual summer lake-year target from Experiment 39. "
            f"For each calendar origin from {BACKTEST_ORIGINS[0]} through {BACKTEST_ORIGINS[-1]}, "
            "remove all lake-years after the origin, fit each method using only the remaining history, "
            "and evaluate against the exact subsequently observed summer target at each requested "
            "horizon. The common comparison cohort requires at least two prior summer lake-years and "
            "at least one observation in the preceding five calendar years."
        ),
        parameters=(
            f"Dataset ID: `{dataset_id}`.\n\n"
            f"Annual target: station-balanced June–September Secchi depth in meters.\n\n"
            f"Origins: `{BACKTEST_ORIGINS[0]}–{BACKTEST_ORIGINS[-1]}`. Horizons: `{HORIZONS}`.\n\n"
            "Baselines:\n"
            "- `Last annual value`: latest observed lake-year target.\n"
            "- `Recent 5-year mean`: mean of observed lake-years in the latest five calendar years.\n"
            "- `Theil-Sen drift`: robust slope/intercept fit to all prior lake-year targets, extrapolated to the forecast year and clipped at zero.\n"
            "- `Local-level state-space`: per-lake random-walk latent level fit by maximum likelihood with a Kalman filter; calendar gaps increase process variance.\n\n"
            "Metrics: MAE, RMSE, mean bias (prediction minus observation), MASE scaled by the in-history mean absolute change between successive observed annual values (calendar gaps are not interpolated), and percentage of lake forecasts beating the last-value naive baseline."
        ),
        results=(
            "### Rolling-Origin Coverage\n\n"
            f"{df_to_markdown_table(coverage, round_decimals=3)}\n\n"
            "### Accuracy by Model and Horizon\n\n"
            f"{df_to_markdown_table(summary.sort_values(['horizon', 'MAE']), round_decimals=4)}\n\n"
            "### Target Sensitivity on a Common Eligible Cohort\n\n"
            "Each row uses the recent 5-year calendar mean fitted from that target's own history. "
            "Eligibility is intersected across all four targets at each origin, horizon, and lake; full-year month effects are re-estimated and frozen at each origin.\n\n"
            f"{df_to_markdown_table(target_sensitivity.sort_values(['horizon', 'target']), round_decimals=4)}\n\n"
            f"![Forecasting baseline accuracy]({plot_path.name})\n\n"
            "### History-Stratified Accuracy\n\n"
            f"{df_to_markdown_table(subgroup.sort_values(['horizon', 'model', 'history_bin']), max_rows=100, round_decimals=4)}\n\n"
            "### Region Diagnostics for 5- and 10-Year Forecasts\n\n"
            f"{df_to_markdown_table(region_summary.sort_values(['horizon', 'model', 'REGION']), max_rows=100, round_decimals=4)}\n\n"
            "### Local-Level Fit Diagnostics\n\n"
            f"Local-level fits attempted: **{diagnostics['local_level_fits']:,}**. Fallback variance fits: **{diagnostics['local_level_fallbacks']:,}**."
        ),
        next_step=(
            "Use the rolling-origin baseline results and common evaluation cohort to fit the hierarchical "
            "lake-level state-space model in Experiment 41, adding predictive distributions and interval calibration."
        ),
    )

    path = write_canonical_report(REPORT_FILENAME, REPORT_TITLE, report)
    print(f"Wrote report to {path}")


if __name__ == "__main__":
    main()
