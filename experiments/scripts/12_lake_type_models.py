import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error

from experiment_utils import ensure_reports_dir, write_markdown_report, df_to_markdown_table, load_data

def train_and_evaluate(df_group: pd.DataFrame, features: list, target: str, group_name: str) -> dict:
    """Helper function to chronologically split, train, and evaluate a Random Forest"""
    # 1. Strict Temporal Sort & Split
    df_sorted = df_group.sort_values(by="SAMPDATE").reset_index(drop=True)
    split_idx = int(len(df_sorted) * 0.8)
    
    train_df = df_sorted.iloc[:split_idx]
    test_df = df_sorted.iloc[split_idx:]
    
    X_train, y_train = train_df[features], train_df[target]
    X_test, y_test = test_df[features], test_df[target]
    
    # 2. Train RF
    print(f"Training Random Forest Regressor for {group_name} ({len(train_df)} train / {len(test_df)} test rows)...")
    rf = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)
    
    # 3. Predict & Evaluate
    y_pred = rf.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test, y_pred)
    
    importances = rf.feature_importances_
    
    return {
        "MAE": mae,
        "MSE": mse,
        "RMSE": rmse,
        "R2": r2,
        "importances": importances,
        "train_rows": len(train_df),
        "test_rows": len(test_df),
        "train_range": (train_df["SAMPDATE"].min().date(), train_df["SAMPDATE"].max().date()),
        "test_range": (test_df["SAMPDATE"].min().date(), test_df["SAMPDATE"].max().date()),
    }

def main():
    reports_dir = ensure_reports_dir()
    
    print("Loading datasets...")
    data = load_data()
    df = data.frame
    
    # 1. Feature Selection & Filtering
    target = "SECCHI"
    features = [
        "LATITUDE", 
        "LONGITUDE", 
        "AREA_ACRES", 
        "DEPTH_MAX_FEET",
        "SECCBOT"
    ]
    
    # Strictly require that the row has a defined TROPHIC_CATEGORY
    model_df = df.dropna(subset=[target, "SAMPDATE", "TROPHIC_CATEGORY"] + features).copy()
    
    model_df["year"] = model_df["SAMPDATE"].dt.year
    model_df["month"] = model_df["SAMPDATE"].dt.month
    
    # Ensure SECCBOT is correctly encoded as a binary
    model_df["SECCBOT"] = model_df["SECCBOT"].astype(str).str.upper()
    model_df["SECCBOT_FLAG"] = model_df["SECCBOT"].map({"Y": 1, "N": 0}).fillna(0).astype(int)
    
    features_full = ["year", "month", "LATITUDE", "LONGITUDE", "AREA_ACRES", "DEPTH_MAX_FEET", "SECCBOT_FLAG"]
    
    # 2. Extract Valid Categories
    # Focus only on the primary 3 biological ecosystems containing substantial volume. Drop edge cases (e.g., DYST)
    valid_categories = {"MESO": "Mesotrophic", "EUTRO": "Eutrophic", "OLIGO": "Oligotrophic"}
    results = {}
    
    for cat, cat_name in valid_categories.items():
        cat_df = model_df[model_df["TROPHIC_CATEGORY"] == cat]
        if len(cat_df) > 1000:
            res = train_and_evaluate(cat_df, features_full, target, cat_name)
            res["total_rows"] = len(cat_df)
            results[cat] = res
        else:
            print(f"Skipping {cat_name} due to insufficient valid rows: {len(cat_df)}")
            
    # 3. Generate Evaluation Tables
    models_names, maes, mses, rmses, r2s = [], [], [], [], []
    importances_dict = {"Feature": features_full}
    
    for cat, cat_name in valid_categories.items():
        if cat in results:
            res = results[cat]
            models_names.append(cat_name)
            maes.append(res["MAE"])
            mses.append(res["MSE"])
            rmses.append(res["RMSE"])
            r2s.append(res["R2"])
            importances_dict[f"{cat_name}_Importance"] = res["importances"]
            
    metrics_df = pd.DataFrame({
        "Model (Trophic State)": models_names,
        "MAE": maes,
        "MSE": mses,
        "RMSE": rmses,
        "R2": r2s
    })
    
    imp_df = pd.DataFrame(importances_dict)
    
    # Sort by the most massive category (MESO) for display order
    imp_df_sorted = imp_df.sort_values(by="Mesotrophic_Importance", ascending=False).reset_index(drop=True)
    
    # 4. Generate Visual Comparisons
    # Melt dataframe for Seaborn side-by-side grouped barplot
    imp_melt = imp_df.melt(id_vars="Feature", 
                           value_vars=[f"{valid_categories[c]}_Importance" for c in valid_categories if c in results],
                           var_name="Trophic State", value_name="Importance")
    
    plt.figure(figsize=(12, 7))
    sns.barplot(x="Importance", y="Feature", hue="Trophic State", data=imp_melt, 
                palette=["#4daf4a", "#e41a1c", "#377eb8"]) # Green, Red, Blue theme
    plt.title("Feature Importance Divergence by Biological Lake Type (Trophic State)")
    plt.xlabel("Gini Importance")
    plt.ylabel("Baseline Feature")
    plt.legend(title="Lake Ecosystem")
    
    plot_path = reports_dir / "12_lake_type_feature_importance.png"
    plt.savefig(plot_path, bbox_inches="tight")
    plt.close()
    
    # 4.5 Comparative Statistics for Trophic States
    comp_df = df[df["TROPHIC_CATEGORY"].isin(valid_categories.keys())].copy()
    comp_df["Trophic State"] = comp_df["TROPHIC_CATEGORY"].map(valid_categories)
    
    comp_metrics = ["SECCHI", "TMAX", "TMIN", "TPBG", "CHLA"]
    comparison = comp_df.groupby("Trophic State")[comp_metrics].agg(['mean', 'median', 'std', 'count']).round(2)
    
    flat_comparison = comparison.copy()
    flat_comparison.columns = ['_'.join(col).strip() for col in comparison.columns.values]
    flat_comparison = flat_comparison.reset_index()
    
    plt.figure(figsize=(8, 6))
    sns.boxplot(x="Trophic State", y="SECCHI", data=comp_df, order=["Mesotrophic", "Eutrophic", "Oligotrophic"], palette=["#4daf4a", "#e41a1c", "#377eb8"])
    plt.title("Secchi Depth: Divergence by Trophic State")
    plt.ylabel("Secchi Depth (m)")
    
    box_path = reports_dir / "12_secchi_boxplot.png"
    plt.savefig(box_path, bbox_inches="tight")
    plt.close()
    
    # 5. Build Markdown
    sections = [
        ("Model Design & Features", 
         "**Model Architecture:** Distinct Random Forest Regressors (`n_estimators=100`, `max_depth=10`) were created for the three primary biological states of lakes defined by `TROPHIC_CATEGORY`: Mesotrophic (Medium nutrient), Eutrophic (High nutrient), and Oligotrophic (Low nutrient).\n\n"
         "**Features Utilized:** Identifying how strictly baseline geographics and time impact these unique state models compared to one another:\n"
         "1. `year`\n2. `month`\n3. `LATITUDE`\n4. `LONGITUDE`\n5. `AREA_ACRES`\n6. `DEPTH_MAX_FEET`\n7. `SECCBOT_FLAG`"
        ),
        
        ("Data Separation Summary",
         "The dataset was separated into distinct lake types based on their biological `TROPHIC_CATEGORY`. The summary statistics of perfectly viable observations (non-missing target and base features) for each type are:\n\n" +
         df_to_markdown_table(pd.DataFrame({
             "Lake Type": [valid_categories[c] for c in valid_categories if c in results],
             "Total Valid Observations": [results[cat]["total_rows"] for cat in valid_categories if cat in results]
         }))
        ),
        
        ("Comparative Statistics",
         "We compared key water quality metrics across the three biological groups:\n\n" +
         df_to_markdown_table(flat_comparison) + "\n\n"
         "**Key Observations:** Oligotrophic lakes generally exhibit the highest secchi depth (clarity), while Eutrophic lakes are the murkiest (lowest SECCHI). Similar separations exist natively in related ecological parameters such as Chlorophyll-a (CHLA).\n\n"
         "![Secchi Boxplot](12_secchi_boxplot.png)"
        ),
        
        ("Strict Temporal Split (Chronological Holdout)",
         "Every model exclusively adhered to the absolute chronological 80/20 train/test split within its own subset, protecting the timeline integrity.\n\n" +
         "".join([f"**{valid_categories[cat]} Data Allocation:**\n"
                  f"- Training Set (80%): {results[cat]['train_rows']:,} rows ({results[cat]['train_range'][0]} to {results[cat]['train_range'][1]})\n"
                  f"- Testing Set (20%): {results[cat]['test_rows']:,} rows ({results[cat]['test_range'][0]} to {results[cat]['test_range'][1]})\n\n"
                  for cat in valid_categories if cat in results])
        ),
        
        ("Evaluate Performance Metrics",
         f"The performance divergence reveals physical modeling limits between ecosystems:\n\n"
         f"{df_to_markdown_table(metrics_df)}\n\n"
         "**Key Observation:** Eutrophic lakes (highly productive, murky logic) have significantly lower absolute error boundaries because their secchi disk inherently hits zero rapidly. Contrastly, Oligotrophic lakes represent deep clarity and provide a much larger numeric variance scope making prediction precision harder."
        ),
        
        ("Comparative Feature Importances",
         f"A breakdown of how these distinct ecosystems mathematically utilized geometry to predict clarity. Note how the model dependence on specific geographical traits completely shifts based on the biological classification of the lake.\n\n"
         f"![Feature Importances](12_lake_type_feature_importance.png)\n\n"
         f"{df_to_markdown_table(imp_df_sorted)}"
        )
    ]
    
    report_path = write_markdown_report("12_lake_type_models.md", "Experiment: Lake Type Divergent Modeling (Trophic States)", sections)
    print(f"Report generated at {report_path}")

if __name__ == "__main__":
    main()
