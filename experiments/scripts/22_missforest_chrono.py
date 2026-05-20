import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error

from experiment_utils import (
    CanonicalReport,
    ensure_reports_dir,
    write_canonical_report,
    df_to_markdown_table,
    load_data,
)

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
        "MAE": mae, "RMSE": rmse, "R2": r2,
        "MAE_Norm": mae_norm, "RMSE_Norm": rmse_norm
    }

def main():
    reports_dir = ensure_reports_dir()
    print("Loading dataset...")
    data = load_data()
    df = data.frame
    
    target = "SECCHI"
    num_cols = ["LATITUDE", "LONGITUDE", "AREA_ACRES", "DEPTH_MAX_FEET"]
    df["year"] = df["SAMPDATE"].dt.year
    df["month"] = df["SAMPDATE"].dt.month
    base_features = ["year", "month"] + num_cols
    
    # Exclude CHLA explicitly per instructions (and missingness overall for target)
    chem_features = ["DOMAX", "DOMIN", "TPEC", "TPBG", "PH", "COLOR", "CONDUCT", "ALK"]
    valid_chems = [c for c in chem_features if c in df.columns]
    
    subset_cols = [target, "SAMPDATE", "MIDAS"] + num_cols 
    model_df = df.dropna(subset=subset_cols).copy()
    model_df = model_df.sort_values(by="SAMPDATE").reset_index(drop=True)
    
    features = base_features + valid_chems
    
    # 80/20 Splitting
    split_idx = int(len(model_df) * 0.8)
    train_df = model_df.iloc[:split_idx]
    test_df = model_df.iloc[split_idx:]
    
    X_train = train_df[features].copy()
    y_train = train_df[target].copy()
    X_test = test_df[features].copy()
    y_test = test_df[target].copy()
    depth_test = test_df["DEPTH_MAX_FEET"]
    
    print("\nFitting MissForest (IterativeImputer with RandomForest)...")
    # Capped exactly as discussed for safety/memory limitations.
    rf_imputer = RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42, n_jobs=1)
    imputer = IterativeImputer(estimator=rf_imputer, max_iter=3, random_state=42)
    
    X_train_imputed = pd.DataFrame(imputer.fit_transform(X_train), columns=features, index=X_train.index)
    X_test_imputed = pd.DataFrame(imputer.transform(X_test), columns=features, index=X_test.index)
    
    print("Training Downstream RandomForest Predictor...")
    predictor = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=1)
    predictor.fit(X_train_imputed, y_train)
    
    y_pred = predictor.predict(X_test_imputed)
    metrics = evaluate_model(y_test, y_pred, depth_test)
    
    # Feature Importances
    importances = predictor.feature_importances_
    imp_df = pd.DataFrame({"Feature": features, "Importance": importances})
    imp_df = imp_df.sort_values(by="Importance", ascending=False).reset_index(drop=True)
    
    plt.figure(figsize=(10, 6))
    sns.barplot(x="Importance", y="Feature", data=imp_df, color='forestgreen')
    plt.title("RandomForest Feature Importances after MissForest Imputation")
    plt.xlabel("Gini Importance")
    plot_path = reports_dir / "22_missforest_importances.png"
    plt.savefig(plot_path, bbox_inches="tight")
    plt.close()
    
    report = CanonicalReport(
        objective=(
            "Evaluate whether MissForest-style imputation improves the chronological Secchi "
            "baseline once chemical features are allowed into the feature set."
        ),
        method=(
            "Create a time-sorted 80/20 split, fit the imputer only on the training slice, "
            "transform train and test features separately, and train a downstream RandomForest "
            "predictor on the imputed training data."
        ),
        parameters=(
            "Imputer:\n"
            "- `IterativeImputer`\n"
            "- estimator: `RandomForestRegressor`\n"
            "- `n_estimators=50`\n"
            "- `max_depth=10`\n"
            "- `max_iter=3`\n"
            "- `random_state=42`\n\n"
            "Predictor:\n"
            "- `RandomForestRegressor`\n"
            "- `n_estimators=100`\n"
            "- `random_state=42`\n\n"
            "Feature policy: baseline geographic and temporal features plus valid chemistry columns, "
            "excluding `CHLA`."
        ),
        results=(
            "### Chronological Test Metrics\n\n"
            f"- R^2: {metrics['R2']:.4f}\n"
            f"- MSE: {(metrics['RMSE']**2):.4f} m^2\n"
            f"- MAE: {metrics['MAE']:.4f} m\n"
            f"- Normalized MSE: {(metrics['RMSE_Norm']**2):.4f}\n"
            f"- Normalized MAE: {metrics['MAE_Norm']:.4f}\n\n"
            "### Top Feature Importances\n\n"
            f"{df_to_markdown_table(imp_df.head(15))}\n\n"
            "![MissForest Gini Weighting](22_missforest_importances.png)"
        ),
        next_step=(
            "Use this imputation-aware baseline as the launch point for leave-one-lake-out "
            "testing, feature elimination, sample-threshold experiments, and dense-lake variants."
        ),
    )

    report_path = write_canonical_report(
        "22_missforest_chrono.md",
        "Experiment 22: MissForest Chronological Test",
        report,
    )
    print(f"\nReport generated at {report_path}")

if __name__ == "__main__":
    main()
