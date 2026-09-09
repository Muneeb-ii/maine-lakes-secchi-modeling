import { useUnitSystem } from "../../context/UnitSystemContext";
import { UNIT_SYSTEM_OPTIONS } from "../../lib/units";

// Display-only unit selector. Switches how convertible quantities (length,
// area, clarity references) are shown across the workspaces. Canonical
// model-trained values in state are never altered, so the backend always
// receives the units it was trained on.
export function UnitSystemToggle({ className = "", workspace = "playground" }) {
  const { system, setSystem } = useUnitSystem();
  const isTrends = workspace === "trends";

  return (
    <div
      role="group"
      aria-label="Measurement units"
      data-claro-target="unit-system-toggle"
      className={`inline-grid grid-cols-2 rounded-full border bg-white p-1 ${
        isTrends ? "border-lake-amber/30" : "border-lake-border"
      } ${className}`}
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
                ? isTrends
                  ? "bg-lake-amber text-white"
                  : "bg-lake-accent text-white"
                : isTrends
                  ? "text-amber-900 hover:bg-amber-50"
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
