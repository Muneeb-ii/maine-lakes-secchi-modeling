# Experiment 34: Chronological Hyperparameter Tuning for CatBoost

## What We Did (Methodology)

We kept the same native-missingness CatBoost setup introduced in Experiment 33, but added a chronological hyperparameter search inside the training window. The first 80% of rows remained the outer training slice and the latest 20% remained the untouched test slice. Inside the outer training slice, we used an 80/20 inner chronological split for tuning so parameter selection did not use the final test period.

## Hyperparameter Search Setup

Feature set: ['year', 'month', 'LATITUDE', 'LONGITUDE', 'AREA_ACRES', 'DEPTH_MAX_FEET', 'DOMAX', 'DOMIN', 'TPEC', 'TPBG', 'CHLA', 'PH', 'COLOR', 'CONDUCT', 'ALK']

Search grid: iterations=[200, 400, 700], depth=[6, 8, 10], learning_rate=[0.03, 0.05, 0.1], l2_leaf_reg=[3, 7, 11]

Total combinations evaluated: 81

Best configuration: {'iterations': 700, 'depth': 10, 'learning_rate': 0.1, 'l2_leaf_reg': 3, 'random_seed': 42, 'loss_function': 'RMSE', 'eval_metric': 'RMSE', 'verbose': False, 'allow_writing_files': False, 'thread_count': 1}

## Chronological Test Results

- **R-Squared (R²):** 0.7410
- **Mean Absolute Error (MAE):** 0.7918 meters
- **Root Mean Squared Error (RMSE):** 1.0727 meters
- **Normalized MAE:** 0.0189
- **Normalized RMSE:** 0.0281

## Search Summary

| iterations | depth | learning_rate | l2_leaf_reg | random_seed | loss_function | eval_metric | verbose | allow_writing_files | thread_count | val_R2 | val_MAE | val_RMSE | val_MAE_Norm |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 700 | 10 | 0.1 | 3 | 42 | RMSE | RMSE | False | False | 1 | 0.782 | 0.721 | 0.969 | 0.017 |
| 400 | 10 | 0.1 | 3 | 42 | RMSE | RMSE | False | False | 1 | 0.782 | 0.724 | 0.97 | 0.017 |
| 700 | 10 | 0.1 | 11 | 42 | RMSE | RMSE | False | False | 1 | 0.781 | 0.724 | 0.973 | 0.017 |
| 700 | 10 | 0.1 | 7 | 42 | RMSE | RMSE | False | False | 1 | 0.781 | 0.724 | 0.973 | 0.017 |
| 700 | 10 | 0.05 | 3 | 42 | RMSE | RMSE | False | False | 1 | 0.78 | 0.727 | 0.974 | 0.017 |
| 400 | 10 | 0.1 | 11 | 42 | RMSE | RMSE | False | False | 1 | 0.78 | 0.729 | 0.975 | 0.017 |
| 400 | 10 | 0.1 | 7 | 42 | RMSE | RMSE | False | False | 1 | 0.779 | 0.73 | 0.976 | 0.017 |
| 700 | 10 | 0.05 | 11 | 42 | RMSE | RMSE | False | False | 1 | 0.779 | 0.732 | 0.977 | 0.017 |
| 700 | 10 | 0.05 | 7 | 42 | RMSE | RMSE | False | False | 1 | 0.778 | 0.732 | 0.98 | 0.017 |
| 700 | 8 | 0.1 | 7 | 42 | RMSE | RMSE | False | False | 1 | 0.776 | 0.734 | 0.982 | 0.017 |
| 700 | 8 | 0.1 | 11 | 42 | RMSE | RMSE | False | False | 1 | 0.775 | 0.736 | 0.986 | 0.017 |
| 700 | 8 | 0.1 | 3 | 42 | RMSE | RMSE | False | False | 1 | 0.775 | 0.734 | 0.986 | 0.017 |
| 200 | 10 | 0.1 | 3 | 42 | RMSE | RMSE | False | False | 1 | 0.775 | 0.742 | 0.986 | 0.017 |
| 400 | 10 | 0.05 | 3 | 42 | RMSE | RMSE | False | False | 1 | 0.774 | 0.743 | 0.988 | 0.017 |
| 400 | 8 | 0.1 | 7 | 42 | RMSE | RMSE | False | False | 1 | 0.774 | 0.745 | 0.989 | 0.018 |

![CatBoost Tuning Search](34_catboost_tuning_search.png)

| Feature | Importance |
| --- | --- |
| DEPTH_MAX_FEET | 30.514 |
| LONGITUDE | 20.206 |
| AREA_ACRES | 16.591 |
| LATITUDE | 16.055 |
| year | 6.446 |
| CHLA | 3.434 |
| month | 2.873 |
| TPEC | 1.077 |
| DOMAX | 0.966 |
| COLOR | 0.808 |
| DOMIN | 0.554 |
| ALK | 0.206 |
| PH | 0.142 |
| CONDUCT | 0.066 |
| TPBG | 0.061 |

![Tuned CatBoost Importances](34_catboost_tuned_importances.png)
