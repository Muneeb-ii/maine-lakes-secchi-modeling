# Secchi Dataset – Non-Linear & Interaction Analysis

## Overview

This report analyzes non-linear feature importances utilizing a Decision Tree Regressor,
and tests simple bivariate multiplier interactions (e.g., Variable A * Variable B).

Unlike previous reports that only checked linear Pearson correlations, 
a Decision Tree evaluates how features segment the target variable (`SECCHI`) 
across specific thresholds.

## Non-Linear Feature Importance (Decision Tree, max_depth=5)

| predictor | tree_importance |
| --- | --- |
| FLUSHING_RATE_TIMES_YR | 0.5311 |
| DEPTH_MEAN_FEET | 0.1144 |
| DEPTH_MAX_FEET | 0.1063 |
| UTM_X | 0.0767 |
| CHLA | 0.0494 |
| ELEVATION_FEET | 0.0346 |
| DIRECT_DRAINAGE_AREA_SQ_MILES | 0.0277 |
| UTM_Y | 0.0185 |
| VOLUME_ACREFEET | 0.0149 |
| TOTAL_DRAINAGE_AREA_SQ_MILES | 0.0117 |
| HUC10_CODE | 0.0097 |
| LATITUDE | 0.0036 |
| DAM | 0.0013 |
| TPEC | 0.0 |

## Top 2-Way Multiplier Interactions with Default Prominent Features

| interaction_term | pearson_r | n |
| --- | --- | --- |
| OXIC * DOMAX | 0.546 | 40171 |
| TMAX * OXIC | 0.538 | 40171 |
| TMIN * COLOR | -0.534 | 14469 |
| TMAX * TPEC | -0.526 | 19943 |
| TMIN * TPEC | -0.52 | 19943 |
| TPEC * DOMAX | -0.517 | 18524 |
| CHLA * TMAX | -0.503 | 20991 |
| SCHMIDT * DOMAX | 0.498 | 40171 |
| TMAX * COLOR | -0.497 | 14469 |
| CHLA * TMIN | -0.489 | 20991 |
| COLOR * DOMAX | -0.488 | 13521 |
| CHLA * DOMAX | -0.475 | 19202 |
| TMIN * SCHMIDT | 0.467 | 44097 |
| TMAX * SCHMIDT | 0.453 | 44097 |
| OXIC * SCHMIDT | 0.421 | 40171 |
