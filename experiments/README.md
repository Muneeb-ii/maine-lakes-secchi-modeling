# Experiment Narrative

This folder is the center of the repository. The experiment sequence is preserved with stable numeric IDs so collaborators can trace how the modeling direction evolved from dataset orientation through model selection.

## Canonical Inputs

- `data/Merged_Dataset.csv` is the canonical modeling dataset.
- `data/Merged_Dataset_Metadata.csv` is the canonical metadata companion.

## How to Read the Experiment History

- Start with the registry in `experiments/registry.json` for stable metadata.
- Use the reports in `reports/` as the committed outputs of record.
- Use this document for the storyline: what each experiment tested, what it produced, and why the next experiments were run.

## Phase 1: Dataset Shape and Feature Scoping

- `01` Missingness and data quality overview. Output: `reports/01_missingness_overview.md`. This established completeness patterns and showed where lake-level sparsity would constrain later models.
- `02` Univariate feature distributions. Output: `reports/02_univariate_distributions.md`. This highlighted variable scale and spread before multivariate modeling.
- `03` Correlations and feature redundancy. Output: `reports/03_correlations_and_redundancy.md`. This reduced ambiguity around overlapping predictors and informed later feature pruning.
- `04` Predictor-to-secchi relationships. Output: `reports/04_predictor_secchi_relationships.md`. This identified which features appeared directly useful for Secchi prediction.
- `05` Feature necessity and candidate sets. Output: `reports/05_feature_necessity_and_sets.md`. This converted the early exploratory work into concrete baseline feature groups.
- `06` Temporal trends and seasonality. Output: `reports/06_temporal_trends.md`. This confirmed that time should be treated explicitly in splits and model inputs.
- `07` Lake-level spatial variance. Output: `reports/07_spatial_variance_midas.md`. This clarified how much variation exists within and across lakes.
- `08` Nonlinear structure and interactions. Output: `reports/08_nonlinear_and_interactions.md`. This justified tree-based baselines instead of relying only on simple linear assumptions.

## Phase 2: Baselines and Generalization Stress Tests

- `09` Deep versus shallow lake structure. Output: `reports/09_deep_vs_shallow.md` plus supporting figures. This tested whether lake morphology should motivate segmented models.
- `10` Baseline predictive model. Output: `reports/10_baseline_model.md`. This established the chronological RandomForest baseline that many later experiments compare against.
- `11` Divergent depth-specific models. Output: `reports/11_divergent_depth_models.md`. This tested whether separate models for depth regimes improved on the shared baseline.
- `12` Lake type and trophic state models. Output: `reports/12_lake_type_models.md`. This checked whether ecological class boundaries aligned with predictive gains.
- `13` Ecological class versus geography. Output: `reports/13_ecological_class_impact.md`. This refined the class-based direction and clarified the role of geography.
- `14` Lake generalization under leave-one-lake-out. Output: `reports/14_lake_generalization.md`. This became a key checkpoint for how well models transfer to unseen lakes.
- `15` Chemical feature expansion. Output: `reports/15_chemical_features.md`. This brought richer chemistry into the candidate feature space.
- `16` Expanding window temporal validation. Output: `reports/16_expanding_window.md`. This tightened the temporal evaluation philosophy.
- `17` Backward expanding validation. Output: `reports/17_backward_expanding.md`. This tested robustness of the time-aware framing under an alternative chronology setup.
- `18` Local versus global modeling. Output: `reports/18_local_vs_global.md`. This compared lake-local time-series behavior against a global transfer-learning style setup.

## Phase 3: Spatial Context, Missingness, and Stronger Tree Models

- `19` Spatial autocorrelation and neighborhood features. Output: `reports/19_spatial_autocorrelation.md`. This explored whether explicit neighborhood context added signal beyond latitude and longitude.
- `20` XGBoost with chemical feature support. Output: `reports/20_xgboost_chemical.md`. This introduced a stronger boosting baseline in the chemically enriched setting.
- `21` LightGBM with chemical feature support. Output: `reports/21_lightgbm_chemical.md`. This compared an alternate boosted-tree family under the same general direction.
- `22` MissForest chronological baseline. Output: `reports/22_missforest_chrono.md`. This became a major reference point by combining chronological evaluation with imputation-aware preprocessing.
- `23` MissForest leave-one-lake-out generalization. Output: `reports/23_missforest_lolo.md`. This checked how the MissForest direction behaves under unseen-lake transfer.
- `24` MissForest backward elimination. Output: `reports/24_missforest_elimination.md`. This narrowed the feature set after the imputation-aware baseline was established.
- `25` Minimum sample threshold sensitivity. Output: `reports/25_minimum_sample_threshold.md`. This tested how lake-density inclusion rules affect performance.
- `26` Dense-lake MissForest benchmark. Output: `reports/26_missforest_chrono_t100.md`. This pushed the best MissForest direction under a denser-lake subset.

## Phase 4: Deep Learning and Region-Specific Follow-ups

- `27` MLP chronological baseline. Output: `reports/27_mlp_chrono.md`. This introduced a neural tabular baseline against the stronger tree-based path.
- `28` TabNet chronological baseline. Output: `reports/28_tabnet_chrono.md`. This compared another modern tabular deep-learning model under the same chronology.
- `29` FT-Transformer chronological baseline. Output: `reports/29_ft_transformer_chrono.md`. This provides a transformer-based tabular baseline under the same imputation-aware chronology contract, with CPU-bounded settings so it remains rerunnable as part of the canonical suite.
- `30` Regional MissForest benchmark: coastal. Output: `reports/30_region_coastal_missforest.md`. This checked whether the MissForest path behaves differently in coastal lakes.
- `31` Regional MissForest benchmark: inland. Output: `reports/31_region_inland_missforest.md`. This repeated the regional framing for inland lakes.
- `32` Regional MissForest benchmark: northern. Output: `reports/32_region_northern_missforest.md`. This completed the regional comparison set.
- `33` CatBoost with chemical feature support. Output: `reports/33_catboost_chemical.md`. This adds a third boosted-tree family to the native-missingness chemistry comparison.
- `34` Chronological hyperparameter tuning for CatBoost. Output: `reports/34_catboost_tuned.md`. This tests how much additional performance can be gained by tuning CatBoost without adding imputation.
- `35` Tuned CatBoost leave-one-lake-out evaluation. Output: `reports/35_catboost_tuned_lolo.md`. This applies the tuned CatBoost model to the original seeded 10-lake comparison set and to a reproducible random 100-lake LOLO sample.

## How This Feeds the Dashboard

- The dashboard should only consume model artifacts that survive this experiment sequence.
- `artifacts/models/` is the boundary between research code and dashboard serving code.
- Once a final model or small final model set is chosen, the dashboard can be refined without reorganizing the experiment layer again.
