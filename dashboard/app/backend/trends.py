"""Read-only loader for the precomputed Experiment 46 trends artifact."""
import json
from pathlib import Path


class TrendsStore:
    def __init__(self, path: Path):
        self.path = path
        self.data = None
        self.error = None

    def load(self) -> None:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            required = {"dataset_id", "observations_through_year", "model", "forecast_years", "target", "support_policy", "validation", "lakes", "details"}
            if not required.issubset(payload) or not isinstance(payload["lakes"], list) or not isinstance(payload["details"], dict):
                raise ValueError("trends artifact has an invalid structure")
            self.data = payload
            self.error = None
        except Exception as exc:
            self.data = None
            self.error = str(exc)

    def require(self) -> dict:
        if self.data is None:
            raise RuntimeError(self.error or "trends artifact is unavailable")
        return self.data

    def index(self) -> dict:
        data = self.require()
        return {key: data[key] for key in ("dataset_id", "observations_through_year", "model", "forecast_years", "target", "support_policy", "validation", "lakes")}

    def detail(self, midas_id: str) -> dict | None:
        return self.require()["details"].get(str(midas_id).strip().lower())
