import { MapPin } from "lucide-react";
import { LAKE_FIELD_LABELS, SECTION_LABELS } from "../../lib/copy";
import { HELP_CONTENT } from "../../lib/helpContent";
import { SECTION_ACCENTS } from "../../lib/theme";
import { SectionHelp } from "../ui/SectionHelp";
import { SectionHeadingIcon } from "../ui/SectionHeadingIcon";

export function LakeProfileCard({ baseline }) {
  return (
    <div
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
            <dt className="info-label">{LAKE_FIELD_LABELS.latitude}</dt>
            <dd className="info-value mt-0.5 tabular-nums">{baseline.LATITUDE?.toFixed(4)}</dd>
          </div>
          <div className="info-card-accent px-2.5 py-2">
            <dt className="info-label">{LAKE_FIELD_LABELS.longitude}</dt>
            <dd className="info-value mt-0.5 tabular-nums">{baseline.LONGITUDE?.toFixed(4)}</dd>
          </div>
          <div className="info-card-accent px-2.5 py-2">
            <dt className="info-label">{LAKE_FIELD_LABELS.areaAcres}</dt>
            <dd className="info-value mt-0.5 tabular-nums">
              {baseline.AREA_ACRES?.toLocaleString()}
            </dd>
          </div>
          <div className="info-card-accent px-2.5 py-2">
            <dt className="info-label">{LAKE_FIELD_LABELS.maxDepth}</dt>
            <dd className="info-value mt-0.5 tabular-nums">
              {baseline.DEPTH_MAX_FEET?.toFixed(1)}
            </dd>
          </div>
        </dl>
      )}
    </div>
  );
}
