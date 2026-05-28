import { MapPin } from "lucide-react";
import {
  LAKE_FIELD_LABELS,
  LAKE_PROFILE_INTRO,
  SECTION_LABELS,
} from "../../lib/copy";
import { HELP_CONTENT } from "../../lib/helpContent";
import { SectionHelp } from "../ui/SectionHelp";

export function LakeProfileCard({ baseline }) {
  return (
    <div className="panel p-5">
      <div className="section-heading">
        <MapPin className="w-4 h-4 text-lake-accent" aria-hidden />
        {SECTION_LABELS.lakeProfile}
        <SectionHelp content={HELP_CONTENT.lakeProfile} />
      </div>
      <p className="mt-3 text-xs text-slate-400">{LAKE_PROFILE_INTRO}</p>
      {baseline && (
        <div className="grid grid-cols-2 gap-3 mt-4">
          <div className="info-card">
            <div className="info-label">{LAKE_FIELD_LABELS.latitude}</div>
            <div className="info-value">{baseline.LATITUDE?.toFixed(4)}</div>
          </div>
          <div className="info-card">
            <div className="info-label">{LAKE_FIELD_LABELS.longitude}</div>
            <div className="info-value">{baseline.LONGITUDE?.toFixed(4)}</div>
          </div>
          <div className="info-card">
            <div className="info-label">{LAKE_FIELD_LABELS.areaAcres}</div>
            <div className="info-value">{baseline.AREA_ACRES?.toLocaleString()}</div>
          </div>
          <div className="info-card">
            <div className="info-label">{LAKE_FIELD_LABELS.maxDepth}</div>
            <div className="info-value">{baseline.DEPTH_MAX_FEET?.toFixed(1)}</div>
          </div>
        </div>
      )}
    </div>
  );
}
