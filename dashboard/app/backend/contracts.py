from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ScenarioPayload(BaseModel):
    midas_id: str = Field(..., min_length=1, max_length=32)
    features: Dict[str, float]
    model_id: Optional[str] = None
    requested_outputs: Optional[List[str]] = None


class WaterfallItemResponse(BaseModel):
    feature: str
    contribution: float
    rendered_value: Optional[float]


class ExplainabilityResponse(BaseModel):
    base_value: float
    waterfall: List[WaterfallItemResponse]


class PredictionPayloadResponse(BaseModel):
    value: float
    unit: str = "m"
    target: str = "SECCHI"


class PredictScenarioResponse(BaseModel):
    schema_version: str = Field(default="1.0.0")
    model_id: str
    model_version: str
    explainability_type: str
    prediction: PredictionPayloadResponse
    explainability: ExplainabilityResponse

    # Compatibility fields for existing frontend consumers.
    prediction_meters: float


class ModelHealthResponse(BaseModel):
    status: str
    models_loaded: bool
    schema_version: str
    active_model: Optional[Dict[str, object]] = None
    startup_errors: List[str] = Field(default_factory=list)


class LakeSearchItem(BaseModel):
    midas_id: str
    lake_name: str


class LakeSearchResponse(BaseModel):
    query: str
    results: List[LakeSearchItem]
