# Secchi Dataset – Feature Necessity & Recommended Variable Sets

## Overview

This report combines missingness, redundancy, and association with `SECCHI` to
propose variable categories and recommended feature sets for modeling.

- **Core variables** (identifiers/target): MIDAS, SAMPDATE, SECCHI
- **Number of high‑value predictors**: 13
- **Number of highly correlated predictor pairs (|r| ≥ 0.8)**: 9

## Variable categories and metrics

| variable | category | pct_missing | abs_corr_with_SECCHI | redundant_with |
| --- | --- | --- | --- | --- |
| LAKE_NAME | categorical_or_date | 0.005 |  |  |
| REGION | categorical_or_date | 0.0 |  |  |
| SECCBOT | categorical_or_date | 0.222 |  |  |
| WATER_QUALITY_STATEMENT | categorical_or_date | 4.436 |  |  |
| TROPHIC_CATEGORY | categorical_or_date | 0.637 |  |  |
| TOWNS | categorical_or_date | 0.005 |  |  |
| COUNTY | categorical_or_date | 0.005 |  |  |
| USGS_QUAD24 | categorical_or_date | 0.005 |  |  |
| MAJOR_DRAINAGE | categorical_or_date | 0.674 |  |  |
| SUB_DRAINAGE | categorical_or_date | 0.674 |  |  |
| HUC10_NAME | categorical_or_date | 0.005 |  |  |
| INVASIVE_PLANT_INFESTATION | categorical_or_date | 0.005 |  |  |
| FISHERY_MANAGEMENT | categorical_or_date | 1.046 |  |  |
| date | categorical_or_date | 0.0 |  |  |
| season | categorical_or_date | 0.0 |  |  |
| MIDAS | core_identifier_or_target | 0.0 |  |  |
| SAMPDATE | core_identifier_or_target | 0.0 |  |  |
| SECCHI | core_identifier_or_target | 0.0 |  |  |
| DEPTH_MEAN_FEET | high_value_predictor | 1.865 | 0.519 | DEPTH_MAX_FEET |
| DEPTH_MAX_FEET | high_value_predictor | 1.353 | 0.48 | DEPTH_MEAN_FEET, OXIC |
| FLUSHING_RATE_TIMES_YR | high_value_predictor | 3.0 | 0.291 |  |
| DAM | high_value_predictor | 1.214 | 0.174 |  |
| HUC10_CODE | high_value_predictor | 0.005 | 0.171 |  |
| VOLUME_ACREFEET | high_value_predictor | 3.0 | 0.161 | AREA_ACRES |
| AREA_ACRES | high_value_predictor | 0.039 | 0.106 | DIRECT_DRAINAGE_AREA_SQ_MILES, PERIMETER_MILES, VOLUME_ACREFEET |
| ELEVATION_FEET | high_value_predictor | 0.005 | 0.082 |  |
| year | high_value_predictor | 0.0 | 0.082 |  |
| DELORME_PAGE | high_value_predictor | 0.005 | 0.081 | LATITUDE, UTM_Y |
| PERIMETER_MILES | high_value_predictor | 0.348 | 0.081 | AREA_ACRES |
| UTM_Y | high_value_predictor | 0.005 | 0.072 | DELORME_PAGE, LATITUDE |
| LATITUDE | high_value_predictor | 0.005 | 0.071 | DELORME_PAGE, UTM_Y |
| TPEC | low_value_or_problematic | 82.552 | 0.549 |  |
| OXIC | low_value_or_problematic | 74.319 | 0.53 | DEPTH_MAX_FEET |
| CHLA | low_value_or_problematic | 81.03 | 0.507 |  |
| COLOR | low_value_or_problematic | 88.298 | 0.504 |  |
| SCHMIDT | low_value_or_problematic | 71.809 | 0.474 |  |
| TMIN | low_value_or_problematic | 71.809 | 0.397 |  |
| DOMAX | low_value_or_problematic | 74.319 | 0.317 |  |
| MLD | low_value_or_problematic | 71.809 | 0.292 |  |
| ALK | low_value_or_problematic | 86.904 | 0.281 |  |
| CONDUCT | low_value_or_problematic | 90.793 | 0.158 |  |
| TPBG | low_value_or_problematic | 95.545 | 0.09 |  |
| TMAX | low_value_or_problematic | 71.809 | 0.065 |  |
| PH | low_value_or_problematic | 89.359 | 0.035 |  |
| TOTAL_DRAINAGE_AREA_SQ_MILES | low_value_or_problematic | 3.783 | 0.031 |  |
| LONGITUDE | low_value_or_problematic | 0.005 | 0.029 | UTM_X |
| UTM_X | low_value_or_problematic | 0.005 | 0.029 | LONGITUDE |
| DIRECT_DRAINAGE_AREA_SQ_MILES | low_value_or_problematic | 3.0 | 0.016 | AREA_ACRES |
| STATION | low_value_or_problematic | 0.0 | 0.012 |  |
| month | low_value_or_problematic | 0.0 | 0.011 |  |
| DOMIN | low_value_or_problematic | 74.319 | 0.009 |  |

## Highly correlated predictor pairs

| var1 | var2 | corr | abs_corr |
| --- | --- | --- | --- |
| LONGITUDE | UTM_X | 1.0 | 1.0 |
| LATITUDE | UTM_Y | 1.0 | 1.0 |
| LATITUDE | DELORME_PAGE | 0.976 | 0.976 |
| UTM_Y | DELORME_PAGE | 0.976 | 0.976 |
| AREA_ACRES | PERIMETER_MILES | 0.918 | 0.918 |
| AREA_ACRES | VOLUME_ACREFEET | 0.911 | 0.911 |
| DEPTH_MEAN_FEET | DEPTH_MAX_FEET | 0.894 | 0.894 |
| OXIC | DEPTH_MAX_FEET | 0.865 | 0.865 |
| AREA_ACRES | DIRECT_DRAINAGE_AREA_SQ_MILES | 0.808 | 0.808 |

## Proposed minimal feature set

- `MIDAS`
- `SAMPDATE`
- `SECCHI`
- `DEPTH_MEAN_FEET`
- `DEPTH_MAX_FEET`
- `FLUSHING_RATE_TIMES_YR`
- `DAM`
- `HUC10_CODE`
- `VOLUME_ACREFEET`
- `AREA_ACRES`
- `ELEVATION_FEET`

## Proposed extended feature set

- `MIDAS`
- `SAMPDATE`
- `SECCHI`
- `DEPTH_MEAN_FEET`
- `DEPTH_MAX_FEET`
- `FLUSHING_RATE_TIMES_YR`
- `DAM`
- `HUC10_CODE`
- `VOLUME_ACREFEET`
- `AREA_ACRES`
- `ELEVATION_FEET`
- `year`
- `DELORME_PAGE`
- `PERIMETER_MILES`
- `UTM_Y`
- `LATITUDE`
