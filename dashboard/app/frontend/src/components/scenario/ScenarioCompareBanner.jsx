import { Minus, Plus } from "lucide-react";
import {
  COMPARE_BANNER_DELTA,
  COMPARE_BANNER_INTRO,
  COMPARE_BANNER_SAVED_ON,
  COMPARE_BANNER_SAVED_VALUE,
} from "../../lib/copy";
import { formatMeters, formatSignedMeters } from "../../lib/formatters";
import { useUnitSystem } from "../../context/UnitSystemContext";

export function ScenarioCompareBanner({ scenario, delta, lakeName }) {
  const { system } = useUnitSystem();
  if (!scenario || typeof delta !== "number") return null;

  const isPositive = delta > 0;
  const isNegative = delta < 0;
  const Icon = isPositive ? Plus : isNegative ? Minus : null;
  const colorClass = isPositive ? "text-delta-up" : isNegative ? "text-delta-down" : "text-slate-700";
  const snapshotName = scenario.label || null;

  return (
    <div className="callout-compare panel p-4 body-copy" role="status">
      <p>
        {COMPARE_BANNER_INTRO}{" "}
        {snapshotName ? (
          <>
            <span className="font-medium">{snapshotName}</span>, {COMPARE_BANNER_SAVED_ON}{" "}
          </>
        ) : (
          <>a snapshot {COMPARE_BANNER_SAVED_ON} </>
        )}
        <time dateTime={scenario.timestamp}>{new Date(scenario.timestamp).toLocaleString()}</time>
        {lakeName ? ` for ${lakeName}` : ""}.
      </p>
      <p className="mt-2 text-slate-700">
        {COMPARE_BANNER_SAVED_VALUE}: {formatMeters(scenario.predictionMeters, system)}
      </p>
      <p className={`mt-2 inline-flex items-center gap-1 font-medium ${colorClass}`}>
        {Icon && <Icon className="w-4 h-4" aria-hidden />}
        {COMPARE_BANNER_DELTA}: {formatSignedMeters(delta, { absolute: true, system })}
      </p>
    </div>
  );
}
