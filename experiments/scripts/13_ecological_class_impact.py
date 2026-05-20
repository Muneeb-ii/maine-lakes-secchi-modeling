import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error

from experiment_utils import ensure_reports_dir, write_markdown_report, df_to_markdown_table, load_data

def prepare_features(train_data, test_data, num_cols, cat_cols):
    if not cat_cols:
        return train_data[num_cols].copy(), test_data[num_cols].copy()
        
    train_cat = train_data[cat_cols].fillna("Unknown")
    test_cat = test_data[cat_cols].fillna("Unknown")
    
    train_encoded = pd.get_dummies(train_cat, drop_first=True)
    test_encoded = pd.get_dummies(test_cat, drop_first=True)
    
    # Align test columns to train columns (in case some categories appear only in train/test)
    test_encoded = test_encoded.reindex(columns=train_encoded.columns, fill_value=0)
    
    X_train = pd.concat([train_data[num_cols], train_encoded], axis=1)
    X_test = pd.concat([test_data[num_cols], test_encoded], axis=1)
    
    return X_train, X_test

def build_model(train_df, test_df, target, num_cols, cat_cols):
    X_train, X_test = prepare_features(train_df, test_df, num_cols, cat_cols)
    y_train = train_df[target]
    y_test = test_df[target]
    
    rf = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)
    
    pred_train = rf.predict(X_train)
    pred_test = rf.predict(X_test)
    
    r2_train = r2_score(y_train, pred_train)
    r2_test = r2_score(y_test, pred_test)
    mae_test = mean_absolute_error(y_test, pred_test)
    rmse_test = np.sqrt(mean_squared_error(y_test, pred_test))
    
    # Store importances mapping
    imp_dict = {feat: imp for feat, imp in zip(X_train.columns, rf.feature_importances_)}
    
    return {
        "MAE": mae_test,
        "RMSE": rmse_test,
        "R2_train": r2_train,
        "R2_test": r2_test,
        "importances": imp_dict
    }

def main():
    reports_dir = ensure_reports_dir()
    
    print("Loading datasets...")
    data = load_data()
    df = data.frame
    
    target = "SECCHI"
    
    # Base configuration
    num_cols = ["LATITUDE", "LONGITUDE", "AREA_ACRES", "DEPTH_MAX_FEET"]
    
    # 1. Filter dataset strictly using base geographical requirements & target & time
    subset_cols = [target, "SAMPDATE"] + num_cols
    model_df = df.dropna(subset=subset_cols).copy()
    
    model_df["year"] = model_df["SAMPDATE"].dt.year
    model_df["month"] = model_df["SAMPDATE"].dt.month
    base_features = ["year", "month", "LATITUDE", "LONGITUDE", "AREA_ACRES", "DEPTH_MAX_FEET"]
    
    # Create a simple depth_category based on DEPTH_MAX_FEET threshold from Exp 9
    model_df["DEPTH_CATEGORY"] = np.where(model_df["DEPTH_MAX_FEET"] >= 34.0, "Deep", "Shallow")
    
    total_valid_rows = len(model_df)
    print(f"Total rows after strict geographic filtering: {total_valid_rows}")
    
    # 2. Strict Chronological Sort & Split
    model_df = model_df.sort_values(by="SAMPDATE").reset_index(drop=True)
    split_idx = int(len(model_df) * 0.8)
    
    train_df = model_df.iloc[:split_idx].copy()
    test_df = model_df.iloc[split_idx:].copy()
    
    # 3. Model Definitions
    # A: baseline geography + time only
    # B: baseline + trophic category
    # C: baseline + depth category (deep vs shallow)
    # D: baseline + trophic + depth category (no regional drainage/county)
    # E: baseline + trophic + depth category + major drainage (reduced regional context)
    models_config = {
        "A": {"name": "Baseline (geo + time)", "cat_cols": []},
        "B": {"name": "+ TROPHIC_CATEGORY", "cat_cols": ["TROPHIC_CATEGORY"]},
        "C": {"name": "+ DEPTH_CATEGORY", "cat_cols": ["DEPTH_CATEGORY"]},
        "D": {
            "name": "+ TROPHIC_CATEGORY + DEPTH_CATEGORY",
            "cat_cols": ["TROPHIC_CATEGORY", "DEPTH_CATEGORY"],
        },
        "E": {
            "name": "+ TROPHIC_CATEGORY + DEPTH_CATEGORY + MAJOR_DRAINAGE",
            "cat_cols": ["TROPHIC_CATEGORY", "DEPTH_CATEGORY", "MAJOR_DRAINAGE"],
        },
    }
    
    results = {}
    for mod_id, config in models_config.items():
        print(f"Evaluating Model {mod_id}: {config['name']}...")
        results[mod_id] = build_model(train_df, test_df, target, base_features, config["cat_cols"])
        
    # 4. Generate Output Tables
    summary_data = []
    for mod_id, config in models_config.items():
        res = results[mod_id]
        summary_data.append({
            "Model": mod_id,
            "Features added": config["name"],
            "MAE": round(res["MAE"], 4),
            "RMSE": round(res["RMSE"], 4),
            "R2_train": round(res["R2_train"], 4),
            "R2_test": float(round(res["R2_test"], 4))
        })
        
    summary_df = pd.DataFrame(summary_data)
    
    # Collect Top Feature Importances (Compare Model A and E)
    imp_a = results["A"]["importances"]
    imp_e = results["E"]["importances"]
    # We want to show top 15 features of Model E, and trace what they were in Model A
    # Sum up one-hot encoded categories for a cleaner view? The user requests raw top 15 list.
    e_sorted = sorted(imp_e.items(), key=lambda item: item[1], reverse=True)[:15]
    
    imp_rows = []
    for feat, e_val in e_sorted:
        a_val = imp_a.get(feat, 0.0)  # Will be 0 if the feature only exists in Model E
        imp_rows.append({
            "Feature": feat,
            "Importance (Model A)": round(a_val, 4) if feat in imp_a else "-",
            "Importance (Model E)": round(e_val, 4)
        })
        
    imp_compare_df = pd.DataFrame(imp_rows)
    
    # Visualizing the Top E Features
    # Create a nice horizontal bar chart for the top features in Model E
    top_d_features = [row["Feature"] for row in imp_rows]
    top_d_values = [row["Importance (Model E)"] for row in imp_rows]
    
    plt.figure(figsize=(10, 6))
    sns.barplot(x=top_d_values, y=top_d_features, color="#2b83ba")
    plt.title("Top 15 Feature Importances (Model E: Baseline + TROPHIC_CATEGORY + DEPTH_CATEGORY + MAJOR_DRAINAGE)")
    plt.xlabel("Gini Importance")
    plt.ylabel("Feature")
    plot_path = reports_dir / "13_feature_importance_mod_d.png"
    plt.savefig(plot_path, bbox_inches="tight")
    plt.close()

    # 5. Build Markdown Interpretation
    r2_a = summary_df[summary_df["Model"] == "A"]["R2_test"].iloc[0]
    r2_b = summary_df[summary_df["Model"] == "B"]["R2_test"].iloc[0]
    r2_c = summary_df[summary_df["Model"] == "C"]["R2_test"].iloc[0]
    r2_d = summary_df[summary_df["Model"] == "D"]["R2_test"].iloc[0]
    r2_e = summary_df[summary_df["Model"] == "E"]["R2_test"].iloc[0]
    
    delta_b = round(r2_b - r2_a, 4)
    delta_c = round(r2_c - r2_a, 4)
    delta_d = round(r2_d - r2_a, 4)
    delta_e = round(r2_e - r2_a, 4)
    
    sections = [
        ("Data Subset Description", 
         f"Tested identical datasets across all models to quantify the specific predictive power generated by identifying structural ecological classes compared to exclusively mapping time and geography.\n\n"
         f"- **Number of valid rows:** {total_valid_rows:,} total rows retained after absolutely strictly filtering down to missing-free data for target (`SECCHI`), time (`SAMPDATE`), and base geographic features.\n"
         f"- **Chronological Array:** The strict 80/20 train/test chronological split was processed identically. Training covers the first 80%, out-of-time testing assesses the final recent 20%."
        ),
        
        ("Model Performance Comparison (A-E)",
         f"{df_to_markdown_table(summary_df)}"
        ),
        
        ("Incremental Benefit Summary",
         f"- Adding `TROPHIC_CATEGORY` identically to the basic geographical representation (Model B) modified the R²_test from {r2_a} to {r2_b} (Δ = {delta_b:+}).\n"
         f"- Adding `DEPTH_CATEGORY` individually (Model C, separating strictly deep versus shallow) shifted the test explained variance by a delta of {delta_c:+}.\n"
         f"- Combining both ecological classifications without regional context (Model D: `TROPHIC_CATEGORY` + `DEPTH_CATEGORY`) changed the test variance explanation by {delta_d:+} relative to the baseline.\n"
         f"- Incorporating a reduced set of regional descriptors (Model E: `TROPHIC_CATEGORY`, `DEPTH_CATEGORY`, `MAJOR_DRAINAGE`) shifted the testing accuracy by {delta_e:+}. Tracking the gap between R²_train and R²_test allows measuring whether adding drainage geography yields genuine out-of-time predictive patterns or mostly introduces overfitting to historical trends."
        ),
        
        ("Feature Importance Comparison (Top 15 in Model E)",
         f"{df_to_markdown_table(imp_compare_df)}\n\n"
         "![Top Model E Features](13_feature_importance_mod_d.png)"
        ),
    ]
    
    report_path = write_markdown_report("13_ecological_class_impact.md", "Experiment 13: Ecological Classes vs Geography", sections)
    print(f"Report generated at {report_path}")

if __name__ == "__main__":
    main()
