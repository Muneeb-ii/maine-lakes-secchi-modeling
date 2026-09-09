from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from experiment_utils import CanonicalReport, df_to_markdown_table, write_canonical_report

ROOT = Path(__file__).resolve().parents[2]
REPORT_FILENAME = "46_baseline_forecast_validation.md"
REPORT_TITLE = "Experiment 46: Later-origin baseline forecast validation"
PREDICTIONS_FILENAME = "46_baseline_forecast_validation.csv"
CALIBRATION_FILENAME = "46_baseline_calibration_residuals.csv"
ASSESSMENT_FILENAME = "46_baseline_forecast_assessment.json"
METRICS_FILENAME = "46_baseline_forecast_metrics.csv"
SUPPORT_METRICS_FILENAME = "46_baseline_support_metrics.csv"
PLOT_FILENAME = "46_baseline_forecast_validation.png"
MODELS = ("Recent 5-year mean", "Local-level state-space")
HORIZONS = (1, 2, 3, 4, 5)
EVAL_ORIGINS = tuple(range(2015, 2020))
CALIBRATION_ORIGINS = tuple(range(1990, 2015))


def _load_40():
    path = Path(__file__).with_name("40_forecasting_baselines.py")
    spec = importlib.util.spec_from_file_location("baseline40", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _finite_width(values: np.ndarray, level: float) -> float:
    if len(values) < 19:
        return float("nan")
    rank = int(np.ceil((len(values) + 1) * level))
    if rank > len(values):
        return float("nan")
    return float(np.sort(values)[rank - 1])


def _cases(mod, target: pd.DataFrame, metadata: pd.DataFrame, origins: tuple[int, ...]) -> pd.DataFrame:
    lookup = target.set_index(["MIDAS", "year"])
    by_lake = {lake: group.sort_values("year") for lake, group in target.groupby("MIDAS", sort=True)}
    meta = metadata.set_index("MIDAS").to_dict(orient="index")
    rows = []
    for origin in origins:
        for lake, lake_target in by_lake.items():
            history = lake_target[lake_target.year <= origin]
            recent = history[history.year >= origin - 4]
            if len(history) < 2 or recent.empty:
                continue
            years = history.year.to_numpy(dtype=int)
            values = history.summer_secchi.to_numpy(dtype=float)
            recent_mean = float(recent.summer_secchi.mean())
            forecast_years = [origin + horizon for horizon in HORIZONS]
            local_values, fallback = mod._local_level_forecast(years, values, forecast_years)
            future = []
            for horizon, year, local in zip(HORIZONS, forecast_years, local_values):
                if (lake, year) not in lookup.index:
                    continue
                actual = float(lookup.loc[(lake, year), "summer_secchi"])
                future.append((horizon, year, actual, recent_mean, float(local), fallback))
            for horizon, year, actual, recent_mean, local, fallback in future:
                mscale = mod._mase_scale(values)
                row = {"origin_year": origin, "forecast_year": year, "horizon": horizon, "MIDAS": lake, "actual": actual, "last_value": float(values[-1]), "history_years": len(history), "gap_since_last": int(origin - years[-1]), "mase_scale": mscale, "REGION": meta.get(lake, {}).get("REGION", "Unknown"), "bottom_hit_rate": float(lookup.loc[(lake, year), "bottom_hit_rate"]) if "bottom_hit_rate" in lookup.columns else np.nan, "local_level_fallback": bool(fallback)}
                row.update({"Recent 5-year mean": recent_mean, "Local-level state-space": local})
                rows.append(row)
    return pd.DataFrame(rows)


def _calibrate(eval_frame: pd.DataFrame, calibration_frame: pd.DataFrame) -> pd.DataFrame:
    out = eval_frame.copy()
    for model in MODELS:
        for level in (80, 95):
            column = f"{model}_half_width_{level}"
            out[column] = np.nan
            for origin in sorted(out.origin_year.unique()):
                # Freeze the entire horizon curve at this origin. Later origins
                # must never change an earlier forecast's calibration widths.
                prior = calibration_frame[
                    (calibration_frame.model == model)
                    & (calibration_frame.origin_year < origin)
                    & (calibration_frame.forecast_year <= origin)
                ]
                running_width = 0.0
                for horizon in HORIZONS:
                    residuals = prior[prior.horizon == horizon]
                    width = _finite_width(np.abs(residuals.prediction - residuals.actual).to_numpy(), level / 100)
                    if np.isfinite(width):
                        running_width = max(running_width, width)
                        mask = (out.origin_year == origin) & (out.horizon == horizon)
                        out.loc[mask, column] = running_width
            out[f"{model}_lower_{level}"] = (out[model] - out[column]).clip(lower=0)
            out[f"{model}_upper_{level}"] = out[model] + out[column]
    return out


def _metrics(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for model in MODELS:
        for horizon, group in frame.groupby("horizon", sort=True):
            error = group[model] - group.actual
            scale = group.mase_scale.to_numpy(float)
            valid = np.isfinite(scale) & (scale > 0)
            if "naive_ae" in group:
                lake = group.assign(model_ae=np.abs(error)).groupby("MIDAS", as_index=False).agg(model_ae=("model_ae", "mean"), naive_ae=("naive_ae", "mean"))
                pct_beat = float(np.mean(lake.model_ae < lake.naive_ae) * 100) if len(lake) else np.nan
            else:
                pct_beat = np.nan
            row = {"model": model, "horizon": int(horizon), "n_cases": len(group), "n_lakes": group.MIDAS.nunique(), "MAE": float(np.mean(np.abs(error))), "RMSE": float(np.sqrt(np.mean(error**2))), "MASE": float(np.mean(np.abs(error[valid] / scale[valid]))) if valid.any() else np.nan, "pct_lakes_beat_persistence": pct_beat}
            for level in (80, 95):
                lo, hi = group[f"{model}_lower_{level}"], group[f"{model}_upper_{level}"]
                valid_i = lo.notna() & hi.notna()
                row[f"n_interval_{level}"] = int(valid_i.sum())
                row[f"coverage_{level}"] = float(np.mean((group.loc[valid_i, "actual"] >= lo[valid_i]) & (group.loc[valid_i, "actual"] <= hi[valid_i]))) if valid_i.any() else np.nan
                row[f"width_{level}"] = float(np.mean((hi[valid_i] - lo[valid_i]))) if valid_i.any() else np.nan
            rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    mod = _load_40()
    target, metadata, _, dataset_id = mod._load_target_and_metadata()
    eval_frame = _cases(mod, target, metadata, EVAL_ORIGINS)
    eval_frame = eval_frame[eval_frame.forecast_year >= 2020].copy()
    calibration = _cases(mod, target, metadata, CALIBRATION_ORIGINS)
    cal_rows = []
    for model in MODELS:
        for _, row in calibration.iterrows():
            cal_rows.append({"origin_year": row.origin_year, "forecast_year": row.forecast_year, "horizon": row.horizon, "MIDAS": row.MIDAS, "model": model, "prediction": row[model], "actual": row.actual})
    calibration_long = pd.DataFrame(cal_rows)
    eval_frame["naive_ae"] = np.abs(eval_frame["actual"] - eval_frame["last_value"])
    result = _calibrate(eval_frame, calibration_long)
    metrics = _metrics(result)
    result.to_csv(ROOT / "reports" / PREDICTIONS_FILENAME, index=False)
    calibration_long.to_csv(ROOT / "reports" / CALIBRATION_FILENAME, index=False)
    group_rows = []
    for model in MODELS:
        for horizon, group in result[result.horizon == 5].groupby("horizon"):
            for label, subset in group.groupby(group.REGION.fillna("Unknown")):
                group_rows.append({"model": model, "group": "REGION", "level": label, "horizon": 5, "MAE": float(np.mean(np.abs(subset[model] - subset.actual)))})
            for label, subset in group.groupby(np.where(group.bottom_hit_rate >= .5, "Yes", "No")):
                group_rows.append({"model": model, "group": "Bottom-hit rate >= 0.5", "level": label, "horizon": 5, "MAE": float(np.mean(np.abs(subset[model] - subset.actual)))})
    group_table = pd.DataFrame(group_rows)
    support = result.assign(support_tier=np.where((result.history_years >= 10) & (result.gap_since_last <= 2), "Full", np.where((result.history_years >= 2) & (result.gap_since_last <= 4), "Limited", "Unavailable")))
    tier_metrics = []
    for tier, subset in support[support.horizon == 5].groupby("support_tier"):
        tier_metrics.append(_metrics(subset).assign(support_tier=tier))
    support_table = pd.concat(tier_metrics, ignore_index=True) if tier_metrics else pd.DataFrame()
    metrics.to_csv(ROOT / "reports" / METRICS_FILENAME, index=False)
    support_table.to_csv(ROOT / "reports" / SUPPORT_METRICS_FILENAME, index=False)
    h5 = metrics[metrics.horizon == 5].set_index("model")
    near_nominal = bool(len(h5) == len(MODELS) and h5.coverage_80.between(.70, .90).all() and h5.coverage_95.between(.85, 1.0).all())
    recommended_model = None
    if near_nominal:
        recommended_model = str(h5.MAE.idxmin())
    recommendation = (f"{recommended_model} is the lower-MAE five-year baseline in this later-origin check and has empirically near-nominal pooled interval coverage; a clearly labeled persistence outlook is defensible only with support tiers and interval availability exposed. This is descriptive evidence, does not establish trend skill, and does not waive or satisfy the registered Experiment 45 release gates." if recommended_model else "The later-origin check does not support releasing even a labeled baseline outlook with the current interval evidence; retain these baselines as comparisons and pursue additional calibration or model research. The registered Experiment 45 release gates remain unchanged.")
    assessment = {"dataset_id": dataset_id, "evaluation": "Later-origin retrospective check (origins 2015-2019, forecast years 2020-2024); not a pristine holdout because those years were present in earlier reports.", "maximum_horizon_years": 5, "recommended_model": recommended_model, "baseline_defensible": bool(recommended_model), "recommendation": recommendation, "evaluation_metrics": ["MAE", "RMSE", "MASE", "pct_lakes_beat_persistence", "coverage_80", "coverage_95", "width_80", "width_95"], "support_policy": {"Full": {"minimum_history_years": 10, "maximum_gap_years": 2}, "Limited": {"minimum_history_years": 2, "maximum_gap_years": 4}}, "metrics_csv": METRICS_FILENAME, "support_metrics_csv": SUPPORT_METRICS_FILENAME, "limitations": ["Pooled rolling-origin residuals are serially correlated empirical calibration scores, not formal coverage guarantees.", "Full-year target sensitivity is handled separately in Experiment 40.", "The registered Experiment 45 release gates remain unchanged."]}
    (ROOT / "reports" / ASSESSMENT_FILENAME).write_text(json.dumps(assessment, indent=2) + "\n")
    reports = ROOT / "reports"
    fig, ax = plt.subplots(figsize=(8, 4))
    for model in MODELS:
        subset = metrics[metrics.model == model]
        ax.plot(subset.horizon, subset.MAE, marker="o", label=model)
    ax.set(xlabel="Horizon (years)", ylabel="MAE (m)", title="Experiment 46: Later-origin baseline validation")
    ax.grid(alpha=.25); ax.legend(fontsize=8); fig.tight_layout(); fig.savefig(reports / PLOT_FILENAME, dpi=150); plt.close(fig)
    report = CanonicalReport(objective="Validate whether recent-mean and local-level baselines can support a clearly labeled lower-complexity outlook with empirically calibrated uncertainty on later origins.", method="Evaluate only origins 2015–2019 for forecast years 2020–2024. Calibrate symmetric intervals from earlier matured residuals (1990–2014), requiring at least 19 residuals and enforcing nondecreasing half-widths over horizon. Fixed Full/ Limited support thresholds are descriptive and were not tuned on evaluation rows.", parameters=f"Dataset ID: `{dataset_id}`. Models: Recent 5-year mean and local-level state-space. Horizons: 1–5 years. Evaluation origins: 2015–2019; calibration origins: 1990–2014.", results=f"### Metrics\n\n{df_to_markdown_table(metrics, round_decimals=4)}\n\n### Five-year support counts\n\n{df_to_markdown_table(support_table, round_decimals=4)}\n\n### Group diagnostics (five-year MAE)\n\n{df_to_markdown_table(group_table, round_decimals=4)}\n\n{assessment['recommendation']}\n\nArtifacts: `{PREDICTIONS_FILENAME}`, `{CALIBRATION_FILENAME}`, `{ASSESSMENT_FILENAME}`, `{METRICS_FILENAME}`, `{SUPPORT_METRICS_FILENAME}`, and `{PLOT_FILENAME}`. Intervals are empirical pooled-residual intervals; they do not establish formal nominal coverage. The later-origin check is retrospective rather than pristine holdout validation.", next_step="The labeled persistence outlook is what Trends serves. Experiment 48 is a simple-model challenger; Experiment 49 is the predefined replacement test and requires post-2024 outcomes before any swap.")
    write_canonical_report(REPORT_FILENAME, REPORT_TITLE, report)


if __name__ == "__main__":
    main()
