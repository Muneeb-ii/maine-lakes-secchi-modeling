# Experiment 45: Forecast Release Decision

## Objective

Record the formal release decision for a skillful multi-year Secchi forecast. This experiment applies the stated gates to Experiments 40–44; it is not a new model.

## Method

Read rolling-origin outputs from Experiments 40–44. A candidate may be released only if it beats last-value and recent-mean baselines at five years, has MASE below 1, improves on a majority of lakes, and has 80% and 95% interval coverage within 0.10 of nominal. Ten-year release requires the same at both horizons. Bayesian candidates also require converged fits. Missing intervals fail the interval gate.

## Parameters

Dataset ID: `secchi-merged-2026-06-29-r1`. Decision horizons: 5 and 10 years. Sources: Experiment 40 baselines, 41 Bayesian state-space, 42 CatBoost, 43 GAM, 44 calibrated CatBoost.

## Results

### Gate results

| model | mae_h5 | mae_h10 | passes_h5 | passes_h10 | fit_valid |
| --- | --- | --- | --- | --- | --- |
| Recent 5-year mean | 0.5525 | 0.638 | False | False | True |
| Local-level state-space | 0.5594 | 0.6399 | False | False | True |
| Direct multi-horizon CatBoost | 0.5707 | 0.6504 | False | False | True |
| Calibrated CatBoost | 0.5707 | 0.6504 | False | False | True |
| Last annual value | 0.6342 | 0.7266 | False | False | True |
| Theil-Sen drift | 0.6527 | 0.833 | False | False | True |
| Hierarchical GAM | 0.7549 | 1.3342 | False | False | True |
| Bayesian hierarchical state-space | 0.8096 | 0.9565 | False | False | False |

**Selected model:** `None`.

**Maximum recommended skillful horizon:** **0 years**.

**Reason:** No candidate passed the five-year skill gates. A persistence baseline is not a passing forecast product under these gates, because beating the recent-mean baseline is required.

Detail tables remain in the source experiment reports. This file is the decision record only.

Artifact contract: `45_forecast_artifact_contract.json`.

## Next Step

Do not publish a skillful forecast. Experiment 46 evaluates a clearly labeled persistence outlook under a different bar. Experiment 49 is the later replacement test for that baseline.
