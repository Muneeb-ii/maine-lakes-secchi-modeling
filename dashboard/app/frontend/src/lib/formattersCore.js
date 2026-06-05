export function formatMeters(value) {
  if (typeof value !== "number" || Number.isNaN(value)) return "--";
  return `${value.toFixed(2)} m`;
}

export function formatSignedMeters(value, { absolute = false } = {}) {
  if (typeof value !== "number" || Number.isNaN(value)) return "--";
  if (absolute) {
    return `${Math.abs(value).toFixed(2)} m`;
  }
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(2)} m`;
}

export function formatValueWithUnit(value, unit) {
  if (typeof value !== "number" || Number.isNaN(value)) return "--";
  const formatted = Number.isInteger(value) ? String(value) : value.toFixed(2);
  return unit ? `${formatted} ${unit}` : formatted;
}
