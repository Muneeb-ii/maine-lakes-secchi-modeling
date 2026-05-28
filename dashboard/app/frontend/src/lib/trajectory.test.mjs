import assert from "node:assert/strict";
import { test } from "node:test";
import {
  buildTrajectoryPoint,
  capTrajectoryHistory,
  computeTrajectorySummary,
  detectChangedFeatures,
  formatLatestChange,
  needsResetConfirmation,
  shouldAppendPoint,
} from "./trajectory.js";

const featureConfig = {
  editable_features: ["PH", "DOMAX"],
  features: {
    PH: { label: "pH Level", unit: "pH" },
    DOMAX: { label: "Dissolved Oxygen Max", unit: "mg/L" },
  },
};

test("detectChangedFeatures finds edited sliders", () => {
  const prev = { PH: 7.0, DOMAX: 8 };
  const next = { PH: 7.4, DOMAX: 8 };
  const changed = detectChangedFeatures(prev, next, featureConfig);
  assert.equal(changed.length, 1);
  assert.equal(changed[0].label, "pH Level");
  assert.equal(changed[0].value, 7.4);
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
    changedFeatures: [{ key: "PH", label: "pH Level", value: 7.4, unit: "pH" }],
    previousPrediction: 3.02,
  });
  assert.equal(formatLatestChange(point), "pH Level changed to 7.4 pH → Secchi +0.18 m");
});

test("computeTrajectorySummary aggregates session", () => {
  const points = [
    { prediction: 2.5, deltaFromBaseline: 0 },
    { prediction: 3.1, deltaFromBaseline: 0.6 },
  ];
  const summary = computeTrajectorySummary(points);
  assert.equal(summary.stepCount, 2);
  assert.equal(summary.min, 2.5);
  assert.equal(summary.max, 3.1);
  assert.equal(summary.latestDeltaFromBaseline, 0.6);
});

test("needsResetConfirmation only above threshold", () => {
  assert.equal(needsResetConfirmation(5), false);
  assert.equal(needsResetConfirmation(6), true);
});
