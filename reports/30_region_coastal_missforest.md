# Experiment 30: Coastal Region (MissForest + Random Forest)

## Objective

Measure Secchi (`SECCHI`) prediction for the **Coastal** region under three setups: chronological forecasting within the region, leave-one-lake-out within the region, and training only on this region while testing on the other two. Methods mirror **Experiment 22** (MissForest + Random Forest).

## Data setup

We used the merged lake monitoring dataset with a **Coastal** filter on `REGION` (values compared in lower case). After requiring non-missing `SECCHI`, `SAMPDATE`, `MIDAS`, and core lake geometry (`LATITUDE`, `LONGITUDE`, `AREA_ACRES`, `DEPTH_MAX_FEET`), this region has **114,823** rows and **464** distinct lakes (`MIDAS`).

Chemical predictors may be missing; we applied **MissForest-style** imputation (`IterativeImputer` with a Random Forest core). We cap all Random Forest estimator counts at **15** in every part for runtime control, and use `max_iter=3` for Parts 1/3 and `max_iter=2` for sampled LOLO folds in Part 2. The imputer is always **fit on training data only** and then applied to the test set, so test values never influence how missing values are filled during training.

`REGION` is **not** included as a model input: within a single region it would be constant, and for cross-region testing it would introduce labels the training rows never saw. The experiment is defined by **which rows belong to which region**, not by a region column inside the model.

**Predictors (14):** `year, month, LATITUDE, LONGITUDE, AREA_ACRES, DEPTH_MAX_FEET, DOMAX, DOMIN, TPEC, TPBG, PH, COLOR, CONDUCT, ALK` (CHLA excluded, as in Experiment 22).

## Part 1: Region chronological train/test (80/20)

**What we did.** We sorted all rows in this region by `SAMPDATE` and used the **first 80%** of rows as training and the **last 20%** as testing. This is a chronological split **inside the region only**, so we are asking how well the model predicts the region's own future from its past.

**Results.**

| Metric | Value |
| --- | --- |
| R² | 0.6440 |
| MAE (m) | 0.8515 |
| MSE (m²) | 1.3625 |
| Normalized MAE | 0.0218 |
| Normalized MSE | 0.0010 |

## Part 2: Leave-one-lake-out within the region

**What we did.** To keep runtime practical while preserving comparability, we used a deterministic LOLO subset. From **464** lakes in this region, we sampled **15** lakes with fixed random seed **42**. For each sampled lake, we trained on all other region lakes and tested on the held-out lake. Metrics below are the mean across **15** successful sampled folds.

**Results (mean over lakes).**

| Metric | Value |
| --- | --- |
| R² | -63.6654 |
| MAE (m) | 1.3851 |
| MSE (m²) | 3.2329 |
| Normalized MAE | 0.0559 |
| Normalized MSE | 0.0108 |

## Part 3: Train on this region, test on the other two

**What we did.** We trained a single model on **all** rows in this region (after the same filters as above). We then tested that model separately on **Inland** and **Northern** rows (each with the same column rules). MissForest was **fit only on the training region** features, then used to impute each out-of-region test set.

**Results — by other region.**

| Test region | R² | MAE | MSE | Norm. MAE | Norm. MSE |
| --- | --- | --- | --- | --- | --- |
| Inland | -0.09 | 1.8618 | 5.8834 | 0.03 | 0.0018 |
| Northern | -0.8628 | 1.7856 | 6.321 | 0.0459 | 0.0045 |

**Mean across the two other regions** (simple average of the two rows above for each metric):

| Metric | Value |
| --- | --- |
| R² | -0.4764 |
| MAE (m) | 1.8237 |
| MSE (m²) | 6.1022 |
| Normalized MAE | 0.0380 |
| Normalized MSE | 0.0031 |

## Takeaway

- **Within-region time (Part 1):** R² = 0.6440, MAE = 0.8515 m.
- **Within-region new lake (Part 2, sampled LOLO):** R² = -63.6654, MAE = 1.3851 m over 15 sampled lakes (seed 42).
- **Out of region (Part 3):** mean test R² across Inland and Northern = -0.4764; Inland R² = -0.0900, Northern R² = -0.8628.
