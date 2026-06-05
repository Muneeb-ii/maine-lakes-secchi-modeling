import { Info, AlertTriangle } from "lucide-react";
import { LAKE_SUPPORT_MESSAGES } from "../../lib/copy";

export function LakeSupportNote({ lakeSupport }) {
  if (!lakeSupport) return null;

  const { supported, isFallback } = lakeSupport;

  let message = LAKE_SUPPORT_MESSAGES.unsupported;
  let variant = "caution";

  if (isFallback) {
    message = LAKE_SUPPORT_MESSAGES.fallback;
    variant = "caution";
  } else if (supported) {
    message = LAKE_SUPPORT_MESSAGES.supported;
    variant = "info";
  }

  const Icon = variant === "caution" ? AlertTriangle : Info;
  const borderClass =
    variant === "caution"
      ? "border-lake-amber/60 bg-lake-amber/10"
      : "border-lake-accent/30 bg-lake-accent/5";

  return (
    <div
      className={`flex gap-2.5 rounded-lg border px-3 py-2.5 text-sm text-slate-700 leading-relaxed ${borderClass}`}
      role="status"
    >
      <Icon className="w-4 h-4 shrink-0 mt-0.5 text-slate-600" aria-hidden />
      <p>{message}</p>
    </div>
  );
}
