import unittest
import json
import math
from pathlib import Path

from feature_contract import CANONICAL_FEATURE_ORDER, FEATURE_DEFINITIONS


# Expected dashboard labels/units aligned with data/Merged_Dataset_Metadata.csv
METADATA_ALIGNED_FEATURES = {
    "DOMAX": {"label": "Dissolved Oxygen Max", "unit": "ppm"},
    "DOMIN": {"label": "Dissolved Oxygen Min", "unit": "ppm"},
    "TPEC": {"label": "Total Phosphorus (Bottom Grab)", "unit": "ppb"},
    "TPBG": {"label": "Total Phosphorus (Epicore)", "unit": "ppb"},
    "PH": {"label": "pH", "unit": ""},
    "COLOR": {"label": "Color", "unit": "SPU"},
    "CONDUCT": {"label": "Specific Conductivity", "unit": "uS/cm"},
    "ALK": {"label": "Alkalinity", "unit": "ppm"},
}


class FeatureContractTests(unittest.TestCase):
    def test_chemistry_features_match_dataset_metadata(self):
        for feature_name, expected in METADATA_ALIGNED_FEATURES.items():
            definition = FEATURE_DEFINITIONS[feature_name]
            self.assertEqual(definition["label"], expected["label"], feature_name)
            self.assertEqual(definition["unit"], expected["unit"], feature_name)
            self.assertEqual(definition["group"], "chemistry", feature_name)

    def test_all_canonical_features_have_definitions(self):
        for feature_name in CANONICAL_FEATURE_ORDER:
            self.assertIn(feature_name, FEATURE_DEFINITIONS)

    def test_slider_ranges_cover_supported_lake_baselines(self):
        baseline_path = Path(__file__).resolve().parents[4] / "artifacts" / "models" / "baseline_lakes_summary.json"
        with baseline_path.open() as f:
            baseline_data = json.load(f)

        for feature_name, definition in FEATURE_DEFINITIONS.items():
            slider = definition.get("slider")
            if not slider:
                continue
            min_value = float(slider["min"])
            max_value = float(slider["max"])
            for lake_id, baseline in baseline_data.items():
                if lake_id == "GLOBAL_FALLBACK":
                    continue
                value = baseline.get(feature_name)
                if value is None:
                    continue
                value = float(value)
                if not math.isfinite(value):
                    continue
                self.assertGreaterEqual(value, min_value, f"{feature_name} below range for {lake_id}")
                self.assertLessEqual(value, max_value, f"{feature_name} above range for {lake_id}")


if __name__ == "__main__":
    unittest.main()
