import { PLAYGROUND_TAGLINE, PLAYGROUND_TITLE } from "../../lib/copy";
import { SECTION_ACCENTS } from "../../lib/theme";
import { LakeSearchCombobox } from "./LakeSearchCombobox";
import { LakeSupportNote } from "./LakeSupportNote";

export function DashboardHeader({ lakeSupport, searchProps }) {
  return (
    <header
      className={`panel mb-1 p-4 sm:p-5 lg:p-6 ${SECTION_ACCENTS.prediction.panelAccentClass}`}
    >
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between lg:gap-6">
        <div className="min-w-0">
          <h1 className="display-title text-2xl leading-tight sm:text-3xl lg:text-4xl">
            {PLAYGROUND_TITLE}
          </h1>
          <p className="body-copy mt-2">{PLAYGROUND_TAGLINE}</p>
        </div>
        <div className="relative z-10 w-full lg:max-w-md shrink-0 space-y-3" data-claro-target="lake-search">
          <LakeSearchCombobox {...searchProps} />
          <LakeSupportNote lakeSupport={lakeSupport} />
        </div>
      </div>
    </header>
  );
}
