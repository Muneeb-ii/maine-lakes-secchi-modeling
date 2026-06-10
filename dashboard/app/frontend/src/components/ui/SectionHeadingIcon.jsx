import { SECTION_ACCENTS } from "../../lib/theme";

export function SectionHeadingIcon({ section, icon: Icon, className = "" }) {
  const accent = SECTION_ACCENTS[section];
  if (!accent || !Icon) return null;

  return (
    <span className={`${accent.badgeClass} ${className}`}>
      <Icon className={`h-4 w-4 ${accent.iconClass}`} aria-hidden />
    </span>
  );
}
