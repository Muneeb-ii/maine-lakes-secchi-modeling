import { Home } from "lucide-react";
import { NAV_HOME } from "../../lib/copy";
import { ROUTES, navigateTo } from "../../lib/routes";

export function InfoPageNav({ className = "mb-8" }) {
  return (
    <button
      type="button"
      onClick={() => navigateTo(ROUTES.landing)}
      className={`action-button w-fit ${className}`}
    >
      <Home className="h-4 w-4" aria-hidden />
      {NAV_HOME}
    </button>
  );
}
