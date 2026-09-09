# Experiment 49: Trends Baseline Replacement Protocol

## Objective

Freeze a replacement test for the served Trends local-level baseline, then apply it. Experiment 48 may rank a simpler level model higher on historical MAE; this experiment decides whether that is enough to swap the dashboard.

## Method

Read Experiment 48's model-specific later-origin predictions. Compare the incumbent local-level model with the 10-year calendar mean, EWMA (alpha 0.20), and last-10-observed-year mean on full-support five-year cases. Gates were written before looking at post-2024 data: model-specific 80%/95% coverage in the stated bands, MAE at least 0.02 m better than local-level, better MAE on a majority of lakes, worse MAE in at most one region, and independent outcomes after 2024. The 2020–2024 window is reported as a dry run and cannot authorize a swap.

## Parameters

Dataset ID: `secchi-merged-2026-06-29-r1`. Incumbent: `Local-level state-space`. Challengers: ['Recent 10-calendar-year mean', 'EWMA alpha 0.20', 'Last 10 observed-year mean']. Confirmation: split `later`, horizon 5, support `Full`. Independent outcomes required after 2024.

## Results

### Dry-run metrics (2020–2024 outcomes; not independent)

| model | role | n_cases | n_lakes | MAE | coverage_80 | coverage_95 | mae_improvement_vs_incumbent | pct_lakes_better_mae | regions_worse_than_incumbent | coverage_gate | mae_gate | lake_gate | region_gate | independent_outcomes_gate | would_replace |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Local-level state-space | incumbent | 1402 | 339 | 0.6353 | 0.7782 | 0.9451 | 0.0 |  | 0 | True | True | True | True | False | False |
| Recent 10-calendar-year mean | challenger | 1402 | 339 | 0.6111 | 0.7903 | 0.9479 | 0.0242 | 56.6372 | 1 | True | True | True | True | False | False |
| EWMA alpha 0.20 | challenger | 1402 | 339 | 0.6122 | 0.7882 | 0.9451 | 0.0232 | 60.767 | 1 | True | True | True | True | False | False |
| Last 10 observed-year mean | challenger | 1402 | 339 | 0.6152 | 0.7953 | 0.9515 | 0.0201 | 53.6873 | 2 | True | True | True | False | False | False |

**Independent post-2024 outcomes available:** False.

**Decision:** Keep the served local-level Trends baseline. No challenger may replace it until post-2024 outcomes exist and the remaining gates pass on that window.

Artifacts: `49_trends_replacement_metrics.csv`, `49_trends_replacement_assessment.json`.

## Next Step

Rerun this experiment when the processed snapshot includes summer outcomes after 2024. Until then, keep the Experiment 46 local-level outlook on the dashboard.
