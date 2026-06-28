import unittest
from types import SimpleNamespace

from fastapi import HTTPException

import main
import rate_limit
from contracts import ScenarioPayload


def request_for(ip="203.0.113.10"):
    return SimpleNamespace(headers={"x-forwarded-for": ip}, client=SimpleNamespace(host=ip))


class ApiBehaviorTests(unittest.TestCase):
    def setUp(self):
        self.original_lake_names = dict(main.lake_names_data)
        self.original_baselines = dict(main.baseline_data)
        self.original_registry = main.registry
        self.original_api_limit = rate_limit._api_limiter.max_requests
        self.original_predict_limit = rate_limit._predict_limiter.max_requests
        rate_limit.reset_rate_limit_state_for_tests()

    def tearDown(self):
        main.lake_names_data = self.original_lake_names
        main.baseline_data = self.original_baselines
        main.registry = self.original_registry
        rate_limit._api_limiter.max_requests = self.original_api_limit
        rate_limit._predict_limiter.max_requests = self.original_predict_limit
        rate_limit.reset_rate_limit_state_for_tests()

    def test_lake_search_returns_matches(self):
        main.lake_names_data = {
            "C3420": "Crystal Lake",
            "A1200": "Alpha Pond",
        }
        main.baseline_data = {
            "C3420": {"LATITUDE": 10.0, "LONGITUDE": -69.0, "AREA_ACRES": 120.0},
            "A1200": {"LATITUDE": 11.0, "LONGITUDE": -70.0},
            "GLOBAL_FALLBACK": {"LATITUDE": 12.0, "LONGITUDE": -71.0},
        }

        body = main.search_lakes(q="crys", limit=5)
        self.assertEqual(body["query"], "crys")
        self.assertEqual(len(body["results"]), 1)
        self.assertEqual(body["results"][0]["midas_id"], "C3420")
        self.assertEqual(body["results"][0]["latitude"], 10.0)
        self.assertEqual(body["results"][0]["longitude"], -69.0)
        self.assertEqual(body["results"][0]["area_acres"], 120.0)

    def test_lake_locations_returns_selectable_lakes_with_coordinates(self):
        main.lake_names_data = {
            "C3420": "Crystal Lake",
            "A1200": "Alpha Pond",
            "B0001": "Missing Location Pond",
        }
        main.baseline_data = {
            "C3420": {"LATITUDE": 10.0, "LONGITUDE": -69.0, "AREA_ACRES": 120.0},
            "A1200": {"LATITUDE": 11.0, "LONGITUDE": -70.0},
            "B0001": {"LATITUDE": 12.0},
            "GLOBAL_FALLBACK": {"LATITUDE": 13.0, "LONGITUDE": -71.0},
        }

        body = main.get_lake_locations()
        ids = [item["midas_id"] for item in body["results"]]

        self.assertEqual(ids, ["A1200", "C3420"])
        self.assertNotIn("B0001", ids)
        self.assertNotIn("GLOBAL_FALLBACK", ids)

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

    def test_sensitivity_returns_items_and_overwrites_locked_baseline(self):
        captured = []

        class StubRegistry:
            def is_ready(self):
                return True

            def startup_errors(self):
                return []

            def active_model_metadata(self):
                return {"model_id": "stub", "model_version": "v1"}

            def predict(self, features, model_id=None, include_explainability=True):
                captured.append(dict(features))
                return SimpleNamespace(
                    prediction_meters=float(features.get("DOMAX", 0.0)),
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
                "DOMAX": 10.0,
                "DOMIN": None,
                "TPEC": 20.0,
                "TPBG": 18.0,
                "PH": 7.0,
                "COLOR": 20.0,
                "CONDUCT": 100.0,
                "ALK": 30.0,
            },
        )

        body = main.predict_scenario_sensitivity(payload, request_for())
        by_feature = {item["feature"]: item for item in body["items"]}

        self.assertEqual(len(body["items"]), 8)
        self.assertEqual(captured[0]["year"], 2026.0)
        self.assertEqual(captured[0]["LATITUDE"], 44.1)
        self.assertEqual(by_feature["DOMAX"]["direction"], "clearer")
        self.assertEqual(by_feature["DOMIN"]["direction"], "unavailable")

    def test_sensitivity_clamps_slider_bounds(self):
        predicted_values = []

        class StubRegistry:
            def is_ready(self):
                return True

            def startup_errors(self):
                return []

            def active_model_metadata(self):
                return {"model_id": "stub", "model_version": "v1"}

            def predict(self, features, model_id=None, include_explainability=True):
                predicted_values.append(features["PH"])
                return SimpleNamespace(
                    prediction_meters=float(features["PH"]),
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
        payload = ScenarioPayload(midas_id="C3420", features={"PH": 10.0})

        body = main.predict_scenario_sensitivity(payload, request_for())
        ph_item = next(item for item in body["items"] if item["feature"] == "PH")

        self.assertEqual(ph_item["value"], 10.0)
        self.assertEqual(ph_item["value_up"], 10.0)
        self.assertEqual(ph_item["value_down"], 9.9)
        self.assertIn(10.0, predicted_values)
        self.assertIn(9.9, predicted_values)

    def test_sensitivity_direction_classification(self):
        self.assertEqual(main._sensitivity_direction(0.02, -0.02), "clearer")
        self.assertEqual(main._sensitivity_direction(-0.02, 0.02), "murkier")
        self.assertEqual(main._sensitivity_direction(0.001, -0.001), "flat")
        self.assertEqual(main._sensitivity_direction(0.02, 0.02), "mixed")
        self.assertEqual(main._direction_from_delta(0.02), "clearer")
        self.assertEqual(main._direction_from_delta(-0.02), "murkier")
        self.assertEqual(main._direction_from_delta(0.001), "flat")
        self.assertEqual(
            main._sensitivity_summary_direction("flat", "clearer"),
            "range_sensitive",
        )
        self.assertEqual(
            main._sensitivity_summary_direction("clearer", "murkier"),
            "mixed",
        )

    def test_range_sensitivity_detects_large_change_after_flat_local_step(self):
        class StubRegistry:
            def predict(self, features, model_id=None, include_explainability=True):
                conduct = float(features["CONDUCT"])
                prediction = 1.0 if conduct < 100 else 1.5
                return SimpleNamespace(
                    prediction_meters=prediction,
                    explainability=SimpleNamespace(
                        base_value=prediction, waterfall=[], explainability_type="none"
                    ),
                )

        main.registry = StubRegistry()
        features = {"CONDUCT": 32.0}
        item = main._sensitivity_item_for_feature(
            "CONDUCT",
            features,
            baseline_prediction=1.0,
        )

        self.assertEqual(item.local_direction, "flat")
        self.assertEqual(item.range_direction, "clearer")
        self.assertEqual(item.direction, "range_sensitive")
        self.assertGreater(item.range_delta_meters, 0.01)

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
        rate_limit._api_limiter.max_requests = 10
        rate_limit._predict_limiter.max_requests = 1
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
        request = request_for("198.51.100.7")

        rate_limit.enforce_api_rate_limit(request)
        rate_limit.enforce_predict_rate_limit(request)
        main.predict_scenario(payload, request)

        rate_limit.enforce_api_rate_limit(request)
        with self.assertRaises(HTTPException) as error_ctx:
            rate_limit.enforce_predict_rate_limit(request)

        self.assertEqual(error_ctx.exception.status_code, 429)


if __name__ == "__main__":
    unittest.main()
