import unittest

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


if __name__ == "__main__":
    unittest.main()
