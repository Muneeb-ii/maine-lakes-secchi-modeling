from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from experiment_utils import get_dataset_artifact_path, load_data


BACKTEST_ORIGINS = tuple(range(2005, 2015))
HORIZONS = (1, 3, 5, 10)
MIN_HISTORY = 2
RECENT_WINDOW_YEARS = 5
SUMMER_TARGET_COLUMNS = {
    "MIDAS",
    "year",
    "summer_secchi",
    "bottom_hit_rate",
    "n_stations",
    "n_station_years",
    "n_summer_dates",
    "n_readings",
}
STATIC_NUMERIC = [
    "LATITUDE",
    "LONGITUDE",
    "AREA_ACRES",
    "DEPTH_MEAN_FEET",
    "DEPTH_MAX_FEET",
    "VOLUME_ACREFEET",
    "ELEVATION_FEET",
]
STATIC_CATEGORICAL = ["REGION", "TROPHIC_CATEGORY"]


def load_target_and_metadata() -> tuple[pd.DataFrame, pd.DataFrame, str]:
    data = load_data()
    target_path = get_dataset_artifact_path("annual_summer_target_path")
    target = pd.read_csv(target_path)
    missing = SUMMER_TARGET_COLUMNS.difference(target.columns)
    if missing:
        raise ValueError(f"Annual summer target is missing columns: {sorted(missing)}")
    target = target.copy()
    target["MIDAS"] = target["MIDAS"].astype(str).str.strip()
    target["year"] = target["year"].astype(int)
    target["summer_secchi"] = pd.to_numeric(target["summer_secchi"], errors="raise")
    target = target.sort_values(["MIDAS", "year"]).reset_index(drop=True)

    available = [column for column in STATIC_NUMERIC + STATIC_CATEGORICAL + ["MIDAS"] if column in data.frame.columns]
    metadata = data.frame[available].copy()
    metadata["MIDAS"] = metadata["MIDAS"].astype(str).str.strip()
    metadata = metadata.drop_duplicates("MIDAS")
    for column in STATIC_NUMERIC:
        if column not in metadata:
            metadata[column] = np.nan
        metadata[column] = pd.to_numeric(metadata[column], errors="coerce")
    for column in STATIC_CATEGORICAL:
        if column not in metadata:
            metadata[column] = "Unknown"
        metadata[column] = metadata[column].fillna("Unknown").astype(str)
    return target, metadata, data.dataset_id


def history_is_eligible(history: pd.DataFrame, origin: int) -> bool:
    recent = history[history["year"] >= origin - RECENT_WINDOW_YEARS + 1]
    return len(history) >= MIN_HISTORY and not recent.empty


def _safe_slope(years: np.ndarray, values: np.ndarray) -> float:
    if len(values) < 2 or np.ptp(years) <= 0:
        return 0.0
    slope = np.polyfit(years.astype(float), values.astype(float), 1)[0]
    return float(slope) if np.isfinite(slope) else 0.0


def feature_row(
    lake_id: str,
    history: pd.DataFrame,
    origin: int,
    horizon: int,
    metadata_lookup: dict[str, dict[str, object]],
) -> dict[str, object] | None:
    if not history_is_eligible(history, origin):
        return None
    history = history.sort_values("year")
    years = history["year"].to_numpy(dtype=int)
    values = history["summer_secchi"].to_numpy(dtype=float)
    recent = history[history["year"] >= origin - RECENT_WINDOW_YEARS + 1]
    recent_years = recent["year"].to_numpy(dtype=int)
    recent_values = recent["summer_secchi"].to_numpy(dtype=float)
    latest = history.iloc[-1]
    recent_window = values[-min(len(values), 5) :]
    recent_window_years = years[-min(len(years), 5) :]
    meta = metadata_lookup.get(lake_id, {})
    row: dict[str, object] = {
        "MIDAS": lake_id,
        "origin_year": origin,
        "horizon": horizon,
        "last_value": float(values[-1]),
        "lag_2": float(values[-2]) if len(values) >= 2 else np.nan,
        "lag_3": float(values[-3]) if len(values) >= 3 else np.nan,
        "recent_mean_5": float(np.mean(recent_values)),
        "recent_slope": _safe_slope(recent_window_years, recent_window),
        "all_history_slope": _safe_slope(years, values),
        "history_mean": float(np.mean(values)),
        "history_std": float(np.std(values, ddof=1)) if len(values) > 1 else 0.0,
        "history_years": len(history),
        "history_span": int(years[-1] - years[0]),
        "gap_since_last": int(origin - years[-1]),
        "latest_bottom_hit_rate": float(latest.get("bottom_hit_rate", np.nan)),
        "latest_n_stations": float(latest.get("n_stations", np.nan)),
        "latest_n_readings": float(latest.get("n_readings", np.nan)),
        "latest_n_summer_dates": float(latest.get("n_summer_dates", np.nan)),
        "REGION": str(meta.get("REGION", "Unknown")),
        "TROPHIC_CATEGORY": str(meta.get("TROPHIC_CATEGORY", "Unknown")),
    }
    for column in STATIC_NUMERIC:
        value = meta.get(column, np.nan)
        row[column] = float(value) if pd.notna(value) else np.nan
    return row


def build_training_examples(
    target_by_lake: dict[str, pd.DataFrame],
    metadata_lookup: dict[str, dict[str, object]],
    maximum_origin: int,
    horizon: int,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    min_year = int(min(group["year"].min() for group in target_by_lake.values()))
    for origin in range(min_year + 1, maximum_origin + 1):
        forecast_year = origin + horizon
        if forecast_year > maximum_origin:
            continue
        for lake_id, lake_target in target_by_lake.items():
            history = lake_target[lake_target["year"] <= origin]
            target_row = lake_target[lake_target["year"] == forecast_year]
            if target_row.empty:
                continue
            features = feature_row(lake_id, history, origin, horizon, metadata_lookup)
            if features is None:
                continue
            rows.append({**features, "actual": float(target_row.iloc[0]["summer_secchi"])})
    return pd.DataFrame(rows)


def build_evaluation_rows(
    target_by_lake: dict[str, pd.DataFrame],
    metadata_lookup: dict[str, dict[str, object]],
    origin: int,
    horizon: int,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for lake_id, lake_target in target_by_lake.items():
        history = lake_target[lake_target["year"] <= origin]
        target_row = lake_target[lake_target["year"] == origin + horizon]
        if target_row.empty:
            continue
        features = feature_row(lake_id, history, origin, horizon, metadata_lookup)
        if features is None:
            continue
        row = target_row.iloc[0]
        rows.append(
            {
                **features,
                "actual": float(row["summer_secchi"]),
                "naive_abs_error": abs(float(history.iloc[-1]["summer_secchi"]) - float(row["summer_secchi"])),
                "mase_scale": float(np.mean(np.abs(np.diff(history["summer_secchi"].to_numpy(dtype=float))))) if len(history) > 1 and np.mean(np.abs(np.diff(history["summer_secchi"].to_numpy(dtype=float)))) > 0 else np.nan,
                "bottom_hit_rate": float(row.get("bottom_hit_rate", np.nan)),
                "n_stations": int(row.get("n_stations", 1)),
            }
        )
    return pd.DataFrame(rows)


def support_tier(history_years: float, gap_since_last: float, full_history: int = 10, full_gap: int = 2, limited_history: int = 2, limited_gap: int = 5) -> str:
    if history_years >= full_history and gap_since_last <= full_gap:
        return "Full"
    if history_years >= limited_history and gap_since_last <= limited_gap:
        return "Limited"
    return "Unavailable"


def summarize_point_predictions(result: pd.DataFrame, prediction_column: str = "prediction") -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for horizon, group in result.groupby("horizon", sort=True):
        actual = group["actual"].to_numpy(dtype=float)
        prediction = group[prediction_column].to_numpy(dtype=float)
        error = prediction - actual
        scales = group["mase_scale"].to_numpy(dtype=float)
        valid = np.isfinite(scales) & (scales > 0)
        lake_compare = group.assign(abs_error=np.abs(error)).groupby("MIDAS").agg(model_mae=("abs_error", "mean"), naive_mae=("naive_abs_error", "mean"))
        rows.append(
            {
                "horizon": int(horizon),
                "n_forecasts": len(group),
                "n_lakes": int(group["MIDAS"].nunique()),
                "MAE": float(np.mean(np.abs(error))),
                "RMSE": float(np.sqrt(np.mean(error**2))),
                "mean_bias": float(np.mean(error)),
                "MASE": float(np.mean(np.abs(error[valid] / scales[valid]))) if valid.any() else np.nan,
                "pct_lakes_beat_naive": float(np.mean(lake_compare["model_mae"] < lake_compare["naive_mae"]) * 100),
            }
        )
    return pd.DataFrame(rows)


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]
