import assert from "node:assert/strict";
import { test } from "node:test";
import {
  CLARO_ROUTE_IDS,
  formatClaroStepProgress,
  getAvailableClaroSteps,
  getClaroRouteConfig,
  getClaroRouteId,
  getStepIndexByDirection,
  isClaroRoute,
  markClaroPromptDismissed,
  markClaroTourCompleted,
  normalizeClaroState,
  shouldShowClaroPrompt,
} from "./claroTourContent.js";

test("Claro only registers workspace routes", () => {
  assert.equal(getClaroRouteId("/playground"), CLARO_ROUTE_IDS.playground);
  assert.equal(getClaroRouteId("/trends"), CLARO_ROUTE_IDS.trends);
  assert.equal(getClaroRouteId("/"), "");
  assert.equal(isClaroRoute("/playground"), true);
  assert.equal(isClaroRoute("/contributors"), false);
});

test("playground route has the full walkthrough", () => {
  const config = getClaroRouteConfig(CLARO_ROUTE_IDS.playground);
  assert.ok(config);
  assert.equal(config.steps.length, 12);
  assert.equal(config.steps[0].id, "intro");
  assert.equal(config.steps.at(-1).id, "scenario-reset");
});

test("playground tour orders try-change before save and reset last", () => {
  const ids = getClaroRouteConfig(CLARO_ROUTE_IDS.playground).steps.map((step) => step.id);
  const parameterPanel = ids.indexOf("parameter-panel");
  const metrics = ids.indexOf("prediction-metrics");
  const trajectory = ids.indexOf("trajectory-chart");
  const drivers = ids.indexOf("drivers-panel");
  const save = ids.indexOf("scenario-save");
  const useSaved = ids.indexOf("scenario-use-saved");
  const reset = ids.indexOf("scenario-reset");

  assert.ok(parameterPanel < metrics);
  assert.ok(metrics < trajectory);
  assert.ok(trajectory < drivers);
  assert.ok(drivers < save);
  assert.ok(save < useSaved);
  assert.ok(useSaved < reset);
  assert.equal(reset, ids.length - 1);
});

test("available steps keep intro and skip missing targets", () => {
  const steps = [
    { id: "intro" },
    { id: "present", target: "lake-search" },
    { id: "missing", target: "drivers-panel" },
  ];
  const available = getAvailableClaroSteps(steps, (target) => target === "lake-search");
  assert.deepEqual(
    available.map((step) => step.id),
    ["intro", "present"]
  );
});

test("prompt state dismisses and completes per route", () => {
  const empty = normalizeClaroState(null);
  assert.equal(shouldShowClaroPrompt(empty, CLARO_ROUTE_IDS.playground), true);

  const dismissed = markClaroPromptDismissed(empty, CLARO_ROUTE_IDS.playground);
  assert.equal(shouldShowClaroPrompt(dismissed, CLARO_ROUTE_IDS.playground), false);
  assert.equal(shouldShowClaroPrompt(dismissed, CLARO_ROUTE_IDS.trends), true);

  const completed = markClaroTourCompleted(empty, CLARO_ROUTE_IDS.trends);
  assert.equal(completed.promptDismissed[CLARO_ROUTE_IDS.trends], true);
  assert.equal(completed.completedTours[CLARO_ROUTE_IDS.trends], true);
  assert.equal(shouldShowClaroPrompt(completed, CLARO_ROUTE_IDS.trends), false);
});

test("step progress label omits internal route id", () => {
  assert.equal(formatClaroStepProgress(0, 12), "1 of 12");
  assert.equal(formatClaroStepProgress(11, 12), "12 of 12");
  assert.equal(formatClaroStepProgress(-1, 12), "");
});

test("step navigation clamps to available bounds", () => {
  const steps = [{ id: "a" }, { id: "b" }, { id: "c" }];
  assert.equal(getStepIndexByDirection(0, -1, steps), 0);
  assert.equal(getStepIndexByDirection(0, 1, steps), 1);
  assert.equal(getStepIndexByDirection(2, 1, steps), 2);
  assert.equal(getStepIndexByDirection(0, 1, []), -1);
});
