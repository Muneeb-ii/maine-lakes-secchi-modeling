import { Minus, Plus } from "lucide-react";
import { COMPARE_BANNER_DELTA, COMPARE_BANNER_INTRO } from "../../lib/copy";
import { formatSignedMeters } from "../../lib/formatters";

export function ScenarioCompareBanner({ scenario, delta }) {
  if (!scenario) return null;

  const isPositive = typeof delta === "number" && delta > 0;
  const isNegative = typeof delta === "number" && delta < 0;
  const Icon = isPositive ? Plus : isNegative ? Minus : null;
  const colorClass = isPositive ? "text-delta-up" : isNegative ? "text-delta-down" : "text-slate-700";

  return (
    <div className="panel p-4 text-base text-slate-700" role="status">
      <p>
        {COMPARE_BANNER_INTRO}{" "}
        <time dateTime={scenario.timestamp}>{new Date(scenario.timestamp).toLocaleString()}</time>.
      </p>
      <p className={`mt-2 inline-flex items-center gap-1 font-medium ${colorClass}`}>
        {Icon && <Icon className="w-4 h-4" aria-hidden />}
        {COMPARE_BANNER_DELTA}: {formatSignedMeters(delta, { absolute: true })}
      </p>
    </div>
  );
}
