export const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
export const RECENT_LAKES_KEY = "dashboardRecentLakes";
export const SAVED_SCENARIOS_KEY = "dashboardSavedScenarios";
export const DEBOUNCE_MS = 220;
export const TRAJECTORY_MAX_STEPS = 30;
export const TRAJECTORY_DEDUPE_METERS = 0.02;
export const TRAJECTORY_RESET_CONFIRM_THRESHOLD = 5;

export const PARAMETER_GROUPS = [{ key: "chemistry", label: "Chemistry" }];

export const CLARITY_BANDS = [
  {
    max: 2,
    tone: "turbid",
    label: "Turbid",
    description: "Under 2 m, hard to see into the water",
  },
  {
    max: 4,
    tone: "moderate",
    label: "Moderate",
    description: "2 to 4 m, common for many Maine lakes",
  },
  {
    max: Infinity,
    tone: "clearer",
    label: "Clearer",
    description: "Over 4 m, unusually clear",
  },
];

export const ICON_MAP_KEYS = ["Beaker", "Droplet", "Activity", "Gauge", "Thermometer"];
