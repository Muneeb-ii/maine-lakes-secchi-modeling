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

test("buildPayloadFeatures sends excluded editable features as null", () => {
  const payload = buildPayloadFeatures(
    { TPEC: 15, TPBG: 30 },
    { LATITUDE: 44.11, TPEC: null, TPBG: null },
    {
      canonical_feature_order: ["LATITUDE", "TPEC", "TPBG"],
      locked_baseline_features: ["LATITUDE"],
      editable_features: ["TPEC", "TPBG"],
    },
    ["TPEC"]
  );

  assert.equal(payload.TPEC, 15);
  assert.equal(payload.TPBG, null);
});

test("buildPayloadFeatures preserves missing editable baseline as null", () => {
  const payload = buildPayloadFeatures(
    {},
    { TPEC: null },
    {
      canonical_feature_order: ["TPEC"],
      locked_baseline_features: [],
      editable_features: ["TPEC"],
    },
    ["TPEC"]
  );

  assert.equal(payload.TPEC, null);
});

test("buildPayloadFeatures does not coerce null chemistry to zero", () => {
  const payload = buildPayloadFeatures(
    { TPBG: 12, TPEC: 8 },
    { TPBG: null, TPEC: null },
    {
      canonical_feature_order: ["TPBG", "TPEC"],
      locked_baseline_features: [],
      editable_features: ["TPBG", "TPEC"],
    },
    ["TPBG", "TPEC"]
  );

  assert.equal(payload.TPBG, 12);
  assert.equal(payload.TPEC, 8);
  assert.notEqual(payload.TPBG, 0);
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
  assert.throws(() => validateFeatureConfig({}), /Water condition settings are incomplete/);
});

test("parseLakeSearchResponse normalizes list", () => {
  const results = parseLakeSearchResponse({
    results: [
      {
        midas_id: "C3420",
        lake_name: "Crystal Lake",
        latitude: 44.12345,
        longitude: -69.98765,
        area_acres: 120.5,
      },
      { midas_id: "A1200", lake_name: "Alpha Pond" },
    ],
  });
  assert.equal(results[0].midasId, "C3420");
  assert.equal(results[0].lakeName, "Crystal Lake");
  assert.equal(results[0].latitude, 44.12345);
  assert.equal(results[0].longitude, -69.98765);
  assert.equal(results[0].areaAcres, 120.5);
  assert.equal(results[1].latitude, undefined);
});

test("parseApiError handles structured detail", () => {
  assert.equal(
    parseApiError({ detail: { message: "Unsupported requested outputs." } }),
    "Unsupported requested outputs."
  );
});
