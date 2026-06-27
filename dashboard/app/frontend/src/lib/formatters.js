import { getClarityTone } from "./theme.js";

export { formatMeters, formatSignedMeters, formatValueWithUnit } from "./formattersCore.js";

export function getClarityBand(meters) {
  return getClarityTone(meters);
}
