from typing import Dict, List, Any


FEATURE_SCHEMA_VERSION = "2.0.0"

# Order must match artifacts/models/model_manifest.json `feature_order`
# and the Experiment 47 `C_measured_locked_chem` feature set.
CANONICAL_FEATURE_ORDER: List[str] = [
    "year",
    "month",
    "LATITUDE",
    "LONGITUDE",
    "AREA_ACRES",
    "DEPTH_MAX_FEET",
    "DOMAX",
    "DOMIN",
    "TMAX",
    "TMIN",
    "TPEC",
    "TPBG",
    "PH",
    "COLOR",
    "CONDUCT",
    "ALK",
]

# Always taken from the lake baseline; client-supplied values are ignored.
# PH, COLOR, CONDUCT, and ALK are fixed lake-level means in the active
# dataset (see data/README.md), so they are lake descriptors, not scenario inputs.
LOCKED_BASELINE_FEATURES: List[str] = [
    "year",
    "month",
    "LATITUDE",
    "LONGITUDE",
    "AREA_ACRES",
    "DEPTH_MAX_FEET",
    "PH",
    "COLOR",
    "CONDUCT",
    "ALK",
]

FEATURE_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "year": {
        "label": "Year",
        "group": "temporal",
        "editable": False,
    },
    "month": {
        "label": "Month",
        "group": "temporal",
        "editable": False,
    },
    "LATITUDE": {
        "label": "Latitude",
        "group": "geographic",
        "editable": False,
    },
    "LONGITUDE": {
        "label": "Longitude",
        "group": "geographic",
        "editable": False,
    },
    "AREA_ACRES": {
        "label": "Area (Acres)",
        "group": "geographic",
        "editable": False,
    },
    "DEPTH_MAX_FEET": {
        "label": "Max Depth (ft)",
        "group": "geographic",
        "editable": False,
    },
    "DOMAX": {
        "label": "Dissolved Oxygen Max",
        "group": "oxygen",
        "editable": True,
        "slider": {"min": 0, "max": 20, "step": 0.1},
        "unit": "ppm",
        "icon": "Droplet",
    },
    "DOMIN": {
        "label": "Dissolved Oxygen Min",
        "group": "oxygen",
        "editable": True,
        "slider": {"min": 0, "max": 16, "step": 0.1},
        "unit": "ppm",
        "icon": "Droplet",
    },
    "TMAX": {
        "label": "Water Temperature Max",
        "group": "temperature",
        "editable": True,
        "slider": {"min": 0, "max": 35, "step": 0.1},
        "unit": "°C",
        "icon": "Thermometer",
    },
    "TMIN": {
        "label": "Water Temperature Min",
        "group": "temperature",
        "editable": True,
        "slider": {"min": 0, "max": 30, "step": 0.1},
        "unit": "°C",
        "icon": "Thermometer",
    },
    "TPEC": {
        "label": "Total Phosphorus (Epicore)",
        "group": "phosphorus",
        "editable": True,
        "slider": {"min": 0, "max": 60, "step": 0.5},
        "unit": "ppb",
        "icon": "Beaker",
    },
    "TPBG": {
        "label": "Total Phosphorus (Bottom Grab)",
        "group": "phosphorus",
        "editable": True,
        "slider": {"min": 0, "max": 14000, "step": 0.5},
        "unit": "ppb",
        "icon": "Beaker",
    },
    "PH": {
        "label": "pH",
        "group": "lake_chemistry",
        "editable": False,
        "unit": "",
    },
    "COLOR": {
        "label": "Color",
        "group": "lake_chemistry",
        "editable": False,
        "unit": "SPU",
    },
    "CONDUCT": {
        "label": "Specific Conductivity",
        "group": "lake_chemistry",
        "editable": False,
        "unit": "uS/cm",
    },
    "ALK": {
        "label": "Alkalinity",
        "group": "lake_chemistry",
        "editable": False,
        "unit": "ppm",
    },
}


def get_feature_config_response() -> Dict[str, Any]:
    editable_features = [f for f in CANONICAL_FEATURE_ORDER if FEATURE_DEFINITIONS[f]["editable"]]
    locked_features = [f for f in CANONICAL_FEATURE_ORDER if not FEATURE_DEFINITIONS[f]["editable"]]
    return {
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "canonical_feature_order": CANONICAL_FEATURE_ORDER,
        "editable_features": editable_features,
        "locked_features": locked_features,
        "locked_baseline_features": LOCKED_BASELINE_FEATURES,
        "features": FEATURE_DEFINITIONS,
    }
