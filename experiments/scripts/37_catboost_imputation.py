from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from catboost import CatBoostRegressor
from tqdm.auto import tqdm

from experiment_utils import (
    CanonicalReport,
    ensure_reports_dir,
    write_canonical_report,
    df_to_markdown_table,
    load_data,
    PROJECT_ROOT,
)

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

MISSFOREST_IMPUTER = {
    "n_estimators": 30,
    "max_depth": 10,
    "random_state": 42,
    "n_jobs": -1,
    "max_iter": 3,
}

NATIVE_CHRONO_R2 = 0.7324
NATIVE_CHRONO_MAE = 0.8122
NATIVE_CHRONO_RMSE = 1.0903
NATIVE_LOLO10_R2 = -1.3806
NATIVE_LOLO10_MAE = 1.2210


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


def build_imputer():
    rf = RandomForestRegressor(
        n_estimators=MISSFOREST_IMPUTER["n_estimators"],
        max_depth=MISSFOREST_IMPUTER["max_depth"],
        random_state=MISSFOREST_IMPUTER["random_state"],
        n_jobs=MISSFOREST_IMPUTER["n_jobs"],
    )
    return IterativeImputer(estimator=rf, max_iter=MISSFOREST_IMPUTER["max_iter"], random_state=42)


def fit_predict_catboost_with_imputation(train_df, test_df, features, target):
    imputer = build_imputer()
    X_train = pd.DataFrame(imputer.fit_transform(train_df[features]), columns=features, index=train_df.index)
    X_test = pd.DataFrame(imputer.transform(test_df[features]), columns=features, index=test_df.index)
    model = CatBoostRegressor(**CATBOOST_PARAMS)
    model.fit(X_train, train_df[target])
    preds = model.predict(X_test)
    metrics = evaluate_model(test_df[target], preds, test_df["DEPTH_MAX_FEET"])
    return model, metrics


def main() -> None:
    reports_dir = ensure_reports_dir()
    print("Loading dataset...")
    df = load_data().frame

    target = "SECCHI"
    num_cols = ["LATITUDE", "LONGITUDE", "AREA_ACRES", "DEPTH_MAX_FEET"]
    base_features = ["year", "month"] + num_cols
    chem_features = ["DOMAX", "DOMIN", "TPEC", "TPBG", "PH", "COLOR", "CONDUCT", "ALK"]
    valid_chems = [c for c in chem_features if c in df.columns]
    features = base_features + valid_chems

    subset_cols = [target, "SAMPDATE", "MIDAS"] + num_cols
    model_df = df.dropna(subset=subset_cols).copy().sort_values("SAMPDATE").reset_index(drop=True)

    split_idx = int(len(model_df) * 0.8)
    train_df = model_df.iloc[:split_idx].copy()
    test_df = model_df.iloc[split_idx:].copy()

    print("Running chronological MissForest + tuned CatBoost evaluation...")
    chrono_model, chrono_metrics = fit_predict_catboost_with_imputation(train_df, test_df, features, target)

    imp_df = pd.DataFrame({
        "Feature": features,
        "Importance": chrono_model.get_feature_importance(),
    }).sort_values(by="Importance", ascending=False).reset_index(drop=True)

    plt.figure(figsize=(10, 6))
    sns.barplot(data=imp_df.head(15), x="Importance", y="Feature", color="#52796f")
    plt.title("CatBoost Feature Importances After MissForest Imputation")
    plt.xlabel("Importance")
    chrono_plot = reports_dir / "37_catboost_imputed_importances.png"
    plt.savefig(chrono_plot, bbox_inches="tight")
    plt.close()

    seed_file = PROJECT_ROOT / "experiments" / "scripts" / "lolo_random_seed_10.txt"
    lake_ids = [line.strip() for line in seed_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    missing_path = PROJECT_ROOT / "data" / "lake_missingness.csv"
    missingness_df = pd.read_csv(missing_path) if missing_path.exists() else pd.DataFrame()

    lolo_rows = []
    lolo_r2 = []
    lolo_mae = []
    print(f"Running seeded 10-lake LOLO MissForest + tuned CatBoost evaluation on {len(lake_ids)} lakes...")
    for lake_id in tqdm(lake_ids, desc="CatBoost imputed LOLO x10", unit="lake"):
        test_lake_df = model_df[model_df["MIDAS"].astype(str).str.strip() == lake_id]
        train_lake_df = model_df[model_df["MIDAS"].astype(str).str.strip() != lake_id]
        if len(test_lake_df) < 2:
            continue
        _, metrics = fit_predict_catboost_with_imputation(train_lake_df, test_lake_df, features, target)
        pct_m = np.nan
        if not missingness_df.empty:
            matches = missingness_df.loc[missingness_df["MIDAS"].astype(str).str.strip() == lake_id, "pct_missing_chemical_overall"].values
            if len(matches) > 0:
                pct_m = matches[0]
        lolo_r2.append(metrics["R2"])
        lolo_mae.append(metrics["MAE"])
        lolo_rows.append({
            "MIDAS": lake_id,
            "pct_missing_overall": round(pct_m, 4) if not np.isnan(pct_m) else pct_m,
            "n_obs": len(test_lake_df),
            "R2": round(metrics["R2"], 4),
            "MAE": round(metrics["MAE"], 4),
            "MAE_Norm": round(metrics["MAE_Norm"], 4),
        })

    lolo_df = pd.DataFrame(lolo_rows)
    lolo_avg_r2 = float(np.nanmean(lolo_r2)) if lolo_r2 else np.nan
    lolo_avg_mae = float(np.nanmean(lolo_mae)) if lolo_mae else np.nan

    comparison_df = pd.DataFrame([
        {
            "Configuration": "Native-missing tuned CatBoost (Exp 34/35)",
            "chrono_R2": NATIVE_CHRONO_R2,
            "chrono_MAE": NATIVE_CHRONO_MAE,
            "chrono_RMSE": NATIVE_CHRONO_RMSE,
            "lolo10_avg_R2": NATIVE_LOLO10_R2,
            "lolo10_avg_MAE": NATIVE_LOLO10_MAE,
        },
        {
            "Configuration": "MissForest-imputed tuned CatBoost",
            "chrono_R2": round(chrono_metrics["R2"], 4),
            "chrono_MAE": round(chrono_metrics["MAE"], 4),
            "chrono_RMSE": round(chrono_metrics["RMSE"], 4),
            "lolo10_avg_R2": round(lolo_avg_r2, 4),
            "lolo10_avg_MAE": round(lolo_avg_mae, 4),
        },
    ])

    plt.figure(figsize=(9, 5))
    plot_df = comparison_df.melt(id_vars="Configuration", value_vars=["chrono_R2", "lolo10_avg_R2"], var_name="metric", value_name="value")
    sns.barplot(data=plot_df, x="metric", y="value", hue="Configuration")
    plt.axhline(0, color="black", linewidth=1, alpha=0.5)
    plt.title("Native-Missing vs MissForest-Imputed CatBoost")
    plt.xlabel("Metric")
    plt.ylabel("R2")
    comparison_plot = reports_dir / "37_catboost_imputation_comparison.png"
    plt.savefig(comparison_plot, bbox_inches="tight")
    plt.close()

    report = CanonicalReport(
        objective=(
            "Test whether the best imputer from Experiment 36 improves tuned CatBoost relative to the native-missing baseline. "
            "The comparison stays on the no-CHLA Secchi prediction feature set so the final-model policy is unchanged."
        ),
        method=(
            "Use the tuned CatBoost parameters from Experiment 34 with the no-CHLA chemistry set. For each split, fit MissForest-style imputation on the training features only, transform training and test features separately, and then train CatBoost on the imputed values. Evaluate once on the chronological 80/20 split and once on the seeded 10-lake LOLO set so the result can be compared directly against Experiments 34 and 35."
        ),
        parameters=(
            f"CatBoost parameters: {CATBOOST_PARAMS}\n\n"
            f"MissForest-style imputer: {MISSFOREST_IMPUTER}\n\n"
            f"Feature set (CHLA excluded): {features}\n\n"
            "LOLO seed file: `lolo_random_seed_10.txt`"
        ),
        results=(
            "### Baseline Comparison\n\n"
            f"{df_to_markdown_table(comparison_df)}\n\n"
            "![Native vs Imputed CatBoost](37_catboost_imputation_comparison.png)\n\n"
            "### Chronological Imputed CatBoost Importances\n\n"
            f"{df_to_markdown_table(imp_df.head(15).round(4))}\n\n"
            "![Imputed CatBoost Importances](37_catboost_imputed_importances.png)\n\n"
            "### Seeded 10-Lake LOLO Results\n\n"
            f"{df_to_markdown_table(lolo_df)}\n\n"
            f"**Average LOLO R² (10 lakes):** {lolo_avg_r2:.4f}"
        ),
        next_step=(
            "If MissForest-imputed CatBoost improves LOLO enough to justify the extra preprocessing cost, extend the comparison to the 100-lake seeded sample. Otherwise keep the native-missing CatBoost path as the preferred simpler model."
        ),
    )

    report_path = write_canonical_report(
        "37_catboost_imputation.md",
        "Experiment 37: Tuned CatBoost with MissForest Imputation",
        report,
    )
    print(f"\nReport generated at {report_path}")


if __name__ == "__main__":
    main()
