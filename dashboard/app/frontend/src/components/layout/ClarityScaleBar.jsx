import { CLARITY_BANDS } from "../../lib/constants";
import { LANDING_CLARITY_TITLE, SECCHI_DIRECTION_NOTE } from "../../lib/copy";
import { getClarityToneByKey } from "../../lib/theme";

const SEGMENT_CLASS = {
  turbid: "bg-delta-down",
  moderate: "bg-lake-amber",
  clearer: "bg-delta-up",
};

function bandThreshold(band, index) {
  if (index === 0) return `<${band.max} m`;
  if (!Number.isFinite(band.max)) {
    const prev = CLARITY_BANDS[index - 1];
    return `>${prev.max} m`;
  }
  const prev = CLARITY_BANDS[index - 1];
  return `${prev.max}–${band.max} m`;
}

export function ClarityScaleBar({ className = "" }) {
  return (
    <figure className={className}>
      <figcaption className="sr-only">
        {LANDING_CLARITY_TITLE}. {SECCHI_DIRECTION_NOTE}
      </figcaption>
      <p className="mb-2 section-subheading text-slate-900">{LANDING_CLARITY_TITLE}</p>
      <div
        className="flex h-3 overflow-hidden rounded-full border border-lake-border/80"
        role="img"
        aria-hidden="true"
      >
        {CLARITY_BANDS.map((band) => (
          <div key={band.tone} className={`flex-1 ${SEGMENT_CLASS[band.tone]}`} />
        ))}
      </div>
      <ul className="mt-2 grid grid-cols-3 gap-2" aria-label="Secchi clarity bands">
        {CLARITY_BANDS.map((band, index) => {
          const tone = getClarityToneByKey(band.tone);
          return (
            <li key={band.tone} className="text-center">
              <span className={`clarity-band-pill inline-block ${tone?.pillClass ?? ""}`}>
                {band.label}
              </span>
              <p className="body-copy mt-1">{bandThreshold(band, index)}</p>
            </li>
          );
        })}
      </ul>
      <p className="body-copy mt-2">{SECCHI_DIRECTION_NOTE}</p>
    </figure>
  );
}
