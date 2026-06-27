import { displayUnitFor } from "./units.js";

/** User-facing labels for model features (playground sliders, explainability, tooltips). */
export const FRIENDLY_FEATURE_LABELS = {
  LATITUDE: "Latitude",
  LONGITUDE: "Longitude",
  AREA_ACRES: "Lake area (acres)",
  DEPTH_MAX_FEET: "Maximum depth (ft)",
  DOMAX: "Highest dissolved oxygen",
  DOMIN: "Lowest dissolved oxygen",
  TPEC: "Total phosphorus at lake bottom",
  TPBG: "Total phosphorus in surface water",
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
  TPEC: {
    title: FRIENDLY_FEATURE_LABELS.TPEC,
    body: "Total phosphorus from a bottom-water sample. Phosphorus is a key nutrient for algae; higher values often indicate greater risk of murkier water.",
  },
  TPBG: {
    title: FRIENDLY_FEATURE_LABELS.TPBG,
    body: "Total phosphorus from the main water-column sample used for surface conditions. It represents nutrient availability that can support algae growth.",
  },
  PH: {
    title: FRIENDLY_FEATURE_LABELS.PH,
    body: "A measure of how acidic or basic the water is. Most Maine lake organisms do best in a moderate pH range.",
  },
  COLOR: {
    title: FRIENDLY_FEATURE_LABELS.COLOR,
    body: "Water color, often influenced by dissolved organic matter from wetlands, soils, and shoreline runoff. Darker water can reduce how deep light travels.",
  },
  CONDUCT: {
    title: FRIENDLY_FEATURE_LABELS.CONDUCT,
    body: "Specific conductivity measures dissolved ions in the water. It can reflect geology, road salt, runoff, or other dissolved materials.",
  },
  ALK: {
    title: FRIENDLY_FEATURE_LABELS.ALK,
    body: "Alkalinity is the water’s buffering capacity, or how well it resists changes in acidity. It is often related to local geology.",
  },
};

/** Locked lake traits shown in explainability (excludes year/month; median date is a stand-in). */
export const EXPLAINABILITY_LAKE_CONTEXT_FEATURES = [
  "LATITUDE",
  "LONGITUDE",
  "AREA_ACRES",
  "DEPTH_MAX_FEET",
];

// Convertible lake-trait features: base label + canonical unit for the
// unit-aware label path. Their FRIENDLY_FEATURE_LABELS entries bake the
// canonical (US) unit and remain the fallback when no system is passed.
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
