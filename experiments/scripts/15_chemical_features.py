import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error

from experiment_utils import ensure_reports_dir, write_markdown_report, df_to_markdown_table, load_data

def evaluate_model(y_true, y_pred, depth):
    mae = mean_absolute_error(y_true, y_pred)
    mse = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_true, y_pred)
    
    # Normalized metrics over depth with zero/NaN-depth guard.
    safe_depth = np.where(pd.Series(depth).to_numpy() > 0, pd.Series(depth).to_numpy(), np.nan)
    pct_error = (pd.Series(y_true).to_numpy() - pd.Series(y_pred).to_numpy()) / safe_depth
    mae_norm = np.mean(np.abs(pct_error))
    mse_norm = np.mean(pct_error ** 2)
    rmse_norm = np.sqrt(mse_norm)
    
    return {
        "MAE": mae,
        "RMSE": rmse,
        "R2": r2,
        "MAE_Norm": mae_norm,
        "RMSE_Norm": rmse_norm,
        "MSE_Norm": mse_norm
    }

def build_model(train_df, test_df, target, features):
    X_train = train_df[features].copy()
    y_train = train_df[target]
    depth_train = train_df["DEPTH_MAX_FEET"]
    
    X_test = test_df[features].copy()
    y_test = test_df[target]
    depth_test = test_df["DEPTH_MAX_FEET"]
    
    rf = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)
    
    pred_train = rf.predict(X_train)
    pred_test = rf.predict(X_test)
    
    metrics_train = evaluate_model(y_train, pred_train, depth_train)
    metrics_test = evaluate_model(y_test, pred_test, depth_test)
    
    imp_dict = {feat: imp for feat, imp in zip(X_train.columns, rf.feature_importances_)}
    
    return {
        "train": metrics_train,
        "test": metrics_test,
        "importances": imp_dict
    }

def main():
    reports_dir = ensure_reports_dir()
    
    print("Loading datasets...")
    data = load_data()
    df = data.frame
    
    target = "SECCHI"
    
    # 1. Base Configuration
    base_geo = ["LATITUDE", "LONGITUDE", "AREA_ACRES", "DEPTH_MAX_FEET"]
    df["year"] = df["SAMPDATE"].dt.year
    df["month"] = df["SAMPDATE"].dt.month
    base_time = ["year", "month"]
    base_features = base_time + base_geo
    
    # 2. Filtering for Baseline
    base_subset_cols = [target, "SAMPDATE"] + base_geo
    base_df = df.dropna(subset=base_subset_cols).copy()
    base_df = base_df.sort_values(by="SAMPDATE").reset_index(drop=True)
    
    # 3. Filtering for Chemical Subset
    chem_features = ["TPBG", "CONDUCT", "PH", "CHLA"]
    chem_subset_cols = base_subset_cols + chem_features
    chem_df = df.dropna(subset=chem_subset_cols).copy()
    chem_df = chem_df.sort_values(by="SAMPDATE").reset_index(drop=True)
    
    # 3b. Filtering for CHLA ONLY Subset
    chla_features = ["CHLA"]
    chla_subset_cols = base_subset_cols + chla_features
    chla_df = df.dropna(subset=chla_subset_cols).copy()
    chla_df = chla_df.sort_values(by="SAMPDATE").reset_index(drop=True)
    
    print(f"Total rows for Baseline: {len(base_df)}")
    print(f"Total rows for Chem Subset: {len(chem_df)}")
    print(f"Total rows for CHLA Subset: {len(chla_df)}")
    
    # 4. Spits
    def split_data(dataset):
        split_idx = int(len(dataset) * 0.8)
        return dataset.iloc[:split_idx].copy(), dataset.iloc[split_idx:].copy()
        
    base_train, base_test = split_data(base_df)
    chem_train, chem_test = split_data(chem_df)
    chla_train, chla_test = split_data(chla_df)
    
    # 5. Build Models
    print("Evaluating Model A: Baseline Data & Features")
    res_a = build_model(base_train, base_test, target, base_features)
    
    print("Evaluating Model B: Chem Data & Base Features")
    res_b = build_model(chem_train, chem_test, target, base_features)
    
    print("Evaluating Model C: Chem Data & Chem Features")
    res_c = build_model(chem_train, chem_test, target, base_features + chem_features)

    print("Evaluating Model D: CHLA Data & Base Features")
    res_d = build_model(chla_train, chla_test, target, base_features)

    print("Evaluating Model E: CHLA Data & CHLA Feature")
    res_e = build_model(chla_train, chla_test, target, base_features + chla_features)
    
    models_info = {
        "A": {"name": "Baseline Data & Features", "res": res_a, "n_rows": len(base_df)},
        "B": {"name": "Chem Subset & Base Features", "res": res_b, "n_rows": len(chem_df)},
        "C": {"name": "Chem Subset & Chem Features", "res": res_c, "n_rows": len(chem_df)},
        "D": {"name": "CHLA Subset & Base Features", "res": res_d, "n_rows": len(chla_df)},
        "E": {"name": "CHLA Subset & CHLA Feature", "res": res_e, "n_rows": len(chla_df)},
    }
    
    summary_data = []
    for mod_id, info in models_info.items():
        r = info["res"]["test"]
        summary_data.append({
            "Model": mod_id,
            "Description": info["name"],
            "N_Rows": info["n_rows"],
            "MAE": round(r["MAE"], 4),
            "RMSE": round(r["RMSE"], 4),
            "R2_test": float(round(r["R2"], 4)),
            "MAE_Norm": round(r["MAE_Norm"], 4),
            "RMSE_Norm": round(r["RMSE_Norm"], 4)
        })
        
    summary_df = pd.DataFrame(summary_data)
    
    # Feature Importances for C
    imp_c = models_info["C"]["res"]["importances"]
    c_sorted = sorted(imp_c.items(), key=lambda item: item[1], reverse=True)[:15]
    
    imp_rows = []
    for feat, val in c_sorted:
        imp_rows.append({
            "Feature": feat,
            "Importance": round(val, 4)
        })
    imp_df = pd.DataFrame(imp_rows)
    
    # Visualize Importances
    plt.figure(figsize=(10, 6))
    sns.barplot(x=[r["Importance"] for r in imp_rows], y=[r["Feature"] for r in imp_rows], color="#2b83ba")
    plt.title("Feature Importances (Model C: Base + Chem Features)")
    plt.xlabel("Gini Importance")
    plt.ylabel("Feature")
    plot_path = reports_dir / "15_feature_importance.png"
    plt.savefig(plot_path, bbox_inches="tight")
    plt.close()
    
    # Report Build
    sections = [
        ("Objective", "Establish a baseline understanding of how incorporating sparse chemical and biological characteristics impacts predictive capability. Part II of this experiment focuses exclusively on `CHLA` since preliminary runs isolated it as the most powerful chemical indicator, allowing us to evaluate if isolating just this one feature recovers more row data while preserving the high predictive signal."),
        ("Data Subsets and Filtering", f"- **Baseline Dataset Rows:** {len(base_df):,} (Filtered strictly for target + geo + time)\n- **Full Chemical Dataset Rows:** {len(chem_df):,} (Strict subset dropping any rows with missing TPBG, CONDUCT, PH, or CHLA)\n- **CHLA-Only Dataset Rows:** {len(chla_df):,} (Subset dropping rows strictly missing CHLA, returning more total rows)"),
        ("Model Performance", f"{df_to_markdown_table(summary_df)}\n\n*Note: `MAE_Norm` and `RMSE_Norm` represent percentage-based absolute prediction errors dynamically corrected relative to `DEPTH_MAX_FEET`.*"),
        ("Feature Importances (Model C: Base + Chem)", f"{df_to_markdown_table(imp_df)}\n\n![Feature Importances](15_feature_importance.png)"),
        ("Executive Summary & Next Steps", f"### What We Did\nTo understand whether adding granular chemical/biological properties (`TPBG`, `CONDUCT`, `PH`, `CHLA`) improves Secchi depth predictions, we tested how complete-case filtering for sparse chemistry affects performance.\n\nWe evaluated two subsets:\n1. A **Full Chemical subset** ({len(chem_df):,} rows where all four chemical features are present).\n2. A **CHLA-only subset** ({len(chla_df):,} rows requiring only CHLA).\n\nWe then evaluated five tracks to isolate signal vs row-loss:\n- **Model A:** Baseline geography+time on the baseline dataset.\n- **Model B:** Baseline geography+time on the full-chemical subset.\n- **Model C:** Geography+time+chemistry on the full-chemical subset.\n- **Model D:** Baseline geography+time on the CHLA-only subset.\n- **Model E:** Geography+time+CHLA on the CHLA-only subset.\n\n### The Outcome\n1. **Data Loss Penalty:** Restrictive complete-case filtering can sharply reduce sample size and hurt generalization.\n2. **Chemical Signal:** Adding chemistry can recover predictive signal despite smaller subsets.\n3. **CHLA Isolation:** Using only CHLA often retains more rows than full chemistry while preserving key signal.\n\n### Moving Forward\nIf chemistry is valuable but sparse, consider models/pipelines that avoid hard row deletion:\n1. **Native sparse-aware models:** `HistGradientBoostingRegressor`, `XGBoost`, or `LightGBM`.\n2. **Imputation pipelines:** e.g., `KNNImputer` with robust validation.")
    ]
    
    report_path = write_markdown_report("15_chemical_features.md", "Experiment 15: Incorporation of Chemical Features", sections)
    print(f"Report generated at {report_path}")

if __name__ == "__main__":
    main()
