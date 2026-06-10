import {
  buildComparableFeatureState,
  detectChangedFeatures,
} from "./trajectory.js";

export const SAVED_SCENARIO_SCHEMA_VERSION = 1;
export const SAVED_SCENARIO_MAX = 12;
export const SAVED_SCENARIO_LABEL_MAX = 60;

export function sanitizeCompareId(savedScenarios, compareScenarioId) {
  if (!compareScenarioId) return "";
  const exists = savedScenarios.some((scenario) => scenario.id === compareScenarioId);
  return exists ? compareScenarioId : "";
}

export function scenariosForLake(savedScenarios, lakeId) {
  if (!lakeId) return [];
  return savedScenarios.filter((scenario) => scenario.lakeId === lakeId);
}

export function countOtherLakeScenarios(savedScenarios, lakeId) {
  if (!lakeId) return savedScenarios.length;
  return savedScenarios.filter((scenario) => scenario.lakeId !== lakeId).length;
}

export function normalizeScenarioLabel(raw) {
  if (raw === null || raw === undefined) return "";
  const collapsed = String(raw).trim().replace(/\s+/g, " ");
  if (!collapsed) return "";
  return collapsed.slice(0, SAVED_SCENARIO_LABEL_MAX);
}

export function inferIncludedFeatures(features, editableFeatures = []) {
  return editableFeatures.filter((key) => {
    const value = features?.[key];
    if (value === null || value === undefined) return false;
    return Number.isFinite(Number(value));
  });
}

export function migrateSavedScenario(raw, editableFeatures = []) {
  if (!raw || typeof raw !== "object" || !raw.id) return null;

  const features = raw.features && typeof raw.features === "object" ? raw.features : {};
  const includedFeatures = Array.isArray(raw.includedFeatures)
    ? raw.includedFeatures
    : inferIncludedFeatures(features, editableFeatures);

  return {
    schemaVersion: raw.schemaVersion ?? SAVED_SCENARIO_SCHEMA_VERSION,
    id: String(raw.id),
    lakeId: raw.lakeId ?? "",
    lakeName: raw.lakeName ?? "",
    label: normalizeScenarioLabel(raw.label),
    predictionMeters: raw.predictionMeters,
    timestamp: raw.timestamp ?? new Date().toISOString(),
    features,
    includedFeatures,
  };
}

export function migrateSavedScenarios(rawList, editableFeatures = []) {
  if (!Array.isArray(rawList)) return [];
  return rawList
    .map((item) => migrateSavedScenario(item, editableFeatures))
    .filter(Boolean)
    .slice(0, SAVED_SCENARIO_MAX);
}

export function buildSavedScenario({
  lakeId,
  lakeName,
  forecast,
  features,
  includedFeatures,
  label,
}) {
  if (!forecast || typeof forecast.predictionMeters !== "number") return null;

  return {
    schemaVersion: SAVED_SCENARIO_SCHEMA_VERSION,
    id: `${Date.now()}`,
    lakeId,
    lakeName,
    label: normalizeScenarioLabel(label),
    predictionMeters: forecast.predictionMeters,
    timestamp: new Date().toISOString(),
    features: { ...features },
    includedFeatures: [...(includedFeatures || [])],
  };
}

export function prependSavedScenario(savedScenarios, scenario) {
  if (!scenario) return savedScenarios;
  return [scenario, ...savedScenarios.filter((item) => item.id !== scenario.id)].slice(
    0,
    SAVED_SCENARIO_MAX
  );
}

export function hasScenarioChangesFromBaseline(
  baseline,
  features,
  featureConfig,
  includedFeatures
) {
  if (!baseline || !featureConfig || !features) return false;

  const baselineIncluded = featureConfig.editable_features?.filter((key) =>
    Number.isFinite(Number(baseline?.[key]))
  );
  const baselineState = buildComparableFeatureState(
    baseline,
    featureConfig,
    baselineIncluded
  );
  const currentState = buildComparableFeatureState(features, featureConfig, includedFeatures);
  return detectChangedFeatures(baselineState, currentState, featureConfig).length > 0;
}

export function hasChangesFromSnapshot(features, includedFeatures, snapshot, featureConfig) {
  if (!snapshot || !featureConfig || !features) return false;

  const snapshotState = buildComparableFeatureState(
    snapshot.features,
    featureConfig,
    snapshot.includedFeatures
  );
  const currentState = buildComparableFeatureState(features, featureConfig, includedFeatures);
  return detectChangedFeatures(snapshotState, currentState, featureConfig).length > 0;
}

export function buildFeaturesFromSnapshot(snapshot, baseline, featureConfig) {
  if (!snapshot || !baseline || !featureConfig) return { ...baseline };

  const editable = new Set(featureConfig.editable_features || []);
  const merged = { ...baseline };

  for (const [key, value] of Object.entries(snapshot.features || {})) {
    if (editable.has(key)) {
      merged[key] = value;
    }
  }

  return merged;
}

export function filterIncludedFeaturesForConfig(includedFeatures, featureConfig) {
  const editable = new Set(featureConfig?.editable_features || []);
  return (includedFeatures || []).filter((key) => editable.has(key));
}

export function compareIdForLake(savedScenarios, compareScenarioId, lakeId) {
  if (!compareScenarioId || !lakeId) return "";
  const scenario = savedScenarios.find((item) => item.id === compareScenarioId);
  if (!scenario || scenario.lakeId !== lakeId) return "";
  return compareScenarioId;
}

export function isCompareScenarioActive(selectedScenario, lakeId, forecast) {
  if (!selectedScenario || !forecast || !lakeId) return false;
  return selectedScenario.lakeId === lakeId;
}
