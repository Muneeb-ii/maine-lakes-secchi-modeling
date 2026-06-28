import {
  TRAJECTORY_STEP_LABEL_ADJUSTMENT,
  TRAJECTORY_STEP_LABEL_MULTI,
  TRAJECTORY_STEP_LABEL_START,
} from "./copy.js";
import { getFriendlyFeatureLabel } from "./featureLabels.js";
import { DEFAULT_UNIT_SYSTEM } from "./units.js";
import { formatSignedMeters } from "./formattersCore.js";

const TRAJECTORY_MAX_STEPS = 30;
const TRAJECTORY_DEDUPE_METERS = 0.02;
const TRAJECTORY_RESET_CONFIRM_THRESHOLD = 5;
const SECCHI_CHART_MAX_METERS = 12;
const DETAIL_MIN_SPAN_METERS = 0.6;
const FULL_CONTEXT_MIN_SPAN_METERS = 6;

export {
  TRAJECTORY_MAX_STEPS,
  TRAJECTORY_DEDUPE_METERS,
  TRAJECTORY_RESET_CONFIRM_THRESHOLD,
  SECCHI_CHART_MAX_METERS,
};

export function featuresMatchForPrediction(previous, next, editableKeys) {
  if (!previous || !next) return false;
  for (const key of editableKeys) {
    const previousValue = previous[key];
    const nextRawValue = next[key];
    if (previousValue === null || nextRawValue === null) {
      if (previousValue !== nextRawValue) return false;
      continue;
    }
    const prev = Number(previousValue);
    const nextValue = Number(nextRawValue);
    if (!Number.isFinite(prev) || !Number.isFinite(nextValue)) return false;
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

export function buildComparableFeatureState(features, featureConfig, includedFeatures = []) {
  const editable = featureConfig?.editable_features || [];
  const included = new Set(includedFeatures || []);
  const comparable = {};

  for (const key of editable) {
    if (!included.has(key)) {
      comparable[key] = null;
      continue;
    }
    const value = Number(features?.[key]);
    comparable[key] = Number.isFinite(value) ? value : null;
  }

  return comparable;
}

export function detectChangedFeatures(previousFeatures, nextFeatures, featureConfig) {
  if (!previousFeatures || !nextFeatures || !featureConfig) return [];
  const editable = featureConfig.editable_features || [];
  const changed = [];

  for (const key of editable) {
    const config = featureConfig.features?.[key] || {};
    const previousValue = previousFeatures[key];
    const nextValue = nextFeatures[key];
    if (previousValue === null || nextValue === null) {
      if (previousValue !== nextValue) {
        changed.push({
          key,
          label: getFriendlyFeatureLabel(key, config.label),
          value: nextValue,
          unit: config.unit || "",
          included: nextValue !== null,
        });
      }
      continue;
    }

    const prev = Number(previousValue);
    const next = Number(nextValue);
    if (!Number.isFinite(prev) || !Number.isFinite(next)) continue;
    if (Math.abs(prev - next) > 0.0001) {
      changed.push({
        key,
        label: getFriendlyFeatureLabel(key, config.label),
        value: next,
        unit: config.unit || "",
        included: true,
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
    return {
      stepCount: 0,
      min: null,
      max: null,
      latest: null,
      latestDeltaFromBaseline: null,
      latestDeltaFromPrevious: null,
      largestMove: null,
    };
  }
  const predictions = points.map((p) => p.prediction);
  const latest = points[points.length - 1];
  const moves = points
    .map((p) => p.deltaFromPrevious)
    .filter((value) => typeof value === "number" && Number.isFinite(value));
  return {
    stepCount: points.length,
    min: Math.min(...predictions),
    max: Math.max(...predictions),
    latest: latest.prediction,
    latestDeltaFromBaseline: latest.deltaFromBaseline,
    latestDeltaFromPrevious: latest.deltaFromPrevious,
    largestMove: moves.length
      ? moves.reduce((largest, value) =>
          Math.abs(value) > Math.abs(largest) ? value : largest
        )
      : null,
  };
}

export function formatLatestChange(point, system = DEFAULT_UNIT_SYSTEM) {
  if (!point || point.step <= 1) return null;
  const change = point.changedFeatures?.[0];
  if (!change || point.deltaFromPrevious === null) return null;

  const deltaText = formatSignedMeters(point.deltaFromPrevious, { system });
  const valueText =
    change.value === null
      ? "not included"
      : change.unit && change.unit.length > 0
        ? `${change.value} ${change.unit}`
        : String(change.value);

  return `${change.label} changed to ${valueText} → Secchi ${deltaText}`;
}

export function formatTrajectoryChangeValue(change) {
  if (!change) return "Typical";
  if (change.value === null) return "Not included";
  if (change.unit && change.unit.length > 0) return `${change.value} ${change.unit}`;
  return String(change.value);
}

export function buildTrajectoryChangeRows(points, maxRows = TRAJECTORY_MAX_STEPS) {
  return points.slice(-maxRows).map((point) => {
    const primaryChange = point.changedFeatures?.[0] || null;
    const extraChangeCount = Math.max(0, (point.changedFeatures?.length || 0) - 1);
    return {
      step: point.step,
      label: primaryChange?.label || point.label || TRAJECTORY_STEP_LABEL_START,
      value: formatTrajectoryChangeValue(primaryChange),
      prediction: point.prediction,
      deltaFromPrevious: point.deltaFromPrevious,
      extraChangeCount,
      isStarting: point.step === 1 || !primaryChange,
    };
  });
}

export function isPlausibleSecchiMeters(value) {
  return typeof value === "number" && Number.isFinite(value) && value >= 0 && value <= SECCHI_CHART_MAX_METERS;
}

export function clampSecchiForChart(value) {
  if (!isPlausibleSecchiMeters(value)) return null;
  return value;
}

function roundDomainBound(value) {
  return Math.round(value * 100) / 100;
}

export function buildYAxisTicks(min, max, mode = "detail") {
  const span = max - min;
  if (!Number.isFinite(min) || !Number.isFinite(max) || span <= 0) {
    return [min, max].filter((value) => Number.isFinite(value));
  }

  let step;
  if (mode === "detail") {
    if (span <= 0.5) step = 0.1;
    else if (span <= 1.2) step = 0.2;
    else if (span <= 2.5) step = 0.5;
    else step = 1;
  } else if (span <= 6) {
    step = 1;
  } else {
    step = 2;
  }

  const ticks = [];
  const start = Math.ceil(min / step) * step;
  for (let value = start; value <= max + step * 0.001; value += step) {
    ticks.push(roundDomainBound(value));
  }

  if (!ticks.length) {
    return [roundDomainBound(min), roundDomainBound(max)];
  }

  if (ticks[0] > min + step * 0.2) {
    ticks.unshift(roundDomainBound(min));
  }
  const lastTick = ticks[ticks.length - 1];
  if (lastTick < max - step * 0.2) {
    ticks.push(roundDomainBound(max));
  }

  return ticks;
}

export function formatYAxisTick(value, mode = "detail") {
  if (typeof value !== "number" || !Number.isFinite(value)) return "";
  const decimals = mode === "detail" && Math.abs(value) < 10 ? 1 : 0;
  return value.toFixed(decimals).replace(/\.0$/, "");
}

export function computeYDomain(points, baseline, compareValue, options = {}) {
  const mode = options.mode || "detail";
  const validValues = points
    .map((p) => p.prediction)
    .filter((value) => isPlausibleSecchiMeters(value));
  if (isPlausibleSecchiMeters(baseline)) validValues.push(baseline);
  if (isPlausibleSecchiMeters(compareValue)) validValues.push(compareValue);
  if (mode === "full") validValues.push(2, 4);
  if (!validValues.length) return [0, 6];
  const rawMin = Math.min(...validValues);
  const rawMax = Math.max(...validValues);
  const minSpan = mode === "full" ? FULL_CONTEXT_MIN_SPAN_METERS : DETAIL_MIN_SPAN_METERS;
  const rawSpan = rawMax - rawMin;
  const paddedSpan = Math.max(rawSpan, minSpan);
  const center = (rawMin + rawMax) / 2;
  const padding = Math.max(mode === "full" ? 0.3 : 0.08, rawSpan * 0.25);
  let min = center - paddedSpan / 2 - padding;
  let max = center + paddedSpan / 2 + padding;

  if (min < 0) {
    max += Math.abs(min);
    min = 0;
  }
  max = Math.min(SECCHI_CHART_MAX_METERS, max);
  if (max - min < minSpan) {
    min = Math.max(0, max - minSpan);
  }
  return [roundDomainBound(min), roundDomainBound(max)];
}

export function needsResetConfirmation(stepCount) {
  return stepCount > TRAJECTORY_RESET_CONFIRM_THRESHOLD;
}
