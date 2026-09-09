import { Sparkles } from "lucide-react";
import { PARAMETER_PANEL_INTRO, SECTION_LABELS } from "../../lib/copy";
import { LINKED_SLIDER_PAIRS, PARAMETER_GROUPS } from "../../lib/constants";
import { HELP_CONTENT } from "../../lib/helpContent";
import { SECTION_ACCENTS } from "../../lib/theme";
import { SectionHeading } from "../ui/SectionHeading";
import { ParameterSlider } from "./ParameterSlider";

function getSliderBounds(config, featureKey, features) {
  const baseMin = Number(config?.slider?.min ?? 0);
  const baseMax = Number(config?.slider?.max ?? 100);
  const pair = LINKED_SLIDER_PAIRS.find(
    ({ minKey, maxKey }) => minKey === featureKey || maxKey === featureKey
  );
  if (!pair) return { min: baseMin, max: baseMax };

  const counterpartKey = pair.minKey === featureKey ? pair.maxKey : pair.minKey;
  const counterpartValue = Number(features?.[counterpartKey]);
  if (!Number.isFinite(counterpartValue)) return { min: baseMin, max: baseMax };

  if (pair.minKey === featureKey) {
    return { min: baseMin, max: Math.max(baseMin, Math.min(baseMax, counterpartValue)) };
  }
  return { min: Math.min(baseMax, Math.max(baseMin, counterpartValue)), max: baseMax };
}

// At xl, groups sit side by side on a 12-column grid. Each group of two sliders
// stacks (one column), so Oxygen / Temperature / Phosphorus each span 4 columns.
// Below xl, groups stack and the pair sits two-up from sm. Tailwind needs
// literal class names, hence the lookup tables.
const GROUP_ROWS = 2;
const SPAN_CLASS_BY_TWELFTHS = {
  3: "xl:col-span-3",
  4: "xl:col-span-4",
  6: "xl:col-span-6",
  8: "xl:col-span-8",
  9: "xl:col-span-9",
  12: "xl:col-span-12",
};
const COLUMNS_CLASS = {
  1: "xl:grid-cols-1",
  2: "xl:grid-cols-2",
  3: "xl:grid-cols-3",
  4: "xl:grid-cols-4",
};

function groupLayout(groups) {
  const columns = groups.map((group) => Math.ceil(group.keys.length / GROUP_ROWS));
  const totalColumns = columns.reduce((sum, count) => sum + count, 0);
  const evenSplit = totalColumns > 0 && 12 % totalColumns === 0;
  return groups.map((group, index) => {
    const spanClass = evenSplit
      ? SPAN_CLASS_BY_TWELFTHS[(12 / totalColumns) * columns[index]]
      : undefined;
    const columnsClass = COLUMNS_CLASS[columns[index]];
    if (!spanClass || !columnsClass) {
      return { ...group, spanClass: "xl:col-span-12", columnsClass: "xl:grid-cols-4" };
    }
    return { ...group, spanClass, columnsClass };
  });
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

  const grouped = groupLayout(
    PARAMETER_GROUPS.map((group) => ({
      ...group,
      keys: editableKeys.filter((key) => featureConfig.features[key]?.group === group.key),
    })).filter((group) => group.keys.length > 0)
  );

  return (
    <div
      data-claro-target="parameter-panel"
      className={`panel p-4 sm:p-5 ${SECTION_ACCENTS.parameters.panelAccentClass}`}
    >
      <div className="flex flex-col gap-2 lg:flex-row lg:flex-wrap lg:items-center lg:justify-between">
        <SectionHeading section="parameters" icon={Sparkles} help={HELP_CONTENT.parameters}>
          {SECTION_LABELS.parameters}
        </SectionHeading>
        <p className="body-copy max-w-2xl">{PARAMETER_PANEL_INTRO}</p>
      </div>
      <div className="mt-4 grid grid-cols-1 gap-5 xl:grid-cols-12 xl:gap-4">
        {grouped.map((group) => (
          <div key={group.key} className={`flex flex-col ${group.spanClass}`}>
            <h3 className="group-label-accent mb-3 self-start">{group.label}</h3>
            <div
              className={`grid flex-1 grid-cols-1 items-stretch gap-4 sm:grid-cols-2 ${group.columnsClass}`}
            >
              {group.keys.map((key) => {
                const config = featureConfig.features[key];
                const val = features[key] !== undefined ? features[key] : 0;
                const { min, max } = getSliderBounds(config, key, features);
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
