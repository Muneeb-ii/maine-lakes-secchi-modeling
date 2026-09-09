from __future__ import annotations

import time

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from catboost import CatBoostRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from tqdm.auto import tqdm

from experiment_utils import (
    CanonicalReport,
    df_to_markdown_table,
    ensure_reports_dir,
    get_dataset_artifact_path,
    load_data,
    write_canonical_report,
)


EXPERIMENT_ID = "47"
REPORT_FILENAME = "47_playground_feature_contract.md"
REPORT_TITLE = "Experiment 47: Playground Feature Contract on the June Dataset"
FIGURE_FILENAME = "47_playground_feature_contract.png"
LOLO_CSV_FILENAME = "47_lolo_per_lake.csv"

BEST_PARAMS = {
    "iterations": 700,
    "depth": 10,
    "learning_rate": 0.05,
    "l2_leaf_reg": 3,
    "random_seed": 42,
    "loss_function": "RMSE",
    "eval_metric": "RMSE",
    "verbose": False,
    "allow_writing_files": False,
    "thread_count": -1,
}

TARGET = "SECCHI"
BASE_FEATURES = ["year", "month", "LATITUDE", "LONGITUDE", "AREA_ACRES", "DEPTH_MAX_FEET"]
LEGACY_EDITABLE = ["DOMAX", "DOMIN", "TPEC", "TPBG"]
MEASURED_EDITABLE = ["DOMAX", "DOMIN", "TMAX", "TMIN", "TPEC", "TPBG"]
LOCKED_LAKE_CHEMISTRY = ["PH", "COLOR", "CONDUCT", "ALK"]
CALCULATED_PROFILE = ["MLD", "THERMO", "SCHMIDT", "OXIC_DEPTH", "EPI_TEMP", "HYPO_TEMP"]

FEATURE_SETS = {
    "A_legacy_served": BASE_FEATURES + LEGACY_EDITABLE + LOCKED_LAKE_CHEMISTRY,
    "B_measured_only": BASE_FEATURES + MEASURED_EDITABLE,
    "C_measured_locked_chem": BASE_FEATURES + MEASURED_EDITABLE + LOCKED_LAKE_CHEMISTRY,
    "D_measured_locked_chem_calculated": BASE_FEATURES
    + MEASURED_EDITABLE
    + LOCKED_LAKE_CHEMISTRY
    + CALCULATED_PROFILE,
}
LOLO_FEATURE_SETS = ["A_legacy_served", "B_measured_only", "C_measured_locked_chem"]
# The 100-lake confirmation only compares the served set with the candidate to keep the run rerunnable.
LOLO_CONFIRMATION_SETS = ["A_legacy_served", "C_measured_locked_chem"]

SUPPORT_MIN_OBS = 100
SUPPORT_MAX_MISSING = 0.90


def evaluate_model(y_true, y_pred, depth) -> dict:
    mae = mean_absolute_error(y_true, y_pred)
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    r2 = r2_score(y_true, y_pred) if len(y_true) > 1 else np.nan
    depth_values = pd.Series(depth).to_numpy()
    safe_depth = np.where(depth_values > 0, depth_values, np.nan)
    pct_error = (pd.Series(y_true).to_numpy() - np.asarray(y_pred)) / safe_depth
    return {
        "MAE": float(mae),
        "RMSE": rmse,
        "R2": float(r2),
        "MAE_Norm": float(np.nanmean(np.abs(pct_error))),
    }


def lake_support_table(model_df: pd.DataFrame, missingness_df: pd.DataFrame) -> pd.DataFrame:
    counts = model_df.groupby("MIDAS").size().rename("n_obs")
    editable_missing = (
        model_df.groupby("MIDAS")[MEASURED_EDITABLE]
        .apply(lambda group: float(group.isna().to_numpy().mean()))
        .rename("pct_missing_measured_editable")
    )
    catalog_missing = missingness_df.set_index("MIDAS")["pct_missing_chemical_overall"].rename(
        "pct_missing_catalog"
    )
    support = pd.concat([counts, editable_missing, catalog_missing], axis=1)
    support = support.loc[support["n_obs"].notna()].copy()
    support["n_obs"] = support["n_obs"].astype(int)
    support["catalog_policy"] = (support["n_obs"] >= SUPPORT_MIN_OBS) & (
        support["pct_missing_catalog"].fillna(1.0) <= SUPPORT_MAX_MISSING
    )
    support["editable_policy"] = (support["n_obs"] >= SUPPORT_MIN_OBS) & (
        support["pct_missing_measured_editable"].fillna(1.0) <= SUPPORT_MAX_MISSING
    )
    return support


def chronological_evaluation(supported_df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, pd.Series]]:
    split_idx = int(len(supported_df) * 0.8)
    train_df = supported_df.iloc[:split_idx]
    test_df = supported_df.iloc[split_idx:]
    rows = []
    importances: dict[str, pd.Series] = {}
    for set_name, features in FEATURE_SETS.items():
        started = time.time()
        model = CatBoostRegressor(**BEST_PARAMS)
        model.fit(train_df[features], train_df[TARGET])
        predictions = model.predict(test_df[features])
        metrics = evaluate_model(test_df[TARGET], predictions, test_df["DEPTH_MAX_FEET"])
        importances[set_name] = pd.Series(model.get_feature_importance(), index=features).sort_values(
            ascending=False
        )
        rows.append(
            {
                "feature_set": set_name,
                "n_features": len(features),
                "R2": round(metrics["R2"], 4),
                "MAE": round(metrics["MAE"], 4),
                "RMSE": round(metrics["RMSE"], 4),
                "MAE_Norm": round(metrics["MAE_Norm"], 4),
                "fit_seconds": int(time.time() - started),
            }
        )
        print(f"Chronological {set_name}: R2={metrics['R2']:.4f} MAE={metrics['MAE']:.4f}")
    return pd.DataFrame(rows), importances


def lolo_evaluation(
    model_df: pd.DataFrame, lake_ids: list[str], support: pd.DataFrame, feature_sets: list[str], label: str
) -> pd.DataFrame:
    rows = []
    for lake_id in tqdm(lake_ids, desc=label, unit="lake"):
        test_df = model_df.loc[model_df["MIDAS"] == lake_id]
        train_df = model_df.loc[model_df["MIDAS"] != lake_id]
        if len(test_df) < 2:
            continue
        for set_name in feature_sets:
            features = FEATURE_SETS[set_name]
            model = CatBoostRegressor(**BEST_PARAMS)
            model.fit(train_df[features], train_df[TARGET])
            predictions = model.predict(test_df[features])
            metrics = evaluate_model(test_df[TARGET], predictions, test_df["DEPTH_MAX_FEET"])
            rows.append(
                {
                    "MIDAS": lake_id,
                    "feature_set": set_name,
                    "n_obs": len(test_df),
                    "pct_missing_measured_editable": round(
                        float(support.loc[lake_id, "pct_missing_measured_editable"]), 4
                    ),
                    "editable_policy": bool(support.loc[lake_id, "editable_policy"]),
                    "R2": round(metrics["R2"], 4),
                    "MAE": round(metrics["MAE"], 4),
                    "MAE_Norm": round(metrics["MAE_Norm"], 4),
                }
            )
    return pd.DataFrame(rows)


def summarize_lolo(lolo_df: pd.DataFrame, sample_label: str) -> pd.DataFrame:
    rows = []
    feature_sets = [name for name in LOLO_FEATURE_SETS if name in set(lolo_df["feature_set"])]
    for policy_label, mask in (
        ("Catalog policy lakes", pd.Series(True, index=lolo_df.index)),
        ("Editable-missingness policy lakes", lolo_df["editable_policy"]),
    ):
        subset = lolo_df.loc[mask]
        for set_name in feature_sets:
            part = subset.loc[subset["feature_set"] == set_name]
            rows.append(
                {
                    "lake_sample": sample_label,
                    "restriction": policy_label,
                    "feature_set": set_name,
                    "n_lakes": int(part["MIDAS"].nunique()),
                    "avg_R2": round(float(part["R2"].mean()), 4) if len(part) else np.nan,
                    "median_R2": round(float(part["R2"].median()), 4) if len(part) else np.nan,
                    "avg_MAE": round(float(part["MAE"].mean()), 4) if len(part) else np.nan,
                }
            )
    return pd.DataFrame(rows)


def plot_summary(chrono_df: pd.DataFrame, lolo_summary: pd.DataFrame, output_path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    axes[0].bar(chrono_df["feature_set"], chrono_df["R2"], color="#2d6a4f")
    axes[0].set_ylim(0.70, max(0.76, chrono_df["R2"].max() + 0.005))
    axes[0].set_title("Chronological R² on supported lakes")
    axes[0].set_ylabel("R²")
    axes[0].tick_params(axis="x", rotation=20)

    hundred = lolo_summary.loc[lolo_summary["lake_sample"].str.startswith("Seeded 100")]
    width = 0.38
    restrictions = list(hundred["restriction"].unique())
    positions = np.arange(len(LOLO_CONFIRMATION_SETS))
    for offset, restriction in enumerate(restrictions):
        part = hundred.loc[hundred["restriction"] == restriction].set_index("feature_set")
        axes[1].bar(
            positions + (offset - 0.5) * width,
            [part.loc[name, "avg_R2"] for name in LOLO_CONFIRMATION_SETS],
            width=width,
            label=restriction,
        )
    axes[1].axhline(0, color="black", linewidth=1, alpha=0.5)
    axes[1].set_xticks(positions)
    axes[1].set_xticklabels(LOLO_CONFIRMATION_SETS, rotation=20)
    axes[1].set_title("LOLO average R² (seeded 100-lake sample)")
    axes[1].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    reports_dir = ensure_reports_dir()
    data = load_data()
    df = data.frame
    df["MIDAS"] = df["MIDAS"].astype(str).str.strip()

    required = [TARGET, "SAMPDATE", "MIDAS", "LATITUDE", "LONGITUDE", "AREA_ACRES", "DEPTH_MAX_FEET"]
    model_df = df.dropna(subset=required).sort_values("SAMPDATE").reset_index(drop=True)

    missingness_df = pd.read_csv(get_dataset_artifact_path("lake_missingness_path"))
    missingness_df["MIDAS"] = missingness_df["MIDAS"].astype(str).str.strip()
    support = lake_support_table(model_df, missingness_df)

    catalog_ids = set(support.index[support["catalog_policy"]])
    supported_df = model_df.loc[model_df["MIDAS"].isin(catalog_ids)].copy()
    print(f"Modeling rows: {len(model_df):,}; supported rows: {len(supported_df):,}; lakes: {len(catalog_ids)}")

    chrono_df, importances = chronological_evaluation(supported_df)

    ten_ids = [
        line.strip()
        for line in get_dataset_artifact_path("lolo_seed_10_path").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    hundred_ids = [
        line.strip()
        for line in get_dataset_artifact_path("lolo_seed_100_path").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    ten_eval = [lake for lake in ten_ids if lake in catalog_ids]
    hundred_eval = [lake for lake in hundred_ids if lake in catalog_ids]
    print(f"LOLO lakes retained: 10-lake set {len(ten_eval)}/{len(ten_ids)}; 100-lake set {len(hundred_eval)}/{len(hundred_ids)}")

    lolo_ten = lolo_evaluation(model_df, ten_eval, support, LOLO_FEATURE_SETS, "LOLO x10 screen")
    lolo_hundred = lolo_evaluation(model_df, hundred_eval, support, LOLO_CONFIRMATION_SETS, "LOLO x100 confirm")
    pd.concat(
        [lolo_ten.assign(lake_sample="seeded_10"), lolo_hundred.assign(lake_sample="seeded_100")],
        ignore_index=True,
    ).to_csv(reports_dir / LOLO_CSV_FILENAME, index=False)
    lolo_summary = pd.concat(
        [
            summarize_lolo(lolo_ten, "Seeded 10-lake set"),
            summarize_lolo(lolo_hundred, "Seeded 100-lake set"),
        ],
        ignore_index=True,
    )
    plot_summary(chrono_df, lolo_summary, reports_dir / FIGURE_FILENAME)

    policy_df = pd.DataFrame(
        [
            {
                "policy": "Catalog missingness (22 profile + lake-chemistry fields)",
                "rule": f"n_obs >= {SUPPORT_MIN_OBS} and pct_missing <= {SUPPORT_MAX_MISSING:.2f}",
                "lakes": int(support["catalog_policy"].sum()),
                "rows": int(model_df["MIDAS"].isin(support.index[support["catalog_policy"]]).sum()),
            },
            {
                "policy": "Measured editable missingness (6 slider fields)",
                "rule": f"n_obs >= {SUPPORT_MIN_OBS} and pct_missing <= {SUPPORT_MAX_MISSING:.2f}",
                "lakes": int(support["editable_policy"].sum()),
                "rows": int(model_df["MIDAS"].isin(support.index[support["editable_policy"]]).sum()),
            },
            {
                "policy": f"n_obs >= {SUPPORT_MIN_OBS} only",
                "rule": f"n_obs >= {SUPPORT_MIN_OBS}",
                "lakes": int((support["n_obs"] >= SUPPORT_MIN_OBS).sum()),
                "rows": int(model_df["MIDAS"].isin(support.index[support["n_obs"] >= SUPPORT_MIN_OBS]).sum()),
            },
        ]
    )

    candidate = "C_measured_locked_chem"
    importance_df = importances[candidate].rename("importance").reset_index().rename(columns={"index": "feature"})
    importance_df["role"] = importance_df["feature"].map(
        lambda name: "editable" if name in MEASURED_EDITABLE else "locked"
    )

    within_lake = pd.DataFrame(
        {
            "field": LOCKED_LAKE_CHEMISTRY,
            "unique_values_per_lake_max": [int(model_df.groupby("MIDAS")[c].nunique().max()) for c in LOCKED_LAKE_CHEMISTRY],
            "lakes_with_value": [int(model_df.loc[model_df[c].notna(), "MIDAS"].nunique()) for c in LOCKED_LAKE_CHEMISTRY],
        }
    )

    report = CanonicalReport(
        objective=(
            "Select the playground feature contract for the active June dataset. In this snapshot PH, COLOR, CONDUCT, and ALK "
            "are fixed lake-level means rather than per-visit measurements, so they can no longer be user-editable, while "
            "the provider added TMAX and TMIN as directly measured profile fields. The experiment tests whether a contract "
            "with only directly measured editable inputs (dissolved oxygen, temperature, phosphorus) plus locked lake "
            "chemistry matches the accuracy of the currently served 14-feature model and of a wider set that adds the "
            "calculated profile metrics."
        ),
        method=(
            "Tuned native-missing CatBoost from Experiments 34 and 38 is refit unchanged for each feature set. Chronological "
            "evaluation uses an 80/20 date-ordered split on lakes that satisfy the Experiment 38 support policy "
            f"(n_obs >= {SUPPORT_MIN_OBS} and cataloged chemistry missingness <= {SUPPORT_MAX_MISSING:.2f}). Leave-one-lake-out "
            "evaluation reuses the seeded 10-lake and 100-lake lists carried over from the 2025 snapshot so results are "
            "comparable with Experiments 35 and 38, restricted to lakes that satisfy the same policy. The 10-lake set screens "
            "the served, measured-only, and measured-plus-locked-chemistry sets; the 100-lake set confirms the served "
            "set against the measured-plus-locked-chemistry candidate only. The calculated-profile set is evaluated "
            "chronologically only because those fields have no provider definitions yet. Lake support is also recomputed "
            "using missingness over the six measured slider fields to check whether the cataloged threshold still "
            "discriminates on this snapshot."
        ),
        parameters=(
            f"Dataset ID: `{data.dataset_id}`.\n\n"
            f"CatBoost parameters: {BEST_PARAMS}\n\n"
            + "\n".join(f"- `{name}` ({len(features)} features): {features}" for name, features in FEATURE_SETS.items())
            + "\n\nCHLA is excluded from every set because it is target-adjacent. `MTB` is excluded because it encodes the "
            "lake-station identifier, and `DEPTH` because it records the profile depth reached on the sampling date "
            "rather than a lake condition."
        ),
        results=(
            "### Chronological evaluation on supported lakes\n\n"
            f"Supported rows: {len(supported_df):,} across {len(catalog_ids)} lakes; test window "
            f"{supported_df.iloc[int(len(supported_df) * 0.8):]['SAMPDATE'].min().year}–"
            f"{supported_df['SAMPDATE'].max().year}.\n\n"
            f"{df_to_markdown_table(chrono_df)}\n\n"
            f"![Feature contract summary]({FIGURE_FILENAME})\n\n"
            f"### Feature importance for `{candidate}`\n\n"
            f"{df_to_markdown_table(importance_df)}\n\n"
            "### Locked lake chemistry in this snapshot\n\n"
            f"{df_to_markdown_table(within_lake)}\n\n"
            "### Leave-one-lake-out summary\n\n"
            f"Retained seeded lakes: 10-lake set {len(ten_eval)}/{len(ten_ids)}, 100-lake set {len(hundred_eval)}/{len(hundred_ids)}. "
            f"Per-lake results for every feature set are in `{LOLO_CSV_FILENAME}`.\n\n"
            f"{df_to_markdown_table(lolo_summary)}\n\n"
            "### Support policy coverage\n\n"
            f"{df_to_markdown_table(policy_df)}"
        ),
        next_step=(
            "Serve the measured-plus-locked-chemistry contract. Keep n_obs >= 100 as the selectability rule. "
            "Flag supported lakes with sparse measured slider fields as thin_history rather than dropping them. "
            "Do not treat the Experiment 38 chemistry-missingness cutoff as an active June filter."
        ),
    )
    path = write_canonical_report(REPORT_FILENAME, REPORT_TITLE, report)
    print(f"Wrote report to {path}")


if __name__ == "__main__":
    main()
