from pathlib import Path
from typing import Dict, List, Optional

from artifact_validation import load_manifest, validate_manifest
from feature_contract import CANONICAL_FEATURE_ORDER
from model_adapters import build_default_placeholder_adapter
from model_interface import ModelAdapter, PredictionResult, ensure_model_adapter_contract


class ModelRegistry:
    def __init__(self, models_path: Path):
        self.models_path = models_path
        self._active_model: Optional[ModelAdapter] = None
        self._startup_errors: List[str] = []
        self._manifest: Optional[Dict[str, object]] = None

    def load(self) -> None:
        manifest_path = self.models_path / "model_manifest.json"
        if not manifest_path.exists():
            self._startup_errors.append("Missing model manifest: model_manifest.json")
            return

        self._manifest = load_manifest(manifest_path)
        manifest_ok, manifest_errors = validate_manifest(
            models_path=self.models_path,
            manifest=self._manifest,
            expected_feature_order=CANONICAL_FEATURE_ORDER,
        )
        if not manifest_ok:
            self._startup_errors.extend(manifest_errors)
            return

        try:
            self._active_model = build_default_placeholder_adapter(
                models_path=self.models_path,
                model_id=str(self._manifest.get("model_id", "placeholder")),
                model_version=str(self._manifest.get("model_version", "unknown")),
                explainability_type=str(
                    self._manifest.get("explainability", {}).get("type", "shap_tree")
                ),
            )
            ensure_model_adapter_contract(self._active_model)
        except Exception as exc:
            self._startup_errors.append(f"Failed to initialize active model: {exc}")

    def is_ready(self) -> bool:
        return self._active_model is not None and len(self._startup_errors) == 0

    def startup_errors(self) -> List[str]:
        return self._startup_errors

    def active_model_metadata(self) -> Optional[Dict[str, object]]:
        if self._active_model is None:
            return None
        metadata = self._active_model.metadata()
        metadata["health"] = self._active_model.health()
        return metadata

    def predict(self, features: Dict[str, float], model_id: Optional[str] = None) -> PredictionResult:
        if self._active_model is None:
            raise RuntimeError("No active model is loaded.")

        if model_id and model_id != self._active_model.model_id:
            raise ValueError(
                f"Requested model_id '{model_id}' is unavailable. Active model: '{self._active_model.model_id}'."
            )

        return self._active_model.predict(features)
