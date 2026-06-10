import assert from "node:assert/strict";
import { test } from "node:test";
import {
  buildTrajectoryPoint,
  buildComparableFeatureState,
  buildYAxisTicks,
  canRecordTrajectory,
  capTrajectoryHistory,
  clampSecchiForChart,
  computeYDomain,
  computeTrajectorySummary,
  detectChangedFeatures,
  featuresMatchForPrediction,
  formatLatestChange,
  formatYAxisTick,
  isPlausibleSecchiMeters,
  needsResetConfirmation,
  shouldAppendPoint,
} from "./trajectory.js";

const featureConfig = {
  editable_features: ["PH", "DOMAX"],
  features: {
    PH: { label: "pH", unit: "" },
    DOMAX: { label: "Dissolved Oxygen Max", unit: "ppm" },
  },
};

test("detectChangedFeatures finds edited sliders", () => {
  const prev = { PH: 7.0, DOMAX: 8 };
  const next = { PH: 7.4, DOMAX: 8 };
  const changed = detectChangedFeatures(prev, next, featureConfig);
  assert.equal(changed.length, 1);
  assert.equal(changed[0].label, "pH");
  assert.equal(changed[0].value, 7.4);
});

test("buildComparableFeatureState represents excluded features as missing", () => {
  const comparable = buildComparableFeatureState(
    { PH: 7.1, DOMAX: 8.2 },
    featureConfig,
    ["PH"]
  );
  assert.deepEqual(comparable, { PH: 7.1, DOMAX: null });
});

test("detectChangedFeatures tracks included-to-missing changes", () => {
  const prev = { PH: 7.0, DOMAX: 8 };
  const next = { PH: 7.0, DOMAX: null };
  const changed = detectChangedFeatures(prev, next, featureConfig);
  assert.equal(changed.length, 1);
  assert.equal(changed[0].label, "Highest dissolved oxygen");
  assert.equal(changed[0].value, null);
  assert.equal(changed[0].included, false);
});

test("shouldAppendPoint dedupes small prediction jitter", () => {
  assert.equal(shouldAppendPoint(3.0, 3.01, false), false);
  assert.equal(shouldAppendPoint(3.0, 3.03, false), true);
  assert.equal(shouldAppendPoint(null, 3.0, true), true);
});

test("capTrajectoryHistory keeps newest steps", () => {
  const points = Array.from({ length: 35 }, (_, i) => ({ step: i + 1 }));
  const capped = capTrajectoryHistory(points, 30);
  assert.equal(capped.length, 30);
  assert.equal(capped[0].step, 6);
  assert.equal(capped[29].step, 35);
});

test("formatLatestChange renders readable line", () => {
  const point = buildTrajectoryPoint({
    step: 2,
    prediction: 3.2,
    baseline: 3.0,
    changedFeatures: [{ key: "PH", label: "pH", value: 7.4, unit: "" }],
    previousPrediction: 3.02,
  });
  assert.equal(formatLatestChange(point), "pH changed to 7.4 → Secchi +0.18 m");
});

test("computeTrajectorySummary aggregates session", () => {
  const points = [
    { prediction: 2.5, deltaFromBaseline: 0, deltaFromPrevious: null },
    { prediction: 3.1, deltaFromBaseline: 0.6, deltaFromPrevious: 0.6 },
    { prediction: 2.9, deltaFromBaseline: 0.4, deltaFromPrevious: -0.2 },
  ];
  const summary = computeTrajectorySummary(points);
  assert.equal(summary.stepCount, 3);
  assert.equal(summary.min, 2.5);
  assert.equal(summary.max, 3.1);
  assert.equal(summary.latest, 2.9);
  assert.equal(summary.latestDeltaFromBaseline, 0.4);
  assert.equal(summary.latestDeltaFromPrevious, -0.2);
  assert.equal(summary.largestMove, 0.6);
});

test("computeYDomain caps extreme upper bounds", () => {
  const domain = computeYDomain([{ prediction: 3.2 }, { prediction: 250 }], 3.1, null);
  assert.ok(domain[1] < 4);
});

test("computeYDomain ignores extreme compare outliers before scaling", () => {
  const domain = computeYDomain([{ prediction: 5.01 }, { prediction: 5.04 }], 5.02, 250);
  assert.ok(domain[1] - domain[0] < 1);
  assert.ok(domain[0] < 5.01);
  assert.ok(domain[1] > 5.04);
});

test("computeYDomain detail mode zooms into small scenario changes", () => {
  const domain = computeYDomain([{ prediction: 5.01 }, { prediction: 5.04 }], 5.02, null);
  assert.ok(domain[1] - domain[0] < 1);
  assert.ok(domain[0] < 5.01);
  assert.ok(domain[1] > 5.04);
});

test("computeYDomain full mode keeps clarity references in view", () => {
  const domain = computeYDomain([{ prediction: 5.01 }, { prediction: 5.04 }], 5.02, null, {
    mode: "full",
  });
  assert.ok(domain[0] <= 2);
  assert.ok(domain[1] >= 4);
});

test("isPlausibleSecchiMeters rejects model outliers", () => {
  assert.equal(isPlausibleSecchiMeters(5.1), true);
  assert.equal(isPlausibleSecchiMeters(12), true);
  assert.equal(isPlausibleSecchiMeters(250), false);
  assert.equal(isPlausibleSecchiMeters(-1), false);
});

test("clampSecchiForChart drops implausible predictions", () => {
  assert.equal(clampSecchiForChart(5.1), 5.1);
  assert.equal(clampSecchiForChart(250), null);
});

test("buildYAxisTicks stays inside computed domain", () => {
  const ticks = buildYAxisTicks(4.8, 5.4, "detail");
  assert.ok(ticks.length >= 2);
  assert.ok(ticks.every((tick) => tick >= 4.8 && tick <= 5.4));
  assert.ok(ticks.every((tick) => tick <= 12));
});

test("formatYAxisTick renders compact labels", () => {
  assert.equal(formatYAxisTick(5, "detail"), "5");
  assert.equal(formatYAxisTick(5.25, "detail"), "5.3");
});

test("needsResetConfirmation only above threshold", () => {
  assert.equal(needsResetConfirmation(5), false);
  assert.equal(needsResetConfirmation(6), true);
});

test("featuresMatchForPrediction requires matching editable values", () => {
  const editable = ["PH", "DOMAX"];
  const baseline = { PH: 7, DOMAX: 8 };
  const changed = { PH: 7.5, DOMAX: 8 };
  assert.equal(featuresMatchForPrediction(baseline, baseline, editable), true);
  assert.equal(featuresMatchForPrediction(baseline, changed, editable), false);
  assert.equal(featuresMatchForPrediction({ PH: null, DOMAX: 8 }, { PH: null, DOMAX: 8 }, editable), true);
  assert.equal(featuresMatchForPrediction({ PH: null, DOMAX: 8 }, { PH: 7, DOMAX: 8 }, editable), false);
  assert.equal(featuresMatchForPrediction(null, changed, editable), false);
});

test("canRecordTrajectory waits for committed prediction and fresh forecast", () => {
  const editable = ["PH"];
  const baseline = { PH: 7 };
  const changed = { PH: 7.5 };

  assert.equal(
    canRecordTrajectory({
      lastRecordedCommit: 0,
      featureCommitVersion: 1,
      lastPredictedFeatures: baseline,
      currentFeatures: changed,
      editableKeys: editable,
      isPredicting: false,
      predictionError: "",
    }),
    false
  );

  assert.equal(
    canRecordTrajectory({
      lastRecordedCommit: 0,
      featureCommitVersion: 1,
      lastPredictedFeatures: changed,
      currentFeatures: changed,
      editableKeys: editable,
      isPredicting: false,
      predictionError: "",
    }),
    true
  );

  assert.equal(
    canRecordTrajectory({
      lastRecordedCommit: 1,
      featureCommitVersion: 1,
      lastPredictedFeatures: changed,
      currentFeatures: changed,
      editableKeys: editable,
      isPredicting: false,
      predictionError: "",
    }),
    false
  );

  assert.equal(
    canRecordTrajectory({
      lastRecordedCommit: 0,
      featureCommitVersion: 1,
      lastPredictedFeatures: changed,
      currentFeatures: changed,
      editableKeys: editable,
      isPredicting: true,
      predictionError: "",
    }),
    false
  );
});
