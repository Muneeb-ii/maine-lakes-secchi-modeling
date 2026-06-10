import { Waves } from "lucide-react";
import { PLAYGROUND_EYEBROW, PLAYGROUND_TAGLINE, PLAYGROUND_TITLE } from "../../lib/copy";
import { SECTION_ACCENTS } from "../../lib/theme";
import { LakeSearchCombobox } from "./LakeSearchCombobox";
import { LakeSupportNote } from "./LakeSupportNote";

export function DashboardHeader({ lakeSupport, searchProps }) {
  return (
    <header
      className={`panel mb-1 p-4 sm:p-5 lg:p-6 ${SECTION_ACCENTS.prediction.panelAccentClass}`}
    >
      <div className="hero-column-wash -mx-4 -mt-4 mb-4 overflow-hidden rounded-t-lg px-4 pb-4 pt-4 sm:-mx-5 sm:-mt-5 sm:px-5 sm:pt-5 lg:-mx-6 lg:-mt-6 lg:px-6 lg:pt-6">
        <p className="inline-flex items-center gap-2 rounded-full border border-lake-accent/25 bg-white px-3 py-1.5 text-sm font-semibold uppercase tracking-wide text-lake-accent">
          <Waves className="h-4 w-4" aria-hidden />
          {PLAYGROUND_EYEBROW}
        </p>
      </div>
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
