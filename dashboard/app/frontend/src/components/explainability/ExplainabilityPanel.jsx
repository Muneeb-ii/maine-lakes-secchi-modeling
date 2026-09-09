import { useEffect, useMemo, useState } from "react";
import { Gauge } from "lucide-react";
import { formatSignedMeters } from "../../lib/formatters";
import {
  ARIA_CONTRIBUTION_CLEARER,
  ARIA_CONTRIBUTION_MURKIER,
  EXPLAINABILITY_ADJUSTMENTS_HEADING,
  EXPLAINABILITY_HIDE_ALL,
  EXPLAINABILITY_LAKE_CONTEXT_HEADING,
  EXPLAINABILITY_LAKE_CONTEXT_NOTE,
  EXPLAINABILITY_MISSING,
  EXPLAINABILITY_SHOW_ALL,
  SECTION_LABELS,
} from "../../lib/copy";
import {
  EXPLAINABILITY_LAKE_CONTEXT_FEATURES,
  getFriendlyFeatureLabel,
} from "../../lib/featureLabels";
import { getContributionDisplay } from "../../lib/playgroundGuards";
import { HELP_CONTENT } from "../../lib/helpContent";
import { SECTION_ACCENTS } from "../../lib/theme";
import { useUnitSystem } from "../../context/UnitSystemContext";
import { SectionHeading } from "../ui/SectionHeading";

function CompactContributorRow({ item, featureConfig, system, rankClass = "" }) {
  const { tone } = getContributionDisplay(item.contribution);
  const toneClass =
    tone === "up"
      ? "text-delta-up"
      : tone === "down"
        ? "text-delta-down"
        : "text-slate-600";

  return (
    <div
      className={`flex justify-between gap-4 border-b border-slate-200 py-1.5 text-base text-slate-700 last:border-0 ${rankClass}`}
    >
      <span>
        {getFriendlyFeatureLabel(item.feature, featureConfig?.features?.[item.feature]?.label, system)}
      </span>
      <span
        className={toneClass}
        aria-label={
          tone === "neutral"
            ? undefined
            : tone === "up"
              ? ARIA_CONTRIBUTION_CLEARER
              : ARIA_CONTRIBUTION_MURKIER
        }
      >
        {formatSignedMeters(item.contribution, { system })}
      </span>
    </div>
  );
}

export function ExplainabilityPanel({ forecast, featureConfig, lakeId }) {
  const { system } = useUnitSystem();
  const [lakeExpanded, setLakeExpanded] = useState(false);
  const lakeContextFeatures = useMemo(
    () => new Set(EXPLAINABILITY_LAKE_CONTEXT_FEATURES),
    []
  );
  const editableFeatures = useMemo(
    () => new Set(featureConfig?.editable_features || []),
    [featureConfig]
  );

  const waterfall = forecast?.explainability?.waterfall || [];

  const contextWaterfall = useMemo(() => {
    return waterfall
      .filter((item) => lakeContextFeatures.has(item.feature))
      .sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution));
  }, [lakeContextFeatures, waterfall]);

  const editableWaterfall = useMemo(() => {
    return waterfall
      .filter((item) => editableFeatures.has(item.feature))
      .sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution));
  }, [editableFeatures, waterfall]);

  useEffect(() => {
    setLakeExpanded(false);
  }, [lakeId, forecast?.predictionMeters, forecast?.modelVersion]);

  const hasDrivers = contextWaterfall.length > 0 || editableWaterfall.length > 0;

  return (
    <div
      data-claro-target="drivers-panel"
      className={`panel flex h-full flex-col p-4 sm:p-5 ${SECTION_ACCENTS.drivers.panelAccentClass}`}
    >
      <SectionHeading section="drivers" icon={Gauge} help={HELP_CONTENT.explainability}>
        {SECTION_LABELS.explainability}
      </SectionHeading>

      {hasDrivers ? (
        <div className="mt-4 space-y-4">
          {editableWaterfall.length > 0 && (
            <section aria-labelledby="explainability-adjustments-heading">
              <h3
                id="explainability-adjustments-heading"
                className="section-subheading"
              >
                {EXPLAINABILITY_ADJUSTMENTS_HEADING}
              </h3>
              <div className="mt-2 space-y-0">
                {editableWaterfall.map((item, index) => (
                  <CompactContributorRow
                    key={item.feature}
                    item={item}
                    featureConfig={featureConfig}
                    system={system}
                    rankClass={index < 3 ? `driver-row-ranked-${index + 1}` : ""}
                  />
                ))}
              </div>
            </section>
          )}

          {contextWaterfall.length > 0 && (
            <section aria-labelledby="explainability-lake-context-heading">
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <h3
                  id="explainability-lake-context-heading"
                  className="section-subheading"
                >
                  {EXPLAINABILITY_LAKE_CONTEXT_HEADING}
                </h3>
                <button
                  type="button"
                  className="rounded px-1 text-base font-semibold text-lake-accent transition hover:text-blue-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-lake-accent"
                  onClick={() => setLakeExpanded((previous) => !previous)}
                  aria-expanded={lakeExpanded}
                >
                  {lakeExpanded ? EXPLAINABILITY_HIDE_ALL : EXPLAINABILITY_SHOW_ALL}
                </button>
              </div>
              <p className="mt-1 text-base text-slate-600">{EXPLAINABILITY_LAKE_CONTEXT_NOTE}</p>
              {lakeExpanded && (
                <div className="mt-2 space-y-0">
                  {contextWaterfall.map((item) => (
                    <CompactContributorRow
                      key={item.feature}
                      item={item}
                      featureConfig={featureConfig}
                      system={system}
                    />
                  ))}
                </div>
              )}
            </section>
          )}
        </div>
      ) : (
        <p className="mt-4 text-base text-lake-amber">{EXPLAINABILITY_MISSING}</p>
      )}
    </div>
  );
}
