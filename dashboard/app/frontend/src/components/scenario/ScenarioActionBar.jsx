import { Bookmark, Layers, RotateCcw } from "lucide-react";
import { SECTION_LABELS } from "../../lib/copy";
import { HELP_CONTENT } from "../../lib/helpContent";
import { SectionHelp } from "../ui/SectionHelp";

export function ScenarioActionBar({
  onReset,
  onSave,
  canSave,
  savedScenarios,
  compareScenarioId,
  onCompareChange,
}) {
  return (
    <div className="panel p-4">
      <div className="section-heading mb-3">
        {SECTION_LABELS.scenarioActions}
        <SectionHelp content={HELP_CONTENT.scenarioActions} />
      </div>
      <div className="grid grid-cols-2 sm:flex sm:flex-wrap gap-3 sm:items-center">
        <button type="button" className="action-button col-span-1" onClick={onReset}>
          <RotateCcw className="w-4 h-4" aria-hidden />
          Reset
        </button>
        <button
          type="button"
          className="action-button col-span-1"
          onClick={onSave}
          disabled={!canSave}
        >
          <Bookmark className="w-4 h-4" aria-hidden />
          Save scenario
        </button>
        <div className="col-span-2 sm:col-span-1 sm:flex-1 sm:min-w-[200px] sm:max-w-sm flex items-center gap-2">
          <Layers className="w-4 h-4 text-slate-400 shrink-0" aria-hidden />
          <label htmlFor="compare-scenario" className="sr-only">
            Compare saved scenario
          </label>
          <select
            id="compare-scenario"
            value={compareScenarioId}
            onChange={(event) => onCompareChange(event.target.value)}
            className="w-full h-11 rounded-lg bg-slate-900/70 border border-slate-700/70 px-3 text-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-lake-accent"
          >
            <option value="">Compare scenario…</option>
            {savedScenarios.map((scenario) => (
              <option key={scenario.id} value={scenario.id}>
                {scenario.lakeId} — {scenario.lakeName} —{" "}
                {new Date(scenario.timestamp).toLocaleString()}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
}
