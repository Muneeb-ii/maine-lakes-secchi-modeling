from dataclasses import dataclass
from typing import Dict, List, Optional, Protocol


@dataclass
class WaterfallEntry:
    feature: str
    contribution: float
    rendered_value: Optional[float]


@dataclass
class ExplainabilityResult:
    base_value: float
    waterfall: List[WaterfallEntry]
    explainability_type: str


@dataclass
class PredictionResult:
    prediction_meters: float
    explainability: ExplainabilityResult


class ModelAdapter(Protocol):
    model_id: str

    def health(self) -> Dict[str, object]:
        ...

    def metadata(self) -> Dict[str, object]:
        ...

    def predict(self, features: Dict[str, float]) -> PredictionResult:
        ...


def ensure_model_adapter_contract(adapter: object) -> None:
    required_attributes = ["model_id", "health", "metadata", "predict"]
    missing = [attr for attr in required_attributes if not hasattr(adapter, attr)]
    if missing:
        raise TypeError(f"Model adapter is missing required attributes: {missing}")
