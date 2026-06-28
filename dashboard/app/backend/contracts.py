from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ScenarioPayload(BaseModel):
    midas_id: str = Field(..., min_length=1, max_length=32)
    features: Dict[str, Optional[float]]
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

class SensitivityItemResponse(BaseModel):
    feature: str
    direction: str
    local_direction: Optional[str] = None
    range_direction: Optional[str] = None
    range_delta_meters: Optional[float] = None
    delta_up_meters: Optional[float] = None
    delta_down_meters: Optional[float] = None
    step: Optional[float] = None
    unit: str = ""
    value: Optional[float] = None
    value_up: Optional[float] = None
    value_down: Optional[float] = None

class SensitivityResponse(BaseModel):
    schema_version: str = Field(default="1.0.0")
    model_id: str
    model_version: str
    baseline_prediction_meters: float
    items: List[SensitivityItemResponse]


class ModelHealthResponse(BaseModel):
    status: str
    models_loaded: bool
    schema_version: str
    active_model: Optional[Dict[str, object]] = None
    startup_errors: List[str] = Field(default_factory=list)


class LakeSearchItem(BaseModel):
    midas_id: str
    lake_name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    area_acres: Optional[float] = None


class LakeSearchResponse(BaseModel):
    query: str
    results: List[LakeSearchItem]


class LakeLocationsResponse(BaseModel):
    results: List[LakeSearchItem]
