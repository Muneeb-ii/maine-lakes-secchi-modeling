import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  getContributionDisplay,
  hasFiniteSliderValue,
  resolveModelBaseline,
  resolveSliderNumericValue,
  shouldResetExplainabilityExpanded,
  stepSearchSuggestion,
} from "./playgroundGuards.js";

describe("playgroundGuards", () => {
  it("resolveSliderNumericValue falls back to min for null and invalid values", () => {
    assert.equal(resolveSliderNumericValue(null, 4), 4);
    assert.equal(resolveSliderNumericValue(undefined, 2), 2);
    assert.equal(resolveSliderNumericValue("", 1), 1);
    assert.equal(resolveSliderNumericValue(7.5, 0), 7.5);
    assert.equal(resolveSliderNumericValue("bad", 3), 3);
  });

  it("hasFiniteSliderValue rejects null without treating it as zero", () => {
    assert.equal(hasFiniteSliderValue(null), false);
    assert.equal(hasFiniteSliderValue(0), true);
    assert.equal(hasFiniteSliderValue(7.2), true);
  });

  it("resolveModelBaseline prefers lake baseline and falls back to API value", () => {
    assert.equal(resolveModelBaseline(5.2, 4.8), 5.2);
    assert.equal(resolveModelBaseline(undefined, 4.8), 4.8);
    assert.equal(resolveModelBaseline(Number.NaN, 4.8), 4.8);
  });

  it("getContributionDisplay treats zero as neutral without minus icon", () => {
    assert.deepEqual(getContributionDisplay(0.15), { icon: "plus", tone: "up" });
    assert.deepEqual(getContributionDisplay(-0.1), { icon: "minus", tone: "down" });
    assert.deepEqual(getContributionDisplay(0), { icon: null, tone: "neutral" });
  });

  it("stepSearchSuggestion clears highlight on ArrowUp from first result", () => {
    assert.equal(stepSearchSuggestion(0, "up", 5), -1);
    assert.equal(stepSearchSuggestion(-1, "up", 5), -1);
    assert.equal(stepSearchSuggestion(0, "down", 5), 1);
    assert.equal(stepSearchSuggestion(4, "down", 5), 4);
  });

  it("shouldResetExplainabilityExpanded when lake changes", () => {
    assert.equal(shouldResetExplainabilityExpanded("C3420", "C3420"), false);
    assert.equal(shouldResetExplainabilityExpanded("C3420", "C4444"), true);
  });
});
