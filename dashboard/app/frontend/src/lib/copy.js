export const DASHBOARD_TITLE = "Maine Lake Water Clarity Dashboard";
export const DASHBOARD_TAGLINE =
  "See how water conditions may affect Secchi depth for lakes across Maine.";

export const PLAYGROUND_EYEBROW = "Playground · Maine lakes";
export const PLAYGROUND_TITLE = "Lake Water Clarity Playground";
export const PLAYGROUND_TAGLINE =
  "Choose a lake, adjust water measurements, and see how predicted Secchi depth compares to that lake’s typical profile.";

export const LANDING_EYEBROW = "Maine lakes · Water clarity";
export const LANDING_TITLE = "Explore Secchi depth";
export const LANDING_HEADER_HOOK =
  "Secchi depth is how far a standard disk stays visible underwater, recorded in meters. It tells us about the water clarity of a lake.";
export const LANDING_HEADER_STATS = [
  { label: "Lakes ready to explore", value: "187" },
  { label: "Monitoring records", value: "87,000+" },
  { label: "Measurements in the model", value: "14" },
];
export const LANDING_CLARITY_TITLE = "How to read Secchi depth";
export const LANDING_HOW_IT_WORKS_TITLE = "What you can do here";
export const LANDING_HIGHLIGHTS = [
  {
    title: "Try “what if” scenarios",
    body: "Pick a lake, adjust chemistry or temperature, and watch predicted Secchi depth update. See which measurements matter most.",
  },
  {
    title: "Trends (coming soon)",
    body: "Track clarity year by year and explore future outlooks. That view is in development. The Playground is ready for hands-on exploration now.",
  },
  {
    title: "Grounded in monitoring data",
    body: "Estimates draw on years of Maine lake monitoring, so results reflect real patterns, not rough guesses.",
  },
];
export const LANDING_WORKSPACES_TITLE = "Get started";

export const LANDING_DESTINATIONS = {
  trends: {
    title: "Trends",
    description:
      "Explore how clarity has changed over time and what may lie ahead for Maine lakes. Available when the trend model launches.",
    status: "Coming soon",
    cta: "Learn more",
  },
  playground: {
    title: "Playground",
    description:
      "Search for a lake, adjust water measurements with sliders, and compare your scenario to that lake’s usual profile.",
    status: "Ready to use",
    cta: "Launch Playground",
  },
};

export const LANDING_TRENDS_PAGE_NOTE =
  "While Trends is being built, use the Playground to explore how water conditions affect Secchi depth for a lake you choose.";

export const SECCHI_DIRECTION_NOTE = "Higher Secchi depth usually means clearer water";

export const SECTION_LABELS = {
  lakeProfile: "About this lake",
  parameters: "Water conditions",
  prediction: "Predicted Secchi depth",
  trajectory: "Changes you tried",
  explainability: "What influenced this prediction",
  scenarioActions: "Save & compare",
};

export const LAKE_PROFILE_INTRO =
  "Location and size for the lake you selected. These stay fixed while you change water measurements.";

export const METRIC_LABELS = {
  modelBaseline: "Typical for this lake",
  deltaFromBaseline: "Change from typical",
  latestChange: "Last slider change",
  steps: "Recorded changes",
  sessionRange: "Depth range",
  latestSecchi: "Latest Secchi",
  latestVsPrevious: "Latest change",
  largestMove: "Largest move",
  latestVsBaseline: "Latest vs typical",
};

export const LAKE_FIELD_LABELS = {
  latitude: "Latitude",
  longitude: "Longitude",
  areaAcres: "Area (acres)",
  maxDepth: "Max depth (ft)",
};

export const UNKNOWN_LAKE_NAME = "Unknown lake";

export const LAKE_SUPPORT_MESSAGES = {
  unsupported:
    "This lake has fewer monitoring records, so treat predictions as rough estimates.",
  fallback:
    "We don’t have a full profile for this lake, so values use a statewide average instead.",
};

export const PARAMETER_PANEL_INTRO =
  "Drag sliders to change water measurements and see how predicted clarity responds.";

export const EXPLAINABILITY_INTRO =
  "How lake traits and the water measurements you changed pushed this prediction toward clearer or murkier water.";
export const EXPLAINABILITY_LAKE_CONTEXT_HEADING = "Lake characteristics";
export const EXPLAINABILITY_LAKE_CONTEXT_NOTE =
  "Location, size, and depth for this lake. These stay fixed while you explore.";
export const EXPLAINABILITY_ADJUSTMENTS_HEADING = "Water conditions you changed";
export const EXPLAINABILITY_SHOW_ALL = "See all water condition factors";
export const EXPLAINABILITY_HIDE_ALL = "Hide full water condition list";
export const EXPLAINABILITY_MISSING =
  "Factor details aren’t available for this prediction.";
export const CONTRIBUTOR_CURRENT_VALUE = "Current value";
export const CONTRIBUTOR_AGGREGATE_VALUE = "Combined effect";
export const ARIA_CONTRIBUTION_CLEARER = "pushes toward clearer water";
export const ARIA_CONTRIBUTION_MURKIER = "pushes toward murkier water";

export const SCENARIO_RESET = "Restore lake defaults";
export const SCENARIO_SAVE = "Save this scenario";
export const SCENARIO_LOAD = "Load snapshot";
export const SCENARIO_DELETE = "Delete saved scenario";
export const SCENARIO_COMPARE_LABEL = "Choose a saved snapshot";
export const SCENARIO_COMPARE_PLACEHOLDER = "Choose a saved snapshot…";
export const SCENARIO_DELETE_CONFIRM =
  "Delete this saved snapshot? You will no longer be able to compare against it.";
export const SCENARIO_LOAD_CONFIRM =
  "Replace your current sliders with this saved snapshot?";
export const SCENARIO_SAVED_STATUS = "Snapshot saved in this browser.";
export const SCENARIO_DELETED_STATUS = "Saved snapshot removed.";
export const SCENARIO_LOADED_STATUS = "Snapshot loaded — sliders updated.";
export const SCENARIO_SAVE_DISABLED_HINT =
  "Adjust at least one water condition from the lake defaults before saving.";
export const SCENARIO_LABEL_PLACEHOLDER = "Name this snapshot (optional)";
export const SCENARIO_GROUP_SESSION = "Your current session";
export const SCENARIO_GROUP_SESSION_DESC =
  "Resets sliders to this lake’s usual values and clears the scenario history chart. Saved snapshots stay in the menu.";
export const SCENARIO_GROUP_SAVE = "Save a snapshot";
export const SCENARIO_GROUP_SAVE_DESC =
  "Bookmarks your current sliders and predicted Secchi in this browser only.";
export const SCENARIO_GROUP_USE_SAVED = "Use a saved snapshot";
export const SCENARIO_GROUP_USE_SAVED_DESC =
  "Pick a snapshot to compare on the chart (reference line). Load restores its sliders; Delete removes it.";
export const SCENARIO_OTHER_LAKE_SAVES = (count) =>
  count === 1
    ? "1 saved snapshot is for another lake — switch lakes to compare it."
    : `${count} saved snapshots are for other lakes — switch lakes to compare them.`;

export function formatSavedScenarioOption(scenario) {
  const when = new Date(scenario.timestamp).toLocaleString();
  if (scenario.label) {
    return `${scenario.label} (${when})`;
  }
  const secchi =
    typeof scenario.predictionMeters === "number"
      ? ` — ${scenario.predictionMeters.toFixed(1)} m`
      : "";
  return `${when}${secchi}`;
}
export const COMPARE_BANNER_INTRO = "Comparing with";
export const COMPARE_BANNER_SAVED_ON = "saved on";
export const COMPARE_BANNER_SAVED_VALUE = "Saved Secchi depth";
export const COMPARE_BANNER_DELTA = "Difference from your current sliders";

export const TRAJECTORY_EMPTY_PROMPT =
  "Move a slider to start a scenario history.";
export const TRAJECTORY_STEP_NOTE =
  "Each dot is one meaningful slider adjustment. Very small tweaks under 0.02 m may be ignored so the chart stays readable.";
export const TRAJECTORY_RESET_CONFIRM =
  "Clear the scenario history chart? Saved scenarios will stay in the comparison menu.";
export const TRAJECTORY_RESET_BUTTON = "Clear chart history";
export const TRAJECTORY_CHART_EMPTY_SUMMARY =
  "Scenario history chart is empty. Adjust water conditions to record meaningful changes.";
export const TRAJECTORY_STEP_LABEL_START = "Typical lake condition";
export const TRAJECTORY_STEP_LABEL_ADJUSTMENT = "Slider adjustment";
export const TRAJECTORY_STEP_LABEL_MULTI = (count) => `${count} measurements changed`;

export const TRAJECTORY_LEGEND = {
  prediction: "Your scenario",
  baselineRef: "Typical for this lake",
  compareRef: "Saved scenario",
  clarity2m: "2 m, turbid reference",
  clarity4m: "4 m, moderate reference",
};

export const TRAJECTORY_AXIS_SESSION = "Scenario history";
export const TRAJECTORY_AXIS_SECCHI = "Secchi depth (m)";
export const TRAJECTORY_TOOLTIP_VS_BASELINE = "vs typical";
export const TRAJECTORY_TOOLTIP_VS_PREVIOUS = "vs previous change";
export const TRAJECTORY_SCALE_LABEL = "Chart scale";
export const TRAJECTORY_SCALE_DETAIL = "Detail";
export const TRAJECTORY_SCALE_FULL = "Full context";
export const TRAJECTORY_SCALE_NOTE_DETAIL =
  "Detail scale zooms in around your scenario so small changes are easier to see.";
export const TRAJECTORY_SCALE_NOTE_FULL =
  "Full context keeps the 2 m and 4 m clarity references in view.";

export const SEARCH_PLACEHOLDER = "Search by lake name…";
export const SEARCH_ARIA_LABEL = "Search for a lake";
export const SEARCH_LOADING = "Searching lakes…";
export const SEARCH_NO_MATCHES = "No lakes match that search.";
export const SEARCH_RECENT_HEADING = "Recently viewed";

export const SLIDER_STARTING_VALUE = "This lake’s usual value";
export const SLIDER_VALUE_LABEL = "Type value";
export const SLIDER_VALUE_ERROR = (min, max, unit = "") =>
  `Enter a value from ${min} to ${max}${unit ? ` ${unit}` : ""}.`;

export const BOOT_LOADING = "Loading lake data and predictions…";
export const BOOT_ERROR_TITLE = "Dashboard couldn’t load";

export const PREDICTION_UPDATING = "Updating prediction…";

export const NAV_HOME = "Back to home";

export function formatLakeSearchDisplay(lakeId, lakeName) {
  const id = String(lakeId || "").trim().toUpperCase();
  const name = String(lakeName || "").trim();
  if (!id) return "";
  if (!name || name === UNKNOWN_LAKE_NAME) return id;
  return `${id}, ${name}`;
}

export function parseLakeSearchInput(query) {
  const trimmed = String(query || "").trim();
  if (!trimmed) return { midasId: "", nameHint: "" };

  const labeledMatch = trimmed.match(/^([A-Za-z]?\d+)\s*,\s*(.+)$/);
  if (labeledMatch) {
    return {
      midasId: labeledMatch[1].toUpperCase(),
      nameHint: labeledMatch[2].trim(),
    };
  }

  const idOnlyMatch = trimmed.match(/^([A-Za-z]?\d+)$/i);
  if (idOnlyMatch) {
    return { midasId: idOnlyMatch[1].toUpperCase(), nameHint: "" };
  }

  return { midasId: trimmed, nameHint: "" };
}

export function formatTrajectorySteps(current, max) {
  return `${current} of ${max} changes shown`;
}

export function formatTrajectoryChartLiveSummary(stepCount, latestSecchi, deltaFromTypical) {
  return `Scenario history chart with ${stepCount} changes. Latest Secchi ${latestSecchi}, ${deltaFromTypical} compared to typical.`;
}
