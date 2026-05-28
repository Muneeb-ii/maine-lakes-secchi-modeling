import json
import math
import os
import time
from collections import defaultdict, deque
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Query
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
from feature_contract import (
    CANONICAL_FEATURE_ORDER,
    FEATURE_DEFINITIONS,
    LOCKED_BASELINE_FEATURES,
    get_feature_config_response,
)
from model_registry import ModelRegistry


app = FastAPI(title="Lake Predictive Engine API")

def _dashboard_debug() -> bool:
    return os.getenv("DASHBOARD_DEBUG", "").strip().lower() in {"1", "true", "yes", "on"}


def _allowed_origins() -> tuple[list[str], bool]:
    raw_origins = os.getenv("API_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    if raw_origins.strip() == "*":
        return ["*"], False
    return [origin.strip() for origin in raw_origins.split(",") if origin.strip()], True


allowed_origins, allow_cors_credentials = _allowed_origins()

# Setup CORS for local development with explicit production override support.
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=allow_cors_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULT_MODELS_PATH = Path(__file__).resolve().parents[3] / "artifacts" / "models"
models_path = Path(os.getenv("MODEL_ARTIFACTS_PATH", str(DEFAULT_MODELS_PATH))).resolve()
baseline_data = {}
lake_names_data = {}
support_policy_data = {}
registry = ModelRegistry(models_path=models_path)
SUPPORTED_REQUESTED_OUTPUTS = {"prediction", "explainability"}
RATE_LIMIT_WINDOW_SECONDS = 60
PREDICT_RATE_LIMIT_PER_MINUTE = int(os.getenv("PREDICT_RATE_LIMIT_PER_MINUTE", "60"))
_predict_request_times = defaultdict(deque)


def _public_startup_errors() -> list[str]:
    return registry.startup_errors() if _dashboard_debug() else []


def _client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for", "")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip() or "unknown"
    return request.client.host if request.client else "unknown"


def _enforce_rate_limit(request: Request) -> None:
    if PREDICT_RATE_LIMIT_PER_MINUTE <= 0:
        return
    now = time.monotonic()
    key = _client_ip(request)
    request_times = _predict_request_times[key]
    while request_times and now - request_times[0] > RATE_LIMIT_WINDOW_SECONDS:
        request_times.popleft()
    if len(request_times) >= PREDICT_RATE_LIMIT_PER_MINUTE:
        raise HTTPException(status_code=429, detail="Prediction rate limit exceeded. Try again shortly.")
    request_times.append(now)


def _normalize_midas_id(midas_id: str) -> str:
    normalized = str(midas_id or "").upper().strip()
    if not normalized or len(normalized) > 32:
        raise HTTPException(status_code=400, detail="Invalid MIDAS ID.")
    return normalized


def _locked_baseline_for_prediction(midas_id: str) -> dict:
    if midas_id not in baseline_data or midas_id == "GLOBAL_FALLBACK":
        raise HTTPException(status_code=400, detail="Predictions require a supported lake MIDAS ID with baseline data.")
    baseline = baseline_data[midas_id]
    missing_locked = [name for name in LOCKED_BASELINE_FEATURES if name not in baseline]
    if missing_locked:
        raise HTTPException(status_code=500, detail="Prediction baseline is incomplete." if _dashboard_debug() else "Prediction service is unavailable.")
    return baseline


def _validate_editable_feature(feature_name: str, value: float) -> None:
    if not math.isfinite(value):
        raise HTTPException(status_code=400, detail=f"Feature {feature_name} must be finite.")
    slider = FEATURE_DEFINITIONS.get(feature_name, {}).get("slider")
    if not slider:
        return
    min_value = slider.get("min")
    max_value = slider.get("max")
    if min_value is not None and value < float(min_value):
        raise HTTPException(status_code=400, detail=f"Feature {feature_name} is below the allowed minimum.")
    if max_value is not None and value > float(max_value):
        raise HTTPException(status_code=400, detail=f"Feature {feature_name} is above the allowed maximum.")


def _prediction_features(payload: ScenarioPayload) -> dict:
    midas_id = _normalize_midas_id(payload.midas_id)
    baseline = _locked_baseline_for_prediction(midas_id)
    normalized_features = {}
    for feature_name in CANONICAL_FEATURE_ORDER:
        if feature_name in LOCKED_BASELINE_FEATURES:
            normalized_features[feature_name] = float(baseline[feature_name])
            continue
        raw_value = payload.features.get(feature_name, baseline.get(feature_name, 0.0))
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail=f"Feature {feature_name} must be numeric.")
        _validate_editable_feature(feature_name, value)
        normalized_features[feature_name] = value
    return normalized_features

@app.on_event("startup")
async def load_ml_objects():
    global baseline_data, lake_names_data, support_policy_data
    print("Mounting ML memory and model registry...")

    registry.load()

    baseline_file = models_path / "baseline_lakes_summary.json"
    names_file = models_path / "lake_names.json"
    support_file = models_path / "supported_lakes_policy.json"

    if baseline_file.exists():
        with open(baseline_file, "r") as f:
            baseline_data = json.load(f)
        print("Loaded baseline geometries from artifact.")

    if names_file.exists():
        with open(names_file, "r") as f:
            raw_lake_names = json.load(f)
        lake_names_data = {str(key).upper(): value for key, value in raw_lake_names.items()}
        print("Loaded lake name mapping dictionary.")

    if support_file.exists():
        with open(support_file, "r") as f:
            support_policy_data = json.load(f)
        print("Loaded supported-lake policy metadata.")

@app.get("/")
def read_root():
    response = ModelHealthResponse(
        status="Lake Predictive Engine Online",
        models_loaded=registry.is_ready(),
        schema_version="1.0.0",
        active_model=registry.active_model_metadata(),
        startup_errors=_public_startup_errors(),
    )
    return response.model_dump()


@app.get("/config/features")
def get_feature_config():
    config = get_feature_config_response()
    config["active_model"] = registry.active_model_metadata()
    config["startup_errors"] = _public_startup_errors()
    return config

@app.get("/lake/{midas_id}")
def get_lake_baseline(midas_id: str):
    """Retrieves the median baseline structure of a specific lake to initialize UI sliders."""
    midas_id = _normalize_midas_id(midas_id)
    
    lake_name = lake_names_data.get(midas_id, "Unknown Ecosystem")
    
    supported_ids = set(str(item).upper() for item in support_policy_data.get("supported_lakes", []))
    quality_rows = support_policy_data.get("lake_quality", [])
    quality = next((row for row in quality_rows if str(row.get("MIDAS", "")).upper() == midas_id), None)
    policy = support_policy_data.get("policy", {})

    # Attempt strict match, otherwise return global fallback.
    if midas_id in baseline_data:
        return {
            "status": "success",
            "lake_name": lake_name,
            "baseline": baseline_data[midas_id],
            "supported": midas_id in supported_ids,
            "support_policy": policy,
            "lake_quality": quality,
        }
    elif "GLOBAL_FALLBACK" in baseline_data:
        return {
            "status": "fallback",
            "lake_name": "Global Fallback Average",
            "baseline": baseline_data["GLOBAL_FALLBACK"],
            "supported": False,
            "support_policy": policy,
            "lake_quality": quality,
        }
    else:
        raise HTTPException(status_code=404, detail="No baseline mapping available.")


@app.get("/lakes/search")
def search_lakes(q: str = Query(..., min_length=1, max_length=80), limit: int = Query(8, ge=1, le=25)):
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
def predict_scenario(payload: ScenarioPayload, request: Request):
    if not registry.is_ready():
        raise HTTPException(
            status_code=503,
            detail={
                "message": "Models are unavailable.",
                "startup_errors": _public_startup_errors(),
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

        _enforce_rate_limit(request)
        normalized_features = _prediction_features(payload)

        include_explainability = "explainability" in requested_outputs
        prediction_result = registry.predict(
            features=normalized_features,
            model_id=payload.model_id,
            include_explainability=include_explainability,
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
        if _dashboard_debug():
            raise HTTPException(status_code=500, detail=str(exc))
        print(f"Prediction failed: {exc}")
        raise HTTPException(status_code=500, detail="Prediction service failed.")
