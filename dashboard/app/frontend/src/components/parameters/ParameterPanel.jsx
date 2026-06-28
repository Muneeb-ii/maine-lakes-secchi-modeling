import { Sparkles } from "lucide-react";
import { PARAMETER_PANEL_INTRO, SECTION_LABELS } from "../../lib/copy";
import { PARAMETER_GROUPS } from "../../lib/constants";
import { HELP_CONTENT } from "../../lib/helpContent";
import { SECTION_ACCENTS } from "../../lib/theme";
import { SectionHelp } from "../ui/SectionHelp";
import { SectionHeadingIcon } from "../ui/SectionHeadingIcon";
import { ParameterSlider } from "./ParameterSlider";

function getSliderBounds(config) {
  return {
    min: config?.slider?.min ?? 0,
    max: config?.slider?.max ?? 100,
  };
}

export function ParameterPanel({
  featureConfig,
  features,
  baseline,
  includedFeatures,
  sensitivityByFeature,
  sensitivityError,
  isCheckingSensitivity,
  onFeatureChange,
  onFeatureCommit,
  onFeatureIncludedChange,
}) {
  const editableKeys = featureConfig?.editable_features || [];

  const grouped = PARAMETER_GROUPS.map((group) => ({
    ...group,
    keys: editableKeys.filter((key) => featureConfig.features[key]?.group === group.key),
  })).filter((group) => group.keys.length > 0);

  return (
    <div
      data-claro-target="parameter-panel"
      className={`panel p-4 sm:p-5 ${SECTION_ACCENTS.parameters.panelAccentClass}`}
    >
      <div className="flex flex-col gap-2 lg:flex-row lg:flex-wrap lg:items-center lg:justify-between">
        <h2 className="section-heading">
          <SectionHeadingIcon section="parameters" icon={Sparkles} />
          {SECTION_LABELS.parameters}
          <SectionHelp content={HELP_CONTENT.parameters} />
        </h2>
        <p className="body-copy max-w-2xl">{PARAMETER_PANEL_INTRO}</p>
      </div>
      <div className="mt-4 space-y-5">
        {grouped.map((group) => (
          <div key={group.key}>
            <h3 className="group-label-accent mb-3">{group.label}</h3>
            <div className="grid grid-cols-1 items-stretch gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {group.keys.map((key) => {
                const config = featureConfig.features[key];
                const val = features[key] !== undefined ? features[key] : 0;
                const { min, max } = getSliderBounds(config);
                return (
                  <ParameterSlider
                    key={key}
                    featureKey={key}
                    config={config}
                    value={val}
                    baselineValue={baseline?.[key]}
                    included={includedFeatures?.includes(key)}
                    sensitivity={sensitivityByFeature?.[key]}
                    sensitivityError={sensitivityError}
                    isCheckingSensitivity={isCheckingSensitivity}
                    min={min}
                    max={max}
                    onChange={onFeatureChange}
                    onCommit={onFeatureCommit}
                    onIncludedChange={onFeatureIncludedChange}
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
