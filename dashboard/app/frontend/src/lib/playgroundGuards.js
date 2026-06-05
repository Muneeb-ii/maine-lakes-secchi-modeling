/** Pure helpers guarding against known playground regressions. */

export function resolveSliderNumericValue(value, min) {
  if (value === null || value === undefined || value === "") {
    return min;
  }
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : min;
}

export function hasFiniteSliderValue(value) {
  if (value === null || value === undefined || value === "") {
    return false;
  }
  return Number.isFinite(Number(value));
}

export function resolveModelBaseline(lakeBaseline, apiBaseValue) {
  return typeof lakeBaseline === "number" && Number.isFinite(lakeBaseline)
    ? lakeBaseline
    : apiBaseValue;
}

export function getContributionDisplay(contribution) {
  if (contribution > 0) {
    return { icon: "plus", tone: "up" };
  }
  if (contribution < 0) {
    return { icon: "minus", tone: "down" };
  }
  return { icon: null, tone: "neutral" };
}

export function stepSearchSuggestion(currentIndex, direction, resultCount) {
  const maxIndex = Math.max(resultCount - 1, 0);
  if (direction === "down") {
    return Math.min(currentIndex + 1, maxIndex);
  }
  return Math.max(currentIndex - 1, -1);
}

export function shouldResetExplainabilityExpanded(previousLakeId, nextLakeId) {
  return previousLakeId !== nextLakeId;
}
