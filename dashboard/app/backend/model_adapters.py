import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional

from feature_contract import CANONICAL_FEATURE_ORDER
from model_interface import (
    ExplainabilityResult,
    PredictionResult,
    WaterfallEntry,
)

try:
    import shap

    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False


class LakeModelAdapter:
    def __init__(
        self,
        models_path: Path,
        model_id: str,
        model_version: str,
        explainability_type: str,
        feature_order: List[str],
    ) -> None:
        self.model_id = model_id
        self.model_version = model_version
        self.explainability_type = explainability_type
        self.feature_order = feature_order
        self._models_path = models_path

        self._predictor = None
        self._explainer = None

        self._load_artifacts()

    def _load_artifacts(self) -> None:
        self._predictor = joblib.load(self._models_path / "catboost_predictor.joblib")

        if SHAP_AVAILABLE and self.explainability_type.startswith("shap"):
            try:
                self._explainer = shap.TreeExplainer(self._predictor)
            except Exception:
                self._explainer = None

    def health(self) -> Dict[str, object]:
        return {
            "ready": self._predictor is not None,
            "explainability_available": self._explainer is not None,
        }

    def metadata(self) -> Dict[str, object]:
        return {
            "model_id": self.model_id,
            "model_version": self.model_version,
            "explainability_type": (
                self.explainability_type if self._explainer is not None else "none"
            ),
            "feature_count": len(self.feature_order),
        }

    def predict(self, features: Dict[str, float]) -> PredictionResult:
        input_data = {name: [features.get(name, np.nan)] for name in self.feature_order}
        df_features = pd.DataFrame(input_data, columns=self.feature_order)
        prediction = float(self._predictor.predict(df_features)[0])

        if self._explainer is None:
            explainability = ExplainabilityResult(
                base_value=prediction,
                waterfall=[],
                explainability_type="none",
            )
            return PredictionResult(prediction_meters=prediction, explainability=explainability)

        shap_values = self._explainer.shap_values(df_features)
        base_expected_value = float(
            self._explainer.expected_value[0]
            if isinstance(self._explainer.expected_value, (list, np.ndarray))
            else self._explainer.expected_value
        )
        contributions = shap_values[0] if isinstance(shap_values, list) else shap_values[0]

        waterfall_data = []
        for idx, feature_name in enumerate(self.feature_order):
            waterfall_data.append(
                WaterfallEntry(
                    feature=feature_name,
                    contribution=float(contributions[idx]),
                    rendered_value=float(df_features.iloc[0][feature_name]),
                )
            )

        waterfall_data.sort(key=lambda item: abs(item.contribution), reverse=True)
        top_influencers = waterfall_data[:5]
        other_contribution = sum(item.contribution for item in waterfall_data[5:])
        top_influencers.append(
            WaterfallEntry(
                feature="Other Combos",
                contribution=float(other_contribution),
                rendered_value=None,
            )
        )

        explainability = ExplainabilityResult(
            base_value=base_expected_value,
            waterfall=top_influencers,
            explainability_type=self.explainability_type,
        )
        return PredictionResult(prediction_meters=prediction, explainability=explainability)


def build_default_placeholder_adapter(
    models_path: Path,
    model_id: str,
    model_version: str,
    explainability_type: str,
) -> LakeModelAdapter:
    return LakeModelAdapter(
        models_path=models_path,
        model_id=model_id,
        model_version=model_version,
        explainability_type=explainability_type,
        feature_order=CANONICAL_FEATURE_ORDER,
    )
