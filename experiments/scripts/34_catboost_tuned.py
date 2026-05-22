import itertools

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from catboost import CatBoostRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
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
    chem_features = ["DOMAX", "DOMIN", "TPEC", "TPBG", "PH", "COLOR", "CONDUCT", "ALK"]
    valid_chems = [c for c in chem_features if c in df.columns]

    subset_cols = [target, "SAMPDATE", "MIDAS"] + num_cols
    model_df = df.dropna(subset=subset_cols).copy()
    model_df = model_df.sort_values(by="SAMPDATE").reset_index(drop=True)
    features = base_features + valid_chems

    split_idx = int(len(model_df) * 0.8)
    train_df = model_df.iloc[:split_idx].copy()
    test_df = model_df.iloc[split_idx:].copy()

    inner_split_idx = int(len(train_df) * 0.8)
    tune_train_df = train_df.iloc[:inner_split_idx].copy()
    tune_val_df = train_df.iloc[inner_split_idx:].copy()

    X_tune_train = tune_train_df[features]
    y_tune_train = tune_train_df[target]
    X_tune_val = tune_val_df[features]
    y_tune_val = tune_val_df[target]
    depth_val = tune_val_df["DEPTH_MAX_FEET"]

    param_grid = {
        "iterations": [200, 400, 700],
        "depth": [6, 8, 10],
        "learning_rate": [0.03, 0.05, 0.1],
        "l2_leaf_reg": [3, 7, 11],
    }
    combos = list(itertools.product(
        param_grid["iterations"],
        param_grid["depth"],
        param_grid["learning_rate"],
        param_grid["l2_leaf_reg"],
    ))

    print(f"Tuning CatBoost across {len(combos)} parameter combinations...")
    search_rows = []
    best = None

    for iterations, depth, learning_rate, l2_leaf_reg in tqdm(combos, desc="CatBoost tuning", unit="combo"):
        params = {
            "iterations": iterations,
            "depth": depth,
            "learning_rate": learning_rate,
            "l2_leaf_reg": l2_leaf_reg,
            "random_seed": 42,
            "loss_function": "RMSE",
            "eval_metric": "RMSE",
            "verbose": False,
            "allow_writing_files": False,
            "thread_count": -1,
        }
        model = CatBoostRegressor(**params)
        model.fit(X_tune_train, y_tune_train)
        val_pred = model.predict(X_tune_val)
        val_metrics = evaluate_model(y_tune_val, val_pred, depth_val)
        row = {
            **params,
            "val_R2": val_metrics["R2"],
            "val_MAE": val_metrics["MAE"],
            "val_RMSE": val_metrics["RMSE"],
            "val_MAE_Norm": val_metrics["MAE_Norm"],
        }
        search_rows.append(row)
        if best is None or row["val_R2"] > best["val_R2"]:
            best = row

    search_df = pd.DataFrame(search_rows).sort_values(by=["val_R2", "val_MAE"], ascending=[False, True]).reset_index(drop=True)

    print("Best validation configuration:")
    print(search_df.head(1).to_string(index=False))

    best_params = {
        "iterations": int(best["iterations"]),
        "depth": int(best["depth"]),
        "learning_rate": float(best["learning_rate"]),
        "l2_leaf_reg": int(best["l2_leaf_reg"]),
        "random_seed": 42,
        "loss_function": "RMSE",
        "eval_metric": "RMSE",
        "verbose": False,
        "allow_writing_files": False,
        "thread_count": -1,
    }

    print("\nRefitting tuned CatBoost on the full chronological training window...")
    final_model = CatBoostRegressor(**best_params)
    final_model.fit(train_df[features], train_df[target])
    test_pred = final_model.predict(test_df[features])
    test_metrics = evaluate_model(test_df[target], test_pred, test_df["DEPTH_MAX_FEET"])

    importances = final_model.get_feature_importance()
    imp_df = pd.DataFrame({"Feature": features, "Importance": importances}).sort_values(by="Importance", ascending=False).reset_index(drop=True)

    plt.figure(figsize=(10, 6))
    sns.barplot(x="Importance", y="Feature", data=imp_df.head(15), color="forestgreen")
    plt.title("Tuned CatBoost Feature Importances")
    plt.xlabel("Importance")
    importance_path = reports_dir / '34_catboost_tuned_importances.png'
    plt.savefig(importance_path, bbox_inches='tight')
    plt.close()

    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=search_df, x='val_MAE', y='val_R2', hue='depth', size='iterations', palette='viridis')
    plt.title('CatBoost Tuning Search Results')
    plt.xlabel('Validation MAE')
    plt.ylabel('Validation R2')
    search_plot_path = reports_dir / '34_catboost_tuning_search.png'
    plt.savefig(search_plot_path, bbox_inches='tight')
    plt.close()

    sections = [
        (
            'What We Did (Methodology)',
            'We kept the same native-missingness CatBoost setup introduced in Experiment 33, but excluded CHLA from the chemistry inputs before tuning because it provides an overly direct proxy for water clarity. We then added a chronological hyperparameter search inside the training window. '
            'The first 80% of rows remained the outer training slice and the latest 20% remained the untouched test slice. '
            'Inside the outer training slice, we used an 80/20 inner chronological split for tuning so parameter selection did not use the final test period.'
        ),
        (
            'Hyperparameter Search Setup',
            f"Feature set (CHLA excluded): {features}\n\n"
            'Search grid: '
            f"iterations={param_grid['iterations']}, depth={param_grid['depth']}, learning_rate={param_grid['learning_rate']}, l2_leaf_reg={param_grid['l2_leaf_reg']}\n\n"
            f"Total combinations evaluated: {len(combos)}\n\n"
            f"Best configuration: {best_params}"
        ),
        (
            'Chronological Test Results',
            f"- **R-Squared (R²):** {test_metrics['R2']:.4f}\n"
            f"- **Mean Absolute Error (MAE):** {test_metrics['MAE']:.4f} meters\n"
            f"- **Root Mean Squared Error (RMSE):** {test_metrics['RMSE']:.4f} meters\n"
            f"- **Normalized MAE:** {test_metrics['MAE_Norm']:.4f}\n"
            f"- **Normalized RMSE:** {test_metrics['RMSE_Norm']:.4f}"
        ),
        (
            'Search Summary',
            f"{df_to_markdown_table(search_df.head(15).round(4))}\n\n"
            '![CatBoost Tuning Search](34_catboost_tuning_search.png)\n\n'
            f"{df_to_markdown_table(imp_df.head(15).round(4))}\n\n"
            '![Tuned CatBoost Importances](34_catboost_tuned_importances.png)'
        ),
    ]

    report_path = write_markdown_report(
        '34_catboost_tuned.md',
        'Experiment 34: Chronological Hyperparameter Tuning for CatBoost',
        sections,
    )
    print(f"\nReport generated at {report_path}")


if __name__ == '__main__':
    main()
