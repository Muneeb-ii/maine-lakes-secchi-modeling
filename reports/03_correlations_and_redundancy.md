# Secchi Dataset – Correlations & Predictor Redundancy

## Overview

This report examines Pearson correlations among numeric predictor variables,
excluding the target `SECCHI`, to identify redundancy.

Number of predictor pairs with valid correlations: **528**

Strongly correlated pairs (e.g. |r| ≥ 0.7) are of particular interest, as they
indicate potential redundancy among predictors.

## Top correlated predictor pairs (by |r|)

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
| DIRECT_DRAINAGE_AREA_SQ_MILES | TOTAL_DRAINAGE_AREA_SQ_MILES | 0.782 | 0.782 |
| PERIMETER_MILES | DIRECT_DRAINAGE_AREA_SQ_MILES | 0.78 | 0.78 |
| OXIC | DEPTH_MEAN_FEET | 0.777 | 0.777 |
| PERIMETER_MILES | VOLUME_ACREFEET | 0.774 | 0.774 |
| SCHMIDT | DEPTH_MEAN_FEET | 0.719 | 0.719 |
| LATITUDE | HUC10_CODE | -0.706 | 0.706 |
| UTM_Y | HUC10_CODE | -0.703 | 0.703 |
| OXIC | SCHMIDT | 0.701 | 0.701 |
| AREA_ACRES | TOTAL_DRAINAGE_AREA_SQ_MILES | 0.7 | 0.7 |
| UTM_X | DELORME_PAGE | 0.693 | 0.693 |
| LONGITUDE | DELORME_PAGE | 0.693 | 0.693 |
| VOLUME_ACREFEET | DIRECT_DRAINAGE_AREA_SQ_MILES | 0.685 | 0.685 |
| SCHMIDT | DEPTH_MAX_FEET | 0.675 | 0.675 |
| DELORME_PAGE | HUC10_CODE | -0.674 | 0.674 |
| PERIMETER_MILES | TOTAL_DRAINAGE_AREA_SQ_MILES | 0.648 | 0.648 |
| LATITUDE | UTM_X | 0.626 | 0.626 |
| LATITUDE | LONGITUDE | 0.625 | 0.625 |
| UTM_X | UTM_Y | 0.621 | 0.621 |
| LONGITUDE | UTM_Y | 0.62 | 0.62 |
| VOLUME_ACREFEET | TOTAL_DRAINAGE_AREA_SQ_MILES | 0.598 | 0.598 |
| TPEC | CHLA | 0.583 | 0.583 |
| DEPTH_MAX_FEET | VOLUME_ACREFEET | 0.579 | 0.579 |
| PERIMETER_MILES | DEPTH_MAX_FEET | 0.551 | 0.551 |
| AREA_ACRES | DEPTH_MAX_FEET | 0.546 | 0.546 |
| TMIN | OXIC | -0.522 | 0.522 |
| TPBG | CONDUCT | 0.518 | 0.518 |
| DEPTH_MEAN_FEET | VOLUME_ACREFEET | 0.513 | 0.513 |
| TMAX | DOMIN | -0.498 | 0.498 |
| TMIN | DEPTH_MAX_FEET | -0.491 | 0.491 |
| MLD | OXIC | 0.474 | 0.474 |
| TMIN | DOMAX | -0.474 | 0.474 |
| ALK | HUC10_CODE | -0.466 | 0.466 |
| DEPTH_MAX_FEET | DIRECT_DRAINAGE_AREA_SQ_MILES | 0.462 | 0.462 |
| MLD | DEPTH_MAX_FEET | 0.459 | 0.459 |
| PH | ALK | 0.453 | 0.453 |
| MLD | DEPTH_MEAN_FEET | 0.449 | 0.449 |
| CONDUCT | ALK | 0.448 | 0.448 |
| AREA_ACRES | DEPTH_MEAN_FEET | 0.441 | 0.441 |
| TMIN | DEPTH_MEAN_FEET | -0.435 | 0.435 |
| TMIN | SCHMIDT | -0.429 | 0.429 |
| OXIC | VOLUME_ACREFEET | 0.424 | 0.424 |

## Strongly correlated predictor pairs (|r| ≥ 0.7)

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
| DIRECT_DRAINAGE_AREA_SQ_MILES | TOTAL_DRAINAGE_AREA_SQ_MILES | 0.782 | 0.782 |
| PERIMETER_MILES | DIRECT_DRAINAGE_AREA_SQ_MILES | 0.78 | 0.78 |
| OXIC | DEPTH_MEAN_FEET | 0.777 | 0.777 |
| PERIMETER_MILES | VOLUME_ACREFEET | 0.774 | 0.774 |
| SCHMIDT | DEPTH_MEAN_FEET | 0.719 | 0.719 |
| LATITUDE | HUC10_CODE | -0.706 | 0.706 |
| UTM_Y | HUC10_CODE | -0.703 | 0.703 |
| OXIC | SCHMIDT | 0.701 | 0.701 |
| AREA_ACRES | TOTAL_DRAINAGE_AREA_SQ_MILES | 0.7 | 0.7 |

## Correlation matrix snippet (predictors only)

| variable | STATION | TMAX | TMIN | DOMAX | DOMIN | MLD | OXIC | SCHMIDT |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| STATION | 1.0 | -0.01 | 0.05 | -0.06 | -0.02 | 0.03 | -0.07 | -0.09 |
| TMAX | -0.01 | 1.0 | 0.22 | -0.31 | -0.5 | -0.21 | -0.12 | 0.23 |
| TMIN | 0.05 | 0.22 | 1.0 | -0.47 | 0.12 | -0.18 | -0.52 | -0.43 |
| DOMAX | -0.06 | -0.31 | -0.47 | 1.0 | 0.29 | 0.08 | 0.33 | 0.24 |
| DOMIN | -0.02 | -0.5 | 0.12 | 0.29 | 1.0 | 0.06 | 0.21 | 0.05 |
| MLD | 0.03 | -0.21 | -0.18 | 0.08 | 0.06 | 1.0 | 0.47 | 0.2 |
| OXIC | -0.07 | -0.12 | -0.52 | 0.33 | 0.21 | 0.47 | 1.0 | 0.7 |
| SCHMIDT | -0.09 | 0.23 | -0.43 | 0.24 | 0.05 | 0.2 | 0.7 | 1.0 |
