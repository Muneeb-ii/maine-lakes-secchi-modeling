import { CLARITY_BANDS } from "./constants";

export function formatMeters(value) {
  if (typeof value !== "number" || Number.isNaN(value)) return "--";
  return `${value.toFixed(2)} m`;
}

export function formatSignedMeters(value) {
  if (typeof value !== "number" || Number.isNaN(value)) return "--";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(2)} m`;
}

export function formatValueWithUnit(value, unit) {
  if (typeof value !== "number" || Number.isNaN(value)) return "--";
  const formatted = Number.isInteger(value) ? String(value) : value.toFixed(2);
  return unit ? `${formatted} ${unit}` : formatted;
}

export function getClarityBand(meters) {
  if (typeof meters !== "number" || Number.isNaN(meters)) return null;
  return CLARITY_BANDS.find((band) => meters < band.max) || CLARITY_BANDS[CLARITY_BANDS.length - 1];
}
