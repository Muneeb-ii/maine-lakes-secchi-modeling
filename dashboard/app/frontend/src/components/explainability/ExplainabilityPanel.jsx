import { useEffect, useMemo, useState } from "react";
import { Gauge } from "lucide-react";
import { formatSignedMeters } from "../../lib/formatters";
import {
  ARIA_CONTRIBUTION_CLEARER,
  ARIA_CONTRIBUTION_MURKIER,
  EXPLAINABILITY_ADJUSTMENTS_HEADING,
  EXPLAINABILITY_HIDE_ALL,
  EXPLAINABILITY_LAKE_CONTEXT_HEADING,
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
import { SectionHelp } from "../ui/SectionHelp";
import { SectionHeadingIcon } from "../ui/SectionHeadingIcon";

function CompactContributorRow({ item, featureConfig, rankClass = "" }) {
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
        {getFriendlyFeatureLabel(item.feature, featureConfig?.features?.[item.feature]?.label)}
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
        {formatSignedMeters(item.contribution)}
      </span>
    </div>
  );
}

export function ExplainabilityPanel({ forecast, featureConfig, lakeId }) {
  const [expanded, setExpanded] = useState(false);
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

  const topEditable = useMemo(() => editableWaterfall.slice(0, 3), [editableWaterfall]);
  const remainingEditable = useMemo(() => editableWaterfall.slice(3), [editableWaterfall]);

  useEffect(() => {
    setExpanded(false);
  }, [lakeId, forecast?.predictionMeters, forecast?.modelVersion]);

  const hasDrivers = contextWaterfall.length > 0 || editableWaterfall.length > 0;

  return (
    <div
      className={`panel flex h-full flex-col p-4 sm:p-5 ${SECTION_ACCENTS.drivers.panelAccentClass}`}
    >
      <h2 className="section-heading">
        <SectionHeadingIcon section="drivers" icon={Gauge} />
        {SECTION_LABELS.explainability}
        <SectionHelp content={HELP_CONTENT.explainability} />
      </h2>

      {hasDrivers ? (
        <div className="mt-4 space-y-4">
          {contextWaterfall.length > 0 && (
            <section aria-labelledby="explainability-lake-context-heading">
              <h3
                id="explainability-lake-context-heading"
                className="section-subheading"
              >
                {EXPLAINABILITY_LAKE_CONTEXT_HEADING}
              </h3>
              <div className="mt-2 space-y-0">
                {contextWaterfall.map((item) => (
                  <CompactContributorRow
                    key={item.feature}
                    item={item}
                    featureConfig={featureConfig}
                  />
                ))}
              </div>
            </section>
          )}

          {editableWaterfall.length > 0 && (
            <section aria-labelledby="explainability-adjustments-heading">
              <h3
                id="explainability-adjustments-heading"
                className="section-subheading"
              >
                {EXPLAINABILITY_ADJUSTMENTS_HEADING}
              </h3>
              <div className="mt-2 space-y-0">
                {topEditable.map((item, index) => (
                  <CompactContributorRow
                    key={item.feature}
                    item={item}
                    featureConfig={featureConfig}
                    rankClass={`driver-row-ranked-${index + 1}`}
                  />
                ))}
              </div>

              {remainingEditable.length > 0 && (
                <>
                  <button
                    type="button"
                    className="mt-3 rounded px-1 text-base font-semibold text-lake-accent transition hover:text-blue-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-lake-accent"
                    onClick={() => setExpanded((previous) => !previous)}
                    aria-expanded={expanded}
                  >
                    {expanded ? EXPLAINABILITY_HIDE_ALL : EXPLAINABILITY_SHOW_ALL}
                  </button>
                  {expanded && (
                    <div className="mt-2 space-y-0">
                      {remainingEditable.map((item) => (
                        <CompactContributorRow
                          key={item.feature}
                          item={item}
                          featureConfig={featureConfig}
                        />
                      ))}
                    </div>
                  )}
                </>
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
