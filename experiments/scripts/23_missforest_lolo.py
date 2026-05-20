import pandas as pd
import numpy as np
from sklearn.experimental import enable_iterative_imputer  # noqa: F401 - registers IterativeImputer
from sklearn.impute import IterativeImputer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error

try:
    from tqdm import tqdm
except ImportError:  # optional dependency
    def tqdm(iterable, **_kwargs):
        return iterable

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
    ensure_reports_dir()
    print("Loading dataset...")
    data = load_data()
    df = data.frame
    
    target = "SECCHI"
    num_cols = ["LATITUDE", "LONGITUDE", "AREA_ACRES", "DEPTH_MAX_FEET"]
    df["year"] = df["SAMPDATE"].dt.year
    df["month"] = df["SAMPDATE"].dt.month
    base_features = ["year", "month"] + num_cols
    
    chem_features = ["DOMAX", "DOMIN", "TPEC", "TPBG", "PH", "COLOR", "CONDUCT", "ALK"]
    valid_chems = [c for c in chem_features if c in df.columns]
    
    subset_cols = [target, "SAMPDATE", "MIDAS"] + num_cols 
    model_df = df.dropna(subset=subset_cols).copy()
    model_df = model_df.sort_values(by="SAMPDATE").reset_index(drop=True)
    
    missing_path = PROJECT_ROOT / "data" / "lake_missingness.csv"
    missingness_df = pd.read_csv(missing_path) if missing_path.exists() else pd.DataFrame()
    
    features = base_features + valid_chems
    
    # --- LOLO Evaluation ---
    seed_file = PROJECT_ROOT / "experiments" / "scripts" / "lolo_random_seed_10.txt"
    sample_lakes = []
    if seed_file.exists():
        with open(seed_file, "r") as f:
            sample_lakes = [line.strip() for line in f if line.strip()]
            
    avg_lolo_r2 = np.nan
    lolo_results = []
    
    if sample_lakes:
        print(f"\nEvaluating MissForest LOLO Pipeline on {len(sample_lakes)} strictly preserved target lakes...")
        r2_list = []
        for L in tqdm(sample_lakes, desc="MissForest LOLO"):
            L_key = str(L).strip()
            test_lake_df = model_df[model_df["MIDAS"].astype(str).str.strip() == L_key]
            train_lake_df = model_df[model_df["MIDAS"].astype(str).str.strip() != L_key]
            
            if len(test_lake_df) == 0:
                continue
                
            X_train = train_lake_df[features].copy()
            y_train = train_lake_df[target].copy()
            X_test = test_lake_df[features].copy()
            y_test = test_lake_df[target].copy()
            
            # 1. Impute
            rf_imputer = RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42, n_jobs=-1)
            imputer = IterativeImputer(estimator=rf_imputer, max_iter=3, random_state=42)
            
            X_train_imputed = imputer.fit_transform(X_train)
            X_test_imputed = imputer.transform(X_test)
            
            # 2. Predict
            predictor = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
            predictor.fit(X_train_imputed, y_train)
            
            pred = predictor.predict(X_test_imputed)
            perf_m = evaluate_model(y_test, pred, test_lake_df["DEPTH_MAX_FEET"])
            
            pct_m = np.nan
            if (
                not missingness_df.empty
                and "MIDAS" in missingness_df.columns
                and "pct_missing_chemical_overall" in missingness_df.columns
            ):
                matches = missingness_df.loc[
                    missingness_df["MIDAS"].astype(str).str.strip() == L_key, "pct_missing_chemical_overall"
                ].values
                if len(matches) > 0:
                    pct_m = matches[0]
                    
            r2_list.append(perf_m["R2"])
            lolo_results.append({
                "MIDAS": L,
                "pct_missing_overall": round(pct_m, 4) if not np.isnan(pct_m) else pct_m,
                "n_obs": len(test_lake_df),
                "R2": round(perf_m["R2"], 4),
                "MAE": round(perf_m["MAE"], 4),
                "MAE_Norm": round(perf_m["MAE_Norm"], 4)
            })
            
        avg_lolo_r2 = np.nanmean(r2_list) if len(r2_list) > 0 else np.nan
        lolo_df = pd.DataFrame(lolo_results)
    else:
        lolo_df = pd.DataFrame()
    
    lolo_avg_line = (
        f"**MissForest RF Average LOLO $R^2$:** {float(avg_lolo_r2):.4f}"
        if pd.notna(avg_lolo_r2)
        else "**MissForest RF Average LOLO $R^2$:** N/A (no seed lakes evaluated)"
    )
    
    lolo_md = df_to_markdown_table(lolo_df) if not lolo_df.empty else "No LOLO targets strictly evaluated."
    
    sections = [
        ("What We Did",
         "In Experiment 23, we tested how well the model generalizes to lakes it has never seen.\n\n"
         "We used a Leave-One-Lake-Out (LOLO) setup. Target lakes are read from `lolo_random_seed_10.txt` (one `MIDAS` ID per line).\n"
         "For each target lake, we ran this process:\n"
         "1. Held out one lake as the test set.\n"
         "2. Used all other lakes as the training set.\n"
         "3. Fit MissForest-style imputation (`IterativeImputer` with Random Forest) on training features only.\n"
         "4. Used `max_iter=3` and `max_depth=10` for controlled runtime and memory use.\n"
         "5. Trained a Random Forest predictor (`n_estimators=100`) on imputed training data.\n"
         "6. Evaluated predictions on the held-out lake."
        ),
        
        ("Predicting Completely Unseen Lakes (LOLO)",
         "The table below shows results for each held-out lake.\n"
         "This reflects geographic generalization after imputation.\n\n"
         "Note: some lakes can still produce low or negative $R^2$ values if local lake dynamics differ from the training lakes.\n\n"
         f"{lolo_md}\n\n"
         f"{lolo_avg_line}"
        )
    ]
    
    report_path = write_markdown_report("23_missforest_lolo.md", "Experiment 23: Out-of-Boundary Regional Prediction (MissForest)", sections)
    print(f"\nReport generated at {report_path}")

if __name__ == "__main__":
    main()
