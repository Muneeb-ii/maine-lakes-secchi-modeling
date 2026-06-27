import { useState } from "react";
import { Bookmark, Download, Layers, RotateCcw, Trash2 } from "lucide-react";
import {
  SCENARIO_COMPARE_LABEL,
  SCENARIO_COMPARE_PLACEHOLDER,
  SCENARIO_DELETE,
  SCENARIO_GROUP_SAVE,
  SCENARIO_GROUP_SAVE_DESC,
  SCENARIO_GROUP_SESSION,
  SCENARIO_GROUP_SESSION_DESC,
  SCENARIO_GROUP_USE_SAVED,
  SCENARIO_GROUP_USE_SAVED_DESC,
  SCENARIO_LABEL_PLACEHOLDER,
  SCENARIO_LOAD,
  SCENARIO_OTHER_LAKE_SAVES,
  SCENARIO_RESET,
  SCENARIO_SAVE,
  SCENARIO_SAVE_DISABLED_HINT,
  SECTION_LABELS,
  formatSavedScenarioOption,
} from "../../lib/copy";
import { SAVED_SCENARIO_LABEL_MAX } from "../../lib/savedScenarios";
import { HELP_CONTENT } from "../../lib/helpContent";
import { SECTION_ACCENTS } from "../../lib/theme";
import { useUnitSystem } from "../../context/UnitSystemContext";
import { SectionHelp } from "../ui/SectionHelp";
import { SectionHeadingIcon } from "../ui/SectionHeadingIcon";

export function ScenarioActionBar({
  onReset,
  onSave,
  onLoad,
  canSave,
  lakeSavedScenarios,
  otherLakeSaveCount = 0,
  compareScenarioId,
  onCompareChange,
  onDeleteScenario,
  actionStatus,
}) {
  const { system } = useUnitSystem();
  const [saveLabel, setSaveLabel] = useState("");
  const compareActive = Boolean(compareScenarioId);
  const canUseSaved = compareActive;

  const handleSave = () => {
    const saved = onSave(saveLabel);
    if (saved) {
      setSaveLabel("");
    }
  };

  return (
    <div
      data-claro-target="scenario-actions"
      className={`panel p-4 ${
        compareActive ? "panel-accent-left panel-accent-compare" : SECTION_ACCENTS.scenario.panelAccentClass
      }`}
    >
      <div className="section-heading mb-4">
        <SectionHeadingIcon section="scenario" icon={Bookmark} />
        {SECTION_LABELS.scenarioActions}
        <SectionHelp content={HELP_CONTENT.scenarioActions} />
      </div>

      <div className="space-y-5">
        <section className="scenario-action-group space-y-2 border-t border-slate-200 pt-4 first:border-t-0 first:pt-0">
          <h3 className="info-label text-slate-900">{SCENARIO_GROUP_SESSION}</h3>
          <p id="scenario-session-desc" className="body-copy text-sm text-slate-600">
            {SCENARIO_GROUP_SESSION_DESC}
          </p>
          <button
            type="button"
            className="action-button w-full sm:w-auto"
            onClick={onReset}
            data-claro-target="scenario-reset"
          >
            <RotateCcw className="w-4 h-4" aria-hidden />
            {SCENARIO_RESET}
          </button>
        </section>

        <section className="scenario-action-group space-y-2 border-t border-slate-200 pt-4">
          <h3 className="info-label text-slate-900">{SCENARIO_GROUP_SAVE}</h3>
          <p id="scenario-save-desc" className="body-copy text-sm text-slate-600">
            {SCENARIO_GROUP_SAVE_DESC}
          </p>
          <div className="flex flex-col gap-2 sm:flex-row sm:items-end">
            <div className="flex-1">
              <label htmlFor="scenario-save-label" className="sr-only">
                {SCENARIO_LABEL_PLACEHOLDER}
              </label>
              <input
                id="scenario-save-label"
                type="text"
                value={saveLabel}
                onChange={(event) => setSaveLabel(event.target.value)}
                placeholder={SCENARIO_LABEL_PLACEHOLDER}
                maxLength={SAVED_SCENARIO_LABEL_MAX}
                aria-describedby="scenario-save-desc"
                className="h-12 w-full rounded-lg border border-slate-300 bg-white px-3 text-base text-slate-950 focus-visible:outline focus-visible:outline-2 focus-visible:outline-lake-accent"
              />
            </div>
            <button
              type="button"
              className="action-button-primary w-full sm:w-auto"
              onClick={handleSave}
              disabled={!canSave}
              title={!canSave ? SCENARIO_SAVE_DISABLED_HINT : undefined}
              data-claro-target="scenario-save"
            >
              <Bookmark className="w-4 h-4" aria-hidden />
              {SCENARIO_SAVE}
            </button>
          </div>
        </section>

        <section
          className="scenario-action-group space-y-2 border-t border-slate-200 pt-4"
          data-claro-target="scenario-use-saved"
        >
          <h3 className="info-label text-slate-900">{SCENARIO_GROUP_USE_SAVED}</h3>
          <p id="scenario-use-saved-desc" className="body-copy text-sm text-slate-600">
            {SCENARIO_GROUP_USE_SAVED_DESC}
          </p>
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 shrink-0 text-lake-sectionCompare" aria-hidden />
            <label htmlFor="compare-scenario" className="sr-only">
              {SCENARIO_COMPARE_LABEL}
            </label>
            <select
              id="compare-scenario"
              value={compareScenarioId}
              onChange={(event) => onCompareChange(event.target.value)}
              aria-describedby="scenario-use-saved-desc"
              className="h-12 w-full rounded-lg border border-slate-300 bg-white px-3 text-base text-slate-950 focus-visible:outline focus-visible:outline-2 focus-visible:outline-lake-accent"
            >
              <option value="">{SCENARIO_COMPARE_PLACEHOLDER}</option>
              {lakeSavedScenarios.map((scenario) => (
                <option key={scenario.id} value={scenario.id}>
                  {formatSavedScenarioOption(scenario, system)}
                </option>
              ))}
            </select>
          </div>
          <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap">
            <button
              type="button"
              className="action-button w-full sm:w-auto"
              onClick={onLoad}
              disabled={!canUseSaved}
            >
              <Download className="w-4 h-4" aria-hidden />
              {SCENARIO_LOAD}
            </button>
            <button
              type="button"
              className="action-button-danger w-full sm:w-auto"
              onClick={onDeleteScenario}
              disabled={!canUseSaved}
            >
              <Trash2 className="w-4 h-4" aria-hidden />
              {SCENARIO_DELETE}
            </button>
          </div>
        </section>
      </div>

      {otherLakeSaveCount > 0 && (
        <p className="mt-4 text-sm text-slate-600">{SCENARIO_OTHER_LAKE_SAVES(otherLakeSaveCount)}</p>
      )}
      {actionStatus && (
        <p className="mt-3 text-sm text-slate-700" role="status">
          {actionStatus}
        </p>
      )}
    </div>
  );
}
