from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data"
DATASET_ID = "secchi-merged-2026-06-29-r1"

SECCHI_SOURCE = (
    DATA_ROOT
    / "raw"
    / "secchi"
    / "secchi-2026-06-29"
    / "Data for Secchi Modeling 6-29-26.xlsx - Data.csv"
)
LEGACY_SECCHI_SOURCE = (
    DATA_ROOT
    / "raw"
    / "secchi"
    / "secchi-2025-04-17"
    / "Data for Secchi Modeling 4-17-25 DJW.xlsx - data.csv"
)
GEOGRAPHY_SOURCE = (
    DATA_ROOT
    / "raw"
    / "geography"
    / "maine-lakes-geography-morphometry-2014-01-24"
    / "MaineLakes_Geography_Morphometry.xls - DATA.csv"
)
CLASSIFICATION_SOURCE = (
    DATA_ROOT
    / "raw"
    / "lake-classification"
    / "lake-classification-undated"
    / "Class_Final_LakeNames.xlsx"
)
CURATED_SOURCE_METADATA = (
    DATA_ROOT / "processed" / DATASET_ID / "source-metadata-project.csv"
)
LEGACY_PROCESSED_METADATA = (
    DATA_ROOT / "processed" / "secchi-merged-2025-04-17-r1" / "metadata.csv"
)
OUTPUT_DIR = DATA_ROOT / "processed" / DATASET_ID
DERIVED_DIR = DATA_ROOT / "derived" / DATASET_ID

STATIC_DESCRIPTOR_COLUMNS = ["PH", "COLOR", "CONDUCT", "ALK"]

SECCHI_RENAME = {
    "Depth": "DEPTH",
    "maxbf": "MAXBF",
    "ctr_buoy": "CTR_BUOY",
    "epi_temp": "EPI_TEMP",
    "hypo_temp": "HYPO_TEMP",
    "int_ener": "INT_ENER",
    "schmidt": "SCHMIDT",
    "thermo": "THERMO",
    "whole_temp": "WHOLE_TEMP",
    "oxic_depth": "OXIC_DEPTH",
    "frac_anoxic": "FRAC_ANOXIC",
}

GEOGRAPHY_RENAME = {
    "Lake Name": "LAKE_NAME",
    "Water Quality Statement": "WATER_QUALITY_STATEMENT",
    "Trophic Category": "TROPHIC_CATEGORY",
    "Area (acres)": "AREA_ACRES",
    "Perimeter (miles)": "PERIMETER_MILES",
    "Depth_Mean (feet)": "DEPTH_MEAN_FEET",
    "Depth_Max (feet)": "DEPTH_MAX_FEET",
    "Volume (acrefeet)": "VOLUME_ACREFEET",
    "Direct Drainage Area (sq miles)": "DIRECT_DRAINAGE_AREA_SQ_MILES",
    "Total Drainage Area (sq miles)": "TOTAL_DRAINAGE_AREA_SQ_MILES",
    "Flushing Rate (times/yr)": "FLUSHING_RATE_TIMES_YR",
    "Elevation (feet)": "ELEVATION_FEET",
    "Dam": "DAM",
    "Latitude": "LATITUDE",
    "Longitude": "LONGITUDE",
    "UTM_X": "UTM_X",
    "UTM_Y": "UTM_Y",
    "Town(s)": "TOWNS",
    "County": "COUNTY",
    "DeLorme Page": "DELORME_PAGE",
    "USGS Quad24": "USGS_QUAD24",
    "Major Drainage": "MAJOR_DRAINAGE",
    "Sub Drainage": "SUB_DRAINAGE",
    "HUC10 Name": "HUC10_NAME",
    "HUC10 Code": "HUC10_CODE",
    "Invasive Plant Infestation": "INVASIVE_PLANT_INFESTATION",
    "Fishery Management": "FISHERY_MANAGEMENT",
}

PROFILE_COLUMNS = [
    "DEPTH",
    "TMAX",
    "TMIN",
    "DOMAX",
    "DOMIN",
    "MLD",
    "MAXBF",
    "CTR_BUOY",
    "EPI_TEMP",
    "HYPO_TEMP",
    "INT_ENER",
    "SCHMIDT",
    "THERMO",
    "WHOLE_TEMP",
    "OXIC_DEPTH",
    "FRAC_ANOXIC",
    "TPEC",
    "TPBG",
    "CHLA",
]


def _require_files(paths: list[Path]) -> None:
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing required inputs: " + ", ".join(missing))


def _parse_provider_ids(values: pd.Series) -> pd.DataFrame:
    parts = values.astype("string").str.extract(r"^(-?\d+)_(\d+)$")
    invalid = parts.isna().any(axis=1)
    if invalid.any():
        examples = values.loc[invalid].astype(str).head(5).tolist()
        raise ValueError(f"Unrecognized provider MIDAS values: {examples}")
    return pd.DataFrame(
        {
            "LAKE_NUMBER": parts[0].astype("int64"),
            "STATION": parts[1].astype("int64"),
        },
        index=values.index,
    )


def _parse_legacy_ids(values: pd.Series) -> pd.DataFrame:
    parts = values.astype("string").str.extract(r"^c(-?\d+)-(\d+)$")
    invalid = parts.isna().any(axis=1)
    if invalid.any():
        examples = values.loc[invalid].astype(str).head(5).tolist()
        raise ValueError(f"Unrecognized legacy MIDAS values: {examples}")
    return pd.DataFrame(
        {
            "LAKE_NUMBER": parts[0].astype("int64"),
            "STATION": parts[1].astype("int64"),
        },
        index=values.index,
    )


def _lake_static_descriptors() -> pd.DataFrame:
    legacy = pd.read_csv(LEGACY_SECCHI_SOURCE, low_memory=False)
    ids = _parse_legacy_ids(legacy["MIDAS"])
    legacy = pd.concat([legacy, ids], axis=1)
    legacy = legacy.loc[legacy["LAKE_NUMBER"] >= 0].copy()
    legacy["SAMPDATE"] = pd.to_datetime(legacy["SAMPDATE"], errors="raise")

    lake_values: list[pd.Series] = []
    for column in STATIC_DESCRIPTOR_COLUMNS:
        observations = legacy[
            ["LAKE_NUMBER", "STATION", "SAMPDATE", column]
        ].dropna(subset=[column])
        # Chemistry is repeated when a station-date has multiple Secchi readings.
        # Collapse those repeats before calculating a fixed lake-level mean.
        station_date = observations.groupby(
            ["LAKE_NUMBER", "STATION", "SAMPDATE"], sort=False
        )[column].mean()
        lake_values.append(station_date.groupby("LAKE_NUMBER").mean().rename(column))

    return pd.concat(lake_values, axis=1)


def _classification_regions() -> tuple[pd.Series, list[int]]:
    classification = pd.read_excel(CLASSIFICATION_SOURCE)
    classification = classification.dropna(subset=["MIDAS"]).copy()
    classification["MIDAS"] = classification["MIDAS"].astype("int64")

    region_counts = classification.groupby("MIDAS")["Region"].nunique(dropna=True)
    conflicts = region_counts.loc[region_counts > 1].index.astype(int).tolist()
    regions = classification.groupby("MIDAS", sort=False)["Region"].first()
    if conflicts:
        regions.loc[conflicts] = pd.NA
    return regions, conflicts


def _clean_secchi() -> tuple[pd.DataFrame, dict]:
    raw = pd.read_csv(SECCHI_SOURCE, low_memory=False)
    raw_rows = len(raw)
    ids = _parse_provider_ids(raw["MIDAS"])
    raw = pd.concat([raw, ids], axis=1)

    negative_counts = (
        raw.loc[raw["LAKE_NUMBER"] < 0, "MIDAS"].value_counts().sort_index().to_dict()
    )
    raw = raw.loc[raw["LAKE_NUMBER"] >= 0].copy()
    raw["SAMPDATE"] = pd.to_datetime(raw["SAMPDATE"], errors="raise")

    seccbot = raw["SECCBOT"].astype("string").str.strip().str.upper()
    invalid_seccbot = seccbot.notna() & ~seccbot.isin(["Y", "N"])
    invalid_seccbot_values = (
        seccbot.loc[invalid_seccbot].value_counts().sort_index().to_dict()
    )
    raw["SECCBOT"] = seccbot.mask(invalid_seccbot)

    domax_error = (
        (raw["LAKE_NUMBER"] == 4606)
        & (raw["STATION"] == 1)
        & (raw["SAMPDATE"] == pd.Timestamp("2006-05-22"))
        & (raw["DOMAX"] == 410.8)
    )
    tmax_tmin_error = (
        (raw["LAKE_NUMBER"] == 5458)
        & (raw["STATION"] == 1)
        & (raw["SAMPDATE"] == pd.Timestamp("2023-04-29"))
        & (raw["TMAX"] == 53.2)
        & (raw["TMIN"] == 46.0)
    )
    if int(domax_error.sum()) != 2:
        raise ValueError("Expected exactly two confirmed DOMAX transcription-error rows.")
    if int(tmax_tmin_error.sum()) != 1:
        raise ValueError("Expected exactly one confirmed TMAX/TMIN transcription-error row.")
    raw.loc[domax_error, "DOMAX"] = pd.NA
    raw.loc[tmax_tmin_error, ["TMAX", "TMIN"]] = pd.NA

    raw["MIDAS"] = "c" + raw["LAKE_NUMBER"].astype(str).str.zfill(4)
    raw["SAMPDATE"] = raw["SAMPDATE"].dt.strftime("%Y-%m-%d")
    raw = raw.rename(columns=SECCHI_RENAME)

    summary = {
        "raw_rows": raw_rows,
        "removed_negative_midas_rows": int(sum(negative_counts.values())),
        "removed_negative_midas_values": negative_counts,
        "invalid_seccbot_set_to_na_rows": int(invalid_seccbot.sum()),
        "invalid_seccbot_values": invalid_seccbot_values,
        "domax_transcription_error_set_to_na_rows": int(domax_error.sum()),
        "tmax_tmin_transcription_error_set_to_na_rows": int(tmax_tmin_error.sum()),
    }
    return raw, summary


def _merge_sources(secchi: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    descriptors = _lake_static_descriptors()
    for column in STATIC_DESCRIPTOR_COLUMNS:
        secchi[column] = secchi["LAKE_NUMBER"].map(descriptors[column])

    geography = pd.read_csv(GEOGRAPHY_SOURCE, low_memory=False)
    if geography["Lake Code (MIDAS)"].duplicated().any():
        raise ValueError("Geography source contains duplicate MIDAS rows.")
    geography = geography[["Lake Code (MIDAS)", *GEOGRAPHY_RENAME]].rename(
        columns={"Lake Code (MIDAS)": "LAKE_NUMBER", **GEOGRAPHY_RENAME}
    )
    secchi = secchi.merge(geography, how="left", on="LAKE_NUMBER", validate="many_to_one")

    regions, region_conflicts = _classification_regions()
    secchi["REGION"] = secchi["LAKE_NUMBER"].map(regions)

    output_columns = [
        "MIDAS",
        "STATION",
        "MTB",
        "LAKE_NAME",
        "REGION",
        "SAMPDATE",
        "SECCHI",
        "SECCBOT",
        *PROFILE_COLUMNS,
        *STATIC_DESCRIPTOR_COLUMNS,
        *[column for column in GEOGRAPHY_RENAME.values() if column != "LAKE_NAME"],
    ]
    merged = secchi[output_columns].copy()

    unique_lakes = merged["MIDAS"].nunique()
    join_summary = {
        "rows_output": len(merged),
        "unique_lakes": int(unique_lakes),
        "unique_lake_stations": int(
            merged[["MIDAS", "STATION"]].drop_duplicates().shape[0]
        ),
        "measurement_date_min": str(merged["SAMPDATE"].min()),
        "measurement_date_max": str(merged["SAMPDATE"].max()),
        "lakes_without_geography": int(
            merged.loc[merged["LAKE_NAME"].isna(), "MIDAS"].nunique()
        ),
        "lakes_without_region": int(
            merged.loc[merged["REGION"].isna(), "MIDAS"].nunique()
        ),
        "classification_region_conflict_midas_set_to_na": region_conflicts,
        "static_descriptor_lake_coverage": {
            column: int(merged.loc[merged[column].notna(), "MIDAS"].nunique())
            for column in STATIC_DESCRIPTOR_COLUMNS
        },
    }
    return merged, join_summary


def _source_metadata_descriptions() -> dict[str, str]:
    metadata = pd.read_csv(
        CURATED_SOURCE_METADATA,
        header=None,
        names=["Field", "Description"],
        dtype=str,
        keep_default_na=False,
    )
    metadata = metadata.loc[metadata["Field"].ne("")].copy()
    field_names = set(
        ["MIDAS", "SAMPDATE", "SECCHI", "SECCBOT", "MTB", "Depth"]
        + [column for column in SECCHI_RENAME if column != "Depth"]
        + ["TMAX", "TMIN", "DOMAX", "DOMIN", "MLD", "TPEC", "TPBG", "CHLA"]
    )
    return metadata.loc[metadata["Field"].isin(field_names)].set_index("Field")[
        "Description"
    ].to_dict()


def _write_processed_metadata(columns: list[str]) -> None:
    source_descriptions = _source_metadata_descriptions()
    processed_source_descriptions = {
        SECCHI_RENAME.get(field, field): description
        for field, description in source_descriptions.items()
    }
    processed_source_descriptions["MIDAS"] = (
        "Canonical lake identifier derived from the lake portion of the provider MIDAS field."
    )
    processed_source_descriptions["STATION"] = (
        "Sampling station number extracted from the provider MIDAS field."
    )

    legacy_metadata = pd.read_csv(LEGACY_PROCESSED_METADATA)
    legacy_descriptions = legacy_metadata.set_index("Field")["Description"].to_dict()
    descriptions = {**legacy_descriptions, **processed_source_descriptions}
    descriptions.update(
        {
            "PH": "Fixed lake descriptor: mean pH across unique legacy station-date observations.",
            "COLOR": "Fixed lake descriptor: mean color in SPU across unique legacy station-date observations.",
            "CONDUCT": "Fixed lake descriptor: mean specific conductivity in uS/cm across unique legacy station-date observations.",
            "ALK": "Fixed lake descriptor: mean alkalinity in ppm across unique legacy station-date observations.",
        }
    )

    secchi_columns = {
        "MIDAS",
        "STATION",
        "MTB",
        "SAMPDATE",
        "SECCHI",
        "SECCBOT",
        *PROFILE_COLUMNS,
    }
    rows = []
    for column in columns:
        if column in STATIC_DESCRIPTOR_COLUMNS:
            source = "Secchi 2025-04-17 lake-level average"
        elif column == "REGION":
            source = "Lake classification workbook (undated)"
        elif column in secchi_columns:
            source = "Secchi 2026-06-29"
        else:
            source = "MaineLakes Geography & Morphometry"
        rows.append(
            {
                "Field": column,
                "Description": descriptions.get(column, "NA"),
                "Source Dataset": source,
            }
        )
    pd.DataFrame(rows).to_csv(OUTPUT_DIR / "metadata.csv", index=False)


def _write_missingness(merged: pd.DataFrame) -> None:
    features = [
        "TMAX",
        "TMIN",
        "DOMAX",
        "DOMIN",
        "MLD",
        "MAXBF",
        "CTR_BUOY",
        "EPI_TEMP",
        "HYPO_TEMP",
        "INT_ENER",
        "SCHMIDT",
        "THERMO",
        "WHOLE_TEMP",
        "OXIC_DEPTH",
        "FRAC_ANOXIC",
        "TPEC",
        "TPBG",
        "CHLA",
        *STATIC_DESCRIPTOR_COLUMNS,
    ]
    records = []
    for midas, group in merged.groupby("MIDAS", sort=True):
        missing = group[features].isna().sum()
        record = {"MIDAS": midas, "total_records": len(group)}
        record.update(
            {f"pct_missing_{feature}": missing[feature] / len(group) for feature in features}
        )
        record["pct_missing_chemical_overall"] = missing.sum() / (
            len(group) * len(features)
        )
        records.append(record)
    output = pd.DataFrame(records).sort_values(
        "pct_missing_chemical_overall", ascending=True
    )
    output.to_csv(DERIVED_DIR / "lake-missingness.csv", index=False)


def build() -> dict:
    _require_files(
        [
            SECCHI_SOURCE,
            LEGACY_SECCHI_SOURCE,
            GEOGRAPHY_SOURCE,
            CLASSIFICATION_SOURCE,
            CURATED_SOURCE_METADATA,
            LEGACY_PROCESSED_METADATA,
        ]
    )
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)

    cleaned, cleaning_summary = _clean_secchi()
    merged, join_summary = _merge_sources(cleaned)
    merged.to_csv(OUTPUT_DIR / "dataset.csv", index=False)
    _write_processed_metadata(merged.columns.tolist())
    _write_missingness(merged)

    summary = {
        "dataset_id": DATASET_ID,
        **cleaning_summary,
        **join_summary,
        "static_descriptor_method": (
            "For each legacy chemistry field, repeated Secchi rows were first averaged "
            "within lake-station-date; those station-date values were then averaged by lake."
        ),
    }
    (OUTPUT_DIR / "build-summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the June 29, 2026 merged dataset.")
    parser.add_argument(
        "--dataset-id",
        default=DATASET_ID,
        choices=[DATASET_ID],
        help="Stable processed dataset identifier.",
    )
    parser.parse_args()
    print(json.dumps(build(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
