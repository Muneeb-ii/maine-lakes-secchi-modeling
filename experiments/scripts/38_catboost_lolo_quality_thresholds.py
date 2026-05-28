from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from catboost import CatBoostRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from tqdm.auto import tqdm

from experiment_utils import (
    CanonicalReport,
    ensure_reports_dir,
    write_canonical_report,
    df_to_markdown_table,
    load_data,
    PROJECT_ROOT,
)

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


TOP_X100_CONFIRMATIONS = 3

QUALITY_SCENARIOS = [
    {"label": "All seeded lakes", "min_obs": 0, "max_missing": 1.0},
    {"label": "Obs >= 100", "min_obs": 100, "max_missing": 1.0},
    {"label": "Obs >= 200", "min_obs": 200, "max_missing": 1.0},
    {"label": "Missing <= 0.90", "min_obs": 0, "max_missing": 0.90},
    {"label": "Missing <= 0.75", "min_obs": 0, "max_missing": 0.75},
    {"label": "Obs >= 100 and missing <= 0.90", "min_obs": 100, "max_missing": 0.90},
    {"label": "Obs >= 100 and missing <= 0.75", "min_obs": 100, "max_missing": 0.75},
]


def evaluate_model(y_true, y_pred, depth):
    if len(y_true) == 0:
        return {"MAE": 0, "RMSE": 0, "R2": 0, "MAE_Norm": 0, "RMSE_Norm": 0}

    mae = mean_absolute_error(y_true, y_pred)
    mse = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_true, y_pred) if len(y_true) > 1 else np.nan

    safe_depth = np.where(pd.Series(depth).to_numpy() > 0, pd.Series(depth).to_numpy(), np.nan)
    pct_error = (pd.Series(y_true).to_numpy() - pd.Series(y_pred).to_numpy()) / safe_depth
    mae_norm = np.nanmean(np.abs(pct_error))
    mse_norm = np.nanmean(pct_error ** 2)
    rmse_norm = np.sqrt(mse_norm)

    return {
        "MAE": mae,
        "RMSE": rmse,
        "R2": r2,
        "MAE_Norm": mae_norm,
        "RMSE_Norm": rmse_norm,
    }


def evaluate_seed_subset(model_df, features, lake_ids, missingness_df, label):
    rows = []
    r2_values = []
    mae_values = []

    for lake_id in tqdm(lake_ids, desc=label, unit='lake'):
        test_lake_df = model_df[model_df['MIDAS'].astype(str).str.strip() == lake_id]
        train_lake_df = model_df[model_df['MIDAS'].astype(str).str.strip() != lake_id]
        if len(test_lake_df) < 2:
            continue

        model = CatBoostRegressor(**BEST_PARAMS)
        model.fit(train_lake_df[features], train_lake_df['SECCHI'])
        pred = model.predict(test_lake_df[features])
        metrics = evaluate_model(test_lake_df['SECCHI'], pred, test_lake_df['DEPTH_MAX_FEET'])

        pct_m = np.nan
        matches = missingness_df.loc[
            missingness_df['MIDAS'].astype(str).str.strip() == lake_id,
            'pct_missing_chemical_overall'
        ].values
        if len(matches) > 0:
            pct_m = matches[0]

        rows.append({
            'MIDAS': lake_id,
            'pct_missing_overall': round(pct_m, 4) if not np.isnan(pct_m) else pct_m,
            'n_obs': len(test_lake_df),
            'R2': round(metrics['R2'], 4),
            'MAE': round(metrics['MAE'], 4),
            'MAE_Norm': round(metrics['MAE_Norm'], 4),
        })
        r2_values.append(metrics['R2'])
        mae_values.append(metrics['MAE'])

    result_df = pd.DataFrame(rows)
    avg_r2 = float(np.nanmean(r2_values)) if r2_values else np.nan
    median_r2 = float(np.nanmedian(r2_values)) if r2_values else np.nan
    avg_mae = float(np.nanmean(mae_values)) if mae_values else np.nan
    return result_df, avg_r2, median_r2, avg_mae


def main() -> None:
    reports_dir = ensure_reports_dir()
    print('Loading dataset...')
    df = load_data().frame

    target = 'SECCHI'
    num_cols = ['LATITUDE', 'LONGITUDE', 'AREA_ACRES', 'DEPTH_MAX_FEET']
    base_features = ['year', 'month'] + num_cols
    chem_features = ['DOMAX', 'DOMIN', 'TPEC', 'TPBG', 'PH', 'COLOR', 'CONDUCT', 'ALK']
    valid_chems = [c for c in chem_features if c in df.columns]
    features = base_features + valid_chems

    subset_cols = [target, 'SAMPDATE', 'MIDAS'] + num_cols
    model_df = df.dropna(subset=subset_cols).copy().sort_values('SAMPDATE').reset_index(drop=True)

    missing_path = PROJECT_ROOT / 'data' / 'lake_missingness.csv'
    missingness_df = pd.read_csv(missing_path)

    ten_seed_path = PROJECT_ROOT / 'experiments' / 'scripts' / 'lolo_random_seed_10.txt'
    hundred_seed_path = PROJECT_ROOT / 'experiments' / 'scripts' / 'lolo_random_seed_100_seed42.txt'
    ten_lakes = [line.strip() for line in ten_seed_path.read_text(encoding='utf-8').splitlines() if line.strip()]
    hundred_lakes = [line.strip() for line in hundred_seed_path.read_text(encoding='utf-8').splitlines() if line.strip()]

    lake_counts = model_df['MIDAS'].astype(str).str.strip().value_counts().rename('n_obs').reset_index()
    lake_counts.columns = ['MIDAS', 'n_obs']
    quality_df = missingness_df[['MIDAS', 'pct_missing_chemical_overall']].copy()
    quality_df['MIDAS'] = quality_df['MIDAS'].astype(str).str.strip()
    quality_df = quality_df.merge(lake_counts, on='MIDAS', how='left')

    summary_rows = []
    detail_sections = []
    scenario_state = []

    for scenario in QUALITY_SCENARIOS:
        scenario_label = scenario['label']
        qualified = quality_df[
            (quality_df['n_obs'].fillna(0) >= scenario['min_obs']) &
            (quality_df['pct_missing_chemical_overall'].fillna(1.0) <= scenario['max_missing'])
        ]
        qualified_ids = set(qualified['MIDAS'].tolist())

        ten_filtered = [lake for lake in ten_lakes if lake in qualified_ids]
        hundred_filtered = [lake for lake in hundred_lakes if lake in qualified_ids]

        print(f"\nScenario: {scenario_label}")
        print(f"Seeded 10 lakes retained: {len(ten_filtered)} / {len(ten_lakes)}")
        print(f"Seeded 100 lakes retained: {len(hundred_filtered)} / {len(hundred_lakes)}")

        ten_df, ten_avg_r2, ten_median_r2, ten_avg_mae = evaluate_seed_subset(
            model_df, features, ten_filtered, missingness_df, f'{scenario_label} | LOLO x10'
        ) if ten_filtered else (pd.DataFrame(), np.nan, np.nan, np.nan)

        scenario_state.append({
            'scenario': scenario,
            'ten_filtered': ten_filtered,
            'hundred_filtered': hundred_filtered,
            'ten_df': ten_df,
            'ten_avg_r2': ten_avg_r2,
            'ten_median_r2': ten_median_r2,
            'ten_avg_mae': ten_avg_mae,
        })

    ranked_for_confirmation = sorted(
        scenario_state,
        key=lambda row: (float('-inf') if pd.isna(row['ten_avg_r2']) else row['ten_avg_r2']),
        reverse=True,
    )
    confirm_labels = {row['scenario']['label'] for row in ranked_for_confirmation[:TOP_X100_CONFIRMATIONS]}

    for row in scenario_state:
        scenario = row['scenario']
        scenario_label = scenario['label']
        hundred_filtered = row['hundred_filtered']
        hundred_df = pd.DataFrame()
        hundred_avg_r2 = np.nan
        hundred_median_r2 = np.nan
        hundred_avg_mae = np.nan

        if scenario_label in confirm_labels and hundred_filtered:
            print(f"\nConfirming top scenario on 100-lake sample: {scenario_label}")
            hundred_df, hundred_avg_r2, hundred_median_r2, hundred_avg_mae = evaluate_seed_subset(
                model_df, features, hundred_filtered, missingness_df, f'{scenario_label} | LOLO x100'
            )

        summary_rows.append({
            'scenario': scenario_label,
            'min_obs': scenario['min_obs'],
            'max_missing': scenario['max_missing'],
            'x10_lakes_retained': len(row['ten_filtered']),
            'x10_avg_R2': round(row['ten_avg_r2'], 4) if pd.notna(row['ten_avg_r2']) else np.nan,
            'x10_median_R2': round(row['ten_median_r2'], 4) if pd.notna(row['ten_median_r2']) else np.nan,
            'x10_avg_MAE': round(row['ten_avg_mae'], 4) if pd.notna(row['ten_avg_mae']) else np.nan,
            'x100_lakes_retained': len(hundred_filtered),
            'x100_avg_R2': round(hundred_avg_r2, 4) if pd.notna(hundred_avg_r2) else np.nan,
            'x100_median_R2': round(hundred_median_r2, 4) if pd.notna(hundred_median_r2) else np.nan,
            'x100_avg_MAE': round(hundred_avg_mae, 4) if pd.notna(hundred_avg_mae) else np.nan,
            'x100_confirmed': scenario_label in confirm_labels,
        })

        detail_sections.append((
            scenario_label,
            f"Qualified lakes retained in seeded 10-lake sample: {len(row['ten_filtered'])}\n\n"
            f"{df_to_markdown_table(row['ten_df'])}\n\n"
            f"Qualified lakes retained in seeded 100-lake sample: {len(hundred_filtered)}\n\n"
            f"100-lake confirmation executed: {'Yes' if scenario_label in confirm_labels else 'No'}\n\n"
            f"Top 10 of retained 100-lake results by R²:\n\n{df_to_markdown_table(hundred_df.sort_values(by='R2', ascending=False).head(10)) if not hundred_df.empty else '_(not run in 100-lake confirmation stage)_'}"
        ))

    summary_df = pd.DataFrame(summary_rows).sort_values(by=['x100_avg_R2', 'x10_avg_R2'], ascending=[False, False], na_position='last').reset_index(drop=True)

    plot_df = summary_df.melt(
        id_vars=['scenario'],
        value_vars=['x10_avg_R2', 'x100_avg_R2'],
        var_name='sample',
        value_name='avg_r2'
    )
    plt.figure(figsize=(12, 6))
    sns.barplot(data=plot_df, x='scenario', y='avg_r2', hue='sample')
    plt.axhline(0, color='black', linewidth=1, alpha=0.5)
    plt.xticks(rotation=25, ha='right')
    plt.title('LOLO Average R² Under Lake-Quality Threshold Policies')
    plt.xlabel('Quality-threshold scenario')
    plt.ylabel('Average LOLO R²')
    plt.tight_layout()
    summary_plot = reports_dir / '38_catboost_lolo_quality_thresholds.png'
    plt.savefig(summary_plot, bbox_inches='tight')
    plt.close()

    best_row = summary_df.iloc[0]
    report = CanonicalReport(
        objective=(
            'Test whether tuned native-missing CatBoost becomes materially more stable under LOLO when evaluation is restricted to higher-quality lakes. '
            'The goal is to identify whether observation count and chemistry missingness thresholds define a more trustworthy deployment region.'
        ),
        method=(
            'Use the tuned no-CHLA CatBoost model from Experiments 34 and 35. For each quality-threshold scenario, filter the fixed seeded 10-lake and seeded 100-lake LOLO sample files down to lakes that satisfy the required minimum observation count and maximum chemistry missingness. Screen all scenarios on the seeded 10-lake set first, then run the more expensive 100-lake confirmation only for the strongest scenarios by 10-lake average R² so the experiment stays rerunnable.'
        ),
        parameters=(
            f"Tuned CatBoost parameters: {BEST_PARAMS}\n\n"
            f"Feature set (CHLA excluded): {features}\n\n"
            f"Quality-threshold scenarios: {QUALITY_SCENARIOS}\n\n"
            f'Observation counts were computed from the full modeling frame after target/date/base-feature filtering. Lake missingness came from `data/lake_missingness.csv`. Top 100-lake confirmations run: {TOP_X100_CONFIRMATIONS}.'
        ),
        results=(
            '### Scenario Summary\n\n'
            f'{df_to_markdown_table(summary_df)}\n\n'
            '![Quality Threshold LOLO Summary](38_catboost_lolo_quality_thresholds.png)\n\n'
            + '\n\n'.join(
                f"### {title}\n\n{body}" for title, body in detail_sections[:4]
            )
        ),
        next_step=(
            f"The current best scenario by 100-lake average R² is `{best_row['scenario']}`. Use this result to decide whether the dashboard should expose predictions for all lakes or only for a higher-quality subset with stronger historical support."
        ),
    )

    report_path = write_canonical_report(
        '38_catboost_lolo_quality_thresholds.md',
        'Experiment 38: LOLO Quality Thresholds for Tuned CatBoost',
        report,
    )
    print(f'\nReport generated at {report_path}')


if __name__ == '__main__':
    main()
