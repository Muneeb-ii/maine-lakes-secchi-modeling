import { CLARITY_BANDS } from "./constants";

export const CLARITY_TONE_KEYS = ["turbid", "moderate", "clearer"];

const CLARITY_TONE_STYLES = {
  turbid: {
    panelClass: "info-card-turbid",
    pillClass: "clarity-band-pill clarity-band-pill-turbid",
    heroWashClass: "hero-wash-turbid",
    listItemClass: "clarity-list-item-turbid",
  },
  moderate: {
    panelClass: "info-card-moderate",
    pillClass: "clarity-band-pill clarity-band-pill-moderate",
    heroWashClass: "hero-wash-moderate",
    listItemClass: "clarity-list-item-moderate",
  },
  clearer: {
    panelClass: "info-card-clearer",
    pillClass: "clarity-band-pill clarity-band-pill-clearer",
    heroWashClass: "hero-wash-clearer",
    listItemClass: "clarity-list-item-clearer",
  },
};

export const SECTION_ACCENTS = {
  prediction: {
    iconClass: "text-lake-accent",
    badgeClass: "section-icon-badge section-icon-badge-prediction",
    panelAccentClass: "panel-accent-left panel-accent-prediction",
  },
  lake: {
    iconClass: "text-lake-sectionLake",
    badgeClass: "section-icon-badge section-icon-badge-lake",
    panelAccentClass: "panel-accent-left panel-accent-lake",
  },
  parameters: {
    iconClass: "text-lake-accent",
    badgeClass: "section-icon-badge section-icon-badge-parameters",
    panelAccentClass: "panel-accent-left panel-accent-parameters",
  },
  trajectory: {
    iconClass: "text-lake-accent",
    badgeClass: "section-icon-badge section-icon-badge-trajectory",
    panelAccentClass: "panel-accent-left panel-accent-trajectory",
  },
  drivers: {
    iconClass: "text-lake-sectionDrivers",
    badgeClass: "section-icon-badge section-icon-badge-drivers",
    panelAccentClass: "panel-accent-left panel-accent-drivers",
  },
  scenario: {
    iconClass: "text-lake-sectionCompare",
    badgeClass: "section-icon-badge section-icon-badge-scenario",
    panelAccentClass: "panel-accent-left panel-accent-scenario",
  },
  trends: {
    iconClass: "text-lake-amber",
    badgeClass: "section-icon-badge section-icon-badge-trends",
    panelAccentClass: "panel-accent-left panel-accent-trends",
  },
};

export const PARAMETER_ICON_COLORS = {
  Beaker: "text-lake-accent",
  Droplet: "text-lake-sectionLake",
  Activity: "text-lake-sectionDrivers",
  Gauge: "text-lake-amber",
  Thermometer: "text-delta-down",
};

export function getClarityToneStyles(toneKey) {
  return CLARITY_TONE_STYLES[toneKey] || CLARITY_TONE_STYLES.moderate;
}

export function getClarityTone(meters) {
  if (typeof meters !== "number" || Number.isNaN(meters)) return null;
  const band =
    CLARITY_BANDS.find((entry) => meters < entry.max) ||
    CLARITY_BANDS[CLARITY_BANDS.length - 1];
  const styles = getClarityToneStyles(band.tone);
  return { ...band, ...styles };
}

export function getClarityToneByKey(toneKey) {
  const band = CLARITY_BANDS.find((entry) => entry.tone === toneKey);
  if (!band) return null;
  return { ...band, ...getClarityToneStyles(band.tone) };
}
