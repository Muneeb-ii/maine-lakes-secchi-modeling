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

def compute_yearly_trends(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate average SECCHI grouped by year."""
    if "SECCHI" not in df.columns or "year" not in df.columns:
        return pd.DataFrame()
        
    # Group by year and calculate mean, std, and count.
    yearly = df.groupby("year")["SECCHI"].agg(
        n_obs="count",
        mean_secchi="mean",
        std_secchi="std"
    ).reset_index()
    
    # Filter out years with very few observations to avoid noise
    yearly = yearly[yearly["n_obs"] >= 10]
    yearly = yearly.sort_values("year").reset_index(drop=True)
    return yearly

def compute_seasonal_trends(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate average SECCHI grouped by month and season."""
    if "SECCHI" not in df.columns or "month" not in df.columns:
        return pd.DataFrame()
        
    monthly = df.groupby(["season", "month"])["SECCHI"].agg(
        n_obs="count",
        mean_secchi="mean",
        std_secchi="std"
    ).reset_index()
    
    # Sort months sequentially
    monthly = monthly.sort_values("month").reset_index(drop=True)
    return monthly

def main() -> None:
    data: LoadedData = load_data()
    df = data.frame
    
    yearly_df = compute_yearly_trends(df)
    monthly_df = compute_seasonal_trends(df)
    
    overview_text = textwrap.dedent(
        f"""
        This report analyzes the temporal patterns of `SECCHI` depth to determine if water clarity 
        is fundamentally changing across decades, and how it behaves across seasons.
        """
    ).strip()
    
    if not yearly_df.empty:
        # Calculate a simple trendline for the yearly data
        years = yearly_df["year"].to_numpy(dtype=float)
        means = yearly_df["mean_secchi"].to_numpy(dtype=float)
        slope, intercept = np.polyfit(years, means, 1)
        direction = "increasing" if slope > 0 else "decreasing"
        trend_text = f"**Overall Multi-Decade Trend:** The average Secchi depth is slightly {direction} at a rate of {abs(slope):.4f} meters per year."
        
        yearly_md = df_to_markdown_table(yearly_df, round_decimals=3)
    else:
        trend_text = "_Not enough yearly data for a trendline._"
        yearly_md = "_No active yearly data found._"
        
    monthly_md = df_to_markdown_table(monthly_df, round_decimals=2) if not monthly_df.empty else "_No monthly data found._"
    
    sections = [
        ("Overview", overview_text),
        ("Multi-Decade Yearly Trends", trend_text + "\n\n" + yearly_md),
        ("Seasonal and Monthly Averages", monthly_md),
    ]
    
    report_path = write_markdown_report(
        filename="06_temporal_trends.md",
        title="Secchi Dataset – Temporal Trends & Seasonality",
        sections=sections,
    )
    
    print(f"Wrote temporal trends report to {report_path}")

if __name__ == "__main__":
    main()
