import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from catboost import CatBoostRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from tqdm.auto import tqdm

from experiment_utils import ensure_reports_dir, write_markdown_report, df_to_markdown_table, load_data, PROJECT_ROOT

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


def evaluate_lake_set(model_df, features, missingness_df, lake_ids, label):
    results = []
    r2_list = []
    for lake_id in tqdm(lake_ids, desc=label, unit='lake'):
        test_lake_df = model_df[model_df['MIDAS'] == lake_id]
        train_lake_df = model_df[model_df['MIDAS'] != lake_id]
        if len(test_lake_df) < 2:
            continue

        model = CatBoostRegressor(**BEST_PARAMS)
        model.fit(train_lake_df[features], train_lake_df['SECCHI'])
        pred = model.predict(test_lake_df[features])
        metrics = evaluate_model(test_lake_df['SECCHI'], pred, test_lake_df['DEPTH_MAX_FEET'])

        pct_m = np.nan
        if not missingness_df.empty:
            matches = missingness_df.loc[missingness_df['MIDAS'] == lake_id, 'pct_missing_chemical_overall'].values
            if len(matches) > 0:
                pct_m = matches[0]

        r2_list.append(metrics['R2'])
        results.append({
            'MIDAS': lake_id,
            'pct_missing_overall': round(pct_m, 4) if not np.isnan(pct_m) else pct_m,
            'n_obs': len(test_lake_df),
            'R2': round(metrics['R2'], 4),
            'MAE': round(metrics['MAE'], 4),
            'MAE_Norm': round(metrics['MAE_Norm'], 4),
        })

    results_df = pd.DataFrame(results)
    avg_r2 = float(np.nanmean(r2_list)) if r2_list else np.nan
    return results_df, avg_r2


def main():
    reports_dir = ensure_reports_dir()
    print('Loading dataset...')
    data = load_data()
    df = data.frame

    target = 'SECCHI'
    num_cols = ['LATITUDE', 'LONGITUDE', 'AREA_ACRES', 'DEPTH_MAX_FEET']
    df['year'] = df['SAMPDATE'].dt.year
    df['month'] = df['SAMPDATE'].dt.month
    base_features = ['year', 'month'] + num_cols
    chem_features = ['DOMAX', 'DOMIN', 'TPEC', 'TPBG', 'PH', 'COLOR', 'CONDUCT', 'ALK']
    valid_chems = [c for c in chem_features if c in df.columns]

    subset_cols = [target, 'SAMPDATE', 'MIDAS'] + num_cols
    model_df = df.dropna(subset=subset_cols).copy()
    model_df = model_df.sort_values(by='SAMPDATE').reset_index(drop=True)
    features = base_features + valid_chems

    missing_path = PROJECT_ROOT / 'data' / 'lake_missingness.csv'
    missingness_df = pd.read_csv(missing_path) if missing_path.exists() else pd.DataFrame()

    ten_seed_path = PROJECT_ROOT / 'experiments' / 'scripts' / 'lolo_random_seed_10.txt'
    hundred_seed_path = PROJECT_ROOT / 'experiments' / 'scripts' / 'lolo_random_seed_100_seed42.txt'

    ten_lakes = [line.strip() for line in ten_seed_path.read_text(encoding='utf-8').splitlines() if line.strip()]
    hundred_lakes = [line.strip() for line in hundred_seed_path.read_text(encoding='utf-8').splitlines() if line.strip()]

    print(f'Evaluating tuned CatBoost on {len(ten_lakes)} seeded comparison lakes...')
    ten_df, ten_avg_r2 = evaluate_lake_set(model_df, features, missingness_df, ten_lakes, 'Tuned CatBoost LOLO x10')

    print(f'\nEvaluating tuned CatBoost on {len(hundred_lakes)} seeded random lakes (seed=42)...')
    hundred_df, hundred_avg_r2 = evaluate_lake_set(model_df, features, missingness_df, hundred_lakes, 'Tuned CatBoost LOLO x100')

    summary_df = pd.DataFrame([
        {'Lake Sample': 'Seeded comparison set (10 lakes)', 'n_lakes_evaluated': len(ten_df), 'avg_R2': round(ten_avg_r2, 4), 'median_R2': round(float(ten_df['R2'].median()), 4), 'avg_MAE': round(float(ten_df['MAE'].mean()), 4)},
        {'Lake Sample': 'Random sample (100 lakes, seed=42)', 'n_lakes_evaluated': len(hundred_df), 'avg_R2': round(hundred_avg_r2, 4), 'median_R2': round(float(hundred_df['R2'].median()), 4), 'avg_MAE': round(float(hundred_df['MAE'].mean()), 4)},
    ])

    plot_df = pd.concat([
        ten_df.assign(sample='10 lakes'),
        hundred_df.assign(sample='100 lakes'),
    ], ignore_index=True)

    plt.figure(figsize=(10, 6))
    sns.boxplot(data=plot_df, x='sample', y='R2', hue='sample', palette=['#2d6a4f', '#40916c'], legend=False)
    plt.axhline(0, color='black', linewidth=1, alpha=0.5)
    plt.title('Tuned CatBoost LOLO R2 Distribution')
    plt.xlabel('Lake sample')
    plt.ylabel('Per-lake R2')
    plot_path = reports_dir / '35_catboost_tuned_lolo_r2.png'
    plt.savefig(plot_path, bbox_inches='tight')
    plt.close()

    top_15 = hundred_df.sort_values(by='R2', ascending=False).head(15)
    bottom_15 = hundred_df.sort_values(by='R2', ascending=True).head(15)

    sections = [
        (
            'What We Did (Methodology)',
            'We fixed the tuned CatBoost parameters from Experiment 34 and used them for two leave-one-lake-out tests after excluding CHLA from the chemistry inputs. '
            'The first repeated the exact 10 seeded comparison lakes used earlier in the boosting experiments. '
            'The second evaluated a reproducible random 100-lake sample drawn with seed 42 from lakes with at least 20 valid observations so every run yields the same lake set and comparable average R².'
        ),
        (
            'Fixed Model Configuration',
            f'Tuned CatBoost parameters from Experiment 34: {BEST_PARAMS}\n\n'
            f'Feature set (CHLA excluded): {features}\n\n'
            f'Seeded 10-lake file: `{ten_seed_path.name}`\n'
            f'Seeded 100-lake file: `{hundred_seed_path.name}`'
        ),
        (
            'LOLO Summary Results',
            f"{df_to_markdown_table(summary_df)}\n\n"
            '![Tuned CatBoost LOLO R2 Distribution](35_catboost_tuned_lolo_r2.png)'
        ),
        (
            'Seeded 10-Lake Results',
            f"{df_to_markdown_table(ten_df)}\n\n"
            f"**Average LOLO R² (10 lakes):** {ten_avg_r2:.4f}"
        ),
        (
            'Random 100-Lake Results',
            'Top 15 lakes by LOLO R²:\n\n'
            f"{df_to_markdown_table(top_15)}\n\n"
            'Bottom 15 lakes by LOLO R²:\n\n'
            f"{df_to_markdown_table(bottom_15)}\n\n"
            f"**Average LOLO R² (100 lakes, seed=42):** {hundred_avg_r2:.4f}"
        ),
    ]

    report_path = write_markdown_report(
        '35_catboost_tuned_lolo.md',
        'Experiment 35: Tuned CatBoost Leave-One-Lake-Out Evaluation',
        sections,
    )
    print(f'\nReport generated at {report_path}')


if __name__ == '__main__':
    main()
