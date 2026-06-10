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
    <div className="callout-amber flex gap-2.5 body-copy" role="status">
      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-lake-amber" aria-hidden />
      <p>{message}</p>
    </div>
  );
}
