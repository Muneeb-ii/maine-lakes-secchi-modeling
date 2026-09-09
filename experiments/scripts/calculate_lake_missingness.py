from __future__ import annotations

"""Build the per-lake chemistry missingness matrix for the loaded snapshot.

The same script covers both processed deliveries: it writes only the chemistry
and profile columns that exist on that dataset. Run with the catalog ID set:

    SECCHI_DATASET_ID=secchi-merged-2025-04-17-r1 python experiments/scripts/calculate_lake_missingness.py
    SECCHI_DATASET_ID=secchi-merged-2026-06-29-r1 python experiments/scripts/calculate_lake_missingness.py

Output path comes from `data/catalog.json` (`derived_artifacts.<id>.lake_missingness_path`).
"""

import pandas as pd

from experiment_utils import get_dataset_artifact_path, load_data

# Union of chemistry/profile fields across snapshots, in a stable order.
# 2025 has OXIC; 2026 replaces it with OXIC_DEPTH plus extra profile metrics.
CHEMISTRY_FEATURE_CANDIDATES = [
    "TMAX",
    "TMIN",
    "DOMAX",
    "DOMIN",
    "MLD",
    "OXIC",
    "MAXBF",
    "CTR_BUOY",
    "EPI_TEMP",
    "HYPO_TEMP",
    "INT_ENER",
    "SCHMIDT",
    "THERMO",
    "WHOLE_TEMP",
    "OXIC_DEPTH",
    "FRAC_ANOXIC",
    "TPEC",
    "TPBG",
    "CHLA",
    "PH",
    "COLOR",
    "CONDUCT",
    "ALK",
]


def main() -> None:
    print("Loading dataset...")
    data = load_data()
    df = data.frame
    valid_features = [name for name in CHEMISTRY_FEATURE_CANDIDATES if name in df.columns]
    if not valid_features:
        raise ValueError("None of the expected chemical features were found in the dataset.")

    print(
        f"Calculating missingness for {len(valid_features)} fields on {data.dataset_id} "
        f"({', '.join(valid_features)})"
    )

    grouped = df.groupby("MIDAS", sort=False)
    missing_frac = grouped[valid_features].apply(lambda group: group.isna().mean())
    missing_frac = missing_frac.rename(columns=lambda name: f"pct_missing_{name}")
    missing_frac["total_records"] = grouped.size()
    missing_frac["pct_missing_chemical_overall"] = missing_frac[
        [f"pct_missing_{name}" for name in valid_features]
    ].mean(axis=1)
    missingness_df = missing_frac.reset_index()
    missingness_df = missingness_df[
        ["MIDAS", "total_records"]
        + [f"pct_missing_{name}" for name in valid_features]
        + ["pct_missing_chemical_overall"]
    ]
    missingness_df = missingness_df.sort_values("pct_missing_chemical_overall", ascending=True)

    output_path = get_dataset_artifact_path("lake_missingness_path", must_exist=False)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    missingness_df.to_csv(output_path, index=False)
    print(f"Missingness matrix successfully saved to {output_path}")
    print(missingness_df.head())


if __name__ == "__main__":
    main()
