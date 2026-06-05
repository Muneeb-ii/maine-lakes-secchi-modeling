import { DASHBOARD_TAGLINE, DASHBOARD_TITLE } from "../../lib/copy";
import { LakeSearchCombobox } from "./LakeSearchCombobox";
import { LakeSupportNote } from "./LakeSupportNote";

export function DashboardHeader({ lakeSupport, searchProps }) {
  return (
    <header className="panel mb-1 p-4 sm:p-5 lg:p-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between lg:gap-6">
        <div className="min-w-0">
          <h1 className="display-title text-2xl leading-tight sm:text-3xl lg:text-4xl">
            {DASHBOARD_TITLE}
          </h1>
          <p className="mt-2 text-base text-slate-700 lg:text-lg">{DASHBOARD_TAGLINE}</p>
        </div>
        <div className="w-full lg:max-w-md shrink-0 space-y-3">
          <LakeSearchCombobox {...searchProps} />
          <LakeSupportNote lakeSupport={lakeSupport} />
        </div>
      </div>
    </header>
  );
}
