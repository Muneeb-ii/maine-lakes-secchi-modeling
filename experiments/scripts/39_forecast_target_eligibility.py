from __future__ import annotations

import pandas as pd
from pathlib import Path

from experiment_utils import (
    CanonicalReport,
    df_to_markdown_table,
    load_data,
    write_canonical_report,
)


EXPERIMENT_ID = "39"
REPORT_FILENAME = "39_forecast_target_eligibility.md"
REPORT_TITLE = "Experiment 39: Forecast Target and Eligibility"
SUMMER_MONTHS = (6, 7, 8, 9)
HISTORY_THRESHOLDS = (5, 10, 15)
RECENCY_THRESHOLDS = (2, 5)
THROUGH_YEAR = 2022
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _summer_readings(df: pd.DataFrame) -> pd.DataFrame:
    work = df.copy()
    work["year"] = work["SAMPDATE"].dt.year.astype("int64")
    work["month"] = work["SAMPDATE"].dt.month.astype("int64")
    work = work.loc[
        work["month"].isin(SUMMER_MONTHS)
        & work["SECCHI"].notna()
        & work["MIDAS"].notna()
        & work["STATION"].notna()
    ].copy()
    work["bottom_hit"] = work["SECCBOT"].eq("Y")
    work["valid_bottom_flag"] = work["SECCBOT"].isin(["Y", "N"])
    return work


def _all_year_readings(df: pd.DataFrame) -> pd.DataFrame:
    """Return all-season readings with a descriptive within-lake-year adjustment."""
    work = df.copy()
    work["year"] = work["SAMPDATE"].dt.year.astype("int64")
    work["month"] = work["SAMPDATE"].dt.month.astype("int64")
    work = work.loc[
        work["SECCHI"].notna()
        & work["MIDAS"].notna()
        & work["STATION"].notna()
    ].copy()
    date_station = work.groupby(
        ["MIDAS", "STATION", "SAMPDATE", "year", "month"], as_index=False
    )["SECCHI"].mean()
    lake_year_mean = date_station.groupby(["MIDAS", "year"])["SECCHI"].transform("mean")
    date_station["resid"] = date_station["SECCHI"] - lake_year_mean
    month_effects = date_station.groupby("month")["resid"].mean()
    summer_effects = month_effects.reindex(SUMMER_MONTHS).dropna()
    center = float(summer_effects.mean()) if not summer_effects.empty else 0.0
    work["SECCHI"] = (
        work["SECCHI"] - work["month"].map(month_effects).fillna(0.0) + center
    ).clip(lower=0.0)
    work["bottom_hit"] = work["SECCBOT"].eq("Y")
    work["valid_bottom_flag"] = work["SECCBOT"].isin(["Y", "N"])
    return work


def _build_lake_year_target(
    summer: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Build date/station, station-year, and station-balanced lake-year panels."""
    date_station = (
        summer.groupby(["MIDAS", "STATION", "SAMPDATE"], as_index=False)
        .agg(
            SECCHI=("SECCHI", "mean"),
            SECCHI_median=("SECCHI", "median"),
            bottom_hit_rate=("bottom_hit", "mean"),
            valid_bottom_flag_rate=("valid_bottom_flag", "mean"),
            n_readings=("SECCHI", "size"),
        )
    )
    date_station["year"] = date_station["SAMPDATE"].dt.year.astype("int64")

    station_year = (
        date_station.groupby(["MIDAS", "STATION", "year"], as_index=False)
        .agg(
            SECCHI=("SECCHI", "mean"),
            SECCHI_median=("SECCHI_median", "median"),
            bottom_hit_rate=("bottom_hit_rate", "mean"),
            valid_bottom_flag_rate=("valid_bottom_flag_rate", "mean"),
            n_summer_dates=("SAMPDATE", "size"),
            n_readings=("n_readings", "sum"),
        )
    )

    # Average station-year values equally so one heavily sampled station does
    # not dominate a lake-year. Station remains available for later modeling.
    lake_year = (
        station_year.groupby(["MIDAS", "year"], as_index=False)
        .agg(
            summer_secchi=("SECCHI", "mean"),
            summer_secchi_median=("SECCHI_median", "median"),
            bottom_hit_rate=("bottom_hit_rate", "mean"),
            valid_bottom_flag_rate=("valid_bottom_flag_rate", "mean"),
            n_stations=("STATION", "nunique"),
            n_station_years=("STATION", "size"),
            n_summer_dates=("n_summer_dates", "sum"),
            n_readings=("n_readings", "sum"),
        )
    )
    return date_station, station_year, lake_year


def _history_frame(lake_year: pd.DataFrame) -> pd.DataFrame:
    history = (
        lake_year.groupby("MIDAS", as_index=False)
        .agg(
            first_summer_year=("year", "min"),
            latest_summer_year=("year", "max"),
            n_summer_years=("year", "size"),
        )
    )
    history["span_years"] = (
        history["latest_summer_year"] - history["first_summer_year"] + 1
    )
    history["internal_missing_summer_years"] = (
        history["span_years"] - history["n_summer_years"]
    )
    return history


def _support_table(history: pd.DataFrame, latest_observed_year: int) -> pd.DataFrame:
    rows = []
    for recency in RECENCY_THRESHOLDS:
        # "Within N years" includes the latest year and the preceding N
        # calendar years (e.g. 2022–2024 for N=2 and latest=2024).
        cutoff = latest_observed_year - recency
        qualified = history[history["latest_summer_year"] >= cutoff]
        rows.append(
            {
                "recency_policy": f"Latest summer observation within {recency} years",
                "latest_year_cutoff": cutoff,
                **{
                    f"history_ge_{threshold}_years": int(
                        (qualified["n_summer_years"] >= threshold).sum()
                    )
                    for threshold in HISTORY_THRESHOLDS
                },
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    data = load_data()
    df = data.frame
    summer = _summer_readings(df)
    date_station, station_year, lake_year = _build_lake_year_target(summer)
    all_year = _all_year_readings(df)
    _, _, all_year_target = _build_lake_year_target(all_year)
    all_year_target = all_year_target.rename(
        columns={
            "summer_secchi": "seasonally_adjusted_secchi",
            "summer_secchi_median": "seasonally_adjusted_secchi_median",
            "bottom_hit_rate": "all_year_bottom_hit_rate",
            "n_stations": "all_year_n_stations",
            "n_station_years": "all_year_n_station_years",
            "n_summer_dates": "all_year_n_dates",
            "n_readings": "all_year_n_readings",
        }
    )
    lake_year = lake_year.merge(
        all_year_target[
            ["MIDAS", "year", "seasonally_adjusted_secchi",
             "seasonally_adjusted_secchi_median", "all_year_bottom_hit_rate",
             "all_year_n_stations", "all_year_n_station_years",
             "all_year_n_dates", "all_year_n_readings"]
        ],
        on=["MIDAS", "year"],
        how="left",
    )
    history = _history_frame(lake_year)

    latest_observed_year = int(lake_year["year"].max())
    support_table = _support_table(history, latest_observed_year)

    lake_year = lake_year.sort_values(["MIDAS", "year"]).reset_index(drop=True)
    derived_dir = PROJECT_ROOT / "data" / "derived" / data.dataset_id
    derived_dir.mkdir(parents=True, exist_ok=True)
    target_path = derived_dir / "annual-summer-lake-year.csv"
    lake_year.to_csv(target_path, index=False)

    all_history_row = {
        "availability_policy": "All summer histories",
        **{
            f"history_ge_{threshold}_years": int(
                (history["n_summer_years"] >= threshold).sum()
            )
            for threshold in HISTORY_THRESHOLDS
        },
    }
    through_2022 = history[history["latest_summer_year"] >= THROUGH_YEAR]
    through_2022_row = {
        "availability_policy": f"Observed through {THROUGH_YEAR} or later",
        **{
            f"history_ge_{threshold}_years": int(
                (through_2022["n_summer_years"] >= threshold).sum()
            )
            for threshold in HISTORY_THRESHOLDS
        },
    }
    availability_table = pd.DataFrame([all_history_row, through_2022_row])

    gap_table = pd.DataFrame(
        [
            {
                "quantity": "Lakes with at least one internal missing summer year",
                "value": int((history["internal_missing_summer_years"] > 0).sum()),
            },
            {
                "quantity": "Total internal missing summer years",
                "value": int(history["internal_missing_summer_years"].sum()),
            },
            {
                "quantity": "Median observed summer years per lake",
                "value": float(history["n_summer_years"].median()),
            },
            {
                "quantity": "Maximum observed summer years per lake",
                "value": int(history["n_summer_years"].max()),
            },
        ]
    )

    bottom_hits = int(summer["bottom_hit"].sum())
    valid_flags = int(summer["valid_bottom_flag"].sum())
    bottom_summary = pd.DataFrame(
        [
            {
                "quantity": "Summer Secchi readings",
                "value": len(summer),
            },
            {
                "quantity": "Summer readings with valid Y/N bottom flag",
                "value": valid_flags,
            },
            {
                "quantity": "Summer readings marked SECCBOT=Y",
                "value": bottom_hits,
            },
            {
                "quantity": "Bottom-hit fraction of all summer readings",
                "value": bottom_hits / len(summer),
            },
            {
                "quantity": "Lake-years with majority bottom-hit readings",
                "value": int(
                    (
                        summer.groupby(["MIDAS", "year"])["bottom_hit"].mean()
                        > 0.5
                    ).sum()
                ),
            },
        ]
    )

    station_summary = pd.DataFrame(
        [
            {
                "quantity": "Lakes with multiple stations in all records",
                "value": int((df.groupby("MIDAS")["STATION"].nunique() > 1).sum()),
            },
            {
                "quantity": "Lakes with multiple stations in summer records",
                "value": int(
                    (summer.groupby("MIDAS")["STATION"].nunique() > 1).sum()
                ),
            },
            {
                "quantity": "Lake-years with multiple summer stations",
                "value": int((lake_year["n_stations"] > 1).sum()),
            },
            {
                "quantity": "Summer date-station rows after duplicate averaging",
                "value": len(date_station),
            },
            {
                "quantity": "Summer station-years",
                "value": len(station_year),
            },
        ]
    )

    target_quantiles = lake_year["summer_secchi"].quantile(
        [0.01, 0.25, 0.5, 0.75, 0.99]
    )
    target_summary = pd.DataFrame(
        {
            "statistic": ["Mean", "P01", "P25", "Median", "P75", "P99"],
            "summer_secchi_m": [
                lake_year["summer_secchi"].mean(),
                target_quantiles.loc[0.01],
                target_quantiles.loc[0.25],
                target_quantiles.loc[0.5],
                target_quantiles.loc[0.75],
                target_quantiles.loc[0.99],
            ],
        }
    )
    target_comparison = pd.DataFrame(
        [
            {"target": "Summer mean", "n_lake_years": int(lake_year["summer_secchi"].notna().sum()), "mean_m": lake_year["summer_secchi"].mean(), "median_m": lake_year["summer_secchi"].median()},
            {"target": "Summer median", "n_lake_years": int(lake_year["summer_secchi_median"].notna().sum()), "mean_m": lake_year["summer_secchi_median"].mean(), "median_m": lake_year["summer_secchi_median"].median()},
            {"target": "Full-year seasonally adjusted mean (full snapshot descriptive)", "n_lake_years": int(lake_year["seasonally_adjusted_secchi"].notna().sum()), "mean_m": lake_year["seasonally_adjusted_secchi"].mean(), "median_m": lake_year["seasonally_adjusted_secchi"].median()},
            {"target": "Full-year seasonally adjusted median (full snapshot descriptive)", "n_lake_years": int(lake_year["seasonally_adjusted_secchi_median"].notna().sum()), "mean_m": lake_year["seasonally_adjusted_secchi_median"].mean(), "median_m": lake_year["seasonally_adjusted_secchi_median"].median()},
        ]
    )

    report = CanonicalReport(
        objective=(
            "Construct the annual summer lake-clarity target for the direct Secchi forecasting track "
            "and quantify the history, recency, station, gap, and bottom-censoring constraints that "
            "will determine forecast support tiers."
        ),
        method=(
            "Use June–September observations from the active June 2026 processed dataset. First average "
            "duplicate Secchi readings within lake, station, and date. Then average station-year values "
            "equally within each lake-year so heavily sampled stations do not dominate the annual target. "
            "Retain station counts, reading counts, gaps, and bottom-hit rates as support and diagnostic "
            "variables. Bottom-hit readings remain in the initial target, but `SECCBOT=Y` is flagged as a "
            "candidate right-censored observation for the later state-space model. In addition, construct "
            "a full-snapshot descriptive target by applying within-lake-year month residual effects, "
            "centered on June–September, before the same date/station and station-balanced aggregation, "
            "and retain median aggregation variants for sensitivity. This full-snapshot target is "
            "descriptive; rolling-origin evaluation re-estimates and freezes month effects at each "
            "origin in Experiment 40."
        ),
        parameters=(
            f"Dataset ID: `{data.dataset_id}`.\n\n"
            f"Summer window: months {SUMMER_MONTHS[0]}–{SUMMER_MONTHS[-1]}.\n\n"
            "Target grain: one station-balanced annual summer Secchi value per `MIDAS` lake and year.\n\n"
            f"History thresholds: {HISTORY_THRESHOLDS} summer years.\n\n"
            f"Recency thresholds: latest summer observation within {RECENCY_THRESHOLDS} years of the latest observed summer year ({latest_observed_year}).\n\n"
            f"Additional availability check: latest summer observation in {THROUGH_YEAR} or later."
        ),
        results=(
            "### Dataset and Target Construction\n\n"
            f"The active snapshot contains **{len(df):,}** processed rows. The summer filter produced **{len(summer):,}** Secchi readings, **{lake_year['MIDAS'].nunique():,}** lakes, and **{len(lake_year):,}** lake-years spanning **{int(lake_year['year'].min())}–{latest_observed_year}**.\n\n"
            f"{df_to_markdown_table(station_summary, round_decimals=3)}\n\n"
            "### Annual Summer Target Distribution\n\n"
            f"{df_to_markdown_table(target_summary, round_decimals=3)}\n\n"
            "### Target Definition Sensitivity\n\n"
            f"{df_to_markdown_table(target_comparison, round_decimals=3)}\n\n"
            "### History and Recency Support\n\n"
            f"{df_to_markdown_table(availability_table, round_decimals=3)}\n\n"
            f"{df_to_markdown_table(support_table, round_decimals=3)}\n\n"
            "### Gaps and Bottom-Hit Censoring\n\n"
            f"{df_to_markdown_table(gap_table, round_decimals=3)}\n\n"
            f"{df_to_markdown_table(bottom_summary, round_decimals=4)}\n\n"
            f"The constructed panel is persisted at `{target_path.relative_to(PROJECT_ROOT)}` for the next forecasting experiment.\n\n"
            "The support table is descriptive only. It does not select final eligibility thresholds; "
            "Experiments 40–44 must evaluate those policies through rolling-origin backtesting and interval calibration."
        ),
        next_step=(
            "Use this station-balanced lake-year panel to benchmark last-value, recent-mean, robust-trend, "
            "and local-level state-space forecasts at horizons 1, 3, 5, and 10."
        ),
    )

    path = write_canonical_report(REPORT_FILENAME, REPORT_TITLE, report)
    print(f"Wrote report to {path}")


if __name__ == "__main__":
    main()
