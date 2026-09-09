import { displayUnitFor } from "./units.js";

/** User-facing labels for model features (playground sliders, explainability, tooltips). */
export const FRIENDLY_FEATURE_LABELS = {
  LATITUDE: "Latitude",
  LONGITUDE: "Longitude",
  AREA_ACRES: "Lake area (acres)",
  DEPTH_MAX_FEET: "Maximum depth (ft)",
  DOMAX: "Highest dissolved oxygen",
  DOMIN: "Lowest dissolved oxygen",
  TMAX: "Warmest water temperature",
  TMIN: "Coldest water temperature",
  TPEC: "Total phosphorus in surface water",
  TPBG: "Total phosphorus at lake bottom",
  PH: "pH",
  COLOR: "Water color",
  CONDUCT: "Conductivity",
  ALK: "Alkalinity",
};

export const FEATURE_HELP_CONTENT = {
  DOMAX: {
    title: FRIENDLY_FEATURE_LABELS.DOMAX,
    body: "The highest dissolved oxygen measured in the water. Oxygen supports aquatic life and can reflect mixing, temperature, and biological activity.",
  },
  DOMIN: {
    title: FRIENDLY_FEATURE_LABELS.DOMIN,
    body: "The lowest dissolved oxygen measured in the water. Low oxygen can occur near the bottom or during warm, stagnant periods and can signal stress for aquatic life.",
  },
  TMAX: {
    title: FRIENDLY_FEATURE_LABELS.TMAX,
    body: "The warmest water temperature measured in the profile on the sampling day, usually near the surface. Warm surface water can favor algae growth and stronger layering.",
  },
  TMIN: {
    title: FRIENDLY_FEATURE_LABELS.TMIN,
    body: "The coldest water temperature measured in the profile on the sampling day, usually near the bottom. A large gap from the warmest reading points to a strongly layered lake.",
  },
  TPEC: {
    title: FRIENDLY_FEATURE_LABELS.TPEC,
    body: "Total phosphorus from an epicore sample of the upper water column. Phosphorus is a key nutrient for algae; higher values often indicate greater risk of murkier water.",
  },
  TPBG: {
    title: FRIENDLY_FEATURE_LABELS.TPBG,
    body: "Total phosphorus from a bottom grab sample near the lake bed. It can reflect nutrients released from sediments, especially when deep water loses oxygen.",
  },
  PH: {
    title: FRIENDLY_FEATURE_LABELS.PH,
    body: "A measure of how acidic or basic the water is. Most Maine lake organisms do best in a moderate pH range. Shown as this lake’s long-term average.",
  },
  COLOR: {
    title: FRIENDLY_FEATURE_LABELS.COLOR,
    body: "Water color, often influenced by dissolved organic matter from wetlands, soils, and shoreline runoff. Darker water can reduce how deep light travels. Shown as this lake’s long-term average.",
  },
  CONDUCT: {
    title: FRIENDLY_FEATURE_LABELS.CONDUCT,
    body: "Specific conductivity measures dissolved ions in the water. It can reflect geology, road salt, runoff, or other dissolved materials. Shown as this lake’s long-term average.",
  },
  ALK: {
    title: FRIENDLY_FEATURE_LABELS.ALK,
    body: "Alkalinity is the water’s buffering capacity, or how well it resists changes in acidity. It is often related to local geology. Shown as this lake’s long-term average.",
  },
};

/** Fixed lake chemistry descriptors (lake-level averages) shown read-only in the lake profile. */
export const LAKE_CHEMISTRY_FEATURES = ["PH", "COLOR", "CONDUCT", "ALK"];

/** Locked lake traits shown in explainability (excludes year/month; median date is a stand-in). */
export const EXPLAINABILITY_LAKE_CONTEXT_FEATURES = [
  "LATITUDE",
  "LONGITUDE",
  "AREA_ACRES",
  "DEPTH_MAX_FEET",
  ...LAKE_CHEMISTRY_FEATURES,
];

// Convertible lake-trait features: base label + canonical unit for the
// unit-aware label path. Their FRIENDLY_FEATURE_LABELS entries bake the
// canonical (imperial) unit and remain the fallback when no system is passed.
const CONVERTIBLE_FEATURE_UNITS = {
  AREA_ACRES: { base: "Lake area", canonicalUnit: "acres" },
  DEPTH_MAX_FEET: { base: "Maximum depth", canonicalUnit: "ft" },
};

export function getFriendlyFeatureLabel(featureKey, fallbackLabel, system) {
  if (system && CONVERTIBLE_FEATURE_UNITS[featureKey]) {
    const { base, canonicalUnit } = CONVERTIBLE_FEATURE_UNITS[featureKey];
    return `${base} (${displayUnitFor(canonicalUnit, system)})`;
  }
  return FRIENDLY_FEATURE_LABELS[featureKey] || fallbackLabel || featureKey;
}
