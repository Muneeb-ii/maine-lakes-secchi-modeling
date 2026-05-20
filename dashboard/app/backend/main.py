import json
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Query
from typing import Dict

from contracts import (
    ExplainabilityResponse,
    LakeSearchItem,
    LakeSearchResponse,
    ModelHealthResponse,
    PredictScenarioResponse,
    PredictionPayloadResponse,
    ScenarioPayload,
    WaterfallItemResponse,
)
from feature_contract import CANONICAL_FEATURE_ORDER, get_feature_config_response
from model_registry import ModelRegistry


app = FastAPI(title="Lake Predictive Engine API")

def _allowed_origins() -> list[str]:
    raw_origins = os.getenv("API_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    if raw_origins.strip() == "*":
        return ["*"]
    return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]


# Setup CORS for local development with explicit production override support.
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULT_MODELS_PATH = Path(__file__).resolve().parents[3] / "artifacts" / "models"
models_path = Path(os.getenv("MODEL_ARTIFACTS_PATH", str(DEFAULT_MODELS_PATH))).resolve()
baseline_data = {}
lake_names_data = {}
registry = ModelRegistry(models_path=models_path)
SUPPORTED_REQUESTED_OUTPUTS = {"prediction", "explainability"}

@app.on_event("startup")
async def load_ml_objects():
    global baseline_data, lake_names_data
    print("Mounting ML memory and model registry...")

    registry.load()

    baseline_file = models_path / "baseline_lakes_summary.json"
    names_file = models_path / "lake_names.json"

    if baseline_file.exists():
        with open(baseline_file, "r") as f:
            baseline_data = json.load(f)
        print("Loaded baseline geometries from artifact.")

    if names_file.exists():
        with open(names_file, "r") as f:
            lake_names_data = json.load(f)
        print("Loaded lake name mapping dictionary.")

@app.get("/")
def read_root():
    response = ModelHealthResponse(
        status="Lake Predictive Engine Online",
        models_loaded=registry.is_ready(),
        schema_version="1.0.0",
        active_model=registry.active_model_metadata(),
        startup_errors=registry.startup_errors(),
    )
    return response.model_dump()


@app.get("/config/features")
def get_feature_config():
    config = get_feature_config_response()
    config["active_model"] = registry.active_model_metadata()
    config["startup_errors"] = registry.startup_errors()
    return config

@app.get("/lake/{midas_id}")
def get_lake_baseline(midas_id: str):
    """Retrieves the median baseline structure of a specific lake to initialize UI sliders."""
    midas_id = str(midas_id).upper().strip()
    
    lake_name = lake_names_data.get(midas_id, "Unknown Ecosystem")
    
    # Attempt strict match, otherwise return global fallback
    if midas_id in baseline_data:
        return {"status": "success", "lake_name": lake_name, "baseline": baseline_data[midas_id]}
    elif "GLOBAL_FALLBACK" in baseline_data:
        return {"status": "fallback", "lake_name": "Global Fallback Average", "baseline": baseline_data["GLOBAL_FALLBACK"]}
    else:
        raise HTTPException(status_code=404, detail="No baseline mapping available.")


@app.get("/lakes/search")
def search_lakes(q: str = Query(..., min_length=1), limit: int = Query(8, ge=1, le=25)):
    query = q.strip().upper()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    baseline_ids = set(str(midas).upper() for midas in baseline_data.keys() if midas != "GLOBAL_FALLBACK")
    matches = []
    for midas_id, lake_name in lake_names_data.items():
        normalized_id = str(midas_id).upper()
        if normalized_id not in baseline_ids:
            continue

        if query in normalized_id or query in str(lake_name).upper():
            matches.append(
                LakeSearchItem(
                    midas_id=normalized_id,
                    lake_name=str(lake_name),
                )
            )

    matches.sort(key=lambda item: (0 if item.midas_id.startswith(query) else 1, item.lake_name))
    response = LakeSearchResponse(query=q, results=matches[:limit])
    return response.model_dump()

@app.post("/predict_scenario")
def predict_scenario(payload: ScenarioPayload):
    if not registry.is_ready():
        raise HTTPException(
            status_code=503,
            detail={
                "message": "Models are unavailable.",
                "startup_errors": registry.startup_errors(),
            },
        )

    try:
        requested_outputs = set(payload.requested_outputs or ["prediction", "explainability"])
        unsupported_outputs = sorted(requested_outputs - SUPPORTED_REQUESTED_OUTPUTS)
        if unsupported_outputs:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Unsupported requested outputs.",
                    "unsupported_outputs": unsupported_outputs,
                    "supported_outputs": sorted(SUPPORTED_REQUESTED_OUTPUTS),
                },
            )

        normalized_features: Dict[str, float] = {}
        for feature_name in CANONICAL_FEATURE_ORDER:
            normalized_features[feature_name] = float(payload.features.get(feature_name, 0.0))

        prediction_result = registry.predict(
            features=normalized_features, model_id=payload.model_id
        )
        active_metadata = registry.active_model_metadata() or {}

        waterfall = [
            WaterfallItemResponse(
                feature=item.feature,
                contribution=item.contribution,
                rendered_value=item.rendered_value,
            )
            for item in prediction_result.explainability.waterfall
        ]

        response = PredictScenarioResponse(
            schema_version="1.0.0",
            model_id=str(active_metadata.get("model_id", "unknown")),
            model_version=str(active_metadata.get("model_version", "unknown")),
            explainability_type=prediction_result.explainability.explainability_type,
            prediction=PredictionPayloadResponse(value=prediction_result.prediction_meters),
            explainability=ExplainabilityResponse(
                base_value=prediction_result.explainability.base_value,
                waterfall=waterfall,
            ),
            prediction_meters=prediction_result.prediction_meters,
        )
        return response.model_dump()
    except HTTPException as exc:
        raise exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
