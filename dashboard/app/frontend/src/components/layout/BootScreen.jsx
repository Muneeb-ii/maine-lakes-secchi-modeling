import { BOOT_ERROR_TITLE, BOOT_LOADING, DASHBOARD_TITLE } from "../../lib/copy";

export function BootScreen({ state, error }) {
  if (state === "loading") {
    return (
      <div className="dashboard-bg flex min-h-screen items-center justify-center px-6">
        <div className="panel hero-wash-prediction panel-accent-left panel-accent-prediction max-w-md px-8 py-10 text-center">
          <div className="text-2xl font-semibold text-lake-accent">{DASHBOARD_TITLE}</div>
          <div className="mt-3 text-base text-slate-700">{BOOT_LOADING}</div>
        </div>
      </div>
    );
  }

  if (state === "error") {
    return (
      <div className="dashboard-bg flex min-h-screen items-center justify-center px-6">
        <div className="panel panel-accent-left panel-accent-error max-w-xl p-8">
          <h1 className="text-2xl font-semibold text-delta-down">{BOOT_ERROR_TITLE}</h1>
          <p className="mt-3 text-base text-slate-700">{error}</p>
        </div>
      </div>
    );
  }

  return null;
}
