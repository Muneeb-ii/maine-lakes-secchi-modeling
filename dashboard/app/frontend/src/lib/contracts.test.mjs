import test from "node:test";
import assert from "node:assert/strict";

import {
  buildPayloadFeatures,
  parseApiError,
  parseLakeSearchResponse,
  parsePredictionResponse,
  validateFeatureConfig,
} from "./contracts.js";

test("buildPayloadFeatures prioritizes baseline locked values", () => {
  const payload = buildPayloadFeatures(
    { TPEC: 15, LATITUDE: 0 },
    { LATITUDE: 44.11, TPEC: 10 },
    {
      canonical_feature_order: ["LATITUDE", "TPEC"],
      locked_baseline_features: ["LATITUDE"],
    }
  );

  assert.equal(payload.LATITUDE, 44.11);
  assert.equal(payload.TPEC, 15);
});

test("parsePredictionResponse supports versioned payload", () => {
  const parsed = parsePredictionResponse({
    schema_version: "1.0.0",
    model_id: "m1",
    model_version: "v1",
    explainability_type: "none",
    prediction: { value: 2.3 },
    explainability: { base_value: 2.1, waterfall: [] },
  });
  assert.equal(parsed.predictionMeters, 2.3);
  assert.equal(parsed.schemaVersion, "1.0.0");
});

test("validateFeatureConfig rejects invalid contract", () => {
  assert.throws(() => validateFeatureConfig({}), /canonical_feature_order/);
});

test("parseLakeSearchResponse normalizes list", () => {
  const results = parseLakeSearchResponse({
    results: [{ midas_id: "C3420", lake_name: "Crystal Lake" }],
  });
  assert.equal(results[0].midasId, "C3420");
  assert.equal(results[0].lakeName, "Crystal Lake");
});

test("parseApiError handles structured detail", () => {
  assert.equal(
    parseApiError({ detail: { message: "Unsupported requested outputs." } }),
    "Unsupported requested outputs."
  );
});
