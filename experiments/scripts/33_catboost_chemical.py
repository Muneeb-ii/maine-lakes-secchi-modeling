import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from catboost import CatBoostRegressor
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

    return {
        "MAE": mae,
        "RMSE": rmse,
        "R2": r2,
        "MAE_Norm": mae_norm,
        "RMSE_Norm": rmse_norm,
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

    chem_features = ["DOMAX", "DOMIN", "TPEC", "TPBG", "CHLA", "PH", "COLOR", "CONDUCT", "ALK"]
    valid_chems = [c for c in chem_features if c in df.columns]

    subset_cols = [target, "SAMPDATE", "MIDAS"] + num_cols
    model_df = df.dropna(subset=subset_cols).copy()
    model_df = model_df.sort_values(by="SAMPDATE").reset_index(drop=True)

    missing_path = PROJECT_ROOT / "data" / "lake_missingness.csv"
    missingness_df = pd.read_csv(missing_path) if missing_path.exists() else pd.DataFrame()

    print(f"Total Rows passed to CatBoost (Native NaNs intact for chem fields): {len(model_df):,}")

    features = base_features + valid_chems
    split_idx = int(len(model_df) * 0.8)
    train_df = model_df.iloc[:split_idx]
    test_df = model_df.iloc[split_idx:]

    X_train = train_df[features].copy()
    y_train = train_df[target].copy()
    depth_test = test_df["DEPTH_MAX_FEET"]

    nan_counts = X_train[valid_chems].isna().sum()
    print("\nChemical Missingness natively handled by CatBoost in Training Set:")
    print(nan_counts)

    print("\nTraining CatBoost Regressor...")
    model = CatBoostRegressor(
        iterations=100,
        depth=10,
        random_seed=42,
        loss_function="RMSE",
        verbose=False,
        allow_writing_files=False,
        thread_count=1,
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(test_df[features])
    metrics_chrono = evaluate_model(test_df[target], y_pred, depth_test)

    importances = model.get_feature_importance()
    imp_df = pd.DataFrame({"Feature": features, "Importance": importances})
    imp_df = imp_df.sort_values(by="Importance", ascending=False).reset_index(drop=True)

    plt.figure(figsize=(10, 6))
    sns.barplot(x="Importance", y="Feature", data=imp_df, color="mediumseagreen")
    plt.title("CatBoost Feature Importances (Native NaN Support)")
    plt.xlabel("Importance")
    plot_path = reports_dir / "33_catboost_importances.png"
    plt.savefig(plot_path, bbox_inches="tight")
    plt.close()

    seed_file = PROJECT_ROOT / "experiments" / "scripts" / "lolo_random_seed_10.txt"
    sample_lakes = []
    if seed_file.exists():
        with open(seed_file, "r", encoding="utf-8") as handle:
            sample_lakes = [line.strip() for line in handle if line.strip()]
    else:
        print("Warning: LOLO random seed file not found. Skipping LOLO...")

    avg_lolo_r2 = np.nan
    lolo_results = []

    if sample_lakes:
        print(f"\nEvaluating CatBoost LOLO on {len(sample_lakes)} strictly preserved target lakes...")
        r2_list = []
        for lake_id in tqdm(sample_lakes, desc="CatBoost LOLO"):
            test_lake_df = model_df[model_df["MIDAS"] == lake_id]
            train_lake_df = model_df[model_df["MIDAS"] != lake_id]

            if len(test_lake_df) == 0:
                continue

            cat_lolo = CatBoostRegressor(
                iterations=100,
                depth=10,
                random_seed=42,
                loss_function="RMSE",
                verbose=False,
                allow_writing_files=False,
                thread_count=1,
            )
            cat_lolo.fit(train_lake_df[features], train_lake_df[target])

            pred = cat_lolo.predict(test_lake_df[features])
            perf_m = evaluate_model(test_lake_df[target], pred, test_lake_df["DEPTH_MAX_FEET"])

            pct_m = np.nan
            if not missingness_df.empty:
                matches = missingness_df.loc[
                    missingness_df["MIDAS"] == lake_id,
                    "pct_missing_chemical_overall",
                ].values
                if len(matches) > 0:
                    pct_m = matches[0]

            r2_list.append(perf_m["R2"])
            lolo_results.append(
                {
                    "MIDAS": lake_id,
                    "pct_missing_overall": round(pct_m, 4) if not np.isnan(pct_m) else pct_m,
                    "n_obs": len(test_lake_df),
                    "R2": round(perf_m["R2"], 4),
                    "MAE": round(perf_m["MAE"], 4),
                    "MAE_Norm": round(perf_m["MAE_Norm"], 4),
                }
            )

        avg_lolo_r2 = np.nanmean(r2_list) if len(r2_list) > 0 else np.nan
        lolo_df = pd.DataFrame(lolo_results)
    else:
        lolo_df = pd.DataFrame()

    lolo_md = df_to_markdown_table(lolo_df) if not lolo_df.empty else "No LOLO targets successfully evaluated."

    sections = [
        (
            "What We Did (Methodology)",
            "Following Experiments 20 and 21, we deployed **CatBoost** on the identical chemistry-enriched setup. "
            "Like the other boosted-tree baselines, CatBoost can retain rows with missing chemistry instead of forcing "
            "global imputation or row deletion. This lets us preserve the same broad geographic-temporal training base "
            "while still testing whether chemistry helps when present.\n\n"
            f"We loaded the baseline geographic limits and the chemical subset: `{valid_chems}`. By preserving native missingness, "
            f"CatBoost trained on **{len(model_df):,}** usable rows."
        ),
        (
            "80/20 Chronological Results",
            "Predicting strictly out-of-time (the latest 20% temporal split) yielded:\n\n"
            f"- **R-Squared (R²):** {metrics_chrono['R2']:.4f}\n"
            f"- **Mean Absolute Error (MAE):** {metrics_chrono['MAE']:.4f} meters\n"
            f"- **Root Mean Squared Error (RMSE):** {metrics_chrono['RMSE']:.4f} meters\n"
            f"- **Normalized MAE:** {metrics_chrono['MAE_Norm']:.4f}\n"
            f"- **Normalized RMSE:** {metrics_chrono['RMSE_Norm']:.4f}\n"
        ),
        (
            "Predicting Completely Unseen Lakes (LOLO)",
            "We evaluated CatBoost on the same seeded 10 target lake IDs used by the XGBoost and LightGBM tests. "
            "This keeps the comparison aligned across boosting families even though full row context can differ slightly. "
            "The table below shows lake-level performance and the overall average LOLO $R^2$ for this run:\n\n"
            f"{lolo_md}\n\n"
            f"**CatBoost Average LOLO $R^2$:** {avg_lolo_r2:.4f}"
        ),
        (
            "Feature Importances",
            "Measured using CatBoost's native feature importance scores after training with missing values left intact.\n\n"
            f"{df_to_markdown_table(imp_df.head(15))}\n\n"
            "![CatBoost Importances](33_catboost_importances.png)"
        ),
    ]

    report_path = write_markdown_report(
        "33_catboost_chemical.md",
        "Experiment 33: Native Missingness Chemical Processing (CatBoost)",
        sections,
    )
    print(f"\nReport generated at {report_path}")


if __name__ == "__main__":
    main()
