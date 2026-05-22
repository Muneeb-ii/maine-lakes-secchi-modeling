from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import SimpleImputer, KNNImputer, IterativeImputer
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import BayesianRidge
from tqdm.auto import tqdm

from experiment_utils import (
    CanonicalReport,
    ensure_reports_dir,
    write_canonical_report,
    df_to_markdown_table,
    load_data,
)

EXPERIMENT_ID = "36"
REPORT_FILENAME = "36_imputation_benchmark.md"
REPORT_TITLE = "Experiment 36: Numerical Chemistry Imputation Benchmark"
RANDOM_SEED = 42
TRAIN_BENCHMARK_ROWS = 6000
TEST_BENCHMARK_ROWS = 2000
MASK_FRACTION = 0.2


def select_benchmark_slice(df: pd.DataFrame, n_rows: int, seed: int) -> pd.DataFrame:
    if len(df) <= n_rows:
        return df.copy().reset_index(drop=True)
    return df.sample(n=n_rows, random_state=seed).sort_values("SAMPDATE").reset_index(drop=True)


def build_masked_test(test_df: pd.DataFrame, chem_features: list[str], rng: np.random.Generator) -> tuple[pd.DataFrame, dict[str, np.ndarray]]:
    masked_df = test_df.copy()
    masked_positions: dict[str, np.ndarray] = {}
    for feature in chem_features:
        observed_idx = np.flatnonzero(masked_df[feature].notna().to_numpy())
        if len(observed_idx) == 0:
            masked_positions[feature] = np.array([], dtype=int)
            continue
        n_mask = max(1, int(len(observed_idx) * MASK_FRACTION))
        chosen = np.sort(rng.choice(observed_idx, size=n_mask, replace=False))
        masked_df.loc[chosen, feature] = np.nan
        masked_positions[feature] = chosen
    return masked_df, masked_positions


def build_imputers() -> dict[str, object]:
    return {
        "Median": SimpleImputer(strategy="median"),
        "KNN": KNNImputer(n_neighbors=5, weights="distance"),
        "Iterative": IterativeImputer(
            estimator=BayesianRidge(),
            max_iter=10,
            random_state=RANDOM_SEED,
            sample_posterior=False,
        ),
        "MissForest": IterativeImputer(
            estimator=RandomForestRegressor(
                n_estimators=30,
                max_depth=10,
                random_state=RANDOM_SEED,
                n_jobs=-1,
            ),
            max_iter=3,
            random_state=RANDOM_SEED,
        ),
    }


def metric_frame(true_values: np.ndarray, pred_values: np.ndarray, feature: str, method: str) -> dict[str, float | str | int]:
    errors = pred_values - true_values
    mae = float(np.mean(np.abs(errors)))
    rmse = float(np.sqrt(np.mean(errors ** 2)))
    mean_abs_true = float(np.mean(np.abs(true_values)))
    norm_mae = mae / mean_abs_true if mean_abs_true > 0 else np.nan
    return {
        "method": method,
        "feature": feature,
        "n_masked": int(len(true_values)),
        "mae": mae,
        "rmse": rmse,
        "norm_mae": norm_mae,
    }


def main() -> None:
    reports_dir = ensure_reports_dir()
    print("Loading dataset...")
    df = load_data().frame

    num_cols = ["LATITUDE", "LONGITUDE", "AREA_ACRES", "DEPTH_MAX_FEET"]
    chem_features = ["DOMAX", "DOMIN", "TPEC", "TPBG", "CHLA", "PH", "COLOR", "CONDUCT", "ALK"]
    valid_chems = [c for c in chem_features if c in df.columns]
    feature_cols = ["year", "month"] + num_cols + valid_chems

    benchmark_df = df.dropna(subset=["SAMPDATE"] + num_cols).copy()
    benchmark_df = benchmark_df.sort_values("SAMPDATE").reset_index(drop=True)

    split_idx = int(len(benchmark_df) * 0.8)
    train_df = select_benchmark_slice(benchmark_df.iloc[:split_idx].copy(), TRAIN_BENCHMARK_ROWS, RANDOM_SEED)
    test_df = select_benchmark_slice(benchmark_df.iloc[split_idx:].copy(), TEST_BENCHMARK_ROWS, RANDOM_SEED)

    rng = np.random.default_rng(RANDOM_SEED)
    masked_test_df, masked_positions = build_masked_test(test_df, valid_chems, rng)

    X_train = train_df[feature_cols].copy()
    X_test_masked = masked_test_df[feature_cols].copy()
    X_test_true = test_df[feature_cols].copy()

    print(f"Benchmark train rows: {len(X_train):,}")
    print(f"Benchmark test rows: {len(X_test_true):,}")
    print(f"Chemistry features benchmarked: {valid_chems}")

    per_feature_rows: list[dict[str, float | str | int]] = []
    overall_rows: list[dict[str, float | str | int]] = []

    imputers = build_imputers()
    for method_name, imputer in tqdm(imputers.items(), desc="Imputation benchmark", unit="method"):
        print(f"\nFitting {method_name}...")
        train_imputed = pd.DataFrame(imputer.fit_transform(X_train), columns=feature_cols, index=X_train.index)
        _ = train_imputed  # explicit fit result retained for parity/debugging
        test_imputed = pd.DataFrame(imputer.transform(X_test_masked), columns=feature_cols, index=X_test_masked.index)

        all_true = []
        all_pred = []
        for feature in valid_chems:
            idx = masked_positions[feature]
            if len(idx) == 0:
                continue
            true_vals = X_test_true.iloc[idx][feature].to_numpy(dtype=float)
            pred_vals = test_imputed.iloc[idx][feature].to_numpy(dtype=float)
            row = metric_frame(true_vals, pred_vals, feature, method_name)
            per_feature_rows.append(row)
            all_true.append(true_vals)
            all_pred.append(pred_vals)

        true_concat = np.concatenate(all_true)
        pred_concat = np.concatenate(all_pred)
        overall = metric_frame(true_concat, pred_concat, "Overall", method_name)
        overall_rows.append(overall)

    per_feature_df = pd.DataFrame(per_feature_rows)
    overall_df = pd.DataFrame(overall_rows).sort_values(by=["rmse", "mae"], ascending=[True, True]).reset_index(drop=True)
    pivot_rmse = per_feature_df.pivot(index="feature", columns="method", values="rmse").loc[valid_chems]

    plt.figure(figsize=(10, 6))
    sns.barplot(data=overall_df, x="method", y="rmse", palette="deep")
    plt.title("Imputation Benchmark Overall RMSE")
    plt.xlabel("Imputation method")
    plt.ylabel("RMSE on masked observed chemistry values")
    overall_plot = reports_dir / "36_imputation_overall_rmse.png"
    plt.savefig(overall_plot, bbox_inches="tight")
    plt.close()

    plt.figure(figsize=(10, 6))
    sns.heatmap(pivot_rmse, annot=True, fmt=".3f", cmap="YlGnBu")
    plt.title("Per-Feature RMSE by Imputation Method")
    plt.xlabel("Imputation method")
    plt.ylabel("Chemistry feature")
    heatmap_plot = reports_dir / "36_imputation_feature_rmse_heatmap.png"
    plt.savefig(heatmap_plot, bbox_inches="tight")
    plt.close()

    best_method = overall_df.iloc[0]["method"]
    report = CanonicalReport(
        objective=(
            "Benchmark numerical chemistry imputers before pairing any of them with the final Secchi prediction model. "
            "This experiment focuses only on how well each method reconstructs masked observed chemistry values."
        ),
        method=(
            "Use a chronological 80/20 split on rows with valid temporal and geographic base features, then cap the benchmark to a reproducible sample of "
            f"{TRAIN_BENCHMARK_ROWS:,} training rows and {TEST_BENCHMARK_ROWS:,} test rows for runtime control. Randomly mask {MASK_FRACTION:.0%} of originally observed values in each chemistry feature on the test slice using seed 42. Fit each imputer on the training slice only, transform the masked test slice, and compare imputed values against the true hidden values."
        ),
        parameters=(
            f"Chemistry features benchmarked (CHLA included for imputation-only evaluation): {valid_chems}\n\n"
            "Imputation methods:\n"
            "- `Median`: `SimpleImputer(strategy='median')`\n"
            "- `KNN`: `KNNImputer(n_neighbors=5, weights='distance')`\n"
            "- `Iterative`: `IterativeImputer(estimator=BayesianRidge(), max_iter=10, random_state=42)`\n"
            "- `MissForest`: `IterativeImputer(estimator=RandomForestRegressor(n_estimators=30, max_depth=10, random_state=42, n_jobs=-1), max_iter=3, random_state=42)`\n\n"
            f"Feature columns supplied to imputers: {feature_cols}"
        ),
        results=(
            "### Overall Reconstruction Ranking\n\n"
            f"{df_to_markdown_table(overall_df.round(4))}\n\n"
            "![Overall Imputation RMSE](36_imputation_overall_rmse.png)\n\n"
            "### Per-Feature Reconstruction Metrics\n\n"
            f"{df_to_markdown_table(per_feature_df.round(4), max_rows=100)}\n\n"
            "![Per-Feature Imputation RMSE](36_imputation_feature_rmse_heatmap.png)"
        ),
        next_step=(
            f"Carry the leading imputation method(s), currently `{best_method}`, into a downstream CatBoost comparison against the native-missing baseline. "
            "The CatBoost experiment should still exclude CHLA from the Secchi prediction feature set even though CHLA was allowed here for imputation evaluation."
        ),
    )

    report_path = write_canonical_report(REPORT_FILENAME, REPORT_TITLE, report)
    print(f"\nReport generated at {report_path}")


if __name__ == "__main__":
    main()
