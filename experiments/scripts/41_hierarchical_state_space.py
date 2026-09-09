from __future__ import annotations

import os
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".cache" / "matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(ROOT / ".cache" / "xdg"))
os.environ.setdefault("PYTENSOR_FLAGS", f"base_compiledir={ROOT / '.cache' / 'pytensor'}")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pytensor")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pymc as pm
import pytensor.tensor as pt
from pytensor.scan import scan
from scipy.stats import norm

from experiment_utils import CanonicalReport, df_to_markdown_table, write_canonical_report
from forecasting_common import BACKTEST_ORIGINS, HORIZONS, history_is_eligible, load_target_and_metadata


REPORT_FILENAME = "41_hierarchical_state_space.md"
REPORT_TITLE = "Experiment 41: Hierarchical Bayesian State-Space Secchi Forecasting"
PLOT_FILENAME = "41_hierarchical_state_space.png"
EXAMPLES_FILENAME = "41_state_space_examples.png"
PREDICTIONS_FILENAME = "41_state_space_predictions.csv"
INTERVAL_LEVELS = (0.50, 0.80, 0.95)
ADVI_STEPS = 3000
POSTERIOR_DRAWS = 200


def _make_model(histories, n_groups, scale):
    n_lakes = len(histories)
    max_length = max(len(values) for _, values, _ in histories)
    deltas = np.zeros((max_length, n_lakes), dtype="float64")
    observations = np.zeros((max_length, n_lakes), dtype="float64")
    mask = np.zeros((max_length, n_lakes), dtype="float64")
    group_indices = np.asarray([group_index for _, _, group_index in histories], dtype="int32")
    for lake_index, (years, values, _) in enumerate(histories):
        observations[: len(values), lake_index] = values
        mask[: len(values), lake_index] = 1.0
        if len(values) > 1:
            deltas[1 : len(values), lake_index] = np.maximum(np.diff(years), 1)
    init_level_var = max(scale, 0.1)
    init_slope_var = max(scale / 25.0, 0.01)
    with pm.Model() as model:
        global_level = pm.Normal("global_level", mu=float(np.mean([values[0] for _, values, _ in histories])), sigma=float(np.sqrt(scale) * 3.0 + 1.0))
        global_slope = pm.Normal("global_slope", mu=0.0, sigma=float(np.sqrt(scale)))
        group_level_sd = pm.HalfNormal("group_level_sd", sigma=float(np.sqrt(scale) + 0.5))
        group_slope_sd = pm.HalfNormal("group_slope_sd", sigma=float(np.sqrt(scale) / 3.0 + 0.1))
        group_level = pm.Normal("group_level", mu=global_level, sigma=group_level_sd, shape=n_groups)
        group_slope = pm.Normal("group_slope", mu=global_slope, sigma=group_slope_sd, shape=n_groups)
        q_level = pm.LogNormal("q_level", mu=np.log(max(scale * 0.08, 1e-4)), sigma=0.9)
        q_slope = pm.LogNormal("q_slope", mu=np.log(max(scale * 0.003, 1e-5)), sigma=0.9)
        measurement_sd = pm.HalfNormal("measurement_sd", sigma=float(np.sqrt(scale) + 0.5))
        delta_tensor = pt.as_tensor_variable(deltas)
        observation_tensor = pt.as_tensor_variable(observations)
        mask_tensor = pt.as_tensor_variable(mask)
        initial_level = group_level[group_indices]
        initial_slope = group_slope[group_indices]
        initial_p00 = pt.as_tensor_variable(np.full(n_lakes, init_level_var))
        initial_p01 = pt.as_tensor_variable(np.zeros(n_lakes))
        initial_p11 = pt.as_tensor_variable(np.full(n_lakes, init_slope_var))
        initial_nll = pt.as_tensor_variable(np.zeros(n_lakes))

        def step(delta, observed, observed_mask, level, slope, p00, p01, p11, accumulated_nll, q_l, q_s, measurement_variance):
            predicted_level = level + delta * slope
            predicted_p00 = p00 + 2.0 * delta * p01 + delta * delta * p11 + q_l * delta + q_s * delta**3 / 3.0
            predicted_p01 = p01 + delta * p11 + q_s * delta**2 / 2.0
            predicted_p11 = p11 + q_s * delta
            innovation_variance = predicted_p00 + measurement_variance
            innovation = observed - predicted_level
            gain_level = predicted_p00 / innovation_variance
            gain_slope = predicted_p01 / innovation_variance
            updated_level = predicted_level + gain_level * innovation
            updated_slope = slope + gain_slope * innovation
            updated_p00 = predicted_p00 - gain_level * predicted_p00
            updated_p01 = predicted_p01 - gain_level * predicted_p01
            updated_p11 = predicted_p11 - gain_slope * predicted_p01
            nll = accumulated_nll + observed_mask * 0.5 * (pt.log(innovation_variance) + innovation * innovation / innovation_variance)
            return (pt.switch(observed_mask, updated_level, level), pt.switch(observed_mask, updated_slope, slope), pt.switch(observed_mask, updated_p00, p00), pt.switch(observed_mask, updated_p01, p01), pt.switch(observed_mask, updated_p11, p11), nll)

        outputs = scan(fn=step, sequences=[delta_tensor, observation_tensor, mask_tensor], outputs_info=[initial_level, initial_slope, initial_p00, initial_p01, initial_p11, initial_nll], non_sequences=[q_level, q_slope, measurement_sd**2], strict=True, return_updates=False)
        pm.Potential("pooled_kalman_likelihood", -pt.sum(outputs[-1][-1]))
    return model


def _fit_origin(histories, n_groups, scale):
    model = _make_model(histories, n_groups, scale)
    with model:
        approx = pm.fit(n=ADVI_STEPS, method="advi", random_seed=42, progressbar=False, callbacks=[pm.callbacks.CheckParametersConvergence(tolerance=0.01, diff="relative")])
        posterior = approx.sample(POSTERIOR_DRAWS, random_seed=42)
    elbo = np.asarray(approx.hist, dtype=float)
    tail = elbo[-min(100, len(elbo)) :]
    diagnostics = {
        "advi_steps": len(elbo),
        "elbo_start": float(elbo[0]),
        "elbo_end": float(elbo[-1]),
        "elbo_tail_relative_change": float(abs(tail[-1] - tail[0]) / max(abs(tail[0]), 1.0)) if len(tail) > 1 else np.nan,
        "posterior_draws": POSTERIOR_DRAWS,
    }
    # A callback stopping before the optimization budget is the only evidence
    # of convergence.  A quiet ELBO tail at the hard budget is still a
    # provisional fit and must not be promoted to valid automatically.
    diagnostics["convergence_valid"] = bool(len(elbo) < ADVI_STEPS)
    return posterior, diagnostics


def _posterior_array(posterior, name):
    values = posterior.posterior[name].stack(sample=("chain", "draw"))
    dims = ["sample"] + [dimension for dimension in values.dims if dimension != "sample"]
    return np.asarray(values.transpose(*dims).values)


def _filter_numpy(years, values, group_level, group_slope, q_level, q_slope, measurement_variance, init_level_var, init_slope_var):
    state = np.array([group_level, group_slope], dtype=float)
    covariance = np.array([[init_level_var, 0.0], [0.0, init_slope_var]], dtype=float)
    previous_year = int(years[0])
    for year, observed in zip(years, values):
        delta = max(int(year) - previous_year, 0)
        transition = np.array([[1.0, delta], [0.0, 1.0]])
        covariance = transition @ covariance @ transition.T + np.array(
            [[q_level * delta + q_slope * delta**3 / 3.0, q_slope * delta**2 / 2.0],
             [q_slope * delta**2 / 2.0, q_slope * delta]], dtype=float
        )
        state = transition @ state
        innovation_variance = covariance[0, 0] + measurement_variance
        gain = covariance[:, 0] / innovation_variance
        state = state + gain * (float(observed) - state[0])
        covariance = covariance - np.outer(gain, covariance[0, :])
        covariance = (covariance + covariance.T) * 0.5
        previous_year = int(year)
    return state, covariance


def _posterior_forecasts(posterior, history, group_index, forecast_years, scale):
    q_level = _posterior_array(posterior, "q_level")
    q_slope = _posterior_array(posterior, "q_slope")
    measurement_sd = _posterior_array(posterior, "measurement_sd")
    group_level = _posterior_array(posterior, "group_level")[:, group_index]
    group_slope = _posterior_array(posterior, "group_slope")[:, group_index]
    years = history["year"].to_numpy(dtype=int)
    values = history["summer_secchi"].to_numpy(dtype=float)
    init_level_var = max(scale, 0.1)
    init_slope_var = max(scale / 25.0, 0.01)
    rng = np.random.default_rng(42)
    output = {year: np.empty(len(q_level), dtype=float) for year in forecast_years}
    for index in range(len(q_level)):
        state, covariance = _filter_numpy(years, values, group_level[index], group_slope[index], q_level[index], q_slope[index], measurement_sd[index] ** 2, init_level_var, init_slope_var)
        for year in forecast_years:
            delta = max(int(year) - int(years[-1]), 1)
            transition = np.array([[1.0, delta], [0.0, 1.0]])
            covariance_forecast = transition @ covariance @ transition.T + np.array(
                [[q_level[index] * delta + q_slope[index] * delta**3 / 3.0, q_slope[index] * delta**2 / 2.0],
                 [q_slope[index] * delta**2 / 2.0, q_slope[index] * delta]], dtype=float
            )
            state_forecast = transition @ state
            variance = max(float(covariance_forecast[0, 0] + measurement_sd[index] ** 2), 1e-8)
            output[year][index] = rng.normal(float(state_forecast[0]), np.sqrt(variance))
    return output


def _summary(result):
    rows = []
    for horizon, group in result.groupby("horizon", sort=True):
        actual = group["actual"].to_numpy(dtype=float)
        prediction = group["prediction"].to_numpy(dtype=float)
        error = prediction - actual
        scales = group["mase_scale"].to_numpy(dtype=float)
        valid = np.isfinite(scales) & (scales > 0)
        lake_compare = group.assign(abs_error=np.abs(error)).groupby("MIDAS").agg(model_mae=("abs_error", "mean"), naive_mae=("naive_abs_error", "mean"))
        row = {"horizon": int(horizon), "n_forecasts": len(group), "n_lakes": int(group["MIDAS"].nunique()), "MAE": float(np.mean(np.abs(error))), "RMSE": float(np.sqrt(np.mean(error**2))), "mean_bias": float(np.mean(error)), "MASE": float(np.mean(np.abs(error[valid] / scales[valid]))) if valid.any() else np.nan, "pct_lakes_beat_naive": float(np.mean(lake_compare["model_mae"] < lake_compare["naive_mae"]) * 100), "CRPS": float(group["crps"].mean())}
        for level in INTERVAL_LEVELS:
            label = int(level * 100)
            lower = group[f"lower_{label}"].to_numpy(dtype=float)
            upper = group[f"upper_{label}"].to_numpy(dtype=float)
            row[f"coverage_{label}"] = float(np.mean((actual >= lower) & (actual <= upper)))
            row[f"width_{label}"] = float(np.mean(upper - lower))
        rows.append(row)
    return pd.DataFrame(rows)


def _make_examples(result: pd.DataFrame, target_by_lake: dict[str, pd.DataFrame], reports_dir: Path) -> Path:
    candidates = result[result["origin_year"] == 2014].copy()
    if candidates.empty:
        return reports_dir / EXAMPLES_FILENAME
    lake_stats = candidates.groupby("MIDAS", as_index=False).agg(history_years=("history_years", "first"), bottom_hit_rate=("bottom_hit_rate", "mean"))
    selected = []
    for selector in [
        lambda frame: frame.sort_values(["history_years", "MIDAS"], ascending=[False, True]).iloc[0],
        lambda frame: frame.assign(distance=(frame["history_years"] - 10).abs()).sort_values(["distance", "MIDAS"]).iloc[0],
        lambda frame: frame.sort_values(["history_years", "MIDAS"], ascending=[True, True]).iloc[0],
        lambda frame: frame.sort_values(["bottom_hit_rate", "MIDAS"], ascending=[False, True]).iloc[0],
    ]:
        remaining = lake_stats[~lake_stats["MIDAS"].isin([item["MIDAS"] for item in selected])]
        if remaining.empty:
            break
        selected.append(selector(remaining).to_dict())
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharex=True)
    for axis, item in zip(axes.flat, selected):
        lake_id = str(item["MIDAS"])
        history = target_by_lake[lake_id][target_by_lake[lake_id]["year"] <= 2014]
        forecasts = candidates[candidates["MIDAS"] == lake_id].sort_values("horizon")
        axis.plot(history["year"], history["summer_secchi"], "o-", color="#333333", label="Observed history")
        prediction_values = forecasts["prediction"].to_numpy(dtype=float)
        lower_values = np.minimum(forecasts["lower_95"].to_numpy(dtype=float), prediction_values)
        upper_values = np.maximum(forecasts["upper_95"].to_numpy(dtype=float), prediction_values)
        axis.errorbar(forecasts["forecast_year"], prediction_values, yerr=[prediction_values - lower_values, upper_values - prediction_values], fmt="o-", color="#1f77b4", capsize=3, label="Posterior median ±95%")
        axis.scatter(forecasts["forecast_year"], forecasts["actual"], color="#d62728", s=24, zorder=3, label="Later observed")
        axis.axvline(2014, color="#777777", linestyle="--")
        axis.set_title(f"{lake_id}: {int(item['history_years'])} prior years")
        axis.set_ylabel("Secchi depth (m)")
        axis.grid(alpha=0.2)
    axes[1, 0].set_xlabel("Calendar year")
    axes[1, 1].set_xlabel("Calendar year")
    axes[0, 0].legend(fontsize=8)
    fig.suptitle("Experiment 41: Bayesian State-Space Lake Examples (origin 2014)")
    fig.tight_layout()
    path = reports_dir / EXAMPLES_FILENAME
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def main():
    target, metadata, dataset_id = load_target_and_metadata()
    target_by_lake = {lake_id: group.sort_values("year") for lake_id, group in target.groupby("MIDAS", sort=True)}
    metadata_lookup = metadata.set_index("MIDAS").to_dict(orient="index")
    result_rows = []
    diagnostics_rows = []
    for origin in BACKTEST_ORIGINS:
        eligible = []
        all_values = []
        group_names = {}
        for lake_id, lake_target in target_by_lake.items():
            history = lake_target[lake_target["year"] <= origin]
            if not history_is_eligible(history, origin):
                continue
            meta = metadata_lookup.get(lake_id, {})
            # The trophic/classification source is undated and the geography
            # join was released in 2014; exclude it from pre-2014 temporal
            # backtests to avoid treating later metadata as historical.
            group_name = f"{meta.get('REGION', 'Unknown')}"
            group_names.setdefault(group_name, len(group_names))
            eligible.append((lake_id, history, group_names[group_name]))
            all_values.extend(history["summer_secchi"].to_numpy(dtype=float).tolist())
        histories = [(history["year"].to_numpy(dtype=int), history["summer_secchi"].to_numpy(dtype=float), group_index) for _, history, group_index in eligible]
        scale = max(float(np.var(np.asarray(all_values), ddof=1)), 1e-4)
        posterior, fit_diagnostics = _fit_origin(histories, len(group_names), scale)
        diagnostics_rows.append({"origin_year": origin, "n_lakes": len(eligible), "n_groups": len(group_names), **fit_diagnostics})
        for lake_id, history, group_index in eligible:
            target_lookup = target_by_lake[lake_id].set_index("year")
            forecast_years = list(range(origin + 1, origin + max(HORIZONS) + 1))
            posterior_samples = _posterior_forecasts(posterior, history, group_index, forecast_years, scale)
            for horizon in HORIZONS:
                forecast_year = origin + horizon
                if forecast_year not in target_lookup.index:
                    continue
                samples = posterior_samples[forecast_year]
                actual = float(target_lookup.loc[forecast_year, "summer_secchi"])
                prediction = max(float(np.quantile(samples, 0.50)), 0.0)
                row = {"origin_year": origin, "forecast_year": forecast_year, "horizon": horizon, "MIDAS": lake_id, "actual": actual, "prediction": prediction, "naive_abs_error": abs(float(history.iloc[-1]["summer_secchi"]) - actual), "mase_scale": float(np.mean(np.abs(np.diff(history["summer_secchi"].to_numpy(dtype=float))))) if len(history) > 1 else np.nan, "history_years": len(history), "gap_since_last": origin - int(history.iloc[-1]["year"]), "REGION": metadata_lookup.get(lake_id, {}).get("REGION", "Unknown"), "bottom_hit_rate": float(target_lookup.loc[forecast_year, "bottom_hit_rate"]), "convergence_valid": bool(fit_diagnostics["convergence_valid"])}
                for level in INTERVAL_LEVELS:
                    label = int(level * 100)
                    row[f"lower_{label}"] = max(float(np.quantile(samples, (1.0 - level) / 2.0)), 0.0)
                    row[f"upper_{label}"] = float(np.quantile(samples, 1.0 - (1.0 - level) / 2.0))
                standard_deviation = max(float(np.std(samples)), 1e-8)
                z = (actual - prediction) / standard_deviation
                row["crps"] = float(standard_deviation * (z * (2.0 * norm.cdf(z) - 1.0) + 2.0 * norm.pdf(z) - 1.0 / np.sqrt(np.pi)))
                result_rows.append(row)
    result = pd.DataFrame(result_rows)
    if result.empty:
        raise RuntimeError("No Bayesian state-space backtest predictions were generated.")
    summary = _summary(result)
    reports_dir = ROOT / "reports"
    result.to_csv(reports_dir / PREDICTIONS_FILENAME, index=False)
    examples_path = _make_examples(result, target_by_lake, reports_dir)
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    axes[0].plot(summary["horizon"], summary["MAE"], marker="o")
    axes[0].set_title("Point accuracy")
    axes[0].set_ylabel("MAE (meters)")
    axes[1].plot(summary["horizon"], summary["CRPS"], marker="o", color="#2ca02c")
    axes[1].set_title("Posterior predictive CRPS")
    axes[1].set_ylabel("CRPS (meters)")
    for level, color in zip(INTERVAL_LEVELS, ["#9467bd", "#ff7f0e", "#d62728"]):
        label = int(level * 100)
        axes[2].plot(summary["horizon"], summary[f"coverage_{label}"] * 100, marker="o", color=color, label=f"{label}%")
        axes[2].axhline(level * 100, linestyle="--", color=color, alpha=0.35)
    axes[2].set_title("Posterior predictive coverage")
    axes[2].set_ylabel("Coverage (%)")
    for axis in axes:
        axis.set_xticks(HORIZONS)
        axis.set_xlabel("Forecast horizon (years)")
        axis.grid(alpha=0.25)
    axes[2].legend()
    fig.suptitle(REPORT_TITLE)
    fig.tight_layout()
    plot_path = reports_dir / PLOT_FILENAME
    fig.savefig(plot_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    diagnostics = pd.DataFrame(diagnostics_rows)
    report = CanonicalReport(
        objective="Fit the recommended hierarchical Bayesian state-space model for direct annual summer Secchi forecasting. The model separates latent lake clarity from measurement noise, shares information by region, and produces posterior predictive distributions.",
        method=f"Use the station-balanced annual summer target from Experiment 39 and refit at each expanding-window origin {BACKTEST_ORIGINS[0]}–{BACKTEST_ORIGINS[-1]}. The latent process is a local-linear trend with irregular calendar-gap process noise. A PyMC potential evaluates the integrated Kalman-filter likelihood, and posterior predictive samples propagate state and hyperparameter uncertainty to horizons 1, 3, 5, and 10.",
        parameters=f"Dataset ID: `{dataset_id}`. Horizons: `{HORIZONS}`.\n\nHierarchy: global level/slope distributions with region group means and scales. Observation model: Gaussian Secchi-depth measurement error. State model: latent level and slope with positive process variances that scale with calendar gaps.\n\nInference: PyMC ADVI with up to `{ADVI_STEPS}` optimization steps, `{POSTERIOR_DRAWS}` posterior draws per origin, seed 42. Diagnostics include ELBO start/end, tail relative change, and an explicit convergence-validity gate; only callback termination before the budget is marked valid, while fits that exhaust the budget remain provisional.\n\nBottom-hit flags remain attached to evaluated lake-years and are reported for diagnostics; explicit censored likelihood treatment is a subsequent refinement because the annual target currently stores the aggregate value plus its bottom-hit rate.",
        results=f"### Posterior Predictive Accuracy and Calibration\n\n{df_to_markdown_table(summary, round_decimals=4)}\n\n![Bayesian state-space accuracy and calibration]({plot_path.name})\n\n### Lake-Level Examples\n\n![Bayesian state-space lake examples]({examples_path.name})\n\n### Variational Convergence Diagnostics\n\n{df_to_markdown_table(diagnostics, round_decimals=6)}\n\nPosterior predictions are persisted at `reports/{PREDICTIONS_FILENAME}` for Experiments 44–45.",
        next_step="Compare this full Bayesian state-space model with the direct multi-horizon CatBoost challenger in Experiment 42 and the nonlinear trend-shape challenger in Experiment 43.",
    )
    path = write_canonical_report(REPORT_FILENAME, REPORT_TITLE, report)
    print(f"Wrote report to {path}")


if __name__ == "__main__":
    main()
