export function buildPayloadFeatures(features, baseline, featureConfig) {
  const canonicalOrder = featureConfig?.canonical_feature_order || [];
  const lockedBaselineFeatures = new Set(featureConfig?.locked_baseline_features || []);
  const payload = {};

  canonicalOrder.forEach((featureName) => {
    if (lockedBaselineFeatures.has(featureName)) {
      payload[featureName] = Number(
        baseline?.[featureName] ?? features?.[featureName] ?? 0
      );
      return;
    }
    payload[featureName] = Number(features?.[featureName] ?? baseline?.[featureName] ?? 0);
  });

  return payload;
}

export function parsePredictionResponse(payload) {
  if (!payload || typeof payload !== "object") {
    throw new Error("Invalid prediction response payload.");
  }

  const predictionMeters =
    typeof payload.prediction_meters === "number"
      ? payload.prediction_meters
      : payload?.prediction?.value;

  if (typeof predictionMeters !== "number" || Number.isNaN(predictionMeters)) {
    throw new Error("Prediction response is missing a numeric prediction value.");
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
    throw new Error("Feature config payload missing.");
  }
  if (!Array.isArray(featureConfig.canonical_feature_order)) {
    throw new Error("Feature config missing canonical_feature_order.");
  }
  if (!featureConfig.features || typeof featureConfig.features !== "object") {
    throw new Error("Feature config missing features map.");
  }
  return true;
}

export function parseLakeSearchResponse(payload) {
  if (!payload || typeof payload !== "object") {
    throw new Error("Invalid lake search payload.");
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
  if (!payload || typeof payload !== "object") return "Unknown API error.";
  if (typeof payload.detail === "string") return payload.detail;
  if (payload.detail && typeof payload.detail.message === "string") return payload.detail.message;
  if (typeof payload.message === "string") return payload.message;
  return "Request failed.";
}
