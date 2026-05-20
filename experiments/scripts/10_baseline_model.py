import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score

from experiment_utils import (
    CanonicalReport,
    ensure_reports_dir,
    write_canonical_report,
    df_to_markdown_table,
    load_data,
)

def main():
    reports_dir = ensure_reports_dir()
    
    print("Loading datasets...")
    data = load_data()
    df = data.frame
    
    # 1. Feature Selection & Filtering
    # We strictly use features with minimal missingness to maximize dataset utilization
    features = [
        "LATITUDE", 
        "LONGITUDE", 
        "AREA_ACRES", 
        "DEPTH_MAX_FEET"
    ]
    target = "SECCHI"
    
    # Drop rows missing the target, datetime, or our minimal predictors
    model_df = df.dropna(subset=[target, "SAMPDATE"] + features).copy()
    
    features_full = ["year", "month"] + features
    print(f"Dataset shape after strictly dropping NaNs in base features: {model_df.shape}")
    
    # 2. Prevent Lookahead Bias: Strict Temporal Splitting
    # We must sort by the date chronologically to do an out-of-time split.
    model_df = model_df.sort_values(by="SAMPDATE").reset_index(drop=True)
    
    # 80/20 train/test split index
    split_idx = int(len(model_df) * 0.8)
    
    train_df = model_df.iloc[:split_idx]
    test_df = model_df.iloc[split_idx:]
    
    # Display temporal bounds to prove zero leakage
    train_start, train_end = train_df["SAMPDATE"].min(), train_df["SAMPDATE"].max()
    test_start, test_end = test_df["SAMPDATE"].min(), test_df["SAMPDATE"].max()
    
    print(f"Training split: {len(train_df)} rows. Range: {train_start.date()} to {train_end.date()}")
    print(f"Testing split:  {len(test_df)} rows. Range: {test_start.date()} to {test_end.date()}")
    
    X_train = train_df[features_full]
    y_train = train_df[target]
    
    X_test = test_df[features_full]
    y_test = test_df[target]
    
    # 3. Model Architecture Training
    # We use a Random Forest Baseline (simple config: n_estimators=100, max_depth slightly constrained to prevent over-memorizing)
    print("Training Random Forest Regressor Baseline...")
    rf_model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=1)
    rf_model.fit(X_train, y_train)
    
    # 4. Predictions & Evaluations
    print("Predicting on out-of-time test set...")
    y_pred = rf_model.predict(X_test)
    
    from sklearn.metrics import mean_absolute_error
    
    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test, y_pred)
    
    print(f"Results -> MAE: {mae:.4f}, MSE: {mse:.4f}, RMSE: {rmse:.4f}, R2: {r2:.4f}")
    
    # 5. Extract Feature Importances
    importances = rf_model.feature_importances_
    feat_df = pd.DataFrame({"Feature": features_full, "Importance": importances})
    feat_df = feat_df.sort_values(by="Importance", ascending=False).reset_index(drop=True)
    
    # Let's create a visual for importances
    plt.figure(figsize=(8, 5))
    sns.barplot(x="Importance", y="Feature", data=feat_df, color='steelblue')
    plt.title("Baseline Model Feature Importances")
    plt.xlabel("Gini Importance")
    
    plot_path = reports_dir / "10_baseline_feature_importance.png"
    plt.savefig(plot_path, bbox_inches="tight")
    plt.close()
    
    # 6. Generate Report strictly addressing the user requirements
    report = CanonicalReport(
        objective=(
            "Create the first chronological predictive baseline for Secchi depth using only the "
            "low-missingness geographic and temporal feature set."
        ),
        method=(
            "Filter to rows with non-missing target, sampling date, and baseline predictors. "
            "Sort by `SAMPDATE`, split the timeline 80/20, train a RandomForestRegressor on the "
            "earlier segment, and evaluate on the held-out future segment."
        ),
        parameters=(
            "Model: `RandomForestRegressor`.\n\n"
            "- `n_estimators=100`\n"
            "- `max_depth=10`\n"
            "- `random_state=42`\n\n"
            "Feature set:\n"
            "- `year`\n"
            "- `month`\n"
            "- `LATITUDE`\n"
            "- `LONGITUDE`\n"
            "- `AREA_ACRES`\n"
            "- `DEPTH_MAX_FEET`\n\n"
            f"Train rows: {len(train_df):,} ({train_start.date()} to {train_end.date()})\n\n"
            f"Test rows: {len(test_df):,} ({test_start.date()} to {test_end.date()})"
        ),
        results=(
            "### Performance Metrics\n\n"
            f"- MAE: {mae:.3f} m\n"
            f"- MSE: {mse:.3f} m^2\n"
            f"- RMSE: {rmse:.3f} m\n"
            f"- R^2: {r2:.3f}\n\n"
            "### Feature Importances\n\n"
            f"{df_to_markdown_table(feat_df)}\n\n"
            "![Feature Importances](10_baseline_feature_importance.png)"
        ),
        next_step=(
            "Use this chronology-aware baseline as the reference point for segmented models, "
            "generalization tests, and later chemically enriched feature sets."
        ),
    )

    report_path = write_canonical_report(
        "10_baseline_model.md",
        "Experiment 10: Baseline Predictive Model for Secchi Depth",
        report,
    )
    print(f"Report generated at {report_path}")

if __name__ == "__main__":
    main()
