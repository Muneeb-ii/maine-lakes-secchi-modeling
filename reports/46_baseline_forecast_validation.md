# Experiment 46: Later-origin baseline forecast validation

## Objective

Validate whether recent-mean and local-level baselines can support a clearly labeled lower-complexity outlook with empirically calibrated uncertainty on later origins.

## Method

Evaluate only origins 2015–2019 for forecast years 2020–2024. Calibrate symmetric intervals from earlier matured residuals (1990–2014), requiring at least 19 residuals and enforcing nondecreasing half-widths over horizon. Fixed Full/ Limited support thresholds are descriptive and were not tuned on evaluation rows.

## Parameters

Dataset ID: `secchi-merged-2026-06-29-r1`. Models: Recent 5-year mean and local-level state-space. Horizons: 1–5 years. Evaluation origins: 2015–2019; calibration origins: 1990–2014.

## Results

### Metrics

| model | horizon | n_cases | n_lakes | MAE | RMSE | MASE | pct_lakes_beat_persistence | n_interval_80 | coverage_80 | width_80 | n_interval_95 | coverage_95 | width_95 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Recent 5-year mean | 1 | 318 | 318 | 0.479 | 0.6649 | 0.8992 | 57.8616 | 318 | 0.8113 | 1.5821 | 318 | 0.9497 | 2.8455 |
| Recent 5-year mean | 2 | 632 | 345 | 0.5119 | 0.7136 | 0.9361 | 51.5942 | 632 | 0.8149 | 1.679 | 632 | 0.9573 | 3.0406 |
| Recent 5-year mean | 3 | 944 | 364 | 0.5225 | 0.748 | 0.964 | 59.0659 | 944 | 0.8316 | 1.7602 | 944 | 0.9534 | 3.1325 |
| Recent 5-year mean | 4 | 1231 | 370 | 0.6398 | 0.8861 | 1.1598 | 48.6486 | 1231 | 0.7612 | 1.7921 | 1231 | 0.9261 | 3.1654 |
| Recent 5-year mean | 5 | 1525 | 381 | 0.6458 | 0.893 | 1.1682 | 58.7927 | 1525 | 0.7652 | 1.8465 | 1525 | 0.937 | 3.3582 |
| Local-level state-space | 1 | 318 | 318 | 0.4763 | 0.6509 | 0.9015 | 65.7233 | 318 | 0.8239 | 1.5981 | 318 | 0.9434 | 2.7618 |
| Local-level state-space | 2 | 632 | 345 | 0.4876 | 0.6788 | 0.8896 | 62.3188 | 632 | 0.8307 | 1.6881 | 632 | 0.9652 | 3.0022 |
| Local-level state-space | 3 | 944 | 364 | 0.5114 | 0.7392 | 0.9475 | 64.5604 | 944 | 0.839 | 1.7873 | 944 | 0.9608 | 3.1683 |
| Local-level state-space | 4 | 1231 | 370 | 0.6115 | 0.8586 | 1.1096 | 57.5676 | 1231 | 0.7742 | 1.8081 | 1231 | 0.9383 | 3.2112 |
| Local-level state-space | 5 | 1525 | 381 | 0.6388 | 0.8952 | 1.1567 | 67.979 | 1525 | 0.7777 | 1.89 | 1525 | 0.943 | 3.3777 |

### Five-year support counts

| model | horizon | n_cases | n_lakes | MAE | RMSE | MASE | pct_lakes_beat_persistence | n_interval_80 | coverage_80 | width_80 | n_interval_95 | coverage_95 | width_95 | support_tier |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Recent 5-year mean | 5 | 1402 | 339 | 0.6411 | 0.882 | 1.1322 | 61.9469 | 1402 | 0.7675 | 1.8466 | 1402 | 0.9387 | 3.3602 | Full |
| Local-level state-space | 5 | 1402 | 339 | 0.6353 | 0.8823 | 1.127 | 69.3215 | 1402 | 0.7782 | 1.8904 | 1402 | 0.9451 | 3.3797 | Full |
| Recent 5-year mean | 5 | 123 | 62 | 0.6995 | 1.0096 | 1.5785 | 37.0968 | 123 | 0.7398 | 1.8446 | 123 | 0.9187 | 3.3351 | Limited |
| Local-level state-space | 5 | 123 | 62 | 0.6783 | 1.0305 | 1.4954 | 54.8387 | 123 | 0.7724 | 1.8855 | 123 | 0.9187 | 3.3547 | Limited |

### Group diagnostics (five-year MAE)

| model | group | level | horizon | MAE |
| --- | --- | --- | --- | --- |
| Recent 5-year mean | REGION | Coastal | 5 | 0.6301 |
| Recent 5-year mean | REGION | Inland | 5 | 0.6915 |
| Recent 5-year mean | REGION | Northern | 5 | 0.6853 |
| Recent 5-year mean | Bottom-hit rate >= 0.5 | No | 5 | 0.6538 |
| Recent 5-year mean | Bottom-hit rate >= 0.5 | Yes | 5 | 0.5436 |
| Local-level state-space | REGION | Coastal | 5 | 0.6338 |
| Local-level state-space | REGION | Inland | 5 | 0.6563 |
| Local-level state-space | REGION | Northern | 5 | 0.6159 |
| Local-level state-space | Bottom-hit rate >= 0.5 | No | 5 | 0.6462 |
| Local-level state-space | Bottom-hit rate >= 0.5 | Yes | 5 | 0.5447 |

Local-level state-space is the lower-MAE five-year baseline in this later-origin check and has empirically near-nominal pooled interval coverage; a clearly labeled persistence outlook is defensible only with support tiers and interval availability exposed. This is descriptive evidence, does not establish trend skill, and does not waive or satisfy the registered Experiment 45 release gates.

Artifacts: `46_baseline_forecast_validation.csv`, `46_baseline_calibration_residuals.csv`, `46_baseline_forecast_assessment.json`, `46_baseline_forecast_metrics.csv`, `46_baseline_support_metrics.csv`, and `46_baseline_forecast_validation.png`. Intervals are empirical pooled-residual intervals; they do not establish formal nominal coverage. The later-origin check is retrospective rather than pristine holdout validation.

## Next Step

The labeled persistence outlook is what Trends serves. Experiment 48 is a simple-model challenger; Experiment 49 is the predefined replacement test and requires post-2024 outcomes before any swap.
