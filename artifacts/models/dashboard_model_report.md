# Dashboard Model Report

## Active Model

- Model family: `CatBoostRegressor`
- Model source: Experiment 34 tuned native-missing CatBoost, promoted with Experiment 38 support policy
- CHLA policy: excluded from Secchi prediction features
- Artifact: `catboost_predictor.joblib`

## Support Policy

The dashboard is restricted to lakes with:

- observations after base filtering >= 100
- `pct_missing_chemical_overall` <= 0.90

### Coverage

| Metric | Count |
| :--- | ---: |
| Total lakes after base filtering | 1,011 |
| Supported lakes | 360 |
| Unsupported lakes | 651 |
| Total rows after base filtering | 163,185 |
| Supported rows | 151,686 |
| Unsupported rows | 11,499 |

## Proof Trail

| Experiment | Report | Dashboard relevance |
| :--- | :--- | :--- |
| 34 | `reports/34_catboost_tuned.md` | Tuned no-CHLA native-missing CatBoost reached chronological R2 0.7324, MAE 0.8122, RMSE 1.0903. |
| 35 | `reports/35_catboost_tuned_lolo.md` | Unrestricted tuned CatBoost LOLO remained weak: x10 average R2 -1.3806 and x100 average R2 -2.2441. |
| 37 | `reports/37_catboost_imputation.md` | MissForest imputation made tuned CatBoost worse than native missing-value handling. |
| 38 | `reports/38_catboost_lolo_quality_thresholds.md` | Restricting to obs >= 100 and missingness <= 0.90 improved confirmed x100 LOLO average R2 to -1.084. |

## Chronological Evaluation On Supported Lakes

| Metric | Value |
| :--- | ---: |
| R2 | 0.733352 |
| MAE | 0.792873 m |
| RMSE | 1.083157 m |
| Normalized MAE | 0.017972 |
| Normalized RMSE | 0.025826 |

## Feature Set

[
  "year",
  "month",
  "LATITUDE",
  "LONGITUDE",
  "AREA_ACRES",
  "DEPTH_MAX_FEET",
  "DOMAX",
  "DOMIN",
  "TPEC",
  "TPBG",
  "PH",
  "COLOR",
  "CONDUCT",
  "ALK"
]

## Feature Importances

| Feature | Importance |
| :--- | ---: |
| COLOR | 27.992654 |
| DEPTH_MAX_FEET | 13.977690 |
| year | 8.703900 |
| CONDUCT | 8.264948 |
| AREA_ACRES | 7.640370 |
| LONGITUDE | 6.778320 |
| LATITUDE | 6.111150 |
| ALK | 5.846726 |
| PH | 5.807372 |
| month | 4.686127 |
| TPEC | 1.633503 |
| DOMAX | 1.337252 |
| DOMIN | 1.057873 |
| TPBG | 0.162115 |
