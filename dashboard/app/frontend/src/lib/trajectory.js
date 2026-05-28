const TRAJECTORY_MAX_STEPS = 30;
const TRAJECTORY_DEDUPE_METERS = 0.02;
const TRAJECTORY_RESET_CONFIRM_THRESHOLD = 5;

export { TRAJECTORY_MAX_STEPS, TRAJECTORY_DEDUPE_METERS, TRAJECTORY_RESET_CONFIRM_THRESHOLD };

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
        label: config.label || key,
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
  let label = "Adjustment";
  if (isStarting) {
    label = "Starting scenario";
  } else if (primaryChange) {
    label = primaryChange.label;
  } else if (changedFeatures.length > 1) {
    label = `${changedFeatures.length} parameters`;
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
  const values = points.map((p) => p.prediction);
  if (typeof baseline === "number") values.push(baseline);
  if (typeof compareValue === "number") values.push(compareValue);
  values.push(2, 4);
  if (!values.length) return [0, 6];
  const min = Math.min(...values) - padding;
  const max = Math.max(...values) + padding;
  return [Math.max(0, min), max];
}

export function needsResetConfirmation(stepCount) {
  return stepCount > TRAJECTORY_RESET_CONFIRM_THRESHOLD;
}
