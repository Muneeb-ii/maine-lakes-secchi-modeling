import json
import math
import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Query
from contracts import (
    ExplainabilityResponse,
    LakeLocationsResponse,
    LakeSearchItem,
    LakeSearchResponse,
    ModelHealthResponse,
    PredictScenarioResponse,
    PredictionPayloadResponse,
    SensitivityItemResponse,
    SensitivityResponse,
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
from rate_limit import enforce_api_rate_limit, enforce_predict_rate_limit


def _dashboard_debug() -> bool:
    return os.getenv("DASHBOARD_DEBUG", "").strip().lower() in {"1", "true", "yes", "on"}


def _allowed_origins() -> tuple[list[str], bool]:
    raw_origins = os.getenv("API_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    if raw_origins.strip() == "*":
        return ["*"], False
    return [origin.strip() for origin in raw_origins.split(",") if origin.strip()], True


DEFAULT_MODELS_PATH = Path(__file__).resolve().parents[3] / "artifacts" / "models"
models_path = Path(os.getenv("MODEL_ARTIFACTS_PATH", str(DEFAULT_MODELS_PATH))).resolve()
baseline_data = {}
lake_names_data = {}
support_policy_data = {}
registry = ModelRegistry(models_path=models_path)
SUPPORTED_REQUESTED_OUTPUTS = {"prediction", "explainability"}
SENSITIVITY_FLAT_THRESHOLD_METERS = 0.01
SENSITIVITY_RANGE_SAMPLE_COUNT = 5


@asynccontextmanager
async def lifespan(app: FastAPI):
    global baseline_data, lake_names_data, support_policy_data
    print("Mounting ML memory and model registry...")

    registry.load()
    if registry.is_ready():
        print("Active prediction model loaded.")
    else:
        for error in registry.startup_errors():
            print(f"Model startup error: {error}")

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

    yield


allowed_origins, allow_cors_credentials = _allowed_origins()

app = FastAPI(title="Lake Predictive Engine API", lifespan=lifespan)

# Setup CORS for local development with explicit production override support.
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=allow_cors_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.method != "OPTIONS":
        enforce_api_rate_limit(request)
        if request.method == "POST" and request.url.path.startswith("/predict_scenario"):
            enforce_predict_rate_limit(request)
    return await call_next(request)


def _public_startup_errors() -> list[str]:
    errors = registry.startup_errors()
    if _dashboard_debug():
        return errors
    if not errors:
        return []
    return [
        "Active model failed to load. Check backend startup logs and run the API from the project virtualenv."
    ]


def _normalize_midas_id(midas_id: str) -> str:
    normalized = str(midas_id or "").upper().strip()
    if not normalized or len(normalized) > 32:
        raise HTTPException(status_code=400, detail="Please choose a valid lake.")
    return normalized


def _locked_baseline_for_prediction(midas_id: str) -> dict:
    if midas_id not in baseline_data or midas_id == "GLOBAL_FALLBACK":
        raise HTTPException(status_code=400, detail="Please choose a lake with enough information for predictions.")
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

def _finite_float_or_none(value) -> float | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return numeric if math.isfinite(numeric) else None

def _lake_location_item(midas_id: str) -> LakeSearchItem | None:
    normalized_id = str(midas_id).upper()
    if normalized_id == "GLOBAL_FALLBACK" or normalized_id not in baseline_data:
        return None

    baseline = baseline_data.get(normalized_id) or {}
    latitude = _finite_float_or_none(baseline.get("LATITUDE"))
    longitude = _finite_float_or_none(baseline.get("LONGITUDE"))
    if latitude is None or longitude is None:
        return None

    return LakeSearchItem(
        midas_id=normalized_id,
        lake_name=str(lake_names_data.get(normalized_id, "Unknown Ecosystem")),
        latitude=latitude,
        longitude=longitude,
        area_acres=_finite_float_or_none(baseline.get("AREA_ACRES")),
    )


def _prediction_features(payload: ScenarioPayload) -> dict:
    midas_id = _normalize_midas_id(payload.midas_id)
    baseline = _locked_baseline_for_prediction(midas_id)
    normalized_features = {}
    for feature_name in CANONICAL_FEATURE_ORDER:
        if feature_name in LOCKED_BASELINE_FEATURES:
            normalized_features[feature_name] = float(baseline[feature_name])
            continue
        raw_value = payload.features.get(feature_name, baseline.get(feature_name, 0.0))
        if raw_value is None:
            normalized_features[feature_name] = float("nan")
            continue
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail=f"Feature {feature_name} must be numeric.")
        _validate_editable_feature(feature_name, value)
        normalized_features[feature_name] = value
    return normalized_features

def _model_prediction(features: dict, model_id: str | None = None) -> float:
    return registry.predict(
        features=features,
        model_id=model_id,
        include_explainability=False,
    ).prediction_meters

def _sensitivity_direction(delta_up: float, delta_down: float) -> str:
    threshold = SENSITIVITY_FLAT_THRESHOLD_METERS
    up_significant = abs(delta_up) >= threshold
    down_significant = abs(delta_down) >= threshold

    if not up_significant and not down_significant:
        return "flat"
    if delta_up >= threshold and (not down_significant or delta_down <= -threshold):
        return "clearer"
    if delta_up <= -threshold and (not down_significant or delta_down >= threshold):
        return "murkier"
    if delta_down <= -threshold and not up_significant:
        return "clearer"
    if delta_down >= threshold and not up_significant:
        return "murkier"
    return "mixed"

def _direction_from_delta(delta: float) -> str:
    threshold = SENSITIVITY_FLAT_THRESHOLD_METERS
    if delta >= threshold:
        return "clearer"
    if delta <= -threshold:
        return "murkier"
    return "flat"

def _sensitivity_summary_direction(local_direction: str, range_direction: str) -> str:
    if local_direction == "flat" and range_direction in {"clearer", "murkier", "mixed"}:
        return "range_sensitive"
    if local_direction in {"clearer", "murkier"} and range_direction not in {"flat", local_direction}:
        return "mixed"
    return local_direction

def _range_sensitivity_for_feature(
    feature_name: str,
    features: dict,
    baseline_prediction: float,
    current_value: float,
    max_value: float,
    model_id: str | None = None,
) -> tuple[str, float]:
    if current_value >= max_value:
        return "flat", 0.0

    sample_count = SENSITIVITY_RANGE_SAMPLE_COUNT
    interval = (max_value - current_value) / sample_count
    deltas = []
    directions = set()
    for index in range(1, sample_count + 1):
        sampled_value = current_value + interval * index
        sampled_features = dict(features)
        sampled_features[feature_name] = sampled_value
        delta = _model_prediction(sampled_features, model_id=model_id) - baseline_prediction
        deltas.append(delta)
        direction = _direction_from_delta(delta)
        if direction != "flat":
            directions.add(direction)

    if len(directions) > 1:
        return "mixed", max(deltas, key=abs)
    if len(directions) == 1:
        direction = next(iter(directions))
        directional_deltas = [delta for delta in deltas if _direction_from_delta(delta) == direction]
        return direction, max(directional_deltas, key=abs)
    return "flat", max(deltas, key=abs) if deltas else 0.0

def _sensitivity_item_for_feature(
    feature_name: str,
    features: dict,
    baseline_prediction: float,
    model_id: str | None = None,
) -> SensitivityItemResponse:
    definition = FEATURE_DEFINITIONS[feature_name]
    slider = definition.get("slider") or {}
    unit = str(definition.get("unit", ""))
    value = features.get(feature_name)

    if value is None or not math.isfinite(float(value)):
        return SensitivityItemResponse(feature=feature_name, direction="unavailable", unit=unit)

    numeric_value = float(value)
    min_value = float(slider.get("min", numeric_value))
    max_value = float(slider.get("max", numeric_value))
    step = float(slider.get("step", 0.1))
    up_value = min(max_value, numeric_value + step)
    down_value = max(min_value, numeric_value - step)

    up_features = dict(features)
    down_features = dict(features)
    up_features[feature_name] = up_value
    down_features[feature_name] = down_value

    up_prediction = _model_prediction(up_features, model_id=model_id)
    down_prediction = _model_prediction(down_features, model_id=model_id)
    delta_up = up_prediction - baseline_prediction
    delta_down = down_prediction - baseline_prediction
    local_direction = _sensitivity_direction(delta_up, delta_down)
    range_direction, range_delta = _range_sensitivity_for_feature(
        feature_name,
        features,
        baseline_prediction,
        numeric_value,
        max_value,
        model_id=model_id,
    )

    return SensitivityItemResponse(
        feature=feature_name,
        direction=_sensitivity_summary_direction(local_direction, range_direction),
        local_direction=local_direction,
        range_direction=range_direction,
        range_delta_meters=range_delta,
        delta_up_meters=delta_up,
        delta_down_meters=delta_down,
        step=step,
        unit=unit,
        value=numeric_value,
        value_up=up_value,
        value_down=down_value,
    )


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
        raise HTTPException(status_code=404, detail="We could not find enough information for that lake.")


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
            item = _lake_location_item(normalized_id)
            if item:
                item.lake_name = str(lake_name)
                matches.append(item)

    matches.sort(key=lambda item: (0 if item.midas_id.startswith(query) else 1, item.lake_name))
    response = LakeSearchResponse(query=q, results=matches[:limit])
    return response.model_dump()

@app.get("/lakes/locations")
def get_lake_locations():
    results = []
    for midas_id in baseline_data.keys():
        item = _lake_location_item(midas_id)
        if item:
            results.append(item)
    results.sort(key=lambda item: (item.lake_name, item.midas_id))
    return LakeLocationsResponse(results=results).model_dump()

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

@app.post("/predict_scenario/sensitivity")
def predict_scenario_sensitivity(payload: ScenarioPayload, request: Request):
    if not registry.is_ready():
        raise HTTPException(
            status_code=503,
            detail={
                "message": "Models are unavailable.",
                "startup_errors": _public_startup_errors(),
            },
        )

    try:
        normalized_features = _prediction_features(payload)
        baseline_prediction = _model_prediction(normalized_features, model_id=payload.model_id)
        active_metadata = registry.active_model_metadata() or {}
        items = [
            _sensitivity_item_for_feature(
                feature_name,
                normalized_features,
                baseline_prediction,
                model_id=payload.model_id,
            )
            for feature_name in get_feature_config_response()["editable_features"]
        ]

        response = SensitivityResponse(
            schema_version="1.0.0",
            model_id=str(active_metadata.get("model_id", "unknown")),
            model_version=str(active_metadata.get("model_version", "unknown")),
            baseline_prediction_meters=baseline_prediction,
            items=items,
        )
        return response.model_dump()
    except HTTPException as exc:
        raise exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        if _dashboard_debug():
            raise HTTPException(status_code=500, detail=str(exc))
        print(f"Sensitivity failed: {exc}")
        raise HTTPException(status_code=500, detail="Sensitivity service failed.")
