from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from experiment_utils import CanonicalReport, df_to_markdown_table, write_canonical_report
from forecasting_common import HORIZONS, load_target_and_metadata, project_root, support_tier


EXPERIMENT_ID = "44"
REPORT_FILENAME = "44_interval_calibration_support.md"
REPORT_TITLE = "Experiment 44: Interval Calibration and Support Policy"
PLOT_FILENAME = "44_interval_calibration_support.png"
PREDICTIONS_FILENAME = "44_calibrated_predictions.csv"
POLICIES = (
    {"name": "Full history 5y / gap 2y", "full_history": 5, "full_gap": 2, "limited_history": 2, "limited_gap": 5},
    {"name": "Full history 5y / gap 5y", "full_history": 5, "full_gap": 5, "limited_history": 2, "limited_gap": 5},
    {"name": "Full history 10y / gap 2y", "full_history": 10, "full_gap": 2, "limited_history": 2, "limited_gap": 5},
    {"name": "Full history 10y / gap 5y", "full_history": 10, "full_gap": 5, "limited_history": 2, "limited_gap": 5},
    {"name": "Full history 15y / gap 2y", "full_history": 15, "full_gap": 2, "limited_history": 2, "limited_gap": 5},
    {"name": "Full history 15y / gap 5y", "full_history": 15, "full_gap": 5, "limited_history": 2, "limited_gap": 5},
)


def _interval_score(actual: np.ndarray, lower: np.ndarray, upper: np.ndarray, level: float) -> np.ndarray:
    alpha = 1.0 - level
    return (upper - lower) + (2.0 / alpha) * (lower - actual) * (actual < lower) + (2.0 / alpha) * (actual - upper) * (actual > upper)


def _policy_tiers(frame: pd.DataFrame, policy: dict[str, object]) -> pd.Series:
    return frame.apply(
        lambda row: support_tier(
            float(row["history_years"]),
            float(row["gap_since_last"]),
            full_history=int(policy["full_history"]),
            full_gap=int(policy["full_gap"]),
            limited_history=int(policy["limited_history"]),
            limited_gap=int(policy["limited_gap"]),
        ),
        axis=1,
    )


def _finite_sample_quantile(values: np.ndarray, level: float) -> float:
    """Conservative split-conformal quantile for a finite residual sample."""
    if len(values) == 0:
        return 0.0
    ordered = np.sort(np.asarray(values, dtype=float))
    rank = int(np.ceil((len(ordered) + 1) * level))
    if rank > len(ordered):
        return float("inf")
    return float(ordered[max(rank, 1) - 1])


def _calibrate(frame: pd.DataFrame, policy: dict[str, object]) -> pd.DataFrame:
    result = frame.copy()
    result["support_tier"] = _policy_tiers(result, policy)
    result["calibration_n"] = 0
    result["calibration_available"] = False
    for column in ["cal_q10", "cal_q90", "cal_q025", "cal_q975"]:
        result[column] = np.nan
    for horizon in HORIZONS:
        horizon_mask = result["horizon"] == horizon
        for origin in sorted(result.loc[horizon_mask, "origin_year"].unique()):
            current_mask = horizon_mask & (result["origin_year"] == origin) & (result["support_tier"] != "Unavailable")
            if not current_mask.any():
                continue
            prior = result[
                horizon_mask
                & (result["origin_year"] < origin)
                # A residual is usable only after its realized outcome year.
                # Earlier origins alone are insufficient for long horizons.
                & (result["forecast_year"] <= origin)
                & (result["support_tier"] != "Unavailable")
            ]
            # Require enough residuals for the finite-sample 95% quantile.
            # With fewer than 19 scores, its conformal rank is beyond the
            # observed sample, so no calibrated interval is claimed.
            if len(prior) < 19:
                continue
            else:
                score_80 = np.maximum.reduce(
                    [prior["q10"].to_numpy() - prior["actual"].to_numpy(), prior["actual"].to_numpy() - prior["q90"].to_numpy(), np.zeros(len(prior))]
                )
                score_95 = np.maximum.reduce(
                    [prior["q025"].to_numpy() - prior["actual"].to_numpy(), prior["actual"].to_numpy() - prior["q975"].to_numpy(), np.zeros(len(prior))]
                )
                adjustment_80 = _finite_sample_quantile(score_80, 0.80)
                adjustment_95 = max(_finite_sample_quantile(score_95, 0.95), adjustment_80)
            result.loc[current_mask, "cal_q10"] = np.maximum(result.loc[current_mask, "q10"] - adjustment_80, 0.0)
            result.loc[current_mask, "cal_q90"] = result.loc[current_mask, "q90"] + adjustment_80
            result.loc[current_mask, "cal_q025"] = np.maximum(result.loc[current_mask, "q025"] - adjustment_95, 0.0)
            result.loc[current_mask, "cal_q975"] = result.loc[current_mask, "q975"] + adjustment_95
            result.loc[current_mask, "calibration_n"] = len(prior)
            result.loc[current_mask, "calibration_available"] = True
    return result


def _summarize(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for keys, group in frame.groupby(columns, sort=True, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(columns, keys))
        actual = group["actual"].to_numpy(dtype=float)
        for level, lower_column, upper_column in [(0.80, "cal_q10", "cal_q90"), (0.95, "cal_q025", "cal_q975")]:
            valid = group[lower_column].notna().to_numpy()
            if not valid.any():
                continue
            lower = group.loc[valid, lower_column].to_numpy(dtype=float)
            upper = group.loc[valid, upper_column].to_numpy(dtype=float)
            observed = actual[valid]
            label = int(level * 100)
            row[f"n_{label}"] = int(valid.sum())
            row[f"coverage_{label}"] = float(np.mean((observed >= lower) & (observed <= upper)))
            row[f"width_{label}"] = float(np.mean(upper - lower))
            row[f"interval_score_{label}"] = float(np.mean(_interval_score(observed, lower, upper, level)))
        rows.append(row)
    return pd.DataFrame(rows)


def _group_diagnostics(frame: pd.DataFrame) -> pd.DataFrame:
    """Compact accuracy and interval diagnostics for the registered groups."""
    grouped = frame.assign(
        bottom_hit_group=np.where(pd.to_numeric(frame["bottom_hit_rate"], errors="coerce") >= 0.5, "Yes", "No")
    )
    rows: list[dict[str, object]] = []
    for group_name, group_column in [("REGION", "REGION"), ("Bottom-hit rate >= 0.5", "bottom_hit_group")]:
        subset_frame = grouped[grouped["horizon"].isin([5, 10])]
        for (horizon, label), subset in subset_frame.groupby(["horizon", group_column], sort=True):
            row: dict[str, object] = {"group": group_name, "level": str(label), "horizon": int(horizon), "n_forecasts": len(subset), "MAE": float(np.mean(np.abs(subset["prediction"] - subset["actual"])))}
            for level, lower, upper in [(80, "cal_q10", "cal_q90"), (95, "cal_q025", "cal_q975")]:
                valid = subset[lower].notna() & subset[upper].notna()
                row[f"n_interval_{level}"] = int(valid.sum())
                row[f"coverage_{level}"] = float(np.mean((subset.loc[valid, "actual"] >= subset.loc[valid, lower]) & (subset.loc[valid, "actual"] <= subset.loc[valid, upper]))) if valid.any() else np.nan
            rows.append(row)
    return pd.DataFrame(rows)


def _policy_score(summary: pd.DataFrame) -> float:
    target = {"coverage_80": 0.80, "coverage_95": 0.95}
    errors = []
    for column, nominal in target.items():
        if column in summary:
            values = summary[column].to_numpy(dtype=float)
            errors.extend(np.abs(values[np.isfinite(values)] - nominal).tolist())
    width_values = summary["width_80"].to_numpy(dtype=float) if "width_80" in summary else np.array([])
    width_values = width_values[np.isfinite(width_values)]
    width_penalty = float(width_values.mean()) * 0.001 if len(width_values) else 100.0
    return float(np.mean(errors) + width_penalty) if errors else 100.0


def _final_support_counts(target: pd.DataFrame, policy: dict[str, object]) -> pd.DataFrame:
    latest_year = int(target["year"].max())
    rows: list[dict[str, object]] = []
    for lake_id, group in target.groupby("MIDAS", sort=True):
        years = group["year"].to_numpy(dtype=int)
        tier = support_tier(
            len(group),
            latest_year - int(years.max()),
            full_history=int(policy["full_history"]),
            full_gap=int(policy["full_gap"]),
            limited_history=int(policy["limited_history"]),
            limited_gap=int(policy["limited_gap"]),
        )
        rows.append({"MIDAS": lake_id, "history_years": len(group), "latest_year": int(years.max()), "gap_since_last": latest_year - int(years.max()), "support_tier": tier})
    result = pd.DataFrame(rows)
    return result.groupby("support_tier", as_index=False).agg(n_lakes=("MIDAS", "size"), median_history_years=("history_years", "median"), median_gap=("gap_since_last", "median"))


def _make_plot(summary: pd.DataFrame, policy_name: str, reports_dir: Path) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    for level, color in [(80, "#ff7f0e"), (95, "#d62728")]:
        subset = summary.sort_values("horizon")
        axes[0].plot(subset["horizon"], subset[f"coverage_{level}"] * 100, marker="o", color=color, label=f"{level}% observed")
        axes[0].axhline(level, linestyle="--", color=color, alpha=0.45, label=f"{level}% nominal")
    axes[0].set_title("Calibrated coverage")
    axes[0].set_ylabel("Coverage (%)")
    axes[1].plot(summary["horizon"], summary["width_80"], marker="o", label="80% interval")
    axes[1].plot(summary["horizon"], summary["width_95"], marker="o", label="95% interval")
    axes[1].set_title("Calibrated interval width")
    axes[1].set_ylabel("Mean width (meters)")
    for axis in axes:
        axis.set_xticks(HORIZONS)
        axis.set_xlabel("Forecast horizon (years)")
        axis.grid(alpha=0.25)
    axes[0].legend(fontsize=8)
    axes[1].legend(fontsize=8)
    fig.suptitle(f"Experiment 44: Interval Calibration ({policy_name})")
    fig.tight_layout()
    path = reports_dir / PLOT_FILENAME
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def main() -> None:
    target, _, dataset_id = load_target_and_metadata()
    predictions_path = project_root() / "reports" / "42_catboost_predictions.csv"
    if not predictions_path.exists():
        raise FileNotFoundError(f"Experiment 42 predictions not found at {predictions_path}")
    predictions = pd.read_csv(predictions_path)
    policy_rows: list[dict[str, object]] = []
    calibrated_by_policy: dict[str, pd.DataFrame] = {}
    for policy in POLICIES:
        calibrated = _calibrate(predictions, policy)
        evaluated = calibrated[calibrated["support_tier"] != "Unavailable"]
        summary = _summarize(evaluated, ["horizon"])
        tier_score_table = _summarize(evaluated[evaluated["horizon"].isin([5, 10])], ["horizon", "support_tier"])
        score = _policy_score(tier_score_table)
        final_counts = _final_support_counts(target, policy)
        counts = final_counts.set_index("support_tier")["n_lakes"].to_dict()
        policy_rows.append({"policy": policy["name"], "selection_score": score, "full_lakes": counts.get("Full", 0), "limited_lakes": counts.get("Limited", 0), "unavailable_lakes": counts.get("Unavailable", 0), "coverage_80_h5_h10": float(summary[summary["horizon"].isin([5, 10])]["coverage_80"].mean()), "coverage_95_h5_h10": float(summary[summary["horizon"].isin([5, 10])]["coverage_95"].mean())})
        calibrated_by_policy[policy["name"]] = calibrated
    policy_table = pd.DataFrame(policy_rows).sort_values(["selection_score", "policy"]).reset_index(drop=True)
    selected_name = str(policy_table.iloc[0]["policy"])
    selected_policy = next(policy for policy in POLICIES if policy["name"] == selected_name)
    calibrated = calibrated_by_policy[selected_name]
    evaluated = calibrated[calibrated["support_tier"] != "Unavailable"]
    summary = _summarize(evaluated, ["horizon"])
    tier_summary = _summarize(evaluated[evaluated["horizon"].isin([5, 10])], ["horizon", "support_tier"])
    group_summary = _group_diagnostics(evaluated)
    final_support = _final_support_counts(target, selected_policy)
    reports_dir = project_root() / "reports"
    plot_path = _make_plot(summary, selected_name, reports_dir)
    output_path = reports_dir / PREDICTIONS_FILENAME
    calibrated.to_csv(output_path, index=False)
    report = CanonicalReport(
        objective=(
            "Calibrate direct CatBoost prediction intervals using only earlier rolling-origin residuals and select a reproducible forecast-support policy. The policy separates full, limited, and unavailable forecasts rather than presenting equal confidence for every lake."
        ),
        method=(
            "Read Experiment 42’s horizon-specific CatBoost quantile predictions. For each origin, horizon, and candidate support policy, compute a conformal-style nonnegative adjustment from residual scores at earlier origins whose outcomes are already observed, then expand the raw q10–q90 and q025–q975 intervals. Rank six history/recency policies on available calibrated coverage error plus a small width penalty."
        ),
        parameters=(
            f"Dataset ID: `{dataset_id}`.\n\n"
            "Candidate full-history thresholds: 5, 10, or 15 observed summer years. Candidate full-recency thresholds: 2 or 5 years. Limited support requires at least 2 observed years and a gap of at most 5 years.\n\n"
            "Conformal scores are horizon-specific and use only earlier origins, avoiding calibration leakage. Intervals are prediction intervals, not confidence intervals. Coverage is empirical over pooled, serially correlated rolling-origin residuals; it is not a formal guarantee."
            " A residual is eligible only when its forecast year is no later than the current origin, so the 10-year backtest has no outcome-matured calibration residuals. Finite-sample conservative quantiles are used, and the 95% adjustment is constrained to be at least the 80% adjustment so intervals remain nested."
        ),
        results=(
            f"### Selected Support Policy\n\n**{selected_name}**. Selection score: **{float(policy_table.iloc[0]['selection_score']):.4f}**.\n\n"
            "### Candidate Policies\n\n"
            f"{df_to_markdown_table(policy_table, round_decimals=4)}\n\n"
            "### Calibrated Coverage and Sharpness\n\n"
            f"{df_to_markdown_table(summary, round_decimals=4)}\n\n"
            f"![Calibrated interval coverage and width]({plot_path.name})\n\n"
            "Rows without outcome-matured calibration residuals are retained in the prediction artifact with null calibrated intervals and are excluded from calibrated coverage/sharpness summaries. The 5-year/10-year columns in the candidate table contain only the available matured horizon (5 years); no 10-year calibration result exists in this backtest. Candidate-policy ranking is exploratory because support labels are selected from the same rolling-origin backtest; it is not an independent confirmation set.\n\n"
            "### Support-Tier Diagnostics at 5 and 10 Years\n\n"
            f"{df_to_markdown_table(tier_summary, round_decimals=4)}\n\n"
            "### Group Diagnostics at 5 and 10 Years\n\n"
            f"{df_to_markdown_table(group_summary, round_decimals=4)}\n\n"
            "### Final-Latest-Year Support Counts\n\n"
            f"{df_to_markdown_table(final_support, round_decimals=3)}\n\n"
            f"Calibrated predictions are persisted at `{output_path.relative_to(project_root())}` for Experiment 45."
        ),
        next_step=(
        "Use the calibrated metrics, support counts, and long-horizon decision gates to select the final candidate in Experiment 45. Treat policy ranking as exploratory because candidate support labels are tuned on the same rolling-origin backtest rows; long-horizon rows without outcome-matured residuals are withheld from calibration metrics."
        ),
    )
    path = write_canonical_report(REPORT_FILENAME, REPORT_TITLE, report)
    print(f"Wrote report to {path}")


if __name__ == "__main__":
    main()
