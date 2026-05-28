import { Minus, Plus } from "lucide-react";
import { formatSignedMeters } from "../../lib/formatters";

export function ScenarioCompareBanner({ scenario, delta }) {
  if (!scenario) return null;

  const isPositive = typeof delta === "number" && delta > 0;
  const isNegative = typeof delta === "number" && delta < 0;
  const Icon = isPositive ? Plus : isNegative ? Minus : null;
  const colorClass = isPositive ? "text-delta-up" : isNegative ? "text-delta-down" : "text-slate-300";

  return (
    <div className="panel p-4 text-sm text-slate-200" role="status">
      <p>
        Comparing against saved scenario from{" "}
        <time dateTime={scenario.timestamp}>{new Date(scenario.timestamp).toLocaleString()}</time>
        .
      </p>
      <p className={`mt-2 inline-flex items-center gap-1 font-medium ${colorClass}`}>
        {Icon && <Icon className="w-4 h-4" aria-hidden />}
        Delta vs selected scenario: {formatSignedMeters(delta)}
      </p>
    </div>
  );
}
