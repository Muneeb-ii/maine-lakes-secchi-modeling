import { AlertTriangle } from "lucide-react";
import { LAKE_SUPPORT_MESSAGES } from "../../lib/copy";

export function LakeSupportNote({ lakeSupport }) {
  if (!lakeSupport) return null;

  const { supported, isFallback } = lakeSupport;

  if (supported && !isFallback) return null;

  const message = isFallback
    ? LAKE_SUPPORT_MESSAGES.fallback
    : LAKE_SUPPORT_MESSAGES.unsupported;

  return (
    <div
      className="flex gap-2.5 rounded-lg border border-lake-amber/60 bg-lake-amber/10 px-3 py-2.5 text-sm text-slate-700 leading-relaxed"
      role="status"
    >
      <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5 text-slate-600" aria-hidden />
      <p>{message}</p>
    </div>
  );
}
