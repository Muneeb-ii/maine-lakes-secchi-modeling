import json
import tempfile
import unittest
from pathlib import Path

import main
from fastapi import HTTPException
from trends import TrendsStore


def payload():
    summary = {"midas_id": "c0001", "lake_name": "Lake One", "region": "Inland", "history_years": 10, "latest_year": 2024, "forecast_available": True, "support_tier": "Full"}
    detail = {**summary, "unavailable_reason": None, "history": [{"year": 2024, "secchi_m": 2.0, "n_readings": 2, "bottom_hit_rate": 0.0}], "forecast": [{"year": 2025, "secchi_m": 2.0, "lower_80": 1.0, "upper_80": 3.0, "lower_95": 0.5, "upper_95": 3.5}]}
    return {"dataset_id": "secchi-merged-2026-06-29-r1", "observations_through_year": 2024, "model": "Local-level state-space", "forecast_years": [2025], "target": "Station-balanced summer Secchi depth", "support_policy": {"minimum_history_years": 10, "maximum_gap_years": 2}, "validation": {"mae_m": .6, "coverage_80": .78, "coverage_95": .94}, "lakes": [summary], "details": {"c0001": detail}}


class TrendsTests(unittest.TestCase):
    def test_store_missing_artifact_is_unavailable(self):
        store = TrendsStore(Path("/tmp/no-such-trends-artifact.json"))
        store.load()
        with self.assertRaises(RuntimeError):
            store.index()

    def test_lookup_is_case_insensitive_and_unknown_is_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trends.json"
            path.write_text(json.dumps(payload()))
            store = TrendsStore(path)
            store.load()
            self.assertEqual(store.detail("C0001")["midas_id"], "c0001")
            self.assertIsNone(store.detail("c9999"))

    def test_intervals_are_nested_and_unsupported_lakes_have_no_forecast(self):
        item = payload()["details"]["c0001"]
        forecast = item["forecast"][0]
        self.assertLessEqual(forecast["lower_95"], forecast["lower_80"])
        self.assertLessEqual(forecast["upper_80"], forecast["upper_95"])
        unsupported = {"forecast_available": False, "forecast": [], "support_tier": "Limited"}
        self.assertFalse(unsupported["forecast_available"])
        self.assertEqual(unsupported["forecast"], [])

    def test_routes_return_contract_and_503(self):
        original = main.trends_store
        try:
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "trends.json"
                path.write_text(json.dumps(payload()))
                main.trends_store = TrendsStore(path)
                main.trends_store.load()
                self.assertEqual(main.get_trends()["observations_through_year"], 2024)
                self.assertEqual(main.get_trends_lake("C0001")["midas_id"], "c0001")
                with self.assertRaises(HTTPException) as missing:
                    main.get_trends_lake("c9999")
                self.assertEqual(missing.exception.status_code, 404)
            main.trends_store = TrendsStore(Path("/tmp/no-such-trends-artifact.json"))
            main.trends_store.load()
            with self.assertRaises(HTTPException) as unavailable:
                main.get_trends()
            self.assertEqual(unavailable.exception.status_code, 503)
        finally:
            main.trends_store = original


if __name__ == "__main__":
    unittest.main()
