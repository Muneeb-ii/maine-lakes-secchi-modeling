import { MapPin } from "lucide-react";
import { useUnitSystem } from "../../context/UnitSystemContext";
import { getLakeFieldLabels, SECTION_LABELS } from "../../lib/copy";
import { HELP_CONTENT } from "../../lib/helpContent";
import { SECTION_ACCENTS } from "../../lib/theme";
import { toDisplay } from "../../lib/units";
import { SectionHelp } from "../ui/SectionHelp";
import { SectionHeadingIcon } from "../ui/SectionHeadingIcon";

export function LakeProfileCard({ baseline }) {
  const { system } = useUnitSystem();
  const labels = getLakeFieldLabels(system);
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
      <div className="section-heading">
        <SectionHeadingIcon section="lake" icon={MapPin} />
        {SECTION_LABELS.lakeProfile}
        <SectionHelp content={HELP_CONTENT.lakeProfile} />
      </div>
      {baseline && (
        <dl className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4 xl:grid-cols-2">
          <div className="info-card-accent px-2.5 py-2">
            <dt className="info-label">{labels.latitude}</dt>
            <dd className="info-value mt-0.5 tabular-nums">{baseline.LATITUDE?.toFixed(4)}</dd>
          </div>
          <div className="info-card-accent px-2.5 py-2">
            <dt className="info-label">{labels.longitude}</dt>
            <dd className="info-value mt-0.5 tabular-nums">{baseline.LONGITUDE?.toFixed(4)}</dd>
          </div>
          <div className="info-card-accent px-2.5 py-2">
            <dt className="info-label">{labels.areaAcres}</dt>
            <dd className="info-value mt-0.5 tabular-nums">{areaDisplay}</dd>
          </div>
          <div className="info-card-accent px-2.5 py-2">
            <dt className="info-label">{labels.maxDepth}</dt>
            <dd className="info-value mt-0.5 tabular-nums">{depthDisplay}</dd>
          </div>
        </dl>
      )}
    </div>
  );
}
