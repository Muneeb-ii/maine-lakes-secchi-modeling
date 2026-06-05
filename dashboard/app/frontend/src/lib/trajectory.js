import {
  TRAJECTORY_STEP_LABEL_ADJUSTMENT,
  TRAJECTORY_STEP_LABEL_MULTI,
  TRAJECTORY_STEP_LABEL_START,
} from "./copy.js";
import { getFriendlyFeatureLabel } from "./featureLabels.js";

const TRAJECTORY_MAX_STEPS = 30;
const TRAJECTORY_DEDUPE_METERS = 0.02;
const TRAJECTORY_RESET_CONFIRM_THRESHOLD = 5;
const SECCHI_CHART_MAX_METERS = 22;

export {
  TRAJECTORY_MAX_STEPS,
  TRAJECTORY_DEDUPE_METERS,
  TRAJECTORY_RESET_CONFIRM_THRESHOLD,
  SECCHI_CHART_MAX_METERS,
};

export function featuresMatchForPrediction(previous, next, editableKeys) {
  if (!previous || !next) return false;
  for (const key of editableKeys) {
    const prev = Number(previous[key]);
    const nextValue = Number(next[key]);
    if (Number.isNaN(prev) || Number.isNaN(nextValue)) return false;
    if (Math.abs(prev - nextValue) > 0.0001) return false;
  }
  return true;
}

export function canRecordTrajectory({
  lastRecordedCommit,
  featureCommitVersion,
  lastPredictedFeatures,
  currentFeatures,
  editableKeys,
  isPredicting,
  predictionError,
}) {
  if (!currentFeatures || isPredicting || predictionError) return false;
  if (lastRecordedCommit === featureCommitVersion) return false;
  return featuresMatchForPrediction(lastPredictedFeatures, currentFeatures, editableKeys);
}

export function detectChangedFeatures(previousFeatures, nextFeatures, featureConfig) {
  if (!previousFeatures || !nextFeatures || !featureConfig) return [];
  const editable = featureConfig.editable_features || [];
  const changed = [];

  for (const key of editable) {
    const prev = Number(previousFeatures[key]);
    const next = Number(nextFeatures[key]);
    if (Number.isNaN(prev) || Number.isNaN(next)) continue;
    if (Math.abs(prev - next) > 0.0001) {
      const config = featureConfig.features?.[key] || {};
      changed.push({
        key,
        label: getFriendlyFeatureLabel(key, config.label),
        value: next,
        unit: config.unit || "",
      });
    }
  }

  return changed;
}

export function shouldAppendPoint(previousPrediction, nextPrediction, isFirstPoint) {
  if (isFirstPoint) return true;
  if (typeof previousPrediction !== "number" || typeof nextPrediction !== "number") return true;
  return Math.abs(nextPrediction - previousPrediction) >= TRAJECTORY_DEDUPE_METERS;
}

export function buildTrajectoryPoint({
  step,
  prediction,
  baseline,
  changedFeatures,
  previousPrediction,
  isStarting = false,
}) {
  const deltaFromBaseline = prediction - baseline;
  const deltaFromPrevious =
    typeof previousPrediction === "number" ? prediction - previousPrediction : null;

  const primaryChange = changedFeatures[0];
  let label = TRAJECTORY_STEP_LABEL_ADJUSTMENT;
  if (isStarting) {
    label = TRAJECTORY_STEP_LABEL_START;
  } else if (primaryChange) {
    label = primaryChange.label;
  } else if (changedFeatures.length > 1) {
    label = TRAJECTORY_STEP_LABEL_MULTI(changedFeatures.length);
  }

  return {
    step,
    prediction,
    baseline,
    deltaFromBaseline,
    deltaFromPrevious,
    changedFeatures,
    label,
  };
}

export function capTrajectoryHistory(points, maxSteps = TRAJECTORY_MAX_STEPS) {
  if (points.length <= maxSteps) return points;
  return points.slice(points.length - maxSteps);
}

export function computeTrajectorySummary(points) {
  if (!points.length) {
    return { stepCount: 0, min: null, max: null, latestDeltaFromBaseline: null };
  }
  const predictions = points.map((p) => p.prediction);
  const latest = points[points.length - 1];
  return {
    stepCount: points.length,
    min: Math.min(...predictions),
    max: Math.max(...predictions),
    latestDeltaFromBaseline: latest.deltaFromBaseline,
  };
}

export function formatLatestChange(point) {
  if (!point || point.step <= 1) return null;
  const change = point.changedFeatures?.[0];
  if (!change || point.deltaFromPrevious === null) return null;

  const sign = point.deltaFromPrevious > 0 ? "+" : "";
  const deltaText = `${sign}${point.deltaFromPrevious.toFixed(2)} m`;
  const valueText =
    change.unit && change.unit.length > 0
      ? `${change.value} ${change.unit}`
      : String(change.value);

  return `${change.label} changed to ${valueText} → Secchi ${deltaText}`;
}

export function computeYDomain(points, baseline, compareValue, padding = 0.3) {
  const values = points
    .map((p) => p.prediction)
    .filter((value) => typeof value === "number" && Number.isFinite(value));
  if (typeof baseline === "number") values.push(baseline);
  if (typeof compareValue === "number") values.push(compareValue);
  values.push(2, 4);
  if (!values.length) return [0, 6];
  const min = Math.min(...values) - padding;
  const max = Math.min(SECCHI_CHART_MAX_METERS, Math.max(...values) + padding);
  return [Math.max(0, min), Math.max(max, 6)];
}

export function needsResetConfirmation(stepCount) {
  return stepCount > TRAJECTORY_RESET_CONFIRM_THRESHOLD;
}
