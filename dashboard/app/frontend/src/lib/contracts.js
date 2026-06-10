function toFiniteNumberOrNull(value) {
  if (value === null || value === undefined || value === "") return null;
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : null;
}

export function buildPayloadFeatures(
  features,
  baseline,
  featureConfig,
  includedEditableFeatures = featureConfig?.editable_features || []
) {
  const canonicalOrder = featureConfig?.canonical_feature_order || [];
  const lockedBaselineFeatures = new Set(featureConfig?.locked_baseline_features || []);
  const editableFeatures = new Set(featureConfig?.editable_features || []);
  const includedEditable = new Set(includedEditableFeatures || []);
  const payload = {};

  canonicalOrder.forEach((featureName) => {
    if (lockedBaselineFeatures.has(featureName)) {
      payload[featureName] = toFiniteNumberOrNull(
        baseline?.[featureName] ?? features?.[featureName]
      );
      return;
    }
    if (editableFeatures.has(featureName) && !includedEditable.has(featureName)) {
      payload[featureName] = null;
      return;
    }
    payload[featureName] = toFiniteNumberOrNull(
      features?.[featureName] ?? baseline?.[featureName]
    );
  });

  return payload;
}

export function parsePredictionResponse(payload) {
  if (!payload || typeof payload !== "object") {
    throw new Error("We could not read the prediction response. Please try again.");
  }

  const predictionMeters =
    typeof payload.prediction_meters === "number"
      ? payload.prediction_meters
      : payload?.prediction?.value;

  if (typeof predictionMeters !== "number" || Number.isNaN(predictionMeters)) {
    throw new Error("The prediction result was incomplete. Please try again.");
  }

  const explainability = payload.explainability || {};
  const baseValueRaw = explainability.base_value;
  const baseValue =
    typeof baseValueRaw === "number" && !Number.isNaN(baseValueRaw)
      ? baseValueRaw
      : predictionMeters;

  const waterfall = Array.isArray(explainability.waterfall)
    ? explainability.waterfall.map((item) => ({
        feature: String(item.feature ?? "Unknown"),
        contribution: Number(item.contribution ?? 0),
        rendered_value:
          item.rendered_value === null || item.rendered_value === undefined
            ? null
            : Number(item.rendered_value),
      }))
    : [];

  return {
    schemaVersion: payload.schema_version || "legacy",
    modelVersion: payload.model_version || "unknown",
    modelId: payload.model_id || "unknown",
    explainabilityType: payload.explainability_type || "unknown",
    predictionMeters,
    explainability: {
      base_value: baseValue,
      waterfall,
    },
  };
}

export function validateFeatureConfig(featureConfig) {
  if (!featureConfig || typeof featureConfig !== "object") {
    throw new Error("Water condition settings could not be loaded.");
  }
  if (!Array.isArray(featureConfig.canonical_feature_order)) {
    throw new Error("Water condition settings are incomplete.");
  }
  if (!featureConfig.features || typeof featureConfig.features !== "object") {
    throw new Error("Water condition labels could not be loaded.");
  }
  return true;
}

export function parseLakeSearchResponse(payload) {
  if (!payload || typeof payload !== "object") {
    throw new Error("Lake search results could not be loaded.");
  }
  const results = Array.isArray(payload.results) ? payload.results : [];
  return results
    .filter((item) => item && item.midas_id)
    .map((item) => ({
      midasId: String(item.midas_id),
      lakeName: String(item.lake_name || "Unknown Lake"),
    }));
}

export function parseApiError(payload) {
  if (typeof payload === "string") return payload;
  if (!payload || typeof payload !== "object") return "Something went wrong. Please try again.";
  if (typeof payload.detail === "string") return payload.detail;
  if (payload.detail && typeof payload.detail.message === "string") return payload.detail.message;
  if (typeof payload.message === "string") return payload.message;
  return "Something went wrong. Please try again.";
}
