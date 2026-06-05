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

/** Locked lake traits shown in explainability (excludes year/month; median date is a stand-in). */
export const EXPLAINABILITY_LAKE_CONTEXT_FEATURES = [
  "LATITUDE",
  "LONGITUDE",
  "AREA_ACRES",
  "DEPTH_MAX_FEET",
];

export function getFriendlyFeatureLabel(featureKey, fallbackLabel) {
  return FRIENDLY_FEATURE_LABELS[featureKey] || fallbackLabel || featureKey;
}
