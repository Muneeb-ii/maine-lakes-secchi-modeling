import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from tqdm.auto import tqdm

from experiment_utils import ensure_reports_dir, write_markdown_report, df_to_markdown_table, load_data

def evaluate_model(y_true, y_pred, depth):
    mae = mean_absolute_error(y_true, y_pred)
    mse = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)
    
    variance = np.var(y_true)
    if variance == 0:
        r2 = 0.0
    else:
        r2 = r2_score(y_true, y_pred)
    
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

def main():
    reports_dir = ensure_reports_dir()
    print("Loading datasets...")
    data = load_data()
    df = data.frame
    
    target = "SECCHI"
    
    base_geo = ["LATITUDE", "LONGITUDE", "AREA_ACRES", "DEPTH_MAX_FEET"]
    # Drop rows without required targets
    subset_cols = [target, "SAMPDATE"] + base_geo
    model_df = df.dropna(subset=subset_cols).copy()
    
    model_df["year"] = model_df["SAMPDATE"].dt.year
    model_df["month"] = model_df["SAMPDATE"].dt.month
    base_features = ["year", "month"] + base_geo
    
    model_df = model_df.sort_values(by="SAMPDATE").reset_index(drop=True)
    
    min_year = int(model_df["year"].min())
    max_year = int(model_df["year"].max())
    
    # We will test three separate epochs to validate if the "Golden Cut-Off" is a universal rule
    target_test_windows = [
        {"test_start": max_year - 2, "test_end": max_year},           # 2020-2022
        {"test_start": max_year - 5, "test_end": max_year - 3},       # 2017-2019
        {"test_start": max_year - 8, "test_end": max_year - 6}        # 2014-2016
    ]
    
    all_iteration_results = []
    
    for sweep in tqdm(target_test_windows, desc="Backward sweeps", unit="sweep"):
        test_start = sweep["test_start"]
        test_end = sweep["test_end"]
        sweep_name = f"{test_start}-{test_end} Forecast"
        
        test_mask = (model_df["year"] >= test_start) & (model_df["year"] <= test_end)
        test_df = model_df[test_mask]
        
        if len(test_df) == 0:
            print(f"Skipping {sweep_name} due to zero test data.")
            continue
            
        X_test = test_df[base_features]
        y_test = test_df[target]
        depth_test = test_df["DEPTH_MAX_FEET"]
        
        # Base configuration: train window stops rigidly directly behind the test start point
        train_end = test_start - 1
        train_start = train_end - 2
        
        iteration_counter = 1
        prev_train_rows = None

        total_iterations = max(0, ((train_start - min_year) // 3) + 1)
        iteration_bar = tqdm(total=total_iterations, desc=sweep_name, unit="fit", leave=False)

        while train_start >= min_year:
            train_mask = (model_df["year"] >= train_start) & (model_df["year"] <= train_end)
            train_df = model_df[train_mask]
            
            if len(train_df) < 50:
                # Skip if there's less than 50 rows in the total historical bounds found
                train_start -= 3
                iteration_bar.update(1)
                continue

            # Stop when expanding backward no longer adds rows (sparse/absent years left of the window).
            if prev_train_rows is not None and len(train_df) == prev_train_rows:
                print(
                    f"Stopping {sweep_name}: train row count plateau at {len(train_df)} "
                    f"(no new data in years before {train_start})."
                )
                break

            X_train = train_df[base_features]
            y_train = train_df[target]
            
            print(f"Running {sweep_name} Iteration {iteration_counter} (Train: {train_start}-{train_end})")
            
            rf = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
            rf.fit(X_train, y_train)
            
            pred_test = rf.predict(X_test)
            metrics = evaluate_model(y_test, pred_test, depth_test)
            
            horizon_years = train_end - train_start + 1
            
            all_iteration_results.append({
                "Sweep": sweep_name,
                "Iteration": f"{iteration_counter}",
                "Historical Horizon (Years)": horizon_years,
                "Train Window": f"{train_start}-{train_end}",
                "Train Rows": len(train_df),
                "Test Rows": len(test_df),
                "MAE": round(metrics["MAE"], 4),
                "RMSE": round(metrics["RMSE"], 4),
                "R2": round(metrics["R2"], 4),
                "MAE_Norm": round(metrics["MAE_Norm"], 4),
                "RMSE_Norm": round(metrics["RMSE_Norm"], 4)
            })

            prev_train_rows = len(train_df)

            # Expand backwards progressively into older eras by capturing 3 more legacy years
            train_start -= 3
            iteration_counter += 1
            iteration_bar.update(1)

        iteration_bar.close()
            
    results_df = pd.DataFrame(all_iteration_results)
    
    # Plotting backward expansion R2 (Cross Era Validation)
    plt.figure(figsize=(12, 6))
    
    sns.lineplot(data=results_df, x="Historical Horizon (Years)", y="R2", hue="Sweep", marker="o", linewidth=2)
    
    # Auto-zoom the Y-axis tightly around the variance
    min_r2 = results_df["R2"].min()
    max_r2 = results_df["R2"].max()
    margin = (max_r2 - min_r2) * 0.1
    if margin == 0: margin = 0.05
    plt.ylim(min_r2 - margin, max_r2 + margin)
    
    plt.title("R² Performance by Expanding Historical Memory Backwards (Cross-Era Validation)")
    plt.xlabel("Historical Training Content Size (Years)")
    plt.ylabel(f"Test Set R²")
    
    plt.tight_layout()
    plot_path = reports_dir / "17_backward_expanding_r2.png"
    plt.savefig(plot_path, bbox_inches="tight")
    plt.close()

    sections = [
        ("Objective", "Assess whether adding progressively older training years helps or hurts out-of-sample Secchi predictions on fixed recent test blocks (**ecological drift / stale history**). **Part II** applies the same backward-expanding design to three eras (2020–2022, 2017–2019, 2014–2016) to see if the pattern is consistent across forecast targets."),
        ("Methodology", f"1. **Multiple Fixed Testing Bounds**: Three separate test sets were anchored rigidly covering distinct eras (2020-2022, 2017-2019, 2014-2016).\n2. **Backward Training Expansion**: For each test boundary, the model started training exclusively on its direct immediate 3 preceding years. Iterations expand backward in 3-year steps until either the calendar hits the dataset minimum or **training row count stops increasing** (no observations in the newly included past years), avoiding redundant refits on identical data."),
        ("Multi-Era Backward-Expanding Forecasts", f"{df_to_markdown_table(results_df)}\n\n![R2 Multi-Era Progression](17_backward_expanding_r2.png)"),
        (
            "Interpretations",
            "### Findings\n"
            "Results **depend on which test era** is held fixed; the table does not support a single rule that “more history always helps” or “always hurts.”\n\n"
            "- **2020–2022 forecast:** $R^2$ is **highest** for the **shortest** train window (iteration 1: train 2017–2019, $R^2 \\approx 0.713$). "
            "Very long histories sit **lower** on average (roughly **0.69–0.70** $R^2$ in the longest horizons), but the series is **not strictly monotone**—some mid-length windows outperform neighboring steps.\n"
            "- **2017–2019 forecast:** The 3-year-only window is **not** best. $R^2$ **rises** when more past years are included and peaks near **iteration 9** (train 1990–2016, $R^2 \\approx 0.676$) versus iteration 1 ($R^2 \\approx 0.656$).\n"
            "- **2014–2016 forecast:** Again, minimal history is not optimal: the best row is **iteration 4** (train 2002–2013, 12-year span, $R^2 \\approx 0.724$) versus iteration 1 ($R^2 \\approx 0.711$). Performance **softens** somewhat if history is pushed even further back beyond that peak.\n\n"
            "Overall, older data sometimes **adds signal** and sometimes **dilutes** it, depending on era and horizon—consistent with **context-dependent** drift or non-stationarity, not a universal “short memory wins” law.\n\n"
            "### Moving Forward\n"
            "- **Choose training span using the backward-expanding curve (or time-based CV)** for the era you care about; avoid a fixed global cutoff not supported by these sweeps.\n"
            "- **Document sweep-specific best windows** from the table when arguing for truncation.\n"
            "- Optional: blocked CV, other learners, or spatial strata if drift differs by region or lake type.",
        ),
    ]
    
    report_path = write_markdown_report("17_backward_expanding.md", "Experiment 17: Backward Expanding (Ecological Drift)", sections)
    print(f"Report generated at {report_path}")

if __name__ == "__main__":
    main()
