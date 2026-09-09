"""Build the read-only Experiment 46 trends artifact for the dashboard."""
from __future__ import annotations

import json
import importlib.util
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments" / "scripts"))
_baseline_spec = importlib.util.spec_from_file_location("baseline40", ROOT / "experiments" / "scripts" / "40_forecasting_baselines.py")
_baseline40 = importlib.util.module_from_spec(_baseline_spec)
assert _baseline_spec.loader is not None
_baseline_spec.loader.exec_module(_baseline40)
_local_level_forecast = _baseline40._local_level_forecast

MODELS_DIR = Path(os.getenv("MODEL_ARTIFACTS_PATH", str(ROOT / "artifacts" / "models"))).resolve()
CATALOG = ROOT / "data" / "catalog.json"
EXPECTED_DATASET = "secchi-merged-2026-06-29-r1"
OBSERVATIONS_THROUGH = 2024
HORIZONS = tuple(range(1, 6))


def _finite_width(values: np.ndarray, level: float) -> float:
    values = values[np.isfinite(values)]
    if len(values) < 19:
        return float("nan")
    rank = int(np.ceil((len(values) + 1) * level))
    return float(np.sort(values)[rank - 1]) if rank <= len(values) else float("nan")


def _paths() -> tuple[Path, Path, str]:
    catalog = json.loads(CATALOG.read_text())
    dataset_id = catalog.get("active_research_dataset_id")
    if dataset_id != EXPECTED_DATASET:
        raise RuntimeError(f"Unexpected active research dataset: {dataset_id!r}")
    processed = catalog["processed_datasets"][dataset_id]
    derived = catalog["derived_artifacts"][dataset_id]
    return ROOT / processed["data_path"], ROOT / derived["annual_summer_target_path"], dataset_id


def _metadata(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, usecols=["MIDAS", "LAKE_NAME", "REGION"])
    frame["MIDAS"] = frame["MIDAS"].astype(str).str.strip().str.lower()
    return frame.drop_duplicates("MIDAS")


def _widths() -> dict[int, dict[str, float]]:
    residual_path = ROOT / "reports" / "46_baseline_calibration_residuals.csv"
    residuals = pd.read_csv(residual_path)
    residuals = residuals[(residuals["model"] == "Local-level state-space") & (residuals["forecast_year"] <= OBSERVATIONS_THROUGH)]
    raw = {}
    for horizon in HORIZONS:
        errors = np.abs(residuals.loc[residuals["horizon"] == horizon, "prediction"].to_numpy(float) - residuals.loc[residuals["horizon"] == horizon, "actual"].to_numpy(float))
        raw[horizon] = {"lower_80": _finite_width(errors, .80), "lower_95": _finite_width(errors, .95)}
    running = {"lower_80": -np.inf, "lower_95": -np.inf}
    for horizon in HORIZONS:
        for level in running:
            value = raw[horizon][level]
            if np.isfinite(value):
                running[level] = max(running[level], value)
            raw[horizon][level] = None if not np.isfinite(running[level]) else float(running[level])
    return raw


def _validation() -> dict[str, float]:
    metrics = pd.read_csv(ROOT / "reports" / "46_baseline_support_metrics.csv")
    row = metrics[(metrics["model"] == "Local-level state-space") & (metrics["horizon"] == 5) & (metrics["support_tier"] == "Full")]
    if len(row) != 1:
        raise RuntimeError("Experiment 46 Full-support validation row is missing")
    row = row.iloc[0]
    return {"mae_m": float(row["MAE"]), "coverage_80": float(row["coverage_80"]), "coverage_95": float(row["coverage_95"])}


def build() -> dict:
    data_path, target_path, dataset_id = _paths()
    assessment = json.loads((ROOT / "reports" / "46_baseline_forecast_assessment.json").read_text())
    if assessment.get("dataset_id") != dataset_id or not assessment.get("baseline_defensible") or assessment.get("recommended_model") != "Local-level state-space":
        raise RuntimeError("Experiment 46 assessment does not authorize the local-level trends artifact")

    metadata = _metadata(data_path)
    target = pd.read_csv(target_path)
    target["MIDAS"] = target["MIDAS"].astype(str).str.strip().str.lower()
    target["year"] = target["year"].astype(int)
    target = target[target["year"] <= OBSERVATIONS_THROUGH].copy()
    widths = _widths()
    lakes = []
    details = {}
    for midas_id, group in target.groupby("MIDAS", sort=True):
        group = group.sort_values("year")
        meta = metadata[metadata["MIDAS"] == midas_id]
        name = str(meta["LAKE_NAME"].iloc[0]) if len(meta) and pd.notna(meta["LAKE_NAME"].iloc[0]) else "Unknown Ecosystem"
        region = str(meta["REGION"].iloc[0]) if len(meta) and pd.notna(meta["REGION"].iloc[0]) else "Unknown"
        history = [{"year": int(row.year), "secchi_m": float(row.summer_secchi), "n_readings": int(row.n_readings), "bottom_hit_rate": float(row.bottom_hit_rate) if pd.notna(row.bottom_hit_rate) else None} for row in group.itertuples() if np.isfinite(row.summer_secchi)]
        latest = int(group["year"].max()) if len(group) else None
        n_history = len(history)
        gap = OBSERVATIONS_THROUGH - latest if latest is not None else 999
        full = n_history >= 10 and gap <= 2
        tier = "Full" if full else ("Limited" if n_history >= 2 and gap <= 4 else "Unavailable")
        forecast = []
        if full:
            years = group["year"].to_numpy(int)
            values = group["summer_secchi"].to_numpy(float)
            predictions, _ = _local_level_forecast(years, values, list(range(OBSERVATIONS_THROUGH + 1, OBSERVATIONS_THROUGH + 6)))
            for horizon, point in zip(HORIZONS, predictions):
                w80, w95 = widths[horizon]["lower_80"], widths[horizon]["lower_95"]
                if w80 is None or w95 is None:
                    forecast = []
                    break
                forecast.append({"year": OBSERVATIONS_THROUGH + horizon, "secchi_m": float(point), "lower_80": max(0.0, float(point) - w80), "upper_80": float(point) + w80, "lower_95": max(0.0, float(point) - w95), "upper_95": float(point) + w95})
        unavailable_reason = None if full else ("Requires at least 10 annual summer observations and latest observation within 2 years of 2024." if tier != "Unavailable" else "Insufficient annual summer history or observation recency.")
        summary = {"midas_id": midas_id, "lake_name": name, "region": region, "history_years": n_history, "latest_year": latest, "forecast_available": bool(forecast), "support_tier": tier}
        lakes.append(summary)
        details[midas_id] = {**summary, "unavailable_reason": unavailable_reason, "history": history, "forecast": forecast}

    return {"schema_version": 1, "dataset_id": dataset_id, "observations_through_year": OBSERVATIONS_THROUGH, "model": "Local-level state-space", "forecast_years": [OBSERVATIONS_THROUGH + h for h in HORIZONS], "target": "Station-balanced summer Secchi depth", "support_policy": {"minimum_history_years": 10, "maximum_gap_years": 2}, "validation": _validation(), "lakes": lakes, "details": details}


if __name__ == "__main__":
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    payload = build()
    (MODELS_DIR / "trends_artifact.json").write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n")
    print(f"Wrote {len(payload['lakes'])} lakes to {MODELS_DIR / 'trends_artifact.json'}")
