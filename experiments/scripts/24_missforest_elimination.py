import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from tqdm import tqdm

from experiment_utils import ensure_reports_dir, write_markdown_report, df_to_markdown_table, load_data, PROJECT_ROOT

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
    
    return {"MAE": mae, "RMSE": rmse, "R2": r2, "MAE_Norm": mae_norm, "RMSE_Norm": rmse_norm}

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
    initial_chems = ["DOMAX", "DOMIN", "TPEC", "TPBG", "PH", "COLOR", "CONDUCT", "ALK"]
    initial_chems = [c for c in initial_chems if c in df.columns]
    
    subset_cols = [target, "SAMPDATE", "MIDAS"] + num_cols 
    model_df = df.dropna(subset=subset_cols).copy()
    model_df = model_df.sort_values(by="SAMPDATE").reset_index(drop=True)
    
    # 80/20 Splitting indices remain static
    split_idx = int(len(model_df) * 0.8)
    train_df = model_df.iloc[:split_idx]
    test_df = model_df.iloc[split_idx:]
    
    y_train = train_df[target].copy()
    y_test = test_df[target].copy()
    depth_test = test_df["DEPTH_MAX_FEET"]
    
    print("\nInitiating Recursive Feature Elimination (Backward)...")
    
    current_chems = list(initial_chems)
    history = []
    
    for i in range(len(initial_chems)):
        features = base_features + current_chems
        
        print(f"\nIteration {i+1} | Evaluating with {len(current_chems)} chemical features...")
        X_train = train_df[features].copy()
        X_test = test_df[features].copy()
        
        # 1. MissForest Impute
        if len(current_chems) > 0:
            rf_imputer = RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42, n_jobs=-1)
            imputer = IterativeImputer(estimator=rf_imputer, max_iter=3, random_state=42)
            
            X_train_imputed = pd.DataFrame(imputer.fit_transform(X_train), columns=features, index=X_train.index)
            X_test_imputed = pd.DataFrame(imputer.transform(X_test), columns=features, index=X_test.index)
        else:
            # Base features have no chemical NaNs
            X_train_imputed = X_train
            X_test_imputed = X_test
            
        # 2. Main Predictor
        predictor = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
        predictor.fit(X_train_imputed, y_train)
        
        y_pred = predictor.predict(X_test_imputed)
        metrics = evaluate_model(y_test, y_pred, depth_test)
        
        # 3. Importances
        importances = predictor.feature_importances_
        imp_df = pd.DataFrame({"Feature": features, "Importance": importances})
        
        # Only chemical features are up for elimination!
        chem_imp_df = imp_df[imp_df["Feature"].isin(current_chems)].sort_values(by="Importance", ascending=True)
        
        if len(chem_imp_df) > 0:
            least_important_chem = chem_imp_df.iloc[0]["Feature"]
            lowest_score = chem_imp_df.iloc[0]["Importance"]
        else:
            least_important_chem = "None"
            lowest_score = 0.0
            
        history.append({
            "Iteration": i + 1,
            "Chemical Count": len(current_chems),
            "R2": round(metrics["R2"], 4),
            "MAE": round(metrics["MAE"], 4),
            "Chemicals Used": ", ".join(current_chems) if len(current_chems) > 0 else "None",
            "Dropped After This Run": least_important_chem
        })
        
        # Execute the drop for the next iteration
        if least_important_chem != "None":
            current_chems.remove(least_important_chem)
            
    # Evaluate the zero-chemical (base only) model
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
    
    # 4. Generate Elimination Curve Chart
    plt.figure(figsize=(10, 6))
    sns.lineplot(data=hist_df, x="Chemical Count", y="R2", marker="o", color="crimson")
    plt.title("R² Predictive Power Decay vs. Imputation Reliance")
    plt.xlabel("Number of Chemical Features Used (Descending via Gini)")
    plt.ylabel("Test $R^2$ Score")
    plt.gca().invert_xaxis() # We want it moving from 8 down to 0
    
    plot_path = reports_dir / "24_missforest_elimination_curve.png"
    plt.savefig(plot_path, bbox_inches="tight")
    plt.close()
    
    # 5. Build Final Markdown
    sections = [
        ("What We Did",
         "In Experiment 24, we ran recursive backward elimination on chemical features.\n"
         "The goal was to see how many chemicals we can remove while keeping prediction quality.\n\n"
         "We followed this process:\n"
         "1. Used a chronological 80/20 split.\n"
         "2. Started with all available chemical features.\n"
         "3. Imputed missing values with MissForest-style imputation (`IterativeImputer` + Random Forest).\n"
         "4. Trained a Random Forest predictor and recorded test $R^2$ and MAE.\n"
         "5. Ranked only chemical features by Gini importance.\n"
         "6. Removed the least important chemical.\n"
         "7. Repeated until no chemicals remained, leaving only base features (`LATITUDE`, `LONGITUDE`, `AREA_ACRES`, `DEPTH_MAX_FEET`, year, month)."
        ),
        
        ("Trade-off Curve Results",
         "The table and chart below show how performance changes as chemical features are removed.\n"
         "This helps identify which chemicals add useful signal and when performance starts to decline.\n\n"
         f"{df_to_markdown_table(hist_df)}\n\n"
         "![Trade-off Curve](24_missforest_elimination_curve.png)"
        )
    ]
    
    report_path = write_markdown_report("24_missforest_elimination.md", "Experiment 24: Iterative Backward Elimination (MissForest)", sections)
    print(f"\nReport generated at {report_path}")

if __name__ == "__main__":
    main()
