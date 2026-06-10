import { NAV_HOME } from "../../lib/copy";
import { ROUTES, navigateTo } from "../../lib/routes";
import { DashboardLogo } from "./DashboardLogo";

export function SiteBrand({
  showLabel = true,
  label = NAV_HOME,
  className = "",
  logoClassName = "h-9 w-9 sm:h-10 sm:w-10",
  onNavigate,
}) {
  const handleClick = () => {
    if (onNavigate) {
      onNavigate();
      return;
    }
    navigateTo(ROUTES.landing);
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      className={`inline-flex items-center gap-2.5 rounded-lg text-left transition hover:opacity-90 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-lake-accent ${className}`}
      aria-label={showLabel ? undefined : label}
    >
      <DashboardLogo className={`shrink-0 ${logoClassName}`} />
      {showLabel && (
        <span className="text-base font-semibold text-slate-900 sm:text-lg">{label}</span>
      )}
    </button>
  );
}
