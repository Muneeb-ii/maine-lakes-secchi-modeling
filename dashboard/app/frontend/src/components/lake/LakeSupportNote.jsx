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
      ? "border-amber-500/35 bg-amber-950/20"
      : "border-lake-accent/30 bg-lake-accent/5";

  return (
    <div
      className={`flex gap-2.5 rounded-lg border px-3 py-2.5 text-xs text-slate-300 leading-relaxed ${borderClass}`}
      role="status"
    >
      <Icon className="w-4 h-4 shrink-0 mt-0.5 text-slate-400" aria-hidden />
      <p>{message}</p>
    </div>
  );
}
