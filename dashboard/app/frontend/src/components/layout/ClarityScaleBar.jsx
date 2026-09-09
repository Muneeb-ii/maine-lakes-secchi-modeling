import { CLARITY_BANDS } from "../../lib/constants";
import { LANDING_CLARITY_TITLE, SECCHI_DIRECTION_NOTE } from "../../lib/copy";
import { getClarityRangeLabel, getClarityToneByKey } from "../../lib/theme";
import { useUnitSystem } from "../../context/UnitSystemContext";

const SEGMENT_CLASS = {
  turbid: "bg-delta-down",
  moderate: "bg-lake-amber",
  clearer: "bg-delta-up",
};

function clarityMarkerPercent(meters) {
  if (meters < 2) return (Math.max(0, meters) / 2) * (100 / 3);
  if (meters < 4) return 100 / 3 + ((meters - 2) / 2) * (100 / 3);
  const t = Math.min(1, (meters - 4) / 6);
  return 200 / 3 + t * (100 / 3);
}

function ScaleTrack({ compact, markerPercent }) {
  return (
    <div className="relative">
      <div
        className={`flex overflow-hidden rounded-full border border-lake-border/80 ${compact ? "h-2.5" : "h-3"}`}
        role="img"
        aria-hidden="true"
      >
        {CLARITY_BANDS.map((band) => (
          <div key={band.tone} className={`flex-1 ${SEGMENT_CLASS[band.tone]}`} />
        ))}
      </div>
      {markerPercent !== null && (
        <div
          className="pointer-events-none absolute top-1/2 h-3.5 w-3.5 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-white bg-slate-900 shadow-sm"
          style={{ left: `${markerPercent}%` }}
        />
      )}
    </div>
  );
}

export function ClarityScaleBar({ className = "", valueMeters, compact = false }) {
  const { system } = useUnitSystem();
  const markerPercent = Number.isFinite(valueMeters) ? clarityMarkerPercent(valueMeters) : null;

  if (compact) {
    return (
      <figure className={className}>
        <figcaption className="sr-only">
          {LANDING_CLARITY_TITLE}. {SECCHI_DIRECTION_NOTE}
        </figcaption>
        <ScaleTrack compact markerPercent={markerPercent} />
        <ul
          className="mt-2 grid grid-cols-3 gap-2 text-center text-sm text-slate-600"
          aria-label="Secchi clarity bands"
        >
          {CLARITY_BANDS.map((band) => (
            <li key={band.tone}>
              <span className="font-semibold text-slate-800">{band.label}</span>
              <span className="block">{getClarityRangeLabel(band, system)}</span>
            </li>
          ))}
        </ul>
      </figure>
    );
  }

  return (
    <figure className={className}>
      <figcaption className="sr-only">
        {LANDING_CLARITY_TITLE}. {SECCHI_DIRECTION_NOTE}
      </figcaption>
      <p className="mb-2 section-subheading text-slate-900">{LANDING_CLARITY_TITLE}</p>
      <ScaleTrack compact={false} markerPercent={markerPercent} />
      <ul className="mt-2 grid grid-cols-3 gap-2" aria-label="Secchi clarity bands">
        {CLARITY_BANDS.map((band) => {
          const tone = getClarityToneByKey(band.tone);
          return (
            <li key={band.tone} className="text-center">
              <span className={`clarity-band-pill inline-block ${tone?.pillClass ?? ""}`}>
                {band.label}
              </span>
              <p className="body-copy mt-1">{getClarityRangeLabel(band, system)}</p>
            </li>
          );
        })}
      </ul>
      <p className="body-copy mt-2">{SECCHI_DIRECTION_NOTE}</p>
    </figure>
  );
}
