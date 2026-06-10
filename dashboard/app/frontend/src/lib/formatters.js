import { getClarityTone } from "./theme";

export { formatMeters, formatSignedMeters, formatValueWithUnit } from "./formattersCore.js";

export function getClarityBand(meters) {
  return getClarityTone(meters);
}
