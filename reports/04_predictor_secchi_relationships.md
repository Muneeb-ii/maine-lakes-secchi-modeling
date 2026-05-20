# Secchi Dataset – Predictor Relationships with SECCHI

## Overview

This report examines relationships between `SECCHI` and each numeric predictor,
using Pearson and Spearman correlations and simple one‑predictor linear models
(`SECCHI ~ predictor`).

Predictors considered: **33** (each with at least 20 overlapping observations).

## Predictor–SECCHI ranking by |Pearson r|

| predictor | n | pearson_r | spearman_r | r_squared | slope |
| --- | --- | --- | --- | --- | --- |
| TPEC | 27293 | -0.549 | -0.761 | 0.302 | -0.118 |
| OXIC | 40171 | 0.53 | 0.566 | 0.281 | 0.127 |
| DEPTH_MEAN_FEET | 153503 | 0.519 | 0.487 | 0.269 | 0.083 |
| CHLA | 29673 | -0.507 | -0.679 | 0.257 | -0.129 |
| COLOR | 18304 | -0.504 | -0.564 | 0.254 | -0.062 |
| DEPTH_MAX_FEET | 154304 | 0.48 | 0.498 | 0.23 | 0.024 |
| SCHMIDT | 44097 | 0.474 | 0.518 | 0.225 | 0.005 |
| TMIN | 44097 | -0.397 | -0.411 | 0.158 | -0.178 |
| DOMAX | 40171 | 0.317 | 0.288 | 0.101 | 0.446 |
| MLD | 44097 | 0.292 | 0.307 | 0.085 | 0.161 |
| FLUSHING_RATE_TIMES_YR | 151728 | -0.291 | -0.515 | 0.085 | -0.104 |
| ALK | 20485 | -0.281 | -0.26 | 0.079 | -0.063 |
| DAM | 154522 | 0.174 | 0.205 | 0.03 | 0.395 |
| HUC10_CODE | 156413 | 0.171 | 0.155 | 0.029 | 0.0 |
| VOLUME_ACREFEET | 151728 | 0.161 | 0.226 | 0.026 | 0.0 |
| CONDUCT | 14402 | -0.158 | -0.165 | 0.025 | -0.006 |
| AREA_ACRES | 156360 | 0.106 | 0.103 | 0.011 | 0.0 |
| TPBG | 6968 | -0.09 | -0.477 | 0.008 | -0.001 |
| ELEVATION_FEET | 156413 | 0.082 | 0.193 | 0.007 | 0.001 |
| year | 156421 | 0.082 | 0.092 | 0.007 | 0.014 |
| DELORME_PAGE | 156413 | -0.081 | -0.111 | 0.007 | -0.012 |
| PERIMETER_MILES | 155876 | 0.081 | 0.08 | 0.007 | 0.008 |
| UTM_Y | 156413 | -0.072 | -0.073 | 0.005 | -0.0 |
| LATITUDE | 156413 | -0.071 | -0.072 | 0.005 | -0.223 |
| TMAX | 44097 | 0.065 | 0.084 | 0.004 | 0.033 |
| PH | 16645 | -0.035 | 0.011 | 0.001 | -0.192 |
| TOTAL_DRAINAGE_AREA_SQ_MILES | 150503 | -0.031 | -0.1 | 0.001 | -0.001 |
| LONGITUDE | 156413 | -0.029 | -0.118 | 0.001 | -0.068 |
| UTM_X | 156413 | -0.029 | -0.115 | 0.001 | -0.0 |
| DIRECT_DRAINAGE_AREA_SQ_MILES | 151728 | -0.016 | -0.093 | 0.0 | -0.001 |
| STATION | 156421 | 0.012 | -0.013 | 0.0 | 0.016 |
| month | 156421 | 0.011 | 0.018 | 0.0 | 0.015 |
| DOMIN | 40171 | 0.009 | -0.026 | 0.0 | 0.005 |

## Top positive relationships (higher SECCHI with higher predictor)

| predictor | pearson_r | spearman_r | r_squared | n |
| --- | --- | --- | --- | --- |
| OXIC | 0.53 | 0.566 | 0.281 | 40171 |
| DEPTH_MEAN_FEET | 0.519 | 0.487 | 0.269 | 153503 |
| DEPTH_MAX_FEET | 0.48 | 0.498 | 0.23 | 154304 |
| SCHMIDT | 0.474 | 0.518 | 0.225 | 44097 |
| DOMAX | 0.317 | 0.288 | 0.101 | 40171 |
| MLD | 0.292 | 0.307 | 0.085 | 44097 |
| DAM | 0.174 | 0.205 | 0.03 | 154522 |
| HUC10_CODE | 0.171 | 0.155 | 0.029 | 156413 |
| VOLUME_ACREFEET | 0.161 | 0.226 | 0.026 | 151728 |
| AREA_ACRES | 0.106 | 0.103 | 0.011 | 156360 |
| ELEVATION_FEET | 0.082 | 0.193 | 0.007 | 156413 |
| year | 0.082 | 0.092 | 0.007 | 156421 |
| PERIMETER_MILES | 0.081 | 0.08 | 0.007 | 155876 |
| TMAX | 0.065 | 0.084 | 0.004 | 44097 |
| STATION | 0.012 | -0.013 | 0.0 | 156421 |

## Top negative relationships (lower SECCHI with higher predictor)

| predictor | pearson_r | spearman_r | r_squared | n |
| --- | --- | --- | --- | --- |
| TPEC | -0.549 | -0.761 | 0.302 | 27293 |
| CHLA | -0.507 | -0.679 | 0.257 | 29673 |
| COLOR | -0.504 | -0.564 | 0.254 | 18304 |
| TMIN | -0.397 | -0.411 | 0.158 | 44097 |
| FLUSHING_RATE_TIMES_YR | -0.291 | -0.515 | 0.085 | 151728 |
| ALK | -0.281 | -0.26 | 0.079 | 20485 |
| CONDUCT | -0.158 | -0.165 | 0.025 | 14402 |
| TPBG | -0.09 | -0.477 | 0.008 | 6968 |
| DELORME_PAGE | -0.081 | -0.111 | 0.007 | 156413 |
| UTM_Y | -0.072 | -0.073 | 0.005 | 156413 |
| LATITUDE | -0.071 | -0.072 | 0.005 | 156413 |
| PH | -0.035 | 0.011 | 0.001 | 16645 |
| TOTAL_DRAINAGE_AREA_SQ_MILES | -0.031 | -0.1 | 0.001 | 150503 |
| LONGITUDE | -0.029 | -0.118 | 0.001 | 156413 |
| UTM_X | -0.029 | -0.115 | 0.001 | 156413 |
