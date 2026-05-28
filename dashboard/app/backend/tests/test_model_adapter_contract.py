import unittest

from model_interface import (
    ExplainabilityResult,
    PredictionResult,
    WaterfallEntry,
    ensure_model_adapter_contract,
)


class GoodAdapter:
    model_id = "good"

    def health(self):
        return {"ready": True}

    def metadata(self):
        return {"model_id": self.model_id}

    def predict(self, features, include_explainability=True):
        return PredictionResult(
            prediction_meters=1.0,
            explainability=ExplainabilityResult(
                base_value=1.0,
                waterfall=[WaterfallEntry(feature="x", contribution=0.1, rendered_value=2.0)],
                explainability_type="none",
            ),
        )


class BadAdapter:
    model_id = "bad"


class ModelAdapterContractTests(unittest.TestCase):
    def test_accepts_valid_adapter(self):
        ensure_model_adapter_contract(GoodAdapter())

    def test_rejects_invalid_adapter(self):
        with self.assertRaises(TypeError):
            ensure_model_adapter_contract(BadAdapter())


if __name__ == "__main__":
    unittest.main()
