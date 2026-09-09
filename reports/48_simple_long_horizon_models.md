# Experiment 48: Simple long-horizon level models

## Objective

Test a small, transparent family of level-based models for long-horizon annual summer Secchi prediction, with the existing local-level model retained as a comparator.

## Method

Evaluate fixed calendar-window means, last-observed-year means, fixed exponential smoothing, fixed shrinkage between recent and long-run lake levels, and the existing local-level state-space model. Use rolling origins 2005–2014 for development and 2015–2019 for a later-origin check against 2020–2024 outcomes. Calibrate symmetric empirical intervals from earlier outcome-matured residuals, with a separate width curve per model.

## Parameters

Dataset ID: `secchi-merged-2026-06-29-r1`. Development horizons: (1, 3, 5, 10); later-origin horizons: (1, 2, 3, 4, 5). Calendar means use observations in the preceding calendar window; observed-year means use the last N available lake-years. EWMA alphas: 0.10, 0.20, 0.30. Recent/long-run shrinkage weights: 25/75, 50/50, 75/25. Full support: at least 10 observed years and no more than a two-year gap; limited support is retained for diagnostics.

## Results

### Development full-support ranking (mean MAE across 5- and 10-year horizons)

| model | mean_MAE_h5_h10 |
| --- | --- |
| EWMA alpha 0.20 | 0.5713 |
| EWMA alpha 0.30 | 0.5716 |
| Shrink recent/long-run 75/25 | 0.5751 |
| Last 5 observed-year mean | 0.5773 |
| Recent 10-calendar-year mean | 0.5776 |

### Later-origin full-support results at five years

| split | support_tier | model | horizon | n_cases | n_lakes | MAE | RMSE | mean_bias | MASE | pct_lakes_beat_naive | n_interval_80 | coverage_80 | width_80 | n_interval_95 | coverage_95 | width_95 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| later | Full | Recent 10-calendar-year mean | 5 | 1402 | 339 | 0.6111 | 0.8586 | -0.0021 | 1.0761 | 70.2065 | 1402 | 0.7903 | 1.8448 | 1402 | 0.9479 | 3.2689 |
| later | Full | EWMA alpha 0.20 | 5 | 1402 | 339 | 0.6122 | 0.8696 | 0.0472 | 1.0789 | 70.5015 | 1402 | 0.7882 | 1.8291 | 1402 | 0.9451 | 3.2998 |
| later | Full | Last 10 observed-year mean | 5 | 1402 | 339 | 0.6152 | 0.8789 | -0.0111 | 1.0813 | 68.1416 | 1402 | 0.7953 | 1.8619 | 1402 | 0.9515 | 3.2894 |
| later | Full | EWMA alpha 0.30 | 5 | 1402 | 339 | 0.6198 | 0.8753 | 0.0944 | 1.0936 | 70.7965 | 1402 | 0.776 | 1.8141 | 1402 | 0.9387 | 3.2457 |
| later | Full | Shrink recent/long-run 50/50 | 5 | 1402 | 339 | 0.6221 | 0.8668 | 0.0147 | 1.0976 | 67.5516 | 1402 | 0.7817 | 1.8103 | 1402 | 0.9401 | 3.1782 |
| later | Full | Shrink recent/long-run 75/25 | 5 | 1402 | 339 | 0.6243 | 0.8643 | 0.0608 | 1.1013 | 68.4366 | 1402 | 0.7725 | 1.8166 | 1402 | 0.9415 | 3.2357 |
| later | Full | EWMA alpha 0.10 | 5 | 1402 | 339 | 0.6262 | 0.8932 | -0.0339 | 1.1006 | 67.2566 | 1402 | 0.8131 | 1.9726 | 1402 | 0.9529 | 3.4918 |
| later | Full | Shrink recent/long-run 25/75 | 5 | 1402 | 339 | 0.6324 | 0.8893 | -0.0315 | 1.1159 | 65.4867 | 1402 | 0.7775 | 1.8558 | 1402 | 0.9444 | 3.2139 |

The later-origin table is the most relevant historical check. Interval widths are model-specific. Experiment 49 decides whether any challenger may replace the served Trends baseline.

Artifacts: `48_simple_long_horizon_predictions.csv`, `48_simple_long_horizon_metrics.csv`, and `48_simple_long_horizon_models.png`.

## Next Step

Experiment 49 is the predefined replacement test. Point metrics here may rank a challenger ahead of local-level; that is not a license to swap the served Trends model until Experiment 49's independent-outcome gate can be evaluated.
