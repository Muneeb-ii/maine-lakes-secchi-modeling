import unittest

from contracts import (
    ExplainabilityResponse,
    PredictScenarioResponse,
    PredictionPayloadResponse,
    WaterfallItemResponse,
)


class PredictionContractTests(unittest.TestCase):
    def test_versioned_prediction_response(self):
        response = PredictScenarioResponse(
            schema_version="1.0.0",
            model_id="secchi-placeholder-rf",
            model_version="2026-04-21-mvp",
            explainability_type="shap_tree",
            prediction=PredictionPayloadResponse(value=3.2),
            explainability=ExplainabilityResponse(
                base_value=2.9,
                waterfall=[
                    WaterfallItemResponse(
                        feature="TPEC", contribution=0.2, rendered_value=10.5
                    )
                ],
            ),
            prediction_meters=3.2,
        )

        self.assertEqual(response.schema_version, "1.0.0")
        self.assertEqual(response.prediction.value, 3.2)
        self.assertEqual(response.prediction_meters, 3.2)
        self.assertEqual(response.explainability.waterfall[0].feature, "TPEC")


if __name__ == "__main__":
    unittest.main()
