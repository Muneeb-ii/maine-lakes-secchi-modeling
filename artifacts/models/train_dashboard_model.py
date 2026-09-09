import hashlib
import json
import math
from datetime import datetime, timezone
from numbers import Integral, Real
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from catboost import CatBoostRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'experiments', 'scripts')))
from experiment_utils import PROJECT_ROOT  # noqa: E402

DASHBOARD_DATASET_ID = "secchi-merged-2026-06-29-r1"

FEATURES = [
    "year",
    "month",
    "LATITUDE",
    "LONGITUDE",
    "AREA_ACRES",
    "DEPTH_MAX_FEET",
    "DOMAX",
    "DOMIN",
    "TMAX",
    "TMIN",
    "TPEC",
    "TPBG",
    "PH",
    "COLOR",
    "CONDUCT",
    "ALK",
]

# Experiment 47 contract: only directly measured per-visit fields are scenario
# inputs; PH, COLOR, CONDUCT, and ALK are fixed lake-level means in the June
# dataset and are served as locked lake descriptors.
EDITABLE_FEATURES = ["DOMAX", "DOMIN", "TMAX", "TMIN", "TPEC", "TPBG"]
LOCKED_LAKE_CHEMISTRY = ["PH", "COLOR", "CONDUCT", "ALK"]

CATBOOST_PARAMS = {
    "iterations": 700,
    "depth": 10,
    "learning_rate": 0.05,
    "l2_leaf_reg": 3,
    "random_seed": 42,
    "loss_function": "RMSE",
    "eval_metric": "RMSE",
    "verbose": False,
    "allow_writing_files": False,
    "thread_count": -1,
}

SUPPORT_POLICY = {
    "min_observations": 100,
    "max_pct_missing_chemical_overall": 0.90,
    "n_obs_threshold_source_experiment": "38",
    "source_experiment": "47",
    "rationale": (
        "The n_obs >= 100 cutoff comes from Experiment 38 on the 2025 snapshot. "
        "On the June 2026 snapshot, Experiment 47 found the inherited chemistry-missingness "
        "cutoff is nearly inert because PH/COLOR/CONDUCT/ALK are filled lake means "
        "(360 supported lakes vs 361 with n_obs >= 100 alone). Lakes remain selectable "
        "under n_obs >= 100; sparse measured slider fields are flagged thin_history."
    ),
    "thin_history_max_pct_missing_measured_editable": 0.90,
    "thin_history_source_experiment": "47",
}

PROOF_EXPERIMENTS = [
    {
        "id": "34",
        "report": "reports/34_catboost_tuned.md",
        "finding": "On the 2025 snapshot, tuned no-CHLA native-missing CatBoost reached chronological R2 0.7324, MAE 0.8122, RMSE 1.0903. Those hyperparameters were transferred to the June model without retuning.",
    },
    {
        "id": "35",
        "report": "reports/35_catboost_tuned_lolo.md",
        "finding": "On the 2025 snapshot, unrestricted tuned CatBoost LOLO remained weak: x10 average R2 -1.3806 and x100 average R2 -2.2441.",
    },
    {
        "id": "37",
        "report": "reports/37_catboost_imputation.md",
        "finding": "On the 2025 snapshot, MissForest imputation made tuned CatBoost worse than native missing-value handling.",
    },
    {
        "id": "38",
        "report": "reports/38_catboost_lolo_quality_thresholds.md",
        "finding": "On the 2025 snapshot, restricting evaluation to obs >= 100 and chemistry missingness <= 0.90 improved confirmed x100 LOLO average R2 to -1.084. That missingness statistic does not transfer to the June snapshot (see Experiment 47).",
    },
    {
        "id": "47",
        "report": "reports/47_playground_feature_contract.md",
        "finding": "On the June snapshot, the 16-feature measured-plus-locked-chemistry contract matched the legacy 14-feature chronological accuracy (R2 0.734 vs 0.733). Leave-one-lake-out on the retained 2025 seed lakes stayed negative (catalog-policy x100 average R2 -0.571). n_obs >= 100 is the operative support rule; 152 supported lakes are flagged thin_history.",
    },
]


def parse_midas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "MIDAS" in df.columns:
        has_dash = df["MIDAS"].astype(str).str.contains("-", na=False)
        if has_dash.any():
            split_midas = df["MIDAS"].astype(str).str.split("-", expand=True)
            df["MIDAS"] = split_midas[0]
    df["MIDAS"] = df["MIDAS"].astype(str).str.upper().str.strip()
    return df


def evaluate_model(y_true, y_pred, depth):
    mae = mean_absolute_error(y_true, y_pred)
    mse = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_true, y_pred) if len(y_true) > 1 else np.nan
    safe_depth = np.where(pd.Series(depth).to_numpy() > 0, pd.Series(depth).to_numpy(), np.nan)
    pct_error = (pd.Series(y_true).to_numpy() - pd.Series(y_pred).to_numpy()) / safe_depth
    return {
        "MAE": float(mae),
        "MSE": float(mse),
        "RMSE": float(rmse),
        "R2": float(r2),
        "MAE_Norm": float(np.nanmean(np.abs(pct_error))),
        "RMSE_Norm": float(np.sqrt(np.nanmean(pct_error ** 2))),
    }


def sha256_for_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload) -> None:
    def json_safe(value):
        if isinstance(value, dict):
            return {key: json_safe(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [json_safe(item) for item in value]
        if isinstance(value, Integral) and not isinstance(value, bool):
            return int(value)
        if isinstance(value, Real):
            numeric = float(value)
            return numeric if math.isfinite(numeric) else None
        return value

    with path.open("w", encoding="utf-8") as handle:
        json.dump(json_safe(payload), handle, indent=2, allow_nan=False)


def dashboard_dataset_paths() -> tuple[Path, Path]:
    catalog_path = PROJECT_ROOT / "data" / "catalog.json"
    with catalog_path.open("r", encoding="utf-8") as handle:
        catalog = json.load(handle)
    processed = catalog["processed_datasets"][DASHBOARD_DATASET_ID]
    derived = catalog["derived_artifacts"][DASHBOARD_DATASET_ID]
    return (
        PROJECT_ROOT / processed["data_path"],
        PROJECT_ROOT / derived["lake_missingness_path"],
    )


def main():
    models_dir = PROJECT_ROOT / "artifacts" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading dashboard dataset {DASHBOARD_DATASET_ID}...")
    csv_path, missing_path = dashboard_dataset_paths()
    df = pd.read_csv(csv_path, low_memory=False)
    df = parse_midas(df)
    df["SAMPDATE"] = pd.to_datetime(df["SAMPDATE"], errors="coerce", utc=True)
    df["year"] = df["SAMPDATE"].dt.year
    df["month"] = df["SAMPDATE"].dt.month

    target = "SECCHI"
    required = [target, "SAMPDATE", "MIDAS", "LATITUDE", "LONGITUDE", "AREA_ACRES", "DEPTH_MAX_FEET"]
    model_df = df.dropna(subset=required).copy().sort_values("SAMPDATE").reset_index(drop=True)

    missingness_df = pd.read_csv(missing_path)
    missingness_df["MIDAS"] = missingness_df["MIDAS"].astype(str).str.upper().str.strip()

    lake_counts = model_df["MIDAS"].value_counts().rename("n_obs").reset_index()
    lake_counts.columns = ["MIDAS", "n_obs"]
    editable_missing_cols = [f"pct_missing_{name}" for name in EDITABLE_FEATURES]
    # Every per-feature column shares the lake's total_records denominator, so the mean is the pooled rate.
    missingness_df["pct_missing_measured_editable"] = missingness_df[editable_missing_cols].mean(axis=1)
    support_df = missingness_df[["MIDAS", "pct_missing_chemical_overall", "pct_missing_measured_editable"]].merge(
        lake_counts, on="MIDAS", how="left"
    )
    support_df["n_obs"] = support_df["n_obs"].fillna(0).astype(int)
    support_df["supported"] = (
        (support_df["n_obs"] >= SUPPORT_POLICY["min_observations"])
        & (support_df["pct_missing_chemical_overall"] <= SUPPORT_POLICY["max_pct_missing_chemical_overall"])
    )
    support_df["thin_history"] = support_df["supported"] & (
        support_df["pct_missing_measured_editable"] > SUPPORT_POLICY["thin_history_max_pct_missing_measured_editable"]
    )
    supported_ids = set(support_df.loc[support_df["supported"], "MIDAS"])
    thin_history_ids = set(support_df.loc[support_df["thin_history"], "MIDAS"])
    supported_df = model_df[model_df["MIDAS"].isin(supported_ids)].copy()

    if supported_df.empty:
        raise RuntimeError("No rows remain after dashboard support policy filtering.")

    split_idx = int(len(supported_df) * 0.8)
    train_df = supported_df.iloc[:split_idx].copy()
    test_df = supported_df.iloc[split_idx:].copy()
    holdout_start_year = int(test_df["year"].min())
    holdout_end_year = int(test_df["year"].max())

    print(f"Total valid modeling rows: {len(model_df):,}")
    print(f"Supported rows: {len(supported_df):,}")
    print(f"Supported lakes: {len(supported_ids):,} / {model_df['MIDAS'].nunique():,}")
    print(f"Thin-history supported lakes: {len(thin_history_ids):,}")
    print(f"Holdout window: {holdout_start_year}–{holdout_end_year}")

    holdout_model = CatBoostRegressor(**CATBOOST_PARAMS)
    holdout_model.fit(train_df[FEATURES], train_df[target])
    holdout_predictions = holdout_model.predict(test_df[FEATURES])
    metrics = evaluate_model(test_df[target], holdout_predictions, test_df["DEPTH_MAX_FEET"])

    print("Fitting served model on all supported rows...")
    served_model = CatBoostRegressor(**CATBOOST_PARAMS)
    served_model.fit(supported_df[FEATURES], supported_df[target])

    predictor_path = models_dir / "catboost_predictor.joblib"
    joblib.dump(served_model, predictor_path)

    baseline = supported_df.groupby("MIDAS")[FEATURES].median().to_dict(orient="index")
    baseline["GLOBAL_FALLBACK"] = supported_df[FEATURES].median().to_dict()
    write_json(models_dir / "baseline_lakes_summary.json", baseline)

    support_payload = {
        "dataset_id": DASHBOARD_DATASET_ID,
        "policy": SUPPORT_POLICY,
        "proof_experiments": PROOF_EXPERIMENTS,
        "counts": {
            "total_lakes_after_base_filter": int(model_df["MIDAS"].nunique()),
            "supported_lakes": int(len(supported_ids)),
            "thin_history_supported_lakes": int(len(thin_history_ids)),
            "unsupported_lakes": int(model_df["MIDAS"].nunique() - len(supported_ids)),
            "total_rows_after_base_filter": int(len(model_df)),
            "supported_rows": int(len(supported_df)),
            "unsupported_rows": int(len(model_df) - len(supported_df)),
        },
        "supported_lakes": sorted(supported_ids),
        "thin_history_lakes": sorted(thin_history_ids),
        "lake_quality": support_df.sort_values("MIDAS").to_dict(orient="records"),
    }
    write_json(models_dir / "supported_lakes_policy.json", support_payload)

    importances = pd.DataFrame(
        {"Feature": FEATURES, "Importance": served_model.get_feature_importance()}
    ).sort_values(by="Importance", ascending=False)

    report = f"""# Dashboard Model Report

## Active Model

- Model family: `CatBoostRegressor`
- Model source: Experiment 34 hyperparameters (2025 snapshot), Experiment 47 June feature contract
- Served weights: trained on **all** supported-lake rows in the June snapshot
- Reported metrics: 80/20 chronological holdout fit (not the served weights)
- CHLA policy: excluded from Secchi prediction features
- Editable scenario inputs: {EDITABLE_FEATURES}
- Locked lake chemistry descriptors (fixed lake means): {LOCKED_LAKE_CHEMISTRY}
- Artifact: `catboost_predictor.joblib`

## Support Policy

Lakes are selectable when they have at least {SUPPORT_POLICY['min_observations']} observations after base filtering.
The inherited Experiment 38 chemistry-missingness cutoff (`pct_missing_chemical_overall` <= {SUPPORT_POLICY['max_pct_missing_chemical_overall']:.2f}) remains in the filter but is nearly inert on this snapshot.

Supported lakes whose measured slider fields ({EDITABLE_FEATURES}) are missing on more than
{SUPPORT_POLICY['thin_history_max_pct_missing_measured_editable']:.0%} of records stay selectable and are flagged `thin_history`
(Experiment 47). The playground warns that slider effects lean on other lakes.

### Coverage

| Metric | Count |
| :--- | ---: |
| Total lakes after base filtering | {support_payload['counts']['total_lakes_after_base_filter']:,} |
| Supported lakes | {support_payload['counts']['supported_lakes']:,} |
| Thin-history supported lakes | {support_payload['counts']['thin_history_supported_lakes']:,} |
| Unsupported lakes | {support_payload['counts']['unsupported_lakes']:,} |
| Total rows after base filtering | {support_payload['counts']['total_rows_after_base_filter']:,} |
| Supported rows | {support_payload['counts']['supported_rows']:,} |
| Unsupported rows | {support_payload['counts']['unsupported_rows']:,} |

## Proof Trail

| Experiment | Report | Dashboard relevance |
| :--- | :--- | :--- |
"""
    for item in PROOF_EXPERIMENTS:
        report += f"| {item['id']} | `{item['report']}` | {item['finding']} |\n"

    report += f"""
## Chronological Holdout On Supported Lakes

These scores come from a date-ordered 80/20 split used only for reporting. The served joblib is a separate fit on all supported rows.

Holdout window: {holdout_start_year}–{holdout_end_year}.

| Metric | Value |
| :--- | ---: |
| R2 | {metrics['R2']:.6f} |
| MAE | {metrics['MAE']:.6f} m |
| RMSE | {metrics['RMSE']:.6f} m |
| Normalized MAE | {metrics['MAE_Norm']:.6f} |
| Normalized RMSE | {metrics['RMSE_Norm']:.6f} |

## Feature Set

{json.dumps(FEATURES, indent=2)}

## Feature Importances

Importances below are from the served (full-data) model.

| Feature | Importance |
| :--- | ---: |
"""
    for _, row in importances.iterrows():
        report += f"| {row['Feature']} | {row['Importance']:.6f} |\n"

    (models_dir / "dashboard_model_report.md").write_text(report, encoding="utf-8")

    artifacts = [
        {"name": "predictor", "path": "catboost_predictor.joblib", "required": True},
        {"name": "baseline", "path": "baseline_lakes_summary.json", "required": True},
        {"name": "lake_names", "path": "lake_names.json", "required": True},
        {"name": "support_policy", "path": "supported_lakes_policy.json", "required": True},
        {"name": "model_report", "path": "dashboard_model_report.md", "required": True},
    ]
    for artifact in artifacts:
        artifact["sha256"] = sha256_for_file(models_dir / artifact["path"])

    manifest = {
        "schema_version": "1.0.0",
        "feature_schema_version": "2.0.0",
        "model_id": "secchi-catboost-supported-lakes",
        "model_version": "2026-06-29-exp34-exp38-exp47",
        "dataset_id": DASHBOARD_DATASET_ID,
        "dataset_sha256": sha256_for_file(csv_path),
        "trained_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "feature_order": FEATURES,
        "editable_features": EDITABLE_FEATURES,
        "locked_lake_chemistry": LOCKED_LAKE_CHEMISTRY,
        "artifacts": artifacts,
        "explainability": {"type": "shap_tree", "fallback": "none"},
        "support_policy": SUPPORT_POLICY,
        "proof_experiments": PROOF_EXPERIMENTS,
        "metrics": {
            "chronological_supported_lakes": metrics,
            "chronological_holdout_window": {
                "start_year": holdout_start_year,
                "end_year": holdout_end_year,
            },
        },
        "served_model_training": "all_supported_rows",
        "compatibility": {"python": "3.11", "catboost": "1.2.10", "scikit_learn": "1.6.1"},
    }
    write_json(models_dir / "model_manifest.json", manifest)

    print("Dashboard CatBoost artifacts exported.")
    print(json.dumps({"metrics": metrics, "counts": support_payload["counts"]}, indent=2))


if __name__ == "__main__":
    main()
