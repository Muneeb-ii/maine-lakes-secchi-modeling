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
| Total lakes after base filtering | 994 |
| Supported lakes | 187 |
| Unsupported lakes | 807 |
| Total rows after base filtering | 154,304 |
| Supported rows | 87,116 |
| Unsupported rows | 67,188 |

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
| R2 | 0.721993 |
| MAE | 0.802358 m |
| RMSE | 1.087382 m |
| Normalized MAE | 0.017751 |
| Normalized RMSE | 0.025338 |

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
| DEPTH_MAX_FEET | 29.113977 |
| LONGITUDE | 21.597720 |
| LATITUDE | 16.484699 |
| AREA_ACRES | 15.237715 |
| year | 6.788923 |
| month | 4.163235 |
| TPEC | 2.988308 |
| DOMAX | 1.350616 |
| COLOR | 0.941409 |
| DOMIN | 0.856974 |
| ALK | 0.200811 |
| PH | 0.165890 |
| CONDUCT | 0.060517 |
| TPBG | 0.049206 |
