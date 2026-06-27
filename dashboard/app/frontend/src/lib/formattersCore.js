import { DEFAULT_UNIT_SYSTEM, displayUnitFor, toDisplay } from "./units.js";

// Secchi values are canonical meters; render them in the active unit system.
// Defaulting to metric keeps existing callers (and tests) byte-for-byte stable.
export function formatMeters(value, system = DEFAULT_UNIT_SYSTEM) {
  if (typeof value !== "number" || Number.isNaN(value)) return "--";
  const display = toDisplay(value, "m", system);
  return `${display.toFixed(2)} ${displayUnitFor("m", system)}`;
}

export function formatSignedMeters(value, { absolute = false, system = DEFAULT_UNIT_SYSTEM } = {}) {
  if (typeof value !== "number" || Number.isNaN(value)) return "--";
  const display = toDisplay(value, "m", system);
  const unit = displayUnitFor("m", system);
  if (absolute) {
    return `${Math.abs(display).toFixed(2)} ${unit}`;
  }
  const sign = display > 0 ? "+" : "";
  return `${sign}${display.toFixed(2)} ${unit}`;
}

// Chemistry values are non-convertible: render with their canonical unit as-is.
export function formatValueWithUnit(value, unit) {
  if (typeof value !== "number" || Number.isNaN(value)) return "--";
  const formatted = Number.isInteger(value) ? String(value) : value.toFixed(2);
  return unit ? `${formatted} ${unit}` : formatted;
}
