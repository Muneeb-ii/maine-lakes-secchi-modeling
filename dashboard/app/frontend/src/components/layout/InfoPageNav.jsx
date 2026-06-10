import { SiteBrand } from "../brand/SiteBrand";

const EYEBROW_TONES = {
  accent: "border-lake-accent/25 bg-white text-lake-accent",
  amber: "border-lake-amber/30 bg-white text-lake-amber",
};

export function InfoPageNav({
  className = "mb-8",
  eyebrow,
  eyebrowTone = "accent",
  eyebrowIcon: EyebrowIcon,
}) {
  if (!eyebrow) {
    return <SiteBrand className={className} />;
  }

  const toneClass = EYEBROW_TONES[eyebrowTone] ?? EYEBROW_TONES.accent;

  return (
    <div className={`flex flex-wrap items-center justify-between gap-3 ${className}`}>
      <SiteBrand className="mb-0" />
      <p
        className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-sm font-semibold uppercase tracking-wide ${toneClass}`}
      >
        {EyebrowIcon ? <EyebrowIcon className="h-4 w-4 shrink-0" aria-hidden /> : null}
        {eyebrow}
      </p>
    </div>
  );
}
