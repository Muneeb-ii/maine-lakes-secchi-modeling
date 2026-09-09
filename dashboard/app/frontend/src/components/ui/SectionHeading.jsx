import { SectionHelp } from "./SectionHelp";
import { SectionHeadingIcon } from "./SectionHeadingIcon";

export function SectionHeading({
  section,
  icon,
  children,
  help,
  as: Tag = "h2",
  className = "",
}) {
  return (
    <Tag className={`section-heading ${className}`.trim()}>
      <SectionHeadingIcon section={section} icon={icon} />
      <span className="min-w-0 leading-none">{children}</span>
      {help ? (
        <SectionHelp
          content={help}
          className="ml-0 h-10 w-10 items-center justify-center p-0"
        />
      ) : null}
    </Tag>
  );
}
