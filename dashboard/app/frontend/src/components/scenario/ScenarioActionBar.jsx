import { Bookmark, Layers, RotateCcw } from "lucide-react";
import {
  SCENARIO_COMPARE_LABEL,
  SCENARIO_COMPARE_PLACEHOLDER,
  SCENARIO_RESET,
  SCENARIO_SAVE,
  SECTION_LABELS,
  formatSavedScenarioOption,
} from "../../lib/copy";
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
          {SCENARIO_RESET}
        </button>
        <button
          type="button"
          className="action-button col-span-1"
          onClick={onSave}
          disabled={!canSave}
        >
          <Bookmark className="w-4 h-4" aria-hidden />
          {SCENARIO_SAVE}
        </button>
        <div className="col-span-2 sm:col-span-1 sm:flex-1 sm:min-w-[200px] sm:max-w-sm flex items-center gap-2">
          <Layers className="w-4 h-4 text-slate-600 shrink-0" aria-hidden />
          <label htmlFor="compare-scenario" className="sr-only">
            {SCENARIO_COMPARE_LABEL}
          </label>
          <select
            id="compare-scenario"
            value={compareScenarioId}
            onChange={(event) => onCompareChange(event.target.value)}
            className="w-full h-12 rounded-lg bg-white border border-slate-300 px-3 text-base text-slate-950 focus-visible:outline focus-visible:outline-2 focus-visible:outline-lake-accent"
          >
            <option value="">{SCENARIO_COMPARE_PLACEHOLDER}</option>
            {savedScenarios.map((scenario) => (
              <option key={scenario.id} value={scenario.id}>
                {formatSavedScenarioOption(
                  scenario.lakeId,
                  scenario.lakeName,
                  scenario.timestamp
                )}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
}
