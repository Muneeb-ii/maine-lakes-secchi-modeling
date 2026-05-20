import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import warnings
from tqdm.auto import tqdm

from experiment_utils import (
    CanonicalReport,
    ensure_reports_dir,
    write_canonical_report,
    df_to_markdown_table,
    load_data,
)

warnings.filterwarnings("ignore")

# Identical RF settings for global and local models so comparisons reflect data scope, not tuning.
RF_KWARGS = dict(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)


def evaluate_model(y_true, y_pred, depth):
    mae = mean_absolute_error(y_true, y_pred)
    mse = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)
    
    variance = np.var(y_true)
    r2 = 0.0 if variance == 0 else r2_score(y_true, y_pred)
    
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
        "RMSE_Norm": rmse_norm
    }

def aggregate_metrics(metrics_list):
    if not metrics_list:
        return {}
    return pd.DataFrame(metrics_list).mean().to_dict()

def main():
    reports_dir = ensure_reports_dir()
    print("Loading dataset...")
    df = load_data().frame
    
    target = "SECCHI"
    base_geo = ["LATITUDE", "LONGITUDE", "AREA_ACRES", "DEPTH_MAX_FEET"]
    req_cols = [target, "SAMPDATE", "MIDAS"] + base_geo
    
    model_df = df.dropna(subset=req_cols).copy()
    model_df["year"] = model_df["SAMPDATE"].dt.year
    model_df["month"] = model_df["SAMPDATE"].dt.month
    base_features = ["year", "month"] + base_geo
    
    model_df = model_df.sort_values(by="SAMPDATE").reset_index(drop=True)
    
    lake_counts = model_df["MIDAS"].value_counts()
    
    # ------------------- PHASE I: DATA-RICH -------------------
    print("\n[Phase I] Analyzing Data-Rich Lakes...")
    rich_lakes = lake_counts[lake_counts >= 500].head(50).index.tolist()
    
    rich_local_metrics = []
    rich_global_metrics = []
    
    for midas in tqdm(rich_lakes, desc="Data-rich lakes", unit="lake"):
        lake_df = model_df[model_df["MIDAS"] == midas]
        
        split_idx_local = int(len(lake_df) * 0.8)
        train_lake = lake_df.iloc[:split_idx_local]
        test_lake = lake_df.iloc[split_idx_local:]
        
        if len(test_lake) == 0:
            continue

        X_local_train = train_lake[base_features]
        y_local_train = train_lake[target]
        X_local_test = test_lake[base_features]
        y_local_test = test_lake[target]
        depth_local_test = test_lake["DEPTH_MAX_FEET"]

        # Local model + LOLO global (train on all rows except this lake); append only if both succeed.
        try:
            rf_local = RandomForestRegressor(**RF_KWARGS)
            rf_local.fit(X_local_train, y_local_train)
            pred_local = rf_local.predict(X_local_test)
            m_local = evaluate_model(y_local_test, pred_local, depth_local_test)

            global_train_lolo = model_df[model_df["MIDAS"] != midas]
            X_global_train = global_train_lolo[base_features]
            y_global_train = global_train_lolo[target]

            rf_global = RandomForestRegressor(**RF_KWARGS)
            rf_global.fit(X_global_train, y_global_train)
            pred_global = rf_global.predict(X_local_test)
            m_global = evaluate_model(y_local_test, pred_global, depth_local_test)

            rich_local_metrics.append(m_local)
            rich_global_metrics.append(m_global)
        except Exception:
            continue
        
    agg_rich_local = aggregate_metrics(rich_local_metrics)
    agg_rich_global = aggregate_metrics(rich_global_metrics)
    
    # ------------------- PHASE II: DATA-POOR -------------------
    print("\n[Phase II] Analyzing Data-Poor Lakes (Transfer Validation)...")
    poor_lakes = lake_counts[(lake_counts >= 15) & (lake_counts <= 40)].head(50).index.tolist()
    
    poor_local_metrics = []
    poor_global_metrics = []
    
    for midas in tqdm(poor_lakes, desc="Data-poor lakes", unit="lake"):
        lake_df = model_df[model_df["MIDAS"] == midas]
        
        split_idx_local = int(len(lake_df) * 0.8)
        train_lake = lake_df.iloc[:split_idx_local]
        test_lake = lake_df.iloc[split_idx_local:]
        
        if len(test_lake) == 0:
            continue

        X_local_train = train_lake[base_features]
        y_local_train = train_lake[target]
        X_local_test = test_lake[base_features]
        y_local_test = test_lake[target]
        depth_local_test = test_lake["DEPTH_MAX_FEET"]

        try:
            rf_local = RandomForestRegressor(**RF_KWARGS)
            rf_local.fit(X_local_train, y_local_train)
            pred_local = rf_local.predict(X_local_test)
            m_local = evaluate_model(y_local_test, pred_local, depth_local_test)

            global_train_lolo = model_df[model_df["MIDAS"] != midas]
            X_global_train = global_train_lolo[base_features]
            y_global_train = global_train_lolo[target]

            rf_global = RandomForestRegressor(**RF_KWARGS)
            rf_global.fit(X_global_train, y_global_train)
            pred_global = rf_global.predict(X_local_test)
            m_global = evaluate_model(y_local_test, pred_global, depth_local_test)

            poor_local_metrics.append(m_local)
            poor_global_metrics.append(m_global)
        except Exception:
            continue
        
    agg_poor_local = aggregate_metrics(poor_local_metrics)
    agg_poor_global = aggregate_metrics(poor_global_metrics)
    
    # Formatting
    rich_table = pd.DataFrame([
        {"Model Scope": "Local (within-lake train)", **agg_rich_local},
        {"Model Scope": "LOLO global (all lakes except target)", **agg_rich_global},
    ]).round(4)

    poor_table = pd.DataFrame([
        {"Model Scope": "Local (within-lake train)", **agg_poor_local},
        {"Model Scope": "LOLO global (all lakes except target)", **agg_poor_global},
    ]).round(4)
    
    # Visual Output: MAE / MAE_Norm comparison
    labels = ["Rich(Local)", "Rich(Global)", "Poor(Local)", "Poor(Global)"]
    mae_scores = [
        agg_rich_local.get("MAE", 0), 
        agg_rich_global.get("MAE", 0), 
        agg_poor_local.get("MAE", 0), 
        agg_poor_global.get("MAE", 0)
    ]
    mae_norm_scores = [
        agg_rich_local.get("MAE_Norm", 0), 
        agg_rich_global.get("MAE_Norm", 0), 
        agg_poor_local.get("MAE_Norm", 0), 
        agg_poor_global.get("MAE_Norm", 0)
    ]
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    colors = ["#3498db", "#2980b9", "#e74c3c", "#c0392b"]
    
    sns.barplot(x=labels, y=mae_scores, palette=colors, ax=axes[0])
    axes[0].set_title("Mean Absolute Error (Raw)")
    for i, v in enumerate(mae_scores):
        axes[0].text(i, v + 0.01, f"{v:.3f}", ha='center', fontweight='bold')
        
    sns.barplot(x=labels, y=mae_norm_scores, palette=colors, ax=axes[1])
    axes[1].set_title("Normalized MAE (Percentage of Depth)")
    for i, v in enumerate(mae_norm_scores):
        axes[1].text(i, v + 0.0005, f"{v:.4f}", ha='center', fontweight='bold')
    
    plt.suptitle("Out-of-Sample Errors (Lower is Better)")
    plt.tight_layout()
    
    plot_path = reports_dir / "18_local_vs_global_mae.png"
    plt.savefig(plot_path)
    plt.close()

    # Visual Output: R2 comparison
    r2_scores = [
        agg_rich_local.get("R2", np.nan),
        agg_rich_global.get("R2", np.nan),
        agg_poor_local.get("R2", np.nan),
        agg_poor_global.get("R2", np.nan),
    ]

    plt.figure(figsize=(10, 6))
    sns.barplot(x=labels, y=r2_scores, palette=colors)
    plt.axhline(0, color="black", linewidth=1, alpha=0.5)
    plt.title("Mean R² Across Held-Out Lake Slices")
    plt.ylabel("Mean per-lake R²")
    for i, v in enumerate(r2_scores):
        if not np.isnan(v):
            plt.text(i, v + 0.05, f"{v:.3f}", ha="center", fontweight="bold")
    r2_plot_path = reports_dir / "18_local_vs_global_r2.png"
    plt.tight_layout()
    plt.savefig(r2_plot_path)
    plt.close()

    rl, rg, pl, pg = agg_rich_local, agg_rich_global, agg_poor_local, agg_poor_global

    def fmt_metric(d, key, nd=4):
        v = d.get(key) if d else None
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return "n/a"
        return f"{float(v):.{nd}f}"

    rich_winner = "Global" if rg.get("MAE", 999) < rl.get("MAE", 999) else "Local"
    poor_winner = "Global" if pg.get("MAE", 999) < pl.get("MAE", 999) else "Local"

    report = CanonicalReport(
        objective=(
            "Compare within-lake chronological training against strict leave-one-lake-out global "
            "training, and measure whether globally pooled knowledge transfers to data-poor lakes."
        ),
        method=(
            "Evaluate two lake cohorts. Data-rich lakes require at least 500 observations and "
            "data-poor lakes require 15 to 40 observations. For each lake, split chronologically "
            "80/20, train a local RandomForest on the lake-only training slice, and compare it "
            "against a global RandomForest trained on all other lakes only."
        ),
        parameters=(
            "- local and global models: `RandomForestRegressor`\n"
            "- `n_estimators=100`\n"
            "- `max_depth=10`\n"
            "- `random_state=42`\n"
            "- feature set: `year`, `month`, `LATITUDE`, `LONGITUDE`, `AREA_ACRES`, `DEPTH_MAX_FEET`\n"
            "- data-rich sample: first 50 lakes with at least 500 observations\n"
            "- data-poor sample: first 50 lakes with 15 to 40 observations"
        ),
        results=(
            "### Data-Rich Lakes\n\n"
            f"{df_to_markdown_table(rich_table)}\n\n"
            "### Data-Poor Lakes\n\n"
            f"{df_to_markdown_table(poor_table)}\n\n"
            "### Diagnostic Notes\n\n"
            f"- Data-rich winner by MAE: {rich_winner}\n"
            f"- Data-poor winner by MAE: {poor_winner}\n"
            f"- Rich global MAE vs local MAE: {fmt_metric(rg, 'MAE', 3)} vs {fmt_metric(rl, 'MAE', 3)}\n"
            f"- Poor global MAE vs local MAE: {fmt_metric(pg, 'MAE', 3)} vs {fmt_metric(pl, 'MAE', 3)}\n\n"
            "![Local vs Global MAE](18_local_vs_global_mae.png)\n\n"
            "![Local vs Global R2](18_local_vs_global_r2.png)"
        ),
        next_step=(
            "Use the transfer-learning outcome to decide whether later chronological and "
            "leave-one-lake-out model families should prioritize lake-specific tuning or pooled "
            "cross-lake structure."
        ),
    )

    report_path = write_canonical_report(
        "18_local_vs_global.md",
        "Experiment 18: Localized Time-Series vs Global Transfer Learning",
        report,
    )
    print(f"Report generated at {report_path}")

if __name__ == "__main__":
    main()
