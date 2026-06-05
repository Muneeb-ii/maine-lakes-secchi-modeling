const FRIENDLY_FEATURE_LABELS = {
  DOMAX: "Highest dissolved oxygen",
  DOMIN: "Lowest dissolved oxygen",
  TPEC: "Total phosphorus near bottom",
  TPBG: "Total phosphorus near surface",
  CONDUCT: "Conductivity",
  AREA_ACRES: "Area (acres)",
  DEPTH_MAX_FEET: "Max depth (ft)",
};

export function getFriendlyFeatureLabel(featureKey, fallbackLabel) {
  return FRIENDLY_FEATURE_LABELS[featureKey] || fallbackLabel || featureKey;
}
