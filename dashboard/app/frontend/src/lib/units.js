// Display-only unit conversion. The backend always receives canonical,
// model-trained units; this module exists purely to render those canonical
// values in the unit system the user prefers.
//
// Canonical (model-trained) units never change:
//   Secchi depth -> meters, max depth -> feet, lake area -> acres.
// Chemistry units (DO ppm, TP ppb, color SPU, conductivity uS/cm, pH,
// alkalinity) are not convertible and always take the identity path.

export const UNIT_SYSTEMS = { METRIC: "metric", US: "us" };
export const DEFAULT_UNIT_SYSTEM = UNIT_SYSTEMS.METRIC;

export const UNIT_SYSTEM_OPTIONS = [
  { value: UNIT_SYSTEMS.METRIC, label: "Metric", hint: "m / ha" },
  { value: UNIT_SYSTEMS.US, label: "US", hint: "ft / acres" },
];

// Each dimension defines its convertible units as ratios to a shared base,
// plus which unit to display per system. Add a dimension here to extend
// coverage (e.g. temperature for the trends dashboard).
const DIMENSIONS = {
  length: {
    units: { m: 1, ft: 0.3048 },
    display: { [UNIT_SYSTEMS.METRIC]: "m", [UNIT_SYSTEMS.US]: "ft" },
  },
  area: {
    units: { acres: 4046.8564224, ha: 10000 },
    display: { [UNIT_SYSTEMS.METRIC]: "ha", [UNIT_SYSTEMS.US]: "acres" },
  },
};

const UNIT_TO_DIMENSION = (() => {
  const map = {};
  for (const [dimension, spec] of Object.entries(DIMENSIONS)) {
    for (const unit of Object.keys(spec.units)) map[unit] = dimension;
  }
  return map;
})();

function dimensionForUnit(unit) {
  return UNIT_TO_DIMENSION[unit] || null;
}

export function isConvertibleUnit(unit) {
  return Boolean(dimensionForUnit(unit));
}

export function normalizeUnitSystem(system) {
  return system === UNIT_SYSTEMS.US ? UNIT_SYSTEMS.US : UNIT_SYSTEMS.METRIC;
}

// The unit label to show for a canonical unit under a given system. Returns
// the canonical unit unchanged for non-convertible (chemistry) units.
export function displayUnitFor(canonicalUnit, system = DEFAULT_UNIT_SYSTEM) {
  const dimension = dimensionForUnit(canonicalUnit);
  if (!dimension) return canonicalUnit;
  return DIMENSIONS[dimension].display[normalizeUnitSystem(system)] || canonicalUnit;
}

// Pure numeric conversion between two units of the same dimension. Identity
// when units match, are non-convertible, or belong to different dimensions.
export function convert(value, fromUnit, toUnit) {
  if (typeof value !== "number" || Number.isNaN(value)) return value;
  if (fromUnit === toUnit) return value;
  const dimension = dimensionForUnit(fromUnit);
  if (!dimension || dimensionForUnit(toUnit) !== dimension) return value;
  const units = DIMENSIONS[dimension].units;
  return (value * units[fromUnit]) / units[toUnit];
}

// Canonical value -> displayed value for the active system.
export function toDisplay(value, canonicalUnit, system = DEFAULT_UNIT_SYSTEM) {
  return convert(value, canonicalUnit, displayUnitFor(canonicalUnit, system));
}

// Displayed value -> canonical value (use at input-commit time only).
export function toCanonical(value, canonicalUnit, system = DEFAULT_UNIT_SYSTEM) {
  return convert(value, displayUnitFor(canonicalUnit, system), canonicalUnit);
}

// One-stop formatter: converts a canonical value to the active system and
// renders it with the right unit label. Non-convertible units render as-is.
export function formatQuantity(
  value,
  {
    canonicalUnit,
    system = DEFAULT_UNIT_SYSTEM,
    decimals = 2,
    signed = false,
    absolute = false,
    withUnit = true,
  } = {}
) {
  if (typeof value !== "number" || Number.isNaN(value)) return "--";
  const display = toDisplay(value, canonicalUnit, system);
  const magnitude = absolute ? Math.abs(display) : display;
  const sign = signed && !absolute && display > 0 ? "+" : "";
  const body = `${sign}${magnitude.toFixed(decimals)}`;
  const unit = displayUnitFor(canonicalUnit, system);
  return withUnit && unit ? `${body} ${unit}` : body;
}
