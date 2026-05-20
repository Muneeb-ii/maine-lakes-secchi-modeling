import unittest
from types import SimpleNamespace

from fastapi import HTTPException

import main
from contracts import ScenarioPayload


class ApiBehaviorTests(unittest.TestCase):
    def setUp(self):
        self.original_lake_names = dict(main.lake_names_data)
        self.original_baselines = dict(main.baseline_data)
        self.original_registry = main.registry

    def tearDown(self):
        main.lake_names_data = self.original_lake_names
        main.baseline_data = self.original_baselines
        main.registry = self.original_registry

    def test_lake_search_returns_matches(self):
        main.lake_names_data = {
            "C3420": "Crystal Lake",
            "A1200": "Alpha Pond",
        }
        main.baseline_data = {
            "C3420": {"LATITUDE": 10.0},
            "A1200": {"LATITUDE": 11.0},
            "GLOBAL_FALLBACK": {"LATITUDE": 12.0},
        }

        body = main.search_lakes(q="crys", limit=5)
        self.assertEqual(body["query"], "crys")
        self.assertEqual(len(body["results"]), 1)
        self.assertEqual(body["results"][0]["midas_id"], "C3420")

    def test_predict_rejects_unsupported_requested_outputs(self):
        class StubRegistry:
            def is_ready(self):
                return True

            def startup_errors(self):
                return []

            def active_model_metadata(self):
                return {"model_id": "stub", "model_version": "v1"}

            def predict(self, features, model_id=None):
                return SimpleNamespace(
                    prediction_meters=1.0,
                    explainability=SimpleNamespace(
                        base_value=1.0, waterfall=[], explainability_type="none"
                    ),
                )

        main.registry = StubRegistry()
        payload = ScenarioPayload(
            features={"year": 2025},
            requested_outputs=["prediction", "uncertainty"],
        )

        with self.assertRaises(HTTPException) as error_ctx:
            main.predict_scenario(payload)

        detail = error_ctx.exception.detail
        self.assertEqual(error_ctx.exception.status_code, 400)
        self.assertEqual(detail["message"], "Unsupported requested outputs.")
        self.assertIn("uncertainty", detail["unsupported_outputs"])


if __name__ == "__main__":
    unittest.main()
