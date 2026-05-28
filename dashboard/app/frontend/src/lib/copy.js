export const DASHBOARD_TITLE = "Maine Lake Water Clarity Dashboard";
export const DASHBOARD_TAGLINE = "Explore how lake conditions affect predicted Secchi depth.";
export const MODEL_FOOTNOTE =
  "Predictions use a CatBoost model trained on Maine lakes with enough monitoring history.";
export const SECCHI_DIRECTION_NOTE = "Higher Secchi depth = clearer water";

export const SECTION_LABELS = {
  lakeProfile: "Lake profile",
  parameters: "Parameters",
  prediction: "Predicted Secchi depth",
  trajectory: "Scenario trajectory",
  explainability: "Prediction drivers",
  scenarioActions: "Scenario actions",
};

export const LAKE_PROFILE_INTRO =
  "Location and size for the selected lake. These fields stay fixed while you adjust water conditions.";

export const METRIC_LABELS = {
  modelBaseline: "Baseline prediction",
  deltaFromBaseline: "Change from baseline",
  latestChange: "Latest change",
  steps: "Steps",
  sessionRange: "Session range",
  latestVsBaseline: "Latest vs baseline",
};

export const LAKE_FIELD_LABELS = {
  latitude: "Latitude",
  longitude: "Longitude",
  areaAcres: "Area (acres)",
  maxDepth: "Max depth (ft)",
};

export const UNKNOWN_LAKE_NAME = "Unknown Ecosystem";

export const LAKE_SUPPORT_MESSAGES = {
  supported:
    "This lake is in the recommended monitoring set for this model.",
  unsupported:
    "Predictions are shown, but this lake is outside the recommended support policy. Treat results as exploratory.",
  fallback:
    "No lake-specific baseline found; showing a statewide fallback profile.",
};

export const TRAJECTORY_STEP_NOTE =
  "A step is recorded when a slider adjustment changes predicted Secchi by at least 0.02 m. Small movements may not appear.";

export const TRAJECTORY_RESET_CONFIRM =
  "Clear all trajectory steps for this session? Your current slider settings will stay the same.";

export function formatLakeContext(lakeName, lakeId) {
  const id = String(lakeId || "").trim().toUpperCase();
  const name = String(lakeName || "").trim();
  const hasReadableName = name && name !== UNKNOWN_LAKE_NAME;
  if (hasReadableName) {
    return `Viewing ${name} (MIDAS ${id})`;
  }
  return `Viewing lake MIDAS ${id}`;
}
