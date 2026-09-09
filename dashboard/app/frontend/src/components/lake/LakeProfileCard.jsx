import { MapPin } from "lucide-react";
import { useUnitSystem } from "../../context/UnitSystemContext";
import {
  LAKE_CHEMISTRY_HEADING,
  LAKE_CHEMISTRY_NOTE,
  LAKE_CHEMISTRY_UNAVAILABLE,
  getLakeFieldLabels,
  SECTION_LABELS,
} from "../../lib/copy";
import { LAKE_CHEMISTRY_GROUP } from "../../lib/constants";
import { getFriendlyFeatureLabel } from "../../lib/featureLabels";
import { formatValueWithUnit } from "../../lib/formatters";
import { HELP_CONTENT } from "../../lib/helpContent";
import { SECTION_ACCENTS } from "../../lib/theme";
import { toDisplay } from "../../lib/units";
import { SectionHeading } from "../ui/SectionHeading";

function lakeChemistryKeys(featureConfig) {
  const locked = featureConfig?.locked_features || [];
  return locked.filter((key) => featureConfig?.features?.[key]?.group === LAKE_CHEMISTRY_GROUP);
}

export function LakeProfileCard({ baseline, featureConfig }) {
  const { system } = useUnitSystem();
  const labels = getLakeFieldLabels(system);
  const chemistryKeys = lakeChemistryKeys(featureConfig);
  // Canonical values stay acres/ft; convert only for display.
  const areaDisplay =
    typeof baseline?.AREA_ACRES === "number"
      ? toDisplay(baseline.AREA_ACRES, "acres", system).toLocaleString(undefined, {
          maximumFractionDigits: 1,
        })
      : undefined;
  const depthDisplay =
    typeof baseline?.DEPTH_MAX_FEET === "number"
      ? toDisplay(baseline.DEPTH_MAX_FEET, "ft", system).toFixed(1)
      : undefined;

  return (
    <div
      data-claro-target="lake-profile"
      className={`panel h-full p-4 sm:p-5 ${SECTION_ACCENTS.lake.panelAccentClass}`}
    >
      <SectionHeading section="lake" icon={MapPin} help={HELP_CONTENT.lakeProfile}>
        {SECTION_LABELS.lakeProfile}
      </SectionHeading>
      {baseline && (
        <>
          <dl className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4 xl:grid-cols-2">
            <div className="info-card-accent px-2.5 py-2">
              <dt className="info-label xl:text-base">{labels.latitude}</dt>
              <dd className="info-value mt-0.5 tabular-nums xl:text-xl">{baseline.LATITUDE?.toFixed(4)}</dd>
            </div>
            <div className="info-card-accent px-2.5 py-2">
              <dt className="info-label xl:text-base">{labels.longitude}</dt>
              <dd className="info-value mt-0.5 tabular-nums xl:text-xl">{baseline.LONGITUDE?.toFixed(4)}</dd>
            </div>
            <div className="info-card-accent px-2.5 py-2">
              <dt className="info-label xl:text-base">{labels.areaAcres}</dt>
              <dd className="info-value mt-0.5 tabular-nums xl:text-xl">{areaDisplay}</dd>
            </div>
            <div className="info-card-accent px-2.5 py-2">
              <dt className="info-label xl:text-base">{labels.maxDepth}</dt>
              <dd className="info-value mt-0.5 tabular-nums xl:text-xl">{depthDisplay}</dd>
            </div>
          </dl>
          {chemistryKeys.length > 0 && (
            <section aria-labelledby="lake-chemistry-heading" className="mt-4">
              <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
                <h3 id="lake-chemistry-heading" className="group-label-accent">
                  {LAKE_CHEMISTRY_HEADING}
                </h3>
                <p className="text-sm text-slate-600 sm:text-base">{LAKE_CHEMISTRY_NOTE}</p>
              </div>
              <dl className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4 xl:grid-cols-2">
                {chemistryKeys.map((key) => {
                  const config = featureConfig.features[key];
                  const value = baseline[key];
                  const hasValue = typeof value === "number" && Number.isFinite(value);
                  const label = getFriendlyFeatureLabel(key, config?.label, system);
                  const labelWithUnit = config?.unit ? `${label} (${config.unit})` : label;
                  return (
                    <div key={key} className="info-card px-2.5 py-2">
                      <dt className="info-label xl:text-base">{labelWithUnit}</dt>
                      <dd className="info-value mt-0.5 tabular-nums xl:text-xl">
                        {hasValue ? formatValueWithUnit(value, "") : LAKE_CHEMISTRY_UNAVAILABLE}
                      </dd>
                    </div>
                  );
                })}
              </dl>
            </section>
          )}
        </>
      )}
    </div>
  );
}
