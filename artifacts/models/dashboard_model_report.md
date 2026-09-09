# Dashboard Model Report

## Active Model

- Model family: `CatBoostRegressor`
- Model source: Experiment 34 hyperparameters (2025 snapshot), Experiment 47 June feature contract
- Served weights: trained on **all** supported-lake rows in the June snapshot
- Reported metrics: 80/20 chronological holdout fit (not the served weights)
- CHLA policy: excluded from Secchi prediction features
- Editable scenario inputs: ['DOMAX', 'DOMIN', 'TMAX', 'TMIN', 'TPEC', 'TPBG']
- Locked lake chemistry descriptors (fixed lake means): ['PH', 'COLOR', 'CONDUCT', 'ALK']
- Artifact: `catboost_predictor.joblib`

## Support Policy

Lakes are selectable when they have at least 100 observations after base filtering.
The inherited Experiment 38 chemistry-missingness cutoff (`pct_missing_chemical_overall` <= 0.90) remains in the filter but is nearly inert on this snapshot.

Supported lakes whose measured slider fields (['DOMAX', 'DOMIN', 'TMAX', 'TMIN', 'TPEC', 'TPBG']) are missing on more than
90% of records stay selectable and are flagged `thin_history`
(Experiment 47). The playground warns that slider effects lean on other lakes.

### Coverage

| Metric | Count |
| :--- | ---: |
| Total lakes after base filtering | 1,011 |
| Supported lakes | 360 |
| Thin-history supported lakes | 152 |
| Unsupported lakes | 651 |
| Total rows after base filtering | 163,185 |
| Supported rows | 151,686 |
| Unsupported rows | 11,499 |

## Proof Trail

| Experiment | Report | Dashboard relevance |
| :--- | :--- | :--- |
| 34 | `reports/34_catboost_tuned.md` | On the 2025 snapshot, tuned no-CHLA native-missing CatBoost reached chronological R2 0.7324, MAE 0.8122, RMSE 1.0903. Those hyperparameters were transferred to the June model without retuning. |
| 35 | `reports/35_catboost_tuned_lolo.md` | On the 2025 snapshot, unrestricted tuned CatBoost LOLO remained weak: x10 average R2 -1.3806 and x100 average R2 -2.2441. |
| 37 | `reports/37_catboost_imputation.md` | On the 2025 snapshot, MissForest imputation made tuned CatBoost worse than native missing-value handling. |
| 38 | `reports/38_catboost_lolo_quality_thresholds.md` | On the 2025 snapshot, restricting evaluation to obs >= 100 and chemistry missingness <= 0.90 improved confirmed x100 LOLO average R2 to -1.084. That missingness statistic does not transfer to the June snapshot (see Experiment 47). |
| 47 | `reports/47_playground_feature_contract.md` | On the June snapshot, the 16-feature measured-plus-locked-chemistry contract matched the legacy 14-feature chronological accuracy (R2 0.734 vs 0.733). Leave-one-lake-out on the retained 2025 seed lakes stayed negative (catalog-policy x100 average R2 -0.571). n_obs >= 100 is the operative support rule; 152 supported lakes are flagged thin_history. |

## Chronological Holdout On Supported Lakes

These scores come from a date-ordered 80/20 split used only for reporting. The served joblib is a separate fit on all supported rows.

Holdout window: 2017–2024.

| Metric | Value |
| :--- | ---: |
| R2 | 0.734226 |
| MAE | 0.789173 m |
| RMSE | 1.081381 m |
| Normalized MAE | 0.017959 |
| Normalized RMSE | 0.025892 |

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
  "TMAX",
  "TMIN",
  "TPEC",
  "TPBG",
  "PH",
  "COLOR",
  "CONDUCT",
  "ALK"
]

## Feature Importances

Importances below are from the served (full-data) model.

| Feature | Importance |
| :--- | ---: |
| COLOR | 26.610828 |
| DEPTH_MAX_FEET | 14.045115 |
| CONDUCT | 8.928092 |
| year | 8.767708 |
| LONGITUDE | 7.725074 |
| AREA_ACRES | 6.989427 |
| LATITUDE | 6.221430 |
| ALK | 5.133856 |
| PH | 4.901971 |
| month | 4.583323 |
| TPEC | 1.904458 |
| DOMAX | 1.326519 |
| TMAX | 1.062349 |
| DOMIN | 0.835984 |
| TMIN | 0.780593 |
| TPBG | 0.183272 |
