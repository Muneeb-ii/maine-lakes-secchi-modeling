from __future__ import annotations

import textwrap
import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeRegressor
from sklearn.impute import SimpleImputer

from experiment_utils import (
    LoadedData,
    df_to_markdown_table,
    load_data,
    write_markdown_report,
)


def compute_nonlinear_importance(df: pd.DataFrame) -> pd.DataFrame:
    """Use a Decision Tree to compute non-linear feature importance for SECCHI."""
    if "SECCHI" not in df.columns:
        return pd.DataFrame()

    # Select highly numeric columns
    numeric_df = df.select_dtypes(include=["number"]).copy()
    
    # Drop columns that shouldn't be predictive or are entirely missing
    drop_cols = ["date", "year", "month"]
    for col in drop_cols:
        if col in numeric_df.columns:
            numeric_df = numeric_df.drop(columns=[col])
            
    if "SECCHI" not in numeric_df.columns:
        return pd.DataFrame()

    # Drop target for X, isolate for y
    # To keep simple for EDA, drop rows with missing SECCHI (near 0)
    data = numeric_df.dropna(subset=["SECCHI"])
    X = data.drop(columns=["SECCHI"])
    y = data["SECCHI"]
    
    feature_names = X.columns.tolist()
    if not feature_names:
        return pd.DataFrame()

    # Impute missing values with the median for the Decision Tree
    imputer = SimpleImputer(strategy="median")
    X_imputed = imputer.fit_transform(X)

    # Train a simple Decision Tree Regressor
    # Max depth limited to prevent extreme overfitting and focus on main architectural splits
    dt = DecisionTreeRegressor(max_depth=5, random_state=42)
    dt.fit(X_imputed, y)

    # Extract feature importances
    importances = dt.feature_importances_
    
    imp_df = pd.DataFrame({
        "predictor": feature_names,
        "tree_importance": importances
    })
    
    imp_df = imp_df[imp_df["tree_importance"] > 0]
    imp_df = imp_df.sort_values("tree_importance", ascending=False).reset_index(drop=True)
    return imp_df


def test_basic_interactions(df: pd.DataFrame) -> pd.DataFrame:
    """Test 2-way interactions between the most important numerical features and SECCHI."""
    if "SECCHI" not in df.columns:
        return pd.DataFrame()

    numeric_df = df.select_dtypes(include=["number"])
    
    # To avoid combinatorial explosion, let's select known prominent variables
    # CHLA (Chlorophyll), TMIN/TMAX (Temperature), COLOR, OXIC
    vars_of_interest = ["CHLA", "TMIN", "TMAX", "COLOR", "OXIC", "TPEC", "SCHMIDT", "DOMAX"]
    available_vars = [v for v in vars_of_interest if v in numeric_df.columns]
    
    if len(available_vars) < 2:
         return pd.DataFrame()
         
    interactions = []
    y = numeric_df["SECCHI"]
    
    # Loop over pairs
    for i in range(len(available_vars)):
        for j in range(i + 1, len(available_vars)):
            v1 = available_vars[i]
            v2 = available_vars[j]
            
            # Create interaction term (v1 * v2)
            combo = pd.DataFrame({
                "y": y,
                "v1": numeric_df[v1],
                "v2": numeric_df[v2],
                "interaction": numeric_df[v1] * numeric_df[v2]
            }).dropna()
            
            if len(combo) < 50:
                continue
                
            y_clean = combo["y"]
            x_inter = combo["interaction"]
            
            r = float(np.corrcoef(x_inter, y_clean)[0, 1])
            
            interactions.append({
                "interaction_term": f"{v1} * {v2}",
                "n": len(combo),
                "pearson_r": r,
                "abs_pearson_r": abs(r)
            })
            
    int_df = pd.DataFrame(interactions)
    if not int_df.empty:
        int_df = int_df.sort_values("abs_pearson_r", ascending=False).reset_index(drop=True)
    return int_df

def main() -> None:
    data: LoadedData = load_data()
    df = data.frame
    
    tree_imp_df = compute_nonlinear_importance(df)
    interaction_df = test_basic_interactions(df)
    
    overview_text = textwrap.dedent(
        f"""
        This report analyzes non-linear feature importances utilizing a Decision Tree Regressor,
        and tests simple bivariate multiplier interactions (e.g., Variable A * Variable B).
        
        Unlike previous reports that only checked linear Pearson correlations, 
        a Decision Tree evaluates how features segment the target variable (`SECCHI`) 
        across specific thresholds.
        """
    ).strip()
    
    if not tree_imp_df.empty:
        tree_md = df_to_markdown_table(tree_imp_df, round_decimals=4)
    else:
        tree_md = "_No non-linear importance could be calculated._"
        
    if not interaction_df.empty:
        # Show top 15 interactions
        int_top = interaction_df.head(15)[["interaction_term", "pearson_r", "n"]]
        interaction_md = df_to_markdown_table(int_top, round_decimals=3)
    else:
        interaction_md = "_No sufficient data to calculate overlapping interaction terms._"
        
    sections = [
        ("Overview", overview_text),
        ("Non-Linear Feature Importance (Decision Tree, max_depth=5)", tree_md),
        ("Top 2-Way Multiplier Interactions with Default Prominent Features", interaction_md),
    ]
    
    report_path = write_markdown_report(
        filename="08_nonlinear_and_interactions.md",
        title="Secchi Dataset – Non-Linear & Interaction Analysis",
        sections=sections,
    )
    
    print(f"Wrote non-linear and interaction report to {report_path}")

if __name__ == "__main__":
    main()
