from typing import Dict, List, Any


FEATURE_SCHEMA_VERSION = "1.0.0"

CANONICAL_FEATURE_ORDER: List[str] = [
    "year",
    "month",
    "LATITUDE",
    "LONGITUDE",
    "AREA_ACRES",
    "DEPTH_MAX_FEET",
    "DOMAX",
    "DOMIN",
    "TPEC",
    "TPBG",
    "PH",
    "COLOR",
    "CONDUCT",
    "ALK",
]

LOCKED_BASELINE_FEATURES: List[str] = [
    "year",
    "month",
    "LATITUDE",
    "LONGITUDE",
    "AREA_ACRES",
    "DEPTH_MAX_FEET",
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
        "group": "chemistry",
        "editable": True,
        "slider": {"min": 0, "max": 20, "step": 0.1},
        "unit": "ppm",
        "icon": "Beaker",
    },
    "DOMIN": {
        "label": "Dissolved Oxygen Min",
        "group": "chemistry",
        "editable": True,
        "slider": {"min": 0, "max": 16, "step": 0.1},
        "unit": "ppm",
        "icon": "Beaker",
    },
    "TPEC": {
        "label": "Total Phosphorus (Bottom Grab)",
        "group": "chemistry",
        "editable": True,
        "slider": {"min": 0, "max": 60, "step": 0.5},
        "unit": "ppb",
        "icon": "Beaker",
    },
    "TPBG": {
        "label": "Total Phosphorus (Epicore)",
        "group": "chemistry",
        "editable": True,
        "slider": {"min": 0, "max": 350, "step": 0.5},
        "unit": "ppb",
        "icon": "Beaker",
    },
    "PH": {
        "label": "pH",
        "group": "chemistry",
        "editable": True,
        "slider": {"min": 4.0, "max": 10.0, "step": 0.1},
        "unit": "",
        "icon": "Beaker",
    },
    "COLOR": {
        "label": "Color",
        "group": "chemistry",
        "editable": True,
        "slider": {"min": 0, "max": 100, "step": 1},
        "unit": "SPU",
        "icon": "Droplet",
    },
    "CONDUCT": {
        "label": "Specific Conductivity",
        "group": "chemistry",
        "editable": True,
        "slider": {"min": 0, "max": 200, "step": 1},
        "unit": "uS/cm",
        "icon": "Activity",
    },
    "ALK": {
        "label": "Alkalinity",
        "group": "chemistry",
        "editable": True,
        "slider": {"min": 0, "max": 100, "step": 0.1},
        "unit": "ppm",
        "icon": "Beaker",
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
