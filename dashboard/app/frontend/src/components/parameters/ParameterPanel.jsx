import { Sparkles } from "lucide-react";
import { SECTION_LABELS } from "../../lib/copy";
import { PARAMETER_GROUPS } from "../../lib/constants";
import { HELP_CONTENT } from "../../lib/helpContent";
import { SectionHelp } from "../ui/SectionHelp";
import { ParameterSlider } from "./ParameterSlider";

function getSliderBounds(key, config, baseline) {
  let sMin = config?.slider?.min ?? 0;
  let sMax = config?.slider?.max ?? 100;
  if (baseline && baseline[key] > sMax) sMax = baseline[key] * 1.5;
  if (baseline && baseline[key] < sMin) sMin = baseline[key] * 0.5;
  return { min: sMin, max: sMax };
}

export function ParameterPanel({ featureConfig, features, baseline, onFeatureChange }) {
  const editableKeys = featureConfig?.editable_features || [];

  const grouped = PARAMETER_GROUPS.map((group) => ({
    ...group,
    keys: editableKeys.filter((key) => featureConfig.features[key]?.group === group.key),
  })).filter((group) => group.keys.length > 0);

  return (
    <div className="panel p-5 max-h-none xl:max-h-[480px] xl:overflow-y-auto">
      <h2 className="section-heading">
        <Sparkles className="w-4 h-4" aria-hidden />
        {SECTION_LABELS.parameters}
        <SectionHelp content={HELP_CONTENT.parameters} />
      </h2>
      <p className="mt-2 text-xs text-slate-400 mb-4">
        Adjust water chemistry and temperature to explore clarity outcomes.
      </p>
      <div className="space-y-6">
        {grouped.map((group) => (
          <div key={group.key}>
            <h3 className="text-xs font-semibold text-slate-500 mb-4">
              {group.label}
            </h3>
            <div className="space-y-5">
              {group.keys.map((key) => {
                const config = featureConfig.features[key];
                const val = features[key] !== undefined ? features[key] : 0;
                const { min, max } = getSliderBounds(key, config, baseline);
                return (
                  <ParameterSlider
                    key={key}
                    featureKey={key}
                    config={config}
                    value={val}
                    baselineValue={baseline?.[key]}
                    min={min}
                    max={max}
                    onChange={onFeatureChange}
                  />
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
