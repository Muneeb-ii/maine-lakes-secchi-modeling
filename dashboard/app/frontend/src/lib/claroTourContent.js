import { ROUTES } from "./routes.js";

export const CLARO_NAME = "Claro";
export const CLARO_STORAGE_KEY = "lake-dashboard-claro-state";

export const CLARO_ROUTE_IDS = {
  playground: "playground",
  trends: "trends",
};

export const CLARO_ROUTE_BY_PATH = {
  [ROUTES.playground]: CLARO_ROUTE_IDS.playground,
};

export const CLARO_PERSONA = {
  name: CLARO_NAME,
  tagline: "Water-clarity guide",
  intro:
    "I can point out what each workspace area does and how to use it without changing your scenario.",
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
          "These traits describe the selected lake itself, like location, area, and depth. They stay fixed while you test water conditions.",
        placement: "left",
      },
      {
        id: "prediction-card",
        target: "prediction-card",
        title: "Read predicted clarity",
        body:
          "This is the model’s current Secchi-depth estimate. Larger values mean clearer water. Beside it, Typical for this lake is this lake’s usual prediction, and Change from typical shows how far your scenario sits above or below that reference.",
        placement: "bottom",
      },
      {
        id: "parameter-include",
        target: "parameter-include",
        title: "Include only known measurements",
        body:
          "Use the checkbox when a measurement is known. If you leave it out, the model treats that chemistry value as missing instead of guessing.",
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
          "Drivers show which lake traits and adjusted measurements pushed the prediction toward clearer or murkier water.",
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
    promptTitle: "Claro will guide Trend Following when it is ready.",
    promptBody:
      "This workspace is still in development, so Claro only has a short orientation here for now.",
    steps: [
      {
        id: "trends-intro",
        target: "trends-page",
        title: "Trend Following is coming",
        body:
          "When this workspace gains interactive trend tools, Claro can use the same guided tour system to explain them.",
        placement: "bottom",
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
