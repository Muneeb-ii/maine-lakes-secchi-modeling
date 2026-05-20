import pandas as pd
import numpy as np
import json
import joblib
from pathlib import Path
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error

# Hack to deal with paths if run from artifacts/models or project root.
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'experiments', 'scripts')))
try:
    from experiment_utils import load_data, PROJECT_ROOT
except ImportError:
    PROJECT_ROOT = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    def load_data():
        pass # Fallback below if needed

def evaluate_model(y_true, y_pred, depth):
    if len(y_true) == 0:
        return {"MAE": 0, "RMSE": 0, "R2": 0, "MAE_Norm": 0, "RMSE_Norm": 0}
        
    mae = mean_absolute_error(y_true, y_pred)
    mse = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_true, y_pred) if len(y_true) > 1 else np.nan
    
    safe_depth = np.where(pd.Series(depth).to_numpy() > 0, pd.Series(depth).to_numpy(), np.nan)
    pct_error = (pd.Series(y_true).to_numpy() - pd.Series(y_pred).to_numpy()) / safe_depth
    mae_norm = np.nanmean(np.abs(pct_error))
    mse_norm = np.nanmean(pct_error ** 2)
    rmse_norm = np.sqrt(mse_norm)
    
    return {
        "MAE": mae, "MSE": mse, "RMSE": rmse, "R2": r2,
        "MAE_Norm": mae_norm, "RMSE_Norm": rmse_norm
    }

def main():
    models_dir = PROJECT_ROOT / "artifacts" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    
    print("Loading dataset...")
    # direct csv load fallback if util fails
    csv_path = PROJECT_ROOT / "data" / "Merged_Dataset.csv"
    if csv_path.exists():
        df = pd.read_csv(csv_path, low_memory=False)
        df["SAMPDATE"] = pd.to_datetime(df["SAMPDATE"])
    else:
        df = load_data().frame

    print(f"Total rows in raw dataset: {len(df):,}")
        
    target = "SECCHI"
    num_cols = ["LATITUDE", "LONGITUDE", "AREA_ACRES", "DEPTH_MAX_FEET"]
    df["year"] = df["SAMPDATE"].dt.year
    df["month"] = df["SAMPDATE"].dt.month
    base_features = ["year", "month"] + num_cols
    
    # Expanded Feature Suite (No CHLA)
    chem_features = ["DOMAX", "DOMIN", "MLD", "OXIC", "SCHMIDT", "TPEC", "TPBG", "PH", "COLOR", "CONDUCT", "ALK"]
    temp_features = ["TMAX", "TMIN"]
    
    requested_features = chem_features + temp_features
    valid_features = [c for c in requested_features if c in df.columns]
    
    target_geography_mask = [target, "SAMPDATE", "MIDAS"] + num_cols
    model_df = df.dropna(subset=target_geography_mask).copy()
    model_df = model_df.sort_values(by="SAMPDATE").reset_index(drop=True)
    
    features = base_features + valid_features
    
    print(f"Rows after strict target/geography NA drop: {len(model_df):,}")
    
    # --- Missingness Analytics for the Report ---
    missing_counts = model_df[features].isna().sum()
    missing_dict = missing_counts[missing_counts > 0].to_dict()
    
    # 80/20 Splitting
    split_idx = int(len(model_df) * 0.8)
    train_df = model_df.iloc[:split_idx]
    test_df = model_df.iloc[split_idx:]
    
    X_train = train_df[features].copy()
    y_train = train_df[target].copy()
    X_test = test_df[features].copy()
    y_test = test_df[target].copy()
    depth_test = test_df["DEPTH_MAX_FEET"]
    
    print(f"Train Rows: {len(X_train):,}")
    print(f"Test Rows: {len(X_test):,}")
    
    # --- Generate Baseline Metadata JSON ---
    print("Generating baseline metadata JSON for Dashboard...")
    # Calculate median baseline for each feature per lake
    grouped = model_df.groupby("MIDAS")[features].median()
    baseline_dict = grouped.to_dict(orient="index")
    # Store global median as fallback
    baseline_dict["GLOBAL_FALLBACK"] = model_df[features].median().to_dict()
    
    with open(models_dir / "baseline_lakes_summary.json", "w") as f:
        json.dump(baseline_dict, f, indent=4)
        
    print("\nFitting MissForest (IterativeImputer with max_iter=10)... THIS WILL TAKE A WHILE.")
    rf_imputer = RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42, n_jobs=-1)
    imputer = IterativeImputer(estimator=rf_imputer, max_iter=10, random_state=42)
    
    X_train_imputed = pd.DataFrame(imputer.fit_transform(X_train), columns=features, index=X_train.index)
    X_test_imputed = pd.DataFrame(imputer.transform(X_test), columns=features, index=X_test.index)
    
    print("Saving Imputer...")
    joblib.dump(imputer, models_dir / "imputer.joblib")
    
    print("Training Downstream RandomForest Predictor...")
    predictor = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    predictor.fit(X_train_imputed, y_train)
    
    print("Saving Predictor...")
    joblib.dump(predictor, models_dir / "rf_predictor.joblib")
    
    y_pred = predictor.predict(X_test_imputed)
    metrics = evaluate_model(y_test, y_pred, depth_test)
    
    # Feature Importances
    importances = predictor.feature_importances_
    imp_df = pd.DataFrame({"Feature": features, "Importance": importances}).sort_values(by="Importance", ascending=False)
    
    # --- Exhaustive Model Report Generation ---
    print("\nGenerating Exhaustive Model Report...")
    report_content = f"""# Dashboard Model Exhaustive Architecture Report

## 1. Pipeline Overview
This document contains the exact serialization snapshot statistics of the model deployed to the dashboard backend.

- **Generation Date:** Automatically populated on script run.
- **Data Source Bounds:** `Merged_Dataset.csv` -> Filtered strictly for Target (`SECCHI`), Geographic, and Time constraints.

## 2. Train/Test Structure
- **Validation Philosophy:** Chronological validation (80/20 temporal split) to strictly prevent future-data lookahead bias during MissForest interpolation.
- **Total Valid Rows Engaged:** {len(model_df):,}
- **Train Constraints:** First {len(X_train):,} chronologically sorted observations.
- **Test Constraints:** Subsequent {len(X_test):,} chronologically sorted unobserved forecasting targets.

## 3. Structural Features & Missingness Topology
The dashboard UI maps to these active {len(features)} node tensors.
Below details the raw blank/missing cells strictly passed into MissForest for algorithmic mathematical interpolation:

### Imputation Requirements Breakdown
| Feature Name | Total `NaN` Blank Rows | Percentage of Total Space |
| :--- | :--- | :--- |
"""
    for f in features:
        misses = missing_counts.get(f, 0)
        pct = (misses / len(model_df)) * 100
        report_content += f"| `{f}` | {misses:,} | {pct:.2f}% |\n"
        
    report_content += f"""
*(Target `SECCHI` missingness rows were immediately physically stripped prior to this table calculation).*

## 4. Hyperparameter Matrix Network
### A. Iterative Imputer (MissForest Architecture)
- **Base Estimator:** `RandomForestRegressor`
- **Internal Estimators per Chain:** 50
- **Internal Tree Max Depth:** 10
- **`max_iter` Boundary:** 10
- **`random_state` Seed:** 42

### B. Downstream Predictor (Forecasting Mainframe)
- **Estimator Class:** `RandomForestRegressor`
- **Total Estimators:** 100
- **Max Depth:** `None` (Fully expanded geometric splits)
- **`n_jobs` Parallelism:** -1

## 5. Algorithmic Evaluation Suite
Tested precisely upon the {len(X_test):,} strictly unobserved chronologically isolated observations:

- **$R^2$ (Explained Variance Coefficient):** {metrics["R2"]:.6f}
- **Mean Absolute Error (MAE):** {metrics["MAE"]:.6f} meters
- **Mean Squared Error (MSE):** {metrics["MSE"]:.6f} meters²
- **Root Mean Squared Error (RMSE):** {metrics["RMSE"]:.6f} meters
- **Normalized MAE (by target depth):** {metrics["MAE_Norm"]:.6f}
- **Normalized RMSE (by target depth):** {metrics["RMSE_Norm"]:.6f}

## 6. Gini Baseline Importance Logic
The following array indicates precisely how structurally dependent the mathematical forecasts are per field:

| Feature Dimension | Node Gini Importance Factor |
| :--- | :--- |
"""
    for _, row in imp_df.iterrows():
        report_content += f"| {row['Feature']} | {row['Importance']:.6f} |\n"
        
    with open(models_dir / "dashboard_model_report.md", "w") as f:
        f.write(report_content)
        
    print(f"Report universally exported to {models_dir / 'dashboard_model_report.md'}")
    print("Dashboard Backend Models are successfully synchronized and serialized.")

if __name__ == "__main__":
    main()
