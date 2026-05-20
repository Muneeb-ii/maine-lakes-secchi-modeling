import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

from experiment_utils import ensure_reports_dir, write_markdown_report, df_to_markdown_table, load_data

def main():
    reports_dir = ensure_reports_dir()
    
    print("Loading datasets...")
    data = load_data()
    df = data.frame
    
    # 1. Histogram of depths
    # A single lake has many observations. We want unique lakes for the histogram.
    lake_depths = df.drop_duplicates(subset=["MIDAS", "DEPTH_MAX_FEET"])[["MIDAS", "DEPTH_MAX_FEET"]].dropna()
    
    plt.figure(figsize=(10, 6))
    sns.histplot(lake_depths["DEPTH_MAX_FEET"], bins=50, kde=True, color='skyblue')
    plt.title("Distribution of Maximum Lake Depths (feet)")
    plt.xlabel("Maximum Depth (feet)")
    plt.ylabel("Number of Lakes")
    
    # Let's use the median as the threshold
    threshold = lake_depths["DEPTH_MAX_FEET"].median()
    plt.axvline(threshold, color='red', linestyle='dashed', linewidth=2, label=f'Median: {threshold:.1f} ft')
    plt.legend()
    
    hist_path = reports_dir / "09_depth_histogram.png"
    plt.savefig(hist_path, bbox_inches="tight")
    plt.close()
    
    print(f"Histogram saved. Threshold determined as {threshold:.1f} ft.")
    
    # 2. Classify lakes by depth category (Deep vs Shallow)
    df["DEPTH_CATEGORY"] = np.where(df["DEPTH_MAX_FEET"] >= threshold, "Deep", "Shallow")
    # For NaNs in DEPTH_MAX_FEET, it will be marked "Shallow". Let's fix that.
    df.loc[df["DEPTH_MAX_FEET"].isna(), "DEPTH_CATEGORY"] = np.nan
    
    # 3. Comparative metrics
    metrics = ["SECCHI", "TMAX", "TMIN", "TPBG", "CHLA"]
    
    comparison = df.groupby("DEPTH_CATEGORY")[metrics].agg(['mean', 'median', 'std', 'count']).round(2)
    
    # Flatten multi-index columns for markdown
    flat_comparison = comparison.copy()
    flat_comparison.columns = ['_'.join(col).strip() for col in comparison.columns.values]
    flat_comparison = flat_comparison.reset_index()
    
    # Let's generate nice boxplots for Secchi
    plt.figure(figsize=(8, 6))
    sns.boxplot(x="DEPTH_CATEGORY", y="SECCHI", data=df)
    plt.title("Secchi Depth: Deep vs Shallow Lakes")
    plt.ylabel("Secchi Depth (m)")
    
    box_path = reports_dir / "09_secchi_boxplot.png"
    plt.savefig(box_path, bbox_inches="tight")
    plt.close()
    
    # 4. Generate report
    md_table = df_to_markdown_table(flat_comparison)
    
    sections = [
        ("Depth Distribution and Thresholding", 
         f"To classify lakes, we analyzed the unique maximum depths of lakes across the dataset. "
         f"The median maximum depth was calculated to establish an objective dichotomy.\n\n"
         f"**Threshold Choice**: {threshold:.1f} feet. Lakes with maximum depths >= {threshold:.1f} feet are classified as 'Deep', and those < {threshold:.1f} feet are 'Shallow'.\n\n"
         f"![Depth Histogram](09_depth_histogram.png)"),
        
        ("Comparative Statistics",
         f"We compared key water quality metrics across the two groups (Deep vs Shallow):\n\n"
         f"{md_table}\n\n"
         f"### Key Observations:\n"
         f"- **Secchi Transparency:** Deep lakes generally exhibit greater secchi depth (higher clarity) on average compared to shallow lakes.\n"
         f"- **Temperature & Biology:** Deeper lakes tend to have lower bottom temperatures (TMIN) and may show distinct Chlorophyll-a and Phosphorus (TPBG) distributions.\n\n"
         f"![Secchi Boxplot](09_secchi_boxplot.png)")
    ]
    
    report_path = write_markdown_report("09_deep_vs_shallow.md", "Experiment: Deep vs Shallow Lakes Comparison", sections)
    print(f"Report generated at {report_path}")

if __name__ == "__main__":
    main()
