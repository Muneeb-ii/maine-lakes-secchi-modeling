import { CLARITY_BANDS } from "./constants.js";
import { DEFAULT_UNIT_SYSTEM, displayUnitFor, toDisplay } from "./units.js";

// Render a canonical-meters Secchi threshold in the active unit system. Rounds
// to one decimal and drops a trailing ".0" so metric stays clean (e.g. "2 m")
// while imperial shows the converted value (e.g. "6.6 ft").
export function formatSecchiThreshold(meters, system = DEFAULT_UNIT_SYSTEM) {
  const value = toDisplay(meters, "m", system);
  const rounded = Math.round(value * 10) / 10;
  const text = Number.isInteger(rounded) ? String(rounded) : rounded.toFixed(1);
  return `${text} ${displayUnitFor("m", system)}`;
}

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

export const CLARO_ACCENTS = {
  iconClass: "text-lake-claro",
  textClass: "text-[#0F6B4A]",
  launcherClass: "claro-launcher",
  buttonClass: "claro-button",
  kickerClass: "claro-kicker",
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

// Short range chip text, e.g. "<2 m", "2–4 m", ">4 m" (imperial: ft equivalents).
export function getClarityRangeLabel(band, system = DEFAULT_UNIT_SYSTEM) {
  const index = CLARITY_BANDS.findIndex((entry) => entry.tone === band.tone);
  if (index <= 0) return `<${formatSecchiThreshold(band.max, system)}`;
  const prev = CLARITY_BANDS[index - 1];
  if (!Number.isFinite(band.max)) return `>${formatSecchiThreshold(prev.max, system)}`;
  return `${formatSecchiThreshold(prev.max, system)}–${formatSecchiThreshold(band.max, system)}`;
}

// Full sentence for the prediction hero, e.g. "2 to 4 m, common for many Maine lakes".
export function getClarityDescription(band, system = DEFAULT_UNIT_SYSTEM) {
  const index = CLARITY_BANDS.findIndex((entry) => entry.tone === band.tone);
  if (index <= 0) return `Under ${formatSecchiThreshold(band.max, system)}, ${band.note}`;
  const prev = CLARITY_BANDS[index - 1];
  if (!Number.isFinite(band.max)) {
    return `Over ${formatSecchiThreshold(prev.max, system)}, ${band.note}`;
  }
  return `${formatSecchiThreshold(prev.max, system)} to ${formatSecchiThreshold(band.max, system)}, ${band.note}`;
}
