import { useUnitSystem } from "../../context/UnitSystemContext";
import { UNIT_SYSTEM_OPTIONS } from "../../lib/units";

// Display-only unit selector. Switches how convertible quantities (length,
// area, clarity references) are shown across the playground. Canonical
// model-trained values in state are never altered, so the backend always
// receives the units it was trained on.
export function UnitSystemToggle({ className = "" }) {
  const { system, setSystem } = useUnitSystem();

  return (
    <div
      role="group"
      aria-label="Measurement units"
      className={`inline-grid grid-cols-2 rounded-full border border-lake-border bg-white p-1 ${className}`}
    >
      {UNIT_SYSTEM_OPTIONS.map((option) => {
        const active = option.value === system;
        return (
          <button
            key={option.value}
            type="button"
            aria-pressed={active}
            title={option.hint}
            onClick={() => setSystem(option.value)}
            className={`rounded-full px-3 py-1 text-sm font-semibold transition ${
              active
                ? "bg-lake-accent text-white"
                : "text-lake-accent hover:bg-blue-50"
            }`}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
