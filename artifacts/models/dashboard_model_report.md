# Dashboard Model Exhaustive Architecture Report

## 1. Pipeline Overview
This document contains the exact serialization snapshot statistics of the model deployed to the dashboard backend.

- **Generation Date:** Automatically populated on script run.
- **Data Source Bounds:** `Merged_Dataset.csv` -> Filtered strictly for Target (`SECCHI`), Geographic, and Time constraints.

## 2. Train/Test Structure
- **Validation Philosophy:** Chronological validation (80/20 temporal split) to strictly prevent future-data lookahead bias during MissForest interpolation.
- **Total Valid Rows Engaged:** 154,304
- **Train Constraints:** First 123,443 chronologically sorted observations.
- **Test Constraints:** Subsequent 30,861 chronologically sorted unobserved forecasting targets.

## 3. Structural Features & Missingness Topology
The dashboard UI maps to these active 19 node tensors.
Below details the raw blank/missing cells strictly passed into MissForest for algorithmic mathematical interpolation:

### Imputation Requirements Breakdown
| Feature Name | Total `NaN` Blank Rows | Percentage of Total Space |
| :--- | :--- | :--- |
| `year` | 0 | 0.00% |
| `month` | 0 | 0.00% |
| `LATITUDE` | 0 | 0.00% |
| `LONGITUDE` | 0 | 0.00% |
| `AREA_ACRES` | 0 | 0.00% |
| `DEPTH_MAX_FEET` | 0 | 0.00% |
| `DOMAX` | 114,139 | 73.97% |
| `DOMIN` | 114,139 | 73.97% |
| `MLD` | 110,213 | 71.43% |
| `OXIC` | 114,139 | 73.97% |
| `SCHMIDT` | 110,213 | 71.43% |
| `TPEC` | 127,279 | 82.49% |
| `TPBG` | 147,365 | 95.50% |
| `PH` | 137,839 | 89.33% |
| `COLOR` | 136,240 | 88.29% |
| `CONDUCT` | 140,133 | 90.82% |
| `ALK` | 134,085 | 86.90% |
| `TMAX` | 110,213 | 71.43% |
| `TMIN` | 110,213 | 71.43% |

*(Target `SECCHI` missingness rows were immediately physically stripped prior to this table calculation).*

## 4. Hyperparameter Matrix Network
### A. Iterative Imputer (MissForest Architecture)
- **Base Estimator:** `RandomForestRegressor`
- **Internal Estimators per Chain:** 50
- **Internal Tree Max Depth:** 10
- **`max_iter` Boundary:** 10
- **`random_state` Seed:** 42

### B. Downstream Predictor (Forecasting Mainframe)
- **Estimator Class:** `RandomForestRegressor`
- **Total Estimators:** 100
- **Max Depth:** `None` (Fully expanded geometric splits)
- **`n_jobs` Parallelism:** -1

## 5. Algorithmic Evaluation Suite
Tested precisely upon the 30,861 strictly unobserved chronologically isolated observations:

- **$R^2$ (Explained Variance Coefficient):** 0.692771
- **Mean Absolute Error (MAE):** 0.859462 meters
- **Mean Squared Error (MSE):** 1.364835 meters²
- **Root Mean Squared Error (RMSE):** 1.168262 meters
- **Normalized MAE (by target depth):** 0.020261
- **Normalized RMSE (by target depth):** 0.030532

## 6. Gini Baseline Importance Logic
The following array indicates precisely how structurally dependent the mathematical forecasts are per field:

| Feature Dimension | Node Gini Importance Factor |
| :--- | :--- |
| TPEC | 0.359928 |
| DEPTH_MAX_FEET | 0.101426 |
| LONGITUDE | 0.075923 |
| AREA_ACRES | 0.072777 |
| OXIC | 0.060692 |
| LATITUDE | 0.057467 |
| COLOR | 0.038073 |
| year | 0.037115 |
| SCHMIDT | 0.029987 |
| TMIN | 0.021073 |
| MLD | 0.019937 |
| ALK | 0.019873 |
| PH | 0.018656 |
| DOMAX | 0.018122 |
| CONDUCT | 0.017894 |
| TPBG | 0.015907 |
| DOMIN | 0.014971 |
| TMAX | 0.012621 |
| month | 0.007558 |
