from __future__ import annotations

import textwrap
import numpy as np
import pandas as pd

from experiment_utils import (
    LoadedData,
    df_to_markdown_table,
    load_data,
    write_markdown_report,
)


def compute_lake_variance(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate the average SECCHI and variance per lake (MIDAS)."""
    if "SECCHI" not in df.columns or "MIDAS" not in df.columns:
        return pd.DataFrame()
        
    # Group by lake and compute statistics
    lake_stats = df.groupby("MIDAS")["SECCHI"].agg(
        n_obs="count",
        mean_secchi="mean",
        std_secchi="std",
        min_secchi="min",
        max_secchi="max"
    ).reset_index()
    
    # Filter for lakes with a meaningful amount of data to avoid extreme noise
    lake_stats = lake_stats[lake_stats["n_obs"] >= 15]
    
    # Calculate Coefficient of Variation (CV) = std / mean
    # High CV means a lake varies a lot internally. Low CV means it's incredibly stable.
    lake_stats["coeff_of_variation"] = lake_stats["std_secchi"] / lake_stats["mean_secchi"]
    
    return lake_stats

def main() -> None:
    data: LoadedData = load_data()
    df = data.frame
    
    lake_stats = compute_lake_variance(df)
    
    overview_text = textwrap.dedent(
        f"""
        This report analyzes spatial variance by looking at how `SECCHI` depth differs from 
        lake to lake (`MIDAS`). 
        
        It identifies the clearest lakes, the murkiest lakes, and lakes that experience 
        the most internal volatility (high coefficient of variation).
        
        Lakes considered: **{len(lake_stats)}** (each with at least 15 observations).
        """
    ).strip()
    
    if lake_stats.empty:
        clearest_md = "_No lakes met the observation threshold._"
        murkiest_md = "_No lakes met the observation threshold._"
        volatile_md = "_No lakes met the observation threshold._"
        stable_md = "_No lakes met the observation threshold._"
    else:
        # Clearest vs Murkiest (by mean)
        clearest = lake_stats.sort_values("mean_secchi", ascending=False).head(15)
        murkiest = lake_stats.sort_values("mean_secchi", ascending=True).head(15)
        
        # Most volatile vs Most stable (by Coefficient of Variation)
        volatile = lake_stats.sort_values("coeff_of_variation", ascending=False).head(15)
        stable = lake_stats.sort_values("coeff_of_variation", ascending=True).head(15)
        
        clearest_md = df_to_markdown_table(clearest, round_decimals=3)
        murkiest_md = df_to_markdown_table(murkiest, round_decimals=3)
        volatile_md = df_to_markdown_table(volatile, round_decimals=3)
        stable_md = df_to_markdown_table(stable, round_decimals=3)
        
    sections = [
        ("Overview", overview_text),
        ("Top 15 Clearest Lakes (Highest Mean SECCHI)", clearest_md),
        ("Top 15 Murkiest Lakes (Lowest Mean SECCHI)", murkiest_md),
        ("Most Volatile Lakes (Highest Coefficient of Variation)", volatile_md),
        ("Most Stable Lakes (Lowest Coefficient of Variation)", stable_md),
    ]
    
    report_path = write_markdown_report(
        filename="07_spatial_variance_midas.md",
        title="Secchi Dataset – Spatial Variance & Lake Stability",
        sections=sections,
    )
    
    print(f"Wrote spatial variance report to {report_path}")

if __name__ == "__main__":
    main()
