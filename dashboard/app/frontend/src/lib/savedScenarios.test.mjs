import assert from "node:assert/strict";
import { test } from "node:test";
import { formatSavedScenarioOption } from "./copy.js";
import {
  buildFeaturesFromSnapshot,
  buildSavedScenario,
  compareIdForLake,
  countOtherLakeScenarios,
  hasChangesFromSnapshot,
  inferIncludedFeatures,
  migrateSavedScenario,
  migrateSavedScenarios,
  normalizeScenarioLabel,
  prependSavedScenario,
  sanitizeCompareId,
  scenariosForLake,
  SAVED_SCENARIO_MAX,
} from "./savedScenarios.js";

const editableFeatures = ["PH", "DOMAX"];

const featureConfig = {
  editable_features: ["PH", "DOMAX"],
  features: {
    PH: { label: "pH", unit: "" },
    DOMAX: { label: "Dissolved Oxygen Max", unit: "ppm" },
  },
};

const legacySnapshot = {
  id: "legacy-1",
  lakeId: "C3420",
  lakeName: "Test Lake",
  predictionMeters: 4.2,
  timestamp: "2024-01-01T12:00:00.000Z",
  features: { PH: 7.1, DOMAX: 8.0 },
};

test("sanitizeCompareId clears orphan compare IDs", () => {
  const scenarios = [{ id: "a" }, { id: "b" }];
  assert.equal(sanitizeCompareId(scenarios, "a"), "a");
  assert.equal(sanitizeCompareId(scenarios, "missing"), "");
  assert.equal(sanitizeCompareId(scenarios, ""), "");
});

test("prependSavedScenario caps saved list at 12", () => {
  const existing = Array.from({ length: 12 }, (_, index) => ({
    id: `existing-${index}`,
    lakeId: "C3420",
  }));
  const next = prependSavedScenario(existing, { id: "new", lakeId: "C3420" });
  assert.equal(next.length, SAVED_SCENARIO_MAX);
  assert.equal(next[0].id, "new");
  assert.equal(next[11].id, "existing-10");
  assert.ok(!next.some((item) => item.id === "existing-11"));
});

test("scenariosForLake excludes other lakes", () => {
  const scenarios = [
    { id: "1", lakeId: "C3420" },
    { id: "2", lakeId: "C9999" },
    { id: "3", lakeId: "C3420" },
  ];
  assert.deepEqual(scenariosForLake(scenarios, "C3420").map((item) => item.id), ["1", "3"]);
  assert.equal(countOtherLakeScenarios(scenarios, "C3420"), 1);
});

test("compareIdForLake only returns IDs for the current lake", () => {
  const scenarios = [
    { id: "lake-a", lakeId: "C3420" },
    { id: "lake-b", lakeId: "C9999" },
  ];
  assert.equal(compareIdForLake(scenarios, "lake-a", "C3420"), "lake-a");
  assert.equal(compareIdForLake(scenarios, "lake-b", "C3420"), "");
});

test("migrateSavedScenario adds includedFeatures for legacy snapshots", () => {
  const migrated = migrateSavedScenario(legacySnapshot, editableFeatures);
  assert.equal(migrated.schemaVersion, 1);
  assert.deepEqual(migrated.includedFeatures, ["PH", "DOMAX"]);
  assert.deepEqual(migrated.features, legacySnapshot.features);
  assert.equal(migrated.label, "");
});

test("migrateSavedScenarios preserves includedFeatures when present", () => {
  const migrated = migrateSavedScenarios(
    [{ ...legacySnapshot, includedFeatures: ["PH"] }],
    editableFeatures
  );
  assert.deepEqual(migrated[0].includedFeatures, ["PH"]);
});

test("buildSavedScenario stores complete snapshot shape", () => {
  const scenario = buildSavedScenario({
    lakeId: "C3420",
    lakeName: "Test Lake",
    forecast: { predictionMeters: 5.1 },
    features: { PH: 7.2 },
    includedFeatures: ["PH"],
    label: "  High phosphorus trial  ",
  });
  assert.equal(scenario.schemaVersion, 1);
  assert.equal(scenario.predictionMeters, 5.1);
  assert.deepEqual(scenario.includedFeatures, ["PH"]);
  assert.equal(scenario.label, "High phosphorus trial");
  assert.equal(buildSavedScenario({ lakeId: "C3420", forecast: null, features: {} }), null);
});

test("inferIncludedFeatures uses finite feature values", () => {
  assert.deepEqual(
    inferIncludedFeatures({ PH: 7.0, DOMAX: null }, editableFeatures),
    ["PH"]
  );
});

test("normalizeScenarioLabel trims and caps length", () => {
  assert.equal(normalizeScenarioLabel("  High   phosphorus  "), "High phosphorus");
  assert.equal(normalizeScenarioLabel(""), "");
  assert.equal(normalizeScenarioLabel(null), "");
  assert.equal(normalizeScenarioLabel("x".repeat(80)).length, 60);
});

test("formatSavedScenarioOption prefers label in display", () => {
  const labeled = formatSavedScenarioOption({
    label: "High phosphorus trial",
    timestamp: "2024-01-01T12:00:00.000Z",
    predictionMeters: 4.2,
  });
  assert.match(labeled, /^High phosphorus trial \(/);

  const unlabeled = formatSavedScenarioOption({
    label: "",
    timestamp: "2024-01-01T12:00:00.000Z",
    predictionMeters: 4.2,
  });
  assert.match(unlabeled, /4\.2 m$/);
});

test("hasChangesFromSnapshot detects slider differences", () => {
  const snapshot = {
    features: { PH: 7.0, DOMAX: 8 },
    includedFeatures: ["PH", "DOMAX"],
  };
  assert.equal(
    hasChangesFromSnapshot(
      { PH: 7.0, DOMAX: 8 },
      ["PH", "DOMAX"],
      snapshot,
      featureConfig
    ),
    false
  );
  assert.equal(
    hasChangesFromSnapshot(
      { PH: 7.5, DOMAX: 8 },
      ["PH", "DOMAX"],
      snapshot,
      featureConfig
    ),
    true
  );
});

test("buildFeaturesFromSnapshot preserves baseline locked keys", () => {
  const snapshot = {
    features: { PH: 7.5, DOMAX: 9.0 },
    includedFeatures: ["PH", "DOMAX"],
  };
  const baseline = { PH: 7.0, DOMAX: 8.0, LAT: 44.5, LON: -69.8 };
  const merged = buildFeaturesFromSnapshot(snapshot, baseline, featureConfig);
  assert.equal(merged.PH, 7.5);
  assert.equal(merged.DOMAX, 9.0);
  assert.equal(merged.LAT, 44.5);
  assert.equal(merged.LON, -69.8);
});
