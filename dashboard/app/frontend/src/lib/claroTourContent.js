import { ROUTES } from "./routes.js";

export const CLARO_NAME = "Claro";
export const CLARO_STORAGE_KEY = "lake-dashboard-claro-state";

export const CLARO_ROUTE_IDS = {
  playground: "playground",
  trends: "trends",
};

export const CLARO_ROUTE_BY_PATH = {
  [ROUTES.playground]: CLARO_ROUTE_IDS.playground,
  [ROUTES.trends]: CLARO_ROUTE_IDS.trends,
};

export const CLARO_PERSONA = {
  name: CLARO_NAME,
  tagline: "Water-clarity guide",
  intro:
    "I can point out what each workspace area does and how to use it without taking over your work.",
};

export const claroTourRoutes = {
  [CLARO_ROUTE_IDS.playground]: {
    routeId: CLARO_ROUTE_IDS.playground,
    promptTitle: "New here? Take a guided tour with Claro.",
    promptBody:
      "Claro will point to the main tools in the playground and explain how to test a lake clarity scenario.",
    steps: [
      {
        id: "intro",
        title: "Meet Claro",
        body:
          "This walkthrough goes from lake selection to trying a change, reading the results, and optionally saving or resetting your scenario.",
        placement: "center",
      },
      {
        id: "unit-system",
        target: "unit-system-toggle",
        title: "Choose how measurements are shown",
        body:
          "Switch between Metric and Imperial in the top bar. This changes display labels and values without changing the model’s underlying measurements.",
        placement: "bottom",
        cursorHint: "click",
      },
      {
        id: "lake-search",
        target: "lake-search",
        title: "Choose a lake",
        body:
          "Search by lake name or MIDAS ID. The rest of the workspace updates around the lake you select.",
        placement: "left",
        cursorHint: "select",
      },
      {
        id: "lake-map",
        target: "lake-map-button",
        title: "Find lakes on the map",
        body:
          "Use the map button to browse lake locations, zoom in for lake-name labels, and open a pin card to choose a lake.",
        placement: "left",
        cursorHint: "click",
      },
      {
        id: "lake-profile",
        target: "lake-profile",
        title: "Check fixed lake traits",
        body:
          "These traits describe the selected lake itself: location, area, depth, and its typical water chemistry. They stay fixed while you test water conditions.",
        placement: "left",
      },
      {
        id: "prediction-card",
        target: "prediction-card",
        title: "Read predicted clarity",
        body:
          "This is the model’s current Secchi-depth estimate. Larger values mean clearer water. Typical for this lake and Change from typical sit beside it. The scale shows where the estimate falls among Maine clarity bands.",
        placement: "bottom",
      },
      {
        id: "parameter-include",
        target: "parameter-include",
        title: "Include only known measurements",
        body:
          "Use the checkbox when a measurement is known. If you leave it out, the model treats that measurement as missing instead of guessing.",
        placement: "right",
        cursorHint: "click",
      },
      {
        id: "parameter-panel",
        target: "parameter-slider-control",
        title: "Try a water-condition change",
        body:
          "Move a slider or type a value, then release or pause briefly. Each card shows nearby sensitivity for this lake and flags when larger changes may behave differently.",
        placement: "top",
        cursorHint: "drag",
      },
      {
        id: "prediction-metrics",
        target: "prediction-metrics",
        title: "See how your change compares",
        body:
          "After a slider change, check whether Secchi moved up or down and how far you are from this lake’s typical prediction.",
        placement: "left",
      },
      {
        id: "trajectory-chart",
        target: "trajectory-chart",
        title: "Follow your scenario path",
        body:
          "After a meaningful change, the chart records your session from typical through each adjustment. The change log lists the same steps, and Detail or Full context controls how much of the y-axis you see.",
        placement: "top",
      },
      {
        id: "drivers-panel",
        target: "drivers-panel",
        title: "See what drove the estimate",
        body:
          "Water conditions you changed are listed in full. Lake characteristics stay collapsed until you open them.",
        placement: "top",
      },
      {
        id: "scenario-save",
        target: "scenario-save",
        title: "Save a scenario",
        body:
          "Once your sliders differ from the lake baseline and a forecast is showing, you can name this setup and save it in this browser.",
        placement: "right",
        cursorHint: "click",
      },
      {
        id: "scenario-use-saved",
        target: "scenario-use-saved",
        title: "Compare, load, or delete saved scenarios",
        body:
          "Pick a saved snapshot to compare on the chart, load its sliders back into the workspace, or delete it.",
        placement: "right",
      },
      {
        id: "scenario-reset",
        target: "scenario-reset",
        title: "Restore lake defaults",
        body:
          "When you are done experimenting, use this to return sliders to the lake baseline and clear the session chart. Saved snapshots stay in the menu.",
        placement: "right",
        cursorHint: "click",
      },
    ],
  },
  [CLARO_ROUTE_IDS.trends]: {
    routeId: CLARO_ROUTE_IDS.trends,
    promptTitle: "Want a quick tour of Trends?",
    promptBody:
      "Claro will show you how to choose a lake, read its observed history, and interpret the baseline outlook.",
    steps: [
      {
        id: "trends-intro",
        title: "Meet Trends",
        body:
          "This workspace separates what was measured from the baseline outlook, so you can read the record first and then explore what the reference scenario shows next.",
        placement: "center",
      },
      {
        id: "trends-units",
        target: "unit-system-toggle",
        title: "Choose how depth is shown",
        body:
          "Use Metric or Imperial in the top bar. The charts and summary values update together while the underlying record stays the same.",
        placement: "bottom",
        cursorHint: "click",
      },
      {
        id: "trends-search",
        target: "trends-lake-search",
        title: "Choose a lake",
        body:
          "Search by lake name or MIDAS ID. Select a result to update the history and outlook shown on the right.",
        placement: "right",
        cursorHint: "select",
      },
      {
        id: "trends-map",
        target: "lake-map-button",
        title: "Find a lake on the map",
        body:
          "Use the amber map button to browse lake locations, zoom in for names, and choose a lake from its pin card.",
        placement: "right",
        cursorHint: "click",
      },
      {
        id: "trends-list",
        target: "trends-lake-list",
        title: "Browse the lake list",
        body:
          "The list shows the available history for each lake. A green label marks lakes with enough recent support for the baseline outlook; history-only lakes still remain useful for the observed record.",
        placement: "right",
      },
      {
        id: "trends-detail",
        target: "trends-detail",
        title: "Read the lake summary",
        body:
          "Start with the latest observed value, the end of the baseline outlook when available, and how many years are in the record.",
        placement: "left",
      },
      {
        id: "trends-history",
        target: "trends-history-chart",
        title: "Start with observed history",
        body:
          "This chart shows measured summer Secchi depth by year. Hover a point to see the value and the number of monitoring readings behind it.",
        placement: "left",
      },
      {
        id: "trends-forecast",
        target: "trends-forecast-chart",
        title: "Interpret the baseline outlook",
        body:
          "The amber line is a reference scenario, while the shaded bands show empirical uncertainty. It is a planning range, not a promise that the lake will improve or decline.",
        placement: "left",
      },
    ],
  },
};

export function getClaroRouteId(pathname) {
  return CLARO_ROUTE_BY_PATH[pathname] || "";
}

export function getClaroRouteConfig(routeId) {
  return claroTourRoutes[routeId] || null;
}

export function isClaroRoute(pathname) {
  return Boolean(getClaroRouteConfig(getClaroRouteId(pathname)));
}

export function normalizeClaroState(value) {
  const source = value && typeof value === "object" ? value : {};
  return {
    promptDismissed: source.promptDismissed && typeof source.promptDismissed === "object"
      ? source.promptDismissed
      : {},
    completedTours: source.completedTours && typeof source.completedTours === "object"
      ? source.completedTours
      : {},
  };
}

export function shouldShowClaroPrompt(state, routeId) {
  if (!routeId) return false;
  const normalized = normalizeClaroState(state);
  return !normalized.promptDismissed[routeId] && !normalized.completedTours[routeId];
}

export function markClaroPromptDismissed(state, routeId) {
  const normalized = normalizeClaroState(state);
  return {
    ...normalized,
    promptDismissed: {
      ...normalized.promptDismissed,
      [routeId]: true,
    },
  };
}

export function markClaroTourCompleted(state, routeId) {
  const normalized = normalizeClaroState(state);
  return {
    ...normalized,
    promptDismissed: {
      ...normalized.promptDismissed,
      [routeId]: true,
    },
    completedTours: {
      ...normalized.completedTours,
      [routeId]: true,
    },
  };
}

export function getAvailableClaroSteps(steps, hasTarget) {
  return steps.filter((step) => {
    if (!step.target) return true;
    return hasTarget(step.target);
  });
}

export function getStepIndexByDirection(currentIndex, direction, steps) {
  if (!steps.length) return -1;
  const next = currentIndex + direction;
  return Math.max(0, Math.min(steps.length - 1, next));
}

/** User-facing tour progress (route id is internal only). */
export function formatClaroStepProgress(stepIndex, totalSteps) {
  if (!totalSteps || stepIndex < 0) return "";
  return `${stepIndex + 1} of ${totalSteps}`;
}
