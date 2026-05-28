import hashlib
import json
from datetime import datetime, timezone
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

FEATURES = [
    "year",
    "month",
    "LATITUDE",
    "LONGITUDE",
    "AREA_ACRES",
    "DEPTH_MAX_FEET",
    "DOMAX",
    "DOMIN",
    "TPEC",
    "TPBG",
    "PH",
    "COLOR",
    "CONDUCT",
    "ALK",
]

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
    "source_experiment": "38",
    "rationale": "Experiment 38 found the best confirmed LOLO operating policy at obs >= 100 and chemistry missingness <= 0.90.",
}

PROOF_EXPERIMENTS = [
    {
        "id": "34",
        "report": "reports/34_catboost_tuned.md",
        "finding": "Tuned no-CHLA native-missing CatBoost reached chronological R2 0.7324, MAE 0.8122, RMSE 1.0903.",
    },
    {
        "id": "35",
        "report": "reports/35_catboost_tuned_lolo.md",
        "finding": "Unrestricted tuned CatBoost LOLO remained weak: x10 average R2 -1.3806 and x100 average R2 -2.2441.",
    },
    {
        "id": "37",
        "report": "reports/37_catboost_imputation.md",
        "finding": "MissForest imputation made tuned CatBoost worse than native missing-value handling.",
    },
    {
        "id": "38",
        "report": "reports/38_catboost_lolo_quality_thresholds.md",
        "finding": "Restricting to obs >= 100 and missingness <= 0.90 improved confirmed x100 LOLO average R2 to -1.084.",
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
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def main():
    models_dir = PROJECT_ROOT / "artifacts" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    print("Loading dataset...")
    csv_path = PROJECT_ROOT / "data" / "Merged_Dataset.csv"
    df = pd.read_csv(csv_path, low_memory=False)
    df = parse_midas(df)
    df["SAMPDATE"] = pd.to_datetime(df["SAMPDATE"], errors="coerce", utc=True)
    df["year"] = df["SAMPDATE"].dt.year
    df["month"] = df["SAMPDATE"].dt.month

    target = "SECCHI"
    required = [target, "SAMPDATE", "MIDAS", "LATITUDE", "LONGITUDE", "AREA_ACRES", "DEPTH_MAX_FEET"]
    model_df = df.dropna(subset=required).copy().sort_values("SAMPDATE").reset_index(drop=True)

    missing_path = PROJECT_ROOT / "data" / "lake_missingness.csv"
    missingness_df = pd.read_csv(missing_path)
    missingness_df["MIDAS"] = missingness_df["MIDAS"].astype(str).str.upper().str.strip()

    lake_counts = model_df["MIDAS"].value_counts().rename("n_obs").reset_index()
    lake_counts.columns = ["MIDAS", "n_obs"]
    support_df = missingness_df[["MIDAS", "pct_missing_chemical_overall"]].merge(lake_counts, on="MIDAS", how="left")
    support_df["n_obs"] = support_df["n_obs"].fillna(0).astype(int)
    support_df["supported"] = (
        (support_df["n_obs"] >= SUPPORT_POLICY["min_observations"])
        & (support_df["pct_missing_chemical_overall"] <= SUPPORT_POLICY["max_pct_missing_chemical_overall"])
    )
    supported_ids = set(support_df.loc[support_df["supported"], "MIDAS"])
    supported_df = model_df[model_df["MIDAS"].isin(supported_ids)].copy()

    if supported_df.empty:
        raise RuntimeError("No rows remain after dashboard support policy filtering.")

    split_idx = int(len(supported_df) * 0.8)
    train_df = supported_df.iloc[:split_idx].copy()
    test_df = supported_df.iloc[split_idx:].copy()

    print(f"Total valid modeling rows: {len(model_df):,}")
    print(f"Supported rows: {len(supported_df):,}")
    print(f"Supported lakes: {len(supported_ids):,} / {model_df['MIDAS'].nunique():,}")

    model = CatBoostRegressor(**CATBOOST_PARAMS)
    model.fit(train_df[FEATURES], train_df[target])
    predictions = model.predict(test_df[FEATURES])
    metrics = evaluate_model(test_df[target], predictions, test_df["DEPTH_MAX_FEET"])

    predictor_path = models_dir / "catboost_predictor.joblib"
    joblib.dump(model, predictor_path)

    baseline = supported_df.groupby("MIDAS")[FEATURES].median().to_dict(orient="index")
    baseline["GLOBAL_FALLBACK"] = supported_df[FEATURES].median().to_dict()
    write_json(models_dir / "baseline_lakes_summary.json", baseline)

    support_payload = {
        "policy": SUPPORT_POLICY,
        "proof_experiments": PROOF_EXPERIMENTS,
        "counts": {
            "total_lakes_after_base_filter": int(model_df["MIDAS"].nunique()),
            "supported_lakes": int(len(supported_ids)),
            "unsupported_lakes": int(model_df["MIDAS"].nunique() - len(supported_ids)),
            "total_rows_after_base_filter": int(len(model_df)),
            "supported_rows": int(len(supported_df)),
            "unsupported_rows": int(len(model_df) - len(supported_df)),
        },
        "supported_lakes": sorted(supported_ids),
        "lake_quality": support_df.sort_values("MIDAS").to_dict(orient="records"),
    }
    write_json(models_dir / "supported_lakes_policy.json", support_payload)

    importances = pd.DataFrame({"Feature": FEATURES, "Importance": model.get_feature_importance()}).sort_values(
        by="Importance", ascending=False
    )

    report = f"""# Dashboard Model Report

## Active Model

- Model family: `CatBoostRegressor`
- Model source: Experiment 34 tuned native-missing CatBoost, promoted with Experiment 38 support policy
- CHLA policy: excluded from Secchi prediction features
- Artifact: `catboost_predictor.joblib`

## Support Policy

The dashboard is restricted to lakes with:

- observations after base filtering >= {SUPPORT_POLICY['min_observations']}
- `pct_missing_chemical_overall` <= {SUPPORT_POLICY['max_pct_missing_chemical_overall']:.2f}

### Coverage

| Metric | Count |
| :--- | ---: |
| Total lakes after base filtering | {support_payload['counts']['total_lakes_after_base_filter']:,} |
| Supported lakes | {support_payload['counts']['supported_lakes']:,} |
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
## Chronological Evaluation On Supported Lakes

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
        "model_id": "secchi-catboost-supported-lakes",
        "model_version": "2026-05-28-exp34-exp38",
        "trained_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "feature_order": FEATURES,
        "artifacts": artifacts,
        "explainability": {"type": "shap_tree", "fallback": "none"},
        "support_policy": SUPPORT_POLICY,
        "proof_experiments": PROOF_EXPERIMENTS,
        "metrics": {"chronological_supported_lakes": metrics},
        "compatibility": {"python": "3.11", "catboost": "1.2.10", "scikit_learn": "1.6.1"},
    }
    write_json(models_dir / "model_manifest.json", manifest)

    print("Dashboard CatBoost artifacts exported.")
    print(json.dumps({"metrics": metrics, "counts": support_payload["counts"]}, indent=2))


if __name__ == "__main__":
    main()
