# Experiment 23: Out-of-Boundary Regional Prediction (MissForest)

## What We Did

In Experiment 23, we tested how well the model generalizes to lakes it has never seen.

We used a Leave-One-Lake-Out (LOLO) setup. Target lakes are read from `lolo_random_seed_10.txt` (one `MIDAS` ID per line).
For each target lake, we ran this process:
1. Held out one lake as the test set.
2. Used all other lakes as the training set.
3. Fit MissForest-style imputation (`IterativeImputer` with Random Forest) on training features only.
4. Used `max_iter=3` and `max_depth=10` for controlled runtime and memory use.
5. Trained a Random Forest predictor (`n_estimators=100`) on imputed training data.
6. Evaluated predictions on the held-out lake.

## Predicting Completely Unseen Lakes (LOLO)

The table below shows results for each held-out lake.
This reflects geographic generalization after imputation.

Note: some lakes can still produce low or negative $R^2$ values if local lake dynamics differ from the training lakes.

| MIDAS | pct_missing_overall | n_obs | R2 | MAE | MAE_Norm |
| --- | --- | --- | --- | --- | --- |
| c0157 | 0.952 | 117 | -20.6 | 0.888 | 0.052 |
| c3420 | 0.606 | 610 | -1.209 | 1.066 | 0.015 |
| c3814 | 0.596 | 1073 | -0.081 | 1.65 | 0.059 |
| c3180 | 0.91 | 80 | -0.012 | 0.845 | 0.02 |
| c0224 | 0.968 | 390 | -4.128 | 4.286 | 0.022 |
| c3448 | 0.399 | 427 | 0.052 | 0.702 | 0.015 |
| c5242 | 0.664 | 451 | -0.106 | 0.666 | 0.024 |
| c3712 | 0.71 | 579 | -0.317 | 0.66 | 0.017 |
| c2222 | 0.91 | 80 | -1.306 | 0.805 | 0.042 |
| c3132 | 0.608 | 628 | -1.032 | 0.778 | 0.013 |

**MissForest RF Average LOLO $R^2$:** -2.8738
