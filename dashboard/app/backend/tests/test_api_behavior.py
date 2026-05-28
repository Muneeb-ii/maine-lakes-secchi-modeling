import unittest
from types import SimpleNamespace

from fastapi import HTTPException

import main
from contracts import ScenarioPayload


def request_for(ip="203.0.113.10"):
    return SimpleNamespace(headers={"x-forwarded-for": ip}, client=SimpleNamespace(host=ip))


class ApiBehaviorTests(unittest.TestCase):
    def setUp(self):
        self.original_lake_names = dict(main.lake_names_data)
        self.original_baselines = dict(main.baseline_data)
        self.original_registry = main.registry
        self.original_rate_limit = main.PREDICT_RATE_LIMIT_PER_MINUTE
        main._predict_request_times.clear()

    def tearDown(self):
        main.lake_names_data = self.original_lake_names
        main.baseline_data = self.original_baselines
        main.registry = self.original_registry
        main.PREDICT_RATE_LIMIT_PER_MINUTE = self.original_rate_limit
        main._predict_request_times.clear()

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

            def predict(self, features, model_id=None, include_explainability=True):
                return SimpleNamespace(
                    prediction_meters=1.0,
                    explainability=SimpleNamespace(
                        base_value=1.0, waterfall=[], explainability_type="none"
                    ),
                )

        main.registry = StubRegistry()
        payload = ScenarioPayload(
            midas_id="C3420",
            features={"year": 2025},
            requested_outputs=["prediction", "uncertainty"],
        )

        with self.assertRaises(HTTPException) as error_ctx:
            main.predict_scenario(payload, request_for())

        detail = error_ctx.exception.detail
        self.assertEqual(error_ctx.exception.status_code, 400)
        self.assertEqual(detail["message"], "Unsupported requested outputs.")
        self.assertIn("uncertainty", detail["unsupported_outputs"])

    def test_predict_overwrites_locked_features_from_baseline(self):
        captured = {}

        class StubRegistry:
            def is_ready(self):
                return True

            def startup_errors(self):
                return []

            def active_model_metadata(self):
                return {"model_id": "stub", "model_version": "v1"}

            def predict(self, features, model_id=None, include_explainability=True):
                captured.update(features)
                return SimpleNamespace(
                    prediction_meters=1.0,
                    explainability=SimpleNamespace(
                        base_value=1.0, waterfall=[], explainability_type="none"
                    ),
                )

        main.registry = StubRegistry()
        main.baseline_data = {
            "C3420": {
                "year": 2026,
                "month": 7,
                "LATITUDE": 44.1,
                "LONGITUDE": -69.1,
                "AREA_ACRES": 120.0,
                "DEPTH_MAX_FEET": 30.0,
            }
        }
        payload = ScenarioPayload(
            midas_id="C3420",
            features={
                "year": 1900,
                "month": 1,
                "LATITUDE": 0.0,
                "LONGITUDE": 0.0,
                "AREA_ACRES": 1.0,
                "DEPTH_MAX_FEET": 1.0,
                "DOMAX": 10.0,
                "DOMIN": 9.0,
                "TPEC": 20.0,
                "TPBG": 18.0,
                "PH": 7.0,
                "COLOR": 20.0,
                "CONDUCT": 100.0,
                "ALK": 30.0,
            },
        )

        main.predict_scenario(payload, request_for())

        self.assertEqual(captured["year"], 2026.0)
        self.assertEqual(captured["LATITUDE"], 44.1)
        self.assertEqual(captured["AREA_ACRES"], 120.0)
        self.assertEqual(captured["DOMAX"], 10.0)

    def test_predict_rejects_out_of_range_editable_feature(self):
        class StubRegistry:
            def is_ready(self):
                return True

            def startup_errors(self):
                return []

            def active_model_metadata(self):
                return {"model_id": "stub", "model_version": "v1"}

            def predict(self, features, model_id=None, include_explainability=True):
                raise AssertionError("Should not predict invalid features")

        main.registry = StubRegistry()
        main.baseline_data = {
            "C3420": {
                "year": 2026,
                "month": 7,
                "LATITUDE": 44.1,
                "LONGITUDE": -69.1,
                "AREA_ACRES": 120.0,
                "DEPTH_MAX_FEET": 30.0,
            }
        }
        payload = ScenarioPayload(midas_id="C3420", features={"PH": 99.0})

        with self.assertRaises(HTTPException) as error_ctx:
            main.predict_scenario(payload, request_for())

        self.assertEqual(error_ctx.exception.status_code, 400)
        self.assertIn("PH", error_ctx.exception.detail)

    def test_predict_rate_limit(self):
        class StubRegistry:
            def is_ready(self):
                return True

            def startup_errors(self):
                return []

            def active_model_metadata(self):
                return {"model_id": "stub", "model_version": "v1"}

            def predict(self, features, model_id=None, include_explainability=True):
                return SimpleNamespace(
                    prediction_meters=1.0,
                    explainability=SimpleNamespace(
                        base_value=1.0, waterfall=[], explainability_type="none"
                    ),
                )

        main.registry = StubRegistry()
        main.PREDICT_RATE_LIMIT_PER_MINUTE = 1
        main.baseline_data = {
            "C3420": {
                "year": 2026,
                "month": 7,
                "LATITUDE": 44.1,
                "LONGITUDE": -69.1,
                "AREA_ACRES": 120.0,
                "DEPTH_MAX_FEET": 30.0,
            }
        }
        payload = ScenarioPayload(midas_id="C3420", features={"PH": 7.0})

        main.predict_scenario(payload, request_for("198.51.100.7"))
        with self.assertRaises(HTTPException) as error_ctx:
            main.predict_scenario(payload, request_for("198.51.100.7"))

        self.assertEqual(error_ctx.exception.status_code, 429)


if __name__ == "__main__":
    unittest.main()
