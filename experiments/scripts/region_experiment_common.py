"""Shared logic for Experiments 30–32: region-stratified MissForest + RF (Secchi).

Matches Experiment 22 feature policy and imputation settings. REGION is used only
to subset rows, not as a model feature.
"""

from __future__ import annotations

import warnings
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.ensemble import RandomForestRegressor
from sklearn.exceptions import ConvergenceWarning
from sklearn.impute import IterativeImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from tqdm.auto import tqdm

from experiment_utils import df_to_markdown_table, load_data

warnings.filterwarnings("ignore", category=ConvergenceWarning)

TARGET = "SECCHI"
NUM_COLS = ["LATITUDE", "LONGITUDE", "AREA_ACRES", "DEPTH_MAX_FEET"]
CHEM_FEATURES = ["DOMAX", "DOMIN", "TPEC", "TPBG", "PH", "COLOR", "CONDUCT", "ALK"]

ALL_REGION_KEYS = ("coastal", "inland", "northern")

REGION_DISPLAY = {"coastal": "Coastal", "inland": "Inland", "northern": "Northern"}

LOLO_SAMPLE_SIZE = 15
LOLO_RANDOM_SEED = 42
MAX_RF_ESTIMATORS = 15


def evaluate_model(
    y_true: pd.Series | np.ndarray,
    y_pred: np.ndarray,
    depth: pd.Series | np.ndarray,
) -> Dict[str, float]:
    """R², MAE, MSE, normalized MAE/MSE (same depth scaling as Experiment 22)."""
    y_true = pd.Series(y_true).reset_index(drop=True)
    y_pred = np.asarray(y_pred).reshape(-1)
    depth = pd.Series(depth).to_numpy()

    if len(y_true) == 0:
        return {
            "R2": float("nan"),
            "MAE": float("nan"),
            "MSE": float("nan"),
            "RMSE": float("nan"),
            "MAE_Norm": float("nan"),
            "MSE_Norm": float("nan"),
        }

    mae = float(mean_absolute_error(y_true, y_pred))
    mse = float(mean_squared_error(y_true, y_pred))
    rmse = float(np.sqrt(mse))
    r2 = float(r2_score(y_true, y_pred)) if len(y_true) > 1 else float("nan")

    safe_depth = np.where(depth > 0, depth, np.nan)
    pct_error = (y_true.to_numpy() - y_pred) / safe_depth
    mae_norm = float(np.nanmean(np.abs(pct_error)))
    mse_norm = float(np.nanmean(pct_error**2))

    return {
        "R2": r2,
        "MAE": mae,
        "MSE": mse,
        "RMSE": rmse,
        "MAE_Norm": mae_norm,
        "MSE_Norm": mse_norm,
    }


def _make_imputer(
    *, n_estimators: int = MAX_RF_ESTIMATORS, max_depth: int = 10, max_iter: int = 3
) -> IterativeImputer:
    n_estimators = min(n_estimators, MAX_RF_ESTIMATORS)
    rf_imputer = RandomForestRegressor(
        n_estimators=n_estimators, max_depth=max_depth, random_state=42, n_jobs=-1
    )
    return IterativeImputer(estimator=rf_imputer, max_iter=max_iter, random_state=42)


def _make_predictor(
    *, n_estimators: int = MAX_RF_ESTIMATORS, max_depth: int | None = None
) -> RandomForestRegressor:
    n_estimators = min(n_estimators, MAX_RF_ESTIMATORS)
    return RandomForestRegressor(
        n_estimators=n_estimators, max_depth=max_depth, random_state=42, n_jobs=-1
    )


def prepare_features(df: pd.DataFrame) -> Tuple[List[str], List[str]]:
    """Return (feature_names, valid_chem_cols) for Exp-22-style inputs."""
    df = df.copy()
    if "SAMPDATE" not in df.columns:
        raise ValueError("SAMPDATE missing")
    df["year"] = df["SAMPDATE"].dt.year
    df["month"] = df["SAMPDATE"].dt.month
    base_features = ["year", "month"] + NUM_COLS
    valid_chems = [c for c in CHEM_FEATURES if c in df.columns]
    features = base_features + valid_chems
    return features, valid_chems


def build_model_frame(df: pd.DataFrame, region_key: str) -> pd.DataFrame:
    """Rows in region with required non-missing core columns; sorted by SAMPDATE."""
    if "REGION" not in df.columns:
        raise ValueError("Merged dataset must include REGION column.")
    work = df.copy()
    work["_rk"] = work["REGION"].astype(str).str.strip().str.lower()
    work = work[work["_rk"] == region_key].drop(columns=["_rk"])
    subset_cols = [TARGET, "SAMPDATE", "MIDAS"] + NUM_COLS
    work = work.dropna(subset=subset_cols).copy()
    work["year"] = work["SAMPDATE"].dt.year
    work["month"] = work["SAMPDATE"].dt.month
    return work.sort_values(by="SAMPDATE").reset_index(drop=True)


def fit_predict_eval(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    features: List[str],
    *,
    imputer_estimators: int = MAX_RF_ESTIMATORS,
    imputer_depth: int = 10,
    imputer_max_iter: int = 3,
    predictor_estimators: int = MAX_RF_ESTIMATORS,
    predictor_depth: int | None = None,
) -> Dict[str, float]:
    """MissForest on train only; RF on imputed train; evaluate on imputed test."""
    X_train = train_df[features].copy()
    y_train = train_df[TARGET].copy()
    X_test = test_df[features].copy()
    y_test = test_df[TARGET].copy()
    depth_test = test_df["DEPTH_MAX_FEET"]

    imputer = _make_imputer(n_estimators=imputer_estimators, max_depth=imputer_depth, max_iter=imputer_max_iter)
    X_train_i = pd.DataFrame(
        imputer.fit_transform(X_train), columns=features, index=X_train.index
    )
    X_test_i = pd.DataFrame(
        imputer.transform(X_test), columns=features, index=X_test.index
    )

    predictor = _make_predictor(n_estimators=predictor_estimators, max_depth=predictor_depth)
    predictor.fit(X_train_i, y_train)
    y_pred = predictor.predict(X_test_i)
    return evaluate_model(y_test, y_pred, depth_test)


def metrics_markdown_table(m: Dict[str, float]) -> str:
    rows = [
        ("R²", f"{m['R2']:.4f}"),
        ("MAE (m)", f"{m['MAE']:.4f}"),
        ("MSE (m²)", f"{m['MSE']:.4f}"),
        ("Normalized MAE", f"{m['MAE_Norm']:.4f}"),
        ("Normalized MSE", f"{m['MSE_Norm']:.4f}"),
    ]
    df = pd.DataFrame(rows, columns=["Metric", "Value"])
    return df_to_markdown_table(df, max_rows=20)


def mean_metrics(rows: List[Dict[str, float]]) -> Dict[str, float]:
    if not rows:
        return {k: float("nan") for k in ["R2", "MAE", "MSE", "MAE_Norm", "MSE_Norm"]}
    out: Dict[str, float] = {}
    for k in ["R2", "MAE", "MSE", "MAE_Norm", "MSE_Norm"]:
        vals = [r[k] for r in rows if np.isfinite(r.get(k, np.nan))]
        out[k] = float(np.mean(vals)) if vals else float("nan")
    return out


def part1_chronological(model_df: pd.DataFrame, features: List[str]) -> Dict[str, float]:
    n = len(model_df)
    split_idx = int(n * 0.8)
    train_df = model_df.iloc[:split_idx]
    test_df = model_df.iloc[split_idx:]
    return fit_predict_eval(train_df, test_df, features)


def part2_lolo(
    model_df: pd.DataFrame,
    features: List[str],
    *,
    log_every: int = 50,
    sample_size: int = LOLO_SAMPLE_SIZE,
    random_seed: int = LOLO_RANDOM_SEED,
) -> Tuple[Dict[str, float], int, int]:
    """LOLO within region over deterministic sampled lakes.

    Returns (mean_metrics, n_folds_used, n_total_region_lakes).
    """
    all_lakes = pd.Series(model_df["MIDAS"].dropna().unique())
    n_total = int(len(all_lakes))
    if n_total == 0:
        return mean_metrics([]), 0, 0

    n_take = min(sample_size, n_total)
    sampled_lakes = (
        all_lakes.sample(n=n_take, random_state=random_seed).tolist()
        if n_take < n_total
        else all_lakes.tolist()
    )

    fold_metrics: List[Dict[str, float]] = []
    lake_iter = tqdm(sampled_lakes, desc="LOLO lakes", unit="lake")
    for i, hold in enumerate(lake_iter):
        train_df = model_df[model_df["MIDAS"] != hold]
        test_df = model_df[model_df["MIDAS"] == hold]
        if len(train_df) == 0 or len(test_df) == 0:
            continue
        m = fit_predict_eval(
            train_df,
            test_df,
            features,
            imputer_estimators=MAX_RF_ESTIMATORS,
            imputer_depth=8,
            imputer_max_iter=2,
            predictor_estimators=MAX_RF_ESTIMATORS,
            predictor_depth=10,
        )
        if np.isfinite(m["MAE"]):
            fold_metrics.append(m)
        if log_every and (i + 1) % log_every == 0:
            print(f"  LOLO progress: {i + 1}/{len(sampled_lakes)} sampled lakes")

    return mean_metrics(fold_metrics), len(fold_metrics), n_total


def part3_cross_region(
    full_df: pd.DataFrame,
    source_key: str,
    features: List[str],
) -> Tuple[Dict[str, float], Dict[str, Dict[str, float]]]:
    """Train on all source-region rows; test on each other region separately."""
    source_df = build_model_frame(full_df, source_key)
    if len(source_df) == 0:
        raise ValueError(f"No rows for source region {source_key}")

    X_src = source_df[features].copy()
    y_src = source_df[TARGET].copy()

    imputer = _make_imputer(
        n_estimators=MAX_RF_ESTIMATORS, max_depth=10, max_iter=3
    )
    X_src_i = pd.DataFrame(
        imputer.fit_transform(X_src), columns=features, index=X_src.index
    )
    predictor = _make_predictor(n_estimators=MAX_RF_ESTIMATORS, max_depth=None)
    predictor.fit(X_src_i, y_src)

    others = [rk for rk in ALL_REGION_KEYS if rk != source_key]
    per_other: Dict[str, Dict[str, float]] = {}
    for rk in tqdm(others, desc="Cross-region tests", unit="region"):
        odf = build_model_frame(full_df, rk)
        if len(odf) == 0:
            per_other[rk] = {k: float("nan") for k in ["R2", "MAE", "MSE", "MAE_Norm", "MSE_Norm"]}
            continue
        X_o = odf[features].copy()
        y_o = odf[TARGET].copy()
        depth_o = odf["DEPTH_MAX_FEET"]
        X_o_i = pd.DataFrame(
            imputer.transform(X_o), columns=features, index=X_o.index
        )
        pred = predictor.predict(X_o_i)
        per_other[rk] = evaluate_model(y_o, pred, depth_o)

    overall = mean_metrics(list(per_other.values()))
    return overall, per_other


def build_region_report_sections(
    *,
    region_key: str,
    experiment_num: int,
) -> Tuple[str, List[Tuple[str, str]]]:
    """Return (report_title, sections) for write_markdown_report."""
    if region_key not in REGION_DISPLAY:
        raise ValueError(f"Unknown region_key: {region_key}")
    display = REGION_DISPLAY[region_key]

    data = load_data()
    df = data.frame
    model_df = build_model_frame(df, region_key)
    features, _ = prepare_features(model_df)

    n_rows = len(model_df)
    n_lakes = int(model_df["MIDAS"].nunique())

    m1: Dict[str, float] = {}
    m2: Dict[str, float] = {}
    m3_overall: Dict[str, float] = {}
    m3_per: Dict[str, Dict[str, float]] = {}
    n_lolo = 0
    n_lakes_total = n_lakes

    steps = tqdm(
        [
            "Part 1: Chronological split",
            "Part 2: LOLO sampled subset",
            "Part 3: Cross-region generalization",
        ],
        desc=f"Experiment {experiment_num} steps",
        unit="part",
    )
    for step in steps:
        if step.startswith("Part 1"):
            m1 = part1_chronological(model_df, features)
            assert np.isfinite(m1["MAE"]), "Part 1 metrics invalid"
        elif step.startswith("Part 2"):
            m2, n_lolo, n_lakes_total = part2_lolo(model_df, features)
            assert n_lolo > 0, "LOLO produced no folds"
        else:
            m3_overall, m3_per = part3_cross_region(df, region_key, features)
            assert len(m3_per) == 2

    others_sorted = sorted(m3_per.keys())
    rk_a, rk_b = others_sorted[0], others_sorted[1]
    label_a = REGION_DISPLAY[rk_a]
    label_b = REGION_DISPLAY[rk_b]

    title = f"Experiment {experiment_num}: {display} Region (MissForest + Random Forest)"

    data_setup = (
        f"We used the merged lake monitoring dataset with a **{display}** filter on `REGION` "
        f"(values compared in lower case). After requiring non-missing `SECCHI`, `SAMPDATE`, `MIDAS`, "
        f"and core lake geometry (`LATITUDE`, `LONGITUDE`, `AREA_ACRES`, `DEPTH_MAX_FEET`), "
        f"this region has **{n_rows:,}** rows and **{n_lakes}** distinct lakes (`MIDAS`).\n\n"
        "Chemical predictors may be missing; we applied **MissForest-style** imputation "
        "(`IterativeImputer` with a Random Forest core). We cap all Random Forest estimator counts at "
        f"**{MAX_RF_ESTIMATORS}** in every part for runtime control, and use `max_iter=3` for Parts 1/3 "
        "and `max_iter=2` for sampled LOLO folds in Part 2. "
        "The imputer is always **fit on training data only** and then applied to the test set, "
        "so test values never influence how missing values are filled during training.\n\n"
        "`REGION` is **not** included as a model input: within a single region it would be constant, "
        "and for cross-region testing it would introduce labels the training rows never saw. "
        "The experiment is defined by **which rows belong to which region**, not by a region column inside the model.\n\n"
        f"**Predictors ({len(features)}):** `{', '.join(features)}` (CHLA excluded, as in Experiment 22)."
    )

    part1_body = (
        "**What we did.** We sorted all rows in this region by `SAMPDATE` and used the **first 80%** "
        "of rows as training and the **last 20%** as testing. This is a chronological split **inside the region only**, "
        "so we are asking how well the model predicts the region's own future from its past.\n\n"
        "**Results.**\n\n"
        f"{metrics_markdown_table(m1)}"
    )

    part2_body = (
        "**What we did.** To keep runtime practical while preserving comparability, we used a deterministic LOLO subset. "
        f"From **{n_lakes_total}** lakes in this region, we sampled **{min(LOLO_SAMPLE_SIZE, n_lakes_total)}** lakes "
        f"with fixed random seed **{LOLO_RANDOM_SEED}**. For each sampled lake, we trained on all other region lakes and tested on the held-out lake. "
        f"Metrics below are the mean across **{n_lolo}** successful sampled folds.\n\n"
        "**Results (mean over lakes).**\n\n"
        f"{metrics_markdown_table(m2)}"
    )

    rows_part3 = []
    for rk in others_sorted:
        m = m3_per[rk]
        rows_part3.append(
            {
                "Test region": REGION_DISPLAY[rk],
                "R²": m["R2"],
                "MAE": m["MAE"],
                "MSE": m["MSE"],
                "Norm. MAE": m["MAE_Norm"],
                "Norm. MSE": m["MSE_Norm"],
            }
        )
    df_p3 = pd.DataFrame(rows_part3)

    part3_body = (
        "**What we did.** We trained a single model on **all** rows in this region (after the same filters as above). "
        f"We then tested that model separately on **{label_a}** and **{label_b}** rows (each with the same column rules). "
        "MissForest was **fit only on the training region** features, then used to impute each out-of-region test set.\n\n"
        "**Results — by other region.**\n\n"
        f"{df_to_markdown_table(df_p3, round_decimals=4)}\n\n"
        "**Mean across the two other regions** (simple average of the two rows above for each metric):\n\n"
        f"{metrics_markdown_table(m3_overall)}"
    )

    takeaway = (
        f"- **Within-region time (Part 1):** R² = {m1['R2']:.4f}, MAE = {m1['MAE']:.4f} m.\n"
        f"- **Within-region new lake (Part 2, sampled LOLO):** R² = {m2['R2']:.4f}, MAE = {m2['MAE']:.4f} m over {n_lolo} sampled lakes (seed {LOLO_RANDOM_SEED}).\n"
        f"- **Out of region (Part 3):** mean test R² across {label_a} and {label_b} = {m3_overall['R2']:.4f}; "
        f"{label_a} R² = {m3_per[rk_a]['R2']:.4f}, {label_b} R² = {m3_per[rk_b]['R2']:.4f}.\n"
    )

    sections: List[Tuple[str, str]] = [
        ("Objective", f"Measure Secchi (`{TARGET}`) prediction for the **{display}** region under three setups: "
         "chronological forecasting within the region, leave-one-lake-out within the region, and training only on this "
         "region while testing on the other two. Methods mirror **Experiment 22** (MissForest + Random Forest)."),
        ("Data setup", data_setup),
        ("Part 1: Region chronological train/test (80/20)", part1_body),
        ("Part 2: Leave-one-lake-out within the region", part2_body),
        ("Part 3: Train on this region, test on the other two", part3_body),
        ("Takeaway", takeaway),
    ]

    return title, sections
