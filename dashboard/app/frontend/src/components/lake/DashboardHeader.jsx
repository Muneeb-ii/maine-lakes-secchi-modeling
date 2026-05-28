import {
  DASHBOARD_TAGLINE,
  DASHBOARD_TITLE,
  MODEL_FOOTNOTE,
  formatLakeContext,
} from "../../lib/copy";
import { LakeSearchCombobox } from "./LakeSearchCombobox";
import { LakeSupportNote } from "./LakeSupportNote";

export function DashboardHeader({ lakeId, lakeName, lakeSupport, searchProps }) {
  return (
    <header className="panel p-6 mb-2">
      <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <h1 className="display-title text-3xl lg:text-4xl">{DASHBOARD_TITLE}</h1>
          <p className="text-slate-300 mt-2 text-sm lg:text-base">{DASHBOARD_TAGLINE}</p>
          <p className="mt-3 text-sm text-slate-200">{formatLakeContext(lakeName, lakeId)}</p>
          <p className="mt-2 text-xs text-slate-500">{MODEL_FOOTNOTE}</p>
        </div>
        <div className="w-full lg:max-w-md shrink-0 space-y-3">
          <LakeSearchCombobox {...searchProps} />
          <LakeSupportNote lakeSupport={lakeSupport} />
        </div>
      </div>
    </header>
  );
}
