import pandas as pd
from experiment_utils import load_data, PROJECT_ROOT

def main():
    print("Loading dataset...")
    data = load_data()
    df = data.frame
    
    # We define the chemical features based on the metadata specifications
    chem_features = [
        "TMAX", "TMIN",
        "DOMAX", "DOMIN",
        "MLD", "OXIC", "SCHMIDT",
        "TPEC", "TPBG",
        "CHLA", "PH",
        "COLOR", "CONDUCT", "ALK"
    ]
    
    # Ensure all features exist in the dataframe to avoid key errors
    valid_features = [f for f in chem_features if f in df.columns]
    
    if not valid_features:
        raise ValueError("None of the expected chemical features were found in the dataset.")

    print(f"Calculating missingness for {len(valid_features)} chemical features across lakes...")
    
    # Group by MIDAS
    grouped = df.groupby("MIDAS")
    
    records = []
    
    for midas, group in grouped:
        total_obs = len(group)
        if total_obs == 0:
            continue
            
        record = {
            "MIDAS": midas,
            "total_records": total_obs,
        }
        
        missing_counts = group[valid_features].isna().sum()
        for f in valid_features:
            record[f"pct_missing_{f}"] = missing_counts[f] / total_obs
            
        # Include overall aggregate for sorting
        total_data_points = total_obs * len(valid_features)
        record["pct_missing_chemical_overall"] = missing_counts.sum() / total_data_points
        
        records.append(record)
        
    missingness_df = pd.DataFrame(records)
    missingness_df = missingness_df.sort_values("pct_missing_chemical_overall", ascending=True)
    
    output_path = PROJECT_ROOT / "data" / "lake_missingness.csv"
    missingness_df.to_csv(output_path, index=False)
    print(f"Missingness matrix successfully saved to {output_path}")
    print(missingness_df.head())

if __name__ == "__main__":
    main()
