import { CLARITY_BANDS } from "./constants";

export { formatMeters, formatSignedMeters, formatValueWithUnit } from "./formattersCore.js";

export function getClarityBand(meters) {
  if (typeof meters !== "number" || Number.isNaN(meters)) return null;
  return CLARITY_BANDS.find((band) => meters < band.max) || CLARITY_BANDS[CLARITY_BANDS.length - 1];
}
