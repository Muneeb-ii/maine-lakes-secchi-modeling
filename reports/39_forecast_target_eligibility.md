# Experiment 39: Forecast Target and Eligibility

## Objective

Construct the annual summer lake-clarity target for the direct Secchi forecasting track and quantify the history, recency, station, gap, and bottom-censoring constraints that will determine forecast support tiers.

## Method

Use June–September observations from the active June 2026 processed dataset. First average duplicate Secchi readings within lake, station, and date. Then average station-year values equally within each lake-year so heavily sampled stations do not dominate the annual target. Retain station counts, reading counts, gaps, and bottom-hit rates as support and diagnostic variables. Bottom-hit readings remain in the initial target, but `SECCBOT=Y` is flagged as a candidate right-censored observation for the later state-space model. In addition, construct a full-snapshot descriptive target by applying within-lake-year month residual effects, centered on June–September, before the same date/station and station-balanced aggregation, and retain median aggregation variants for sensitivity. This full-snapshot target is descriptive; rolling-origin evaluation re-estimates and freezes month effects at each origin in Experiment 40.

## Parameters

Dataset ID: `secchi-merged-2026-06-29-r1`.

Summer window: months 6–9.

Target grain: one station-balanced annual summer Secchi value per `MIDAS` lake and year.

History thresholds: (5, 10, 15) summer years.

Recency thresholds: latest summer observation within (2, 5) years of the latest observed summer year (2024).

Additional availability check: latest summer observation in 2022 or later.

## Results

### Dataset and Target Construction

The active snapshot contains **165,243** processed rows. The summer filter produced **133,387** Secchi readings, **1,084** lakes, and **15,365** lake-years spanning **1952–2024**.

| quantity | value |
| --- | --- |
| Lakes with multiple stations in all records | 209 |
| Lakes with multiple stations in summer records | 201 |
| Lake-years with multiple summer stations | 1954 |
| Summer date-station rows after duplicate averaging | 111554 |
| Summer station-years | 18190 |

### Annual Summer Target Distribution

| statistic | summer_secchi_m |
| --- | --- |
| Mean | 5.345 |
| P01 | 1.233 |
| P25 | 3.942 |
| Median | 5.175 |
| P75 | 6.511 |
| P99 | 11.658 |

### Target Definition Sensitivity

| target | n_lake_years | mean_m | median_m |
| --- | --- | --- | --- |
| Summer mean | 15365 | 5.345 | 5.175 |
| Summer median | 15365 | 5.358 | 5.2 |
| Full-year seasonally adjusted mean (full snapshot descriptive) | 15365 | 5.333 | 5.151 |
| Full-year seasonally adjusted median (full snapshot descriptive) | 15365 | 5.344 | 5.154 |

### History and Recency Support

| availability_policy | history_ge_5_years | history_ge_10_years | history_ge_15_years |
| --- | --- | --- | --- |
| All summer histories | 576 | 444 | 393 |
| Observed through 2022 or later | 388 | 352 | 330 |

| recency_policy | latest_year_cutoff | history_ge_5_years | history_ge_10_years | history_ge_15_years |
| --- | --- | --- | --- | --- |
| Latest summer observation within 2 years | 2022 | 388 | 352 | 330 |
| Latest summer observation within 5 years | 2019 | 440 | 382 | 353 |

### Gaps and Bottom-Hit Censoring

| quantity | value |
| --- | --- |
| Lakes with at least one internal missing summer year | 699.0 |
| Total internal missing summer years | 9692.0 |
| Median observed summer years per lake | 5.0 |
| Maximum observed summer years per lake | 54.0 |

| quantity | value |
| --- | --- |
| Summer Secchi readings | 133387.0 |
| Summer readings with valid Y/N bottom flag | 133122.0 |
| Summer readings marked SECCBOT=Y | 6100.0 |
| Bottom-hit fraction of all summer readings | 0.0457 |
| Lake-years with majority bottom-hit readings | 895.0 |

The constructed panel is persisted at `data/derived/secchi-merged-2026-06-29-r1/annual-summer-lake-year.csv` for the next forecasting experiment.

The support table is descriptive only. It does not select final eligibility thresholds; Experiments 40–44 must evaluate those policies through rolling-origin backtesting and interval calibration.

## Next Step

Use this station-balanced lake-year panel to benchmark last-value, recent-mean, robust-trend, and local-level state-space forecasts at horizons 1, 3, 5, and 10.
