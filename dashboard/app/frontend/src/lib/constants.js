export const API_URL = import.meta.env?.VITE_API_URL || "http://localhost:8000";
export const RECENT_LAKES_KEY = "dashboardRecentLakes";
export const SAVED_SCENARIOS_KEY = "dashboardSavedScenarios";
export const UNIT_SYSTEM_KEY = "dashboardUnitSystem";
export const DEBOUNCE_MS = 220;
export const TRAJECTORY_MAX_STEPS = 30;
export const TRAJECTORY_DEDUPE_METERS = 0.02;
export const TRAJECTORY_RESET_CONFIRM_THRESHOLD = 5;

export const PARAMETER_GROUPS = [{ key: "chemistry", label: "Chemistry" }];

// `max` thresholds are canonical Secchi meters and must stay in meters
// (getClarityTone compares prediction meters against them). The `note` is the
// qualitative tail; range text and unit are rendered per active unit system.
export const CLARITY_BANDS = [
  {
    max: 2,
    tone: "turbid",
    label: "Turbid",
    note: "hard to see into the water",
  },
  {
    max: 4,
    tone: "moderate",
    label: "Moderate",
    note: "common for many Maine lakes",
  },
  {
    max: Infinity,
    tone: "clearer",
    label: "Clearer",
    note: "unusually clear",
  },
];

export const ICON_MAP_KEYS = ["Beaker", "Droplet", "Activity", "Gauge", "Thermometer"];
