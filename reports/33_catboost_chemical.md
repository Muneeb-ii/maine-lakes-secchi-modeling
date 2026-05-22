# Experiment 33: Native Missingness Chemical Processing (CatBoost)

## What We Did (Methodology)

Following Experiments 20 and 21, we deployed **CatBoost** on the identical chemistry-enriched setup. Like the other boosted-tree baselines, CatBoost can retain rows with missing chemistry instead of forcing global imputation or row deletion. This lets us preserve the same broad geographic-temporal training base while still testing whether chemistry helps when present.

We loaded the baseline geographic limits and the chemical subset: `['DOMAX', 'DOMIN', 'TPEC', 'TPBG', 'CHLA', 'PH', 'COLOR', 'CONDUCT', 'ALK']`. By preserving native missingness, CatBoost trained on **154,304** usable rows.

## 80/20 Chronological Results

Predicting strictly out-of-time (the latest 20% temporal split) yielded:

- **R-Squared (R²):** 0.7280
- **Mean Absolute Error (MAE):** 0.8180 meters
- **Root Mean Squared Error (RMSE):** 1.0992 meters
- **Normalized MAE:** 0.0197
- **Normalized RMSE:** 0.0296

## Predicting Completely Unseen Lakes (LOLO)

We evaluated CatBoost on the same seeded 10 target lake IDs used by the XGBoost and LightGBM tests. This keeps the comparison aligned across boosting families even though full row context can differ slightly. The table below shows lake-level performance and the overall average LOLO $R^2$ for this run:

| MIDAS | pct_missing_overall | n_obs | R2 | MAE | MAE_Norm |
| --- | --- | --- | --- | --- | --- |
| c0157 | 0.952 | 117 | -27.644 | 1.079 | 0.064 |
| c3420 | 0.606 | 610 | -5.053 | 1.968 | 0.027 |
| c3814 | 0.596 | 1073 | 0.111 | 1.477 | 0.053 |
| c3180 | 0.91 | 80 | -0.191 | 0.922 | 0.021 |
| c0224 | 0.968 | 390 | -5.959 | 5.176 | 0.026 |
| c3448 | 0.399 | 427 | -1.436 | 1.262 | 0.026 |
| c5242 | 0.664 | 451 | -0.244 | 0.701 | 0.025 |
| c3712 | 0.71 | 579 | 0.006 | 0.58 | 0.015 |
| c2222 | 0.91 | 80 | -1.8 | 0.948 | 0.05 |
| c3132 | 0.608 | 628 | -0.046 | 0.508 | 0.009 |

**CatBoost Average LOLO $R^2$:** -4.2258

## Feature Importances

Measured using CatBoost's native feature importance scores after training with missing values left intact.

| Feature | Importance |
| --- | --- |
| DEPTH_MAX_FEET | 27.568 |
| LONGITUDE | 21.347 |
| AREA_ACRES | 17.757 |
| LATITUDE | 17.566 |
| year | 6.413 |
| CHLA | 3.509 |
| month | 2.713 |
| TPEC | 0.76 |
| DOMAX | 0.738 |
| COLOR | 0.64 |
| DOMIN | 0.5 |
| ALK | 0.366 |
| CONDUCT | 0.06 |
| PH | 0.046 |
| TPBG | 0.018 |

![CatBoost Importances](33_catboost_importances.png)
