import { DASHBOARD_TITLE } from "../../lib/copy";

export function BootScreen({ state, error }) {
  if (state === "loading") {
    return (
      <div className="min-h-screen flex items-center justify-center dashboard-bg px-6">
        <div className="panel px-8 py-10 text-center max-w-md">
          <div className="text-xl font-semibold text-lake-accent">{DASHBOARD_TITLE}</div>
          <div className="mt-3 text-sm text-slate-400">Connecting to the lake inference service…</div>
        </div>
      </div>
    );
  }

  if (state === "error") {
    return (
      <div className="min-h-screen flex items-center justify-center dashboard-bg px-6">
        <div className="panel max-w-xl p-8">
          <h1 className="text-2xl font-semibold text-red-300">Could not start dashboard</h1>
          <p className="text-sm text-slate-300 mt-3">{error}</p>
        </div>
      </div>
    );
  }

  return null;
}
