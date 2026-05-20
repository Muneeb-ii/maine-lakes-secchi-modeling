import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.experimental import enable_iterative_imputer  # noqa: F401 (enables IterativeImputer)
from sklearn.impute import IterativeImputer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from tqdm.auto import tqdm

from experiment_utils import ensure_reports_dir, write_markdown_report, df_to_markdown_table, load_data

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
    
    # Exclude CHLA explicitly per instructions
    initial_chems = ["DOMAX", "DOMIN", "TPEC", "TPBG", "PH", "COLOR", "CONDUCT", "ALK"]
    initial_chems = [c for c in initial_chems if c in df.columns]
    
    subset_cols = [target, "SAMPDATE", "MIDAS"] + num_cols 
    model_df = df.dropna(subset=subset_cols).copy()
    
    # Filter for lakes with >= 100 samples
    lake_counts = model_df["MIDAS"].value_counts()
    included_lakes = lake_counts[lake_counts >= 100].index
    model_df = model_df[model_df["MIDAS"].isin(included_lakes)].copy()
    print(f"Filtered to lakes with >= 100 samples. Remaining lakes: {len(included_lakes)}")
    if model_df.empty:
        raise ValueError("No rows remain after T>=100 filtering. Cannot run Experiment 26.")
    
    # Strict chronological sort for global temporal split
    model_df = model_df.sort_values(by="SAMPDATE").reset_index(drop=True)
    
    # 80/20 Splitting
    split_idx = int(len(model_df) * 0.8)
    train_df = model_df.iloc[:split_idx]
    test_df = model_df.iloc[split_idx:]
    if train_df.empty or test_df.empty:
        raise ValueError("Chronological 80/20 split produced an empty train or test set.")
    
    y_train = train_df[target].copy()
    y_test = test_df[target].copy()
    depth_test = test_df["DEPTH_MAX_FEET"]
    
    # ---------------------------------------------------------
    # PART 1: BASE MISSFOREST EXPERIMENT (All Chems)
    # ---------------------------------------------------------
    features = base_features + initial_chems
    X_train = train_df[features].copy()
    X_test = test_df[features].copy()
    
    print("\n[PART 1] Fitting Base MissForest (All Chems) on T>=100...")
    rf_imputer = RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42, n_jobs=-1)
    imputer = IterativeImputer(estimator=rf_imputer, max_iter=3, random_state=42)
    
    X_train_imputed = pd.DataFrame(imputer.fit_transform(X_train), columns=features, index=X_train.index)
    X_test_imputed = pd.DataFrame(imputer.transform(X_test), columns=features, index=X_test.index)
    
    predictor = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    predictor.fit(X_train_imputed, y_train)
    
    y_pred = predictor.predict(X_test_imputed)
    base_metrics = evaluate_model(y_test, y_pred, depth_test)
    
    # Feature Importances Plot for Base Run
    importances = predictor.feature_importances_
    imp_df = pd.DataFrame({"Feature": features, "Importance": importances})
    imp_df = imp_df.sort_values(by="Importance", ascending=False).reset_index(drop=True)
    
    plt.figure(figsize=(10, 6))
    sns.barplot(x="Importance", y="Feature", data=imp_df, color='darkorange')
    plt.title("RandomForest Feature Importances after MissForest Imputation (T=100)")
    plt.xlabel("Gini Importance")
    plot_path = reports_dir / "26_missforest_t100_importances.png"
    plt.savefig(plot_path, bbox_inches="tight")
    plt.close()
    
    # ---------------------------------------------------------
    # PART 2: BACKWARD ELIMINATION
    # ---------------------------------------------------------
    print("\n[PART 2] Initiating Recursive Feature Elimination (Backward) on T>=100...")
    current_chems = list(initial_chems)
    history = []
    
    for i in tqdm(range(len(initial_chems)), desc="Dense-lake elimination", unit="step"):
        features = base_features + current_chems
        
        print(f"\nIteration {i+1} | Evaluating with {len(current_chems)} chemical features...")
        X_train = train_df[features].copy()
        X_test = test_df[features].copy()
        
        if len(current_chems) > 0:
            rf_imputer = RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42, n_jobs=-1)
            imputer = IterativeImputer(estimator=rf_imputer, max_iter=3, random_state=42)
            
            X_train_imputed = pd.DataFrame(imputer.fit_transform(X_train), columns=features, index=X_train.index)
            X_test_imputed = pd.DataFrame(imputer.transform(X_test), columns=features, index=X_test.index)
        else:
            X_train_imputed = X_train
            X_test_imputed = X_test
            
        predictor = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
        predictor.fit(X_train_imputed, y_train)
        
        y_pred = predictor.predict(X_test_imputed)
        metrics = evaluate_model(y_test, y_pred, depth_test)
        
        importances = predictor.feature_importances_
        temp_imp_df = pd.DataFrame({"Feature": features, "Importance": importances})
        
        chem_imp_df = temp_imp_df[temp_imp_df["Feature"].isin(current_chems)].sort_values(by="Importance", ascending=True)
        
        if len(chem_imp_df) > 0:
            least_important_chem = chem_imp_df.iloc[0]["Feature"]
        else:
            least_important_chem = "None"
            
        history.append({
            "Iteration": i + 1,
            "Chemical Count": len(current_chems),
            "R2": round(metrics["R2"], 4),
            "MAE": round(metrics["MAE"], 4),
            "Chemicals Used": ", ".join(current_chems) if len(current_chems) > 0 else "None",
            "Dropped After This Run": least_important_chem
        })
        
        if least_important_chem != "None":
            current_chems.remove(least_important_chem)
            
    # Zero chemical baseline
    features = base_features
    print(f"\nIteration {len(initial_chems)+1} | Evaluating with 0 chemical features (Base Geography/Time only)...")
    X_train = train_df[features].copy()
    X_test = test_df[features].copy()
    
    predictor = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    predictor.fit(X_train, y_train)
    y_pred = predictor.predict(X_test)
    metrics = evaluate_model(y_test, y_pred, depth_test)
    
    history.append({
        "Iteration": len(initial_chems) + 1,
        "Chemical Count": 0,
        "R2": round(metrics["R2"], 4),
        "MAE": round(metrics["MAE"], 4),
        "Chemicals Used": "None",
        "Dropped After This Run": "N/A"
    })
    
    hist_df = pd.DataFrame(history)
    
    # Plot Elimination Curve
    plt.figure(figsize=(10, 6))
    sns.lineplot(data=hist_df, x="Chemical Count", y="R2", marker="o", color="crimson")
    plt.title("R² Predictive Power Decay vs. Imputation Reliance (Lakes >= 100 Samples)")
    plt.xlabel("Number of Chemical Features Used (Descending via Gini)")
    plt.ylabel("Test $R^2$ Score")
    plt.gca().invert_xaxis()
    plot_path = reports_dir / "26_missforest_t100_elimination_curve.png"
    plt.savefig(plot_path, bbox_inches="tight")
    plt.close()
    
    # ---------------------------------------------------------
    # WRITE REPORT
    # ---------------------------------------------------------
    sections = [
        ("What We Did",
         "In this experiment, we combined three core methodologies to identify the absolute optimal model structure:\n\n"
         "1. **Experiment 25 ($T \ge 100$ filtering):** We removed any lake from the dataset with fewer than 100 historical samples to ensure the imputer and model are fed high-quality, dense histories.\n"
         "2. **Experiment 22 (MissForest Imputation):** We imputed missing chemical features using an `IterativeImputer` with a Random Forest core, fitted strictly on the chronologically split training set.\n"
         "3. **Experiment 24 (Backward Elimination):** We recursively dropped the lowest-importance chemical feature to see how $T \ge 100$ impacts the decay of predictive power."
        ),
        
        ("Part 1: Base MissForest Results (Threshold = 100)",
         "The performance of the model using *all* valid imputed chemical features on the dense ($T \ge 100$) lake subset:\n\n"
         f"- **R-Squared (R²):** {base_metrics['R2']:.4f}\n"
         f"- **Mean Squared Error (MSE):** {(base_metrics['RMSE']**2):.4f} meters²\n"
         f"- **Mean Absolute Error (MAE):** {base_metrics['MAE']:.4f} meters\n"
         f"- **Normalized MSE:** {(base_metrics['RMSE_Norm']**2):.4f}\n"
         f"- **Normalized MAE:** {base_metrics['MAE_Norm']:.4f}\n\n"
         "Note: normalized errors divide SECCHI residuals by `DEPTH_MAX_FEET`, so this metric is a depth-relative ratio.\n\n"
         f"{df_to_markdown_table(imp_df.head(15))}\n\n"
         "![MissForest Gini Weighting](26_missforest_t100_importances.png)"
        ),
        
        ("Part 2: Iterative Backward Elimination",
         "We progressively removed the lowest-impact chemical feature to see if imputation on highly-dense lakes provides durable signal, or if it can be stripped away.\n\n"
         f"{df_to_markdown_table(hist_df)}\n\n"
         "![Trade-off Curve](26_missforest_t100_elimination_curve.png)"
        ),
        
        ("Interpretations",
         "### How does $T \ge 100$ affect imputation reliance?\n\n"
         "By strictly filtering the lakes before performing MissForest imputation and backward elimination, we can compare these results directly to Experiment 24.\n"
         "If the $R^2$ curve stays higher for longer (or decays slower) here than it did in Experiment 24, it proves that providing the imputer with dense, $T \ge 100$ histories creates *meaningful, high-fidelity chemical guesses* rather than just statistical noise. Conversely, it allows us to see precisely how many chemical features are strictly necessary to maintain peak accuracy when working with high-quality lakes."
        )
    ]
    
    report_path = write_markdown_report("26_missforest_chrono_t100.md", "Experiment 26: Optimal Dense-Lake Forecasting (Imputation + Elimination)", sections)
    print(f"\nReport generated at {report_path}")

if __name__ == "__main__":
    main()
