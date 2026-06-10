import { RefreshCw } from "lucide-react";
import {
  INFO_PAGE_IN_PROGRESS_NOTICE,
  SHOW_INFO_PAGES_IN_PROGRESS_NOTICE,
} from "../../lib/siteStatus";

export function PageInProgressNotice({ className = "mb-5" }) {
  if (!SHOW_INFO_PAGES_IN_PROGRESS_NOTICE) {
    return null;
  }

  const { title, body } = INFO_PAGE_IN_PROGRESS_NOTICE;

  return (
    <div className={`callout-amber flex gap-2.5 body-copy ${className}`} role="status">
      <RefreshCw className="mt-0.5 h-4 w-4 shrink-0 text-lake-amber" aria-hidden />
      <p>
        <span className="font-semibold text-slate-900">{title}.</span> {body}
      </p>
    </div>
  );
}
