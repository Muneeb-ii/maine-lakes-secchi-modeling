export const DASHBOARD_TITLE = "Maine Lake Water Clarity Dashboard";
export const DASHBOARD_TAGLINE =
  "See how water conditions may affect Secchi depth for lakes across Maine.";

export const LANDING_EYEBROW = "Maine lakes · Water clarity";
export const LANDING_TITLE = "Explore Secchi depth for Maine lakes";
export const LANDING_INTRO =
  "Secchi depth is how far you can see into the water. Deeper usually means clearer. Choose a lake, try different water conditions, and see how clarity might change.";
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
export const LANDING_WORKSPACES_INTRO =
  "Open the Playground to explore scenarios today, or visit Trends to see what’s coming next.";

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

export const FOOTER_DEVELOPERS =
  "Developed by Tahiya Chowdhury and Muneeb Nafees at Colby College, in collaboration with 7 Lakes Alliance, with support from USGS funding.";
export const FOOTER_PARTNERS_LABEL = "Project partners";
export const MODEL_FOOTNOTE =
  "Estimates use a statistical model trained on Maine lakes with enough long-term monitoring to support reliable predictions.";
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
  steps: "Points recorded",
  sessionRange: "Range this session",
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
  supported:
    "This lake is well represented in the model, so you can explore scenarios with more confidence.",
  unsupported:
    "This lake has fewer monitoring records, so treat predictions as rough estimates.",
  fallback:
    "We don’t have a full profile for this lake, so values use a statewide average instead.",
};

export const PARAMETER_PANEL_INTRO =
  "Drag sliders to change water measurements and see how predicted clarity responds.";

export const EXPLAINABILITY_INTRO =
  "The three measurements that most pushed this prediction toward clearer or murkier water.";
export const EXPLAINABILITY_SHOW_ALL = "See all contributing factors";
export const EXPLAINABILITY_HIDE_ALL = "Hide full factor list";
export const EXPLAINABILITY_MISSING =
  "Factor details aren’t available for this prediction.";
export const CONTRIBUTOR_CURRENT_VALUE = "Current value";
export const CONTRIBUTOR_AGGREGATE_VALUE = "Combined effect";
export const ARIA_CONTRIBUTION_CLEARER = "pushes toward clearer water";
export const ARIA_CONTRIBUTION_MURKIER = "pushes toward murkier water";

export const SCENARIO_RESET = "Restore lake defaults";
export const SCENARIO_SAVE = "Save this scenario";
export const SCENARIO_COMPARE_LABEL = "Compare with a saved scenario";
export const SCENARIO_COMPARE_PLACEHOLDER = "Choose a saved scenario…";

export function formatSavedScenarioOption(lakeId, lakeName, timestamp) {
  const when = new Date(timestamp).toLocaleString();
  return `${lakeId}, ${lakeName} (${when})`;
}
export const COMPARE_BANNER_INTRO = "Comparing with a scenario you saved on";
export const COMPARE_BANNER_DELTA = "Difference from that scenario";

export const TRAJECTORY_EMPTY_PROMPT =
  "Move a slider to record your first change.";
export const TRAJECTORY_STEP_NOTE =
  "A point is added when predicted Secchi changes by at least 0.02 m (about 0.8 in). Very small tweaks may not show up.";
export const TRAJECTORY_RESET_CONFIRM =
  "Clear every recorded change? Your slider settings will stay as they are.";
export const TRAJECTORY_RESET_BUTTON = "Clear changes";
export const TRAJECTORY_CHART_EMPTY_SUMMARY =
  "Changes chart is empty. Adjust water conditions to record points.";
export const TRAJECTORY_STEP_LABEL_START = "Starting point";
export const TRAJECTORY_STEP_LABEL_ADJUSTMENT = "Adjustment";
export const TRAJECTORY_STEP_LABEL_MULTI = (count) => `${count} measurements changed`;

export const TRAJECTORY_LEGEND = {
  prediction: "Your scenario",
  baselineRef: "Typical for this lake",
  compareRef: "Saved scenario",
  clarity2m: "2 m, turbid reference",
  clarity4m: "4 m, moderate reference",
};

export const TRAJECTORY_AXIS_SESSION = "Adjustments you made";
export const TRAJECTORY_AXIS_SECCHI = "Secchi depth (m)";
export const TRAJECTORY_TOOLTIP_VS_BASELINE = "vs typical";

export const SEARCH_PLACEHOLDER = "Search by lake name…";
export const SEARCH_ARIA_LABEL = "Search for a lake";
export const SEARCH_LOADING = "Searching lakes…";
export const SEARCH_NO_MATCHES = "No lakes match that search.";
export const SEARCH_RECENT_HEADING = "Recently viewed";

export const SLIDER_STARTING_VALUE = "This lake’s usual value";

export const BOOT_LOADING = "Loading lake data and predictions…";
export const BOOT_ERROR_TITLE = "Dashboard couldn’t load";

export const PREDICTION_UPDATING = "Updating prediction…";

export const NAV_HOME = "Back to home";

export function formatLakeContext(lakeName, lakeId) {
  const id = String(lakeId || "").trim().toUpperCase();
  const name = String(lakeName || "").trim();
  const hasReadableName = name && name !== UNKNOWN_LAKE_NAME;
  if (hasReadableName) {
    return `Exploring ${name}`;
  }
  return `Exploring lake ${id}`;
}

export function formatTrajectorySteps(current, max) {
  return `${current} of ${max} points`;
}

export function formatTrajectoryChartLiveSummary(stepCount, latestSecchi, deltaFromTypical) {
  return `Chart with ${stepCount} points. Latest Secchi ${latestSecchi}, ${deltaFromTypical} compared to typical.`;
}
