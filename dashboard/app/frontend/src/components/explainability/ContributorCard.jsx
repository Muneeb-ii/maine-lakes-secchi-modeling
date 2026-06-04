import { Minus, Plus } from "lucide-react";
import { formatSignedMeters, formatValueWithUnit } from "../../lib/formatters";

export function ContributorCard({ item, label, unit = "" }) {
  const isPositive = item.contribution >= 0;
  const Icon = isPositive ? Plus : Minus;
  const colorClass = isPositive ? "text-delta-up" : "text-delta-down";
  const displayLabel = label || item.feature;

  return (
    <div className="info-card">
      <div className="flex justify-between items-center gap-3">
        <span className="text-sm text-slate-200">{displayLabel}</span>
        <span className={`inline-flex items-center gap-1 text-sm font-medium ${colorClass}`}>
          <Icon className="w-3.5 h-3.5" aria-hidden />
          {formatSignedMeters(item.contribution)}
        </span>
      </div>
      <p className="mt-1 text-xs text-slate-400">
        Input:{" "}
        {item.rendered_value === null
          ? "aggregate"
          : formatValueWithUnit(Number(item.rendered_value), unit)}
      </p>
    </div>
  );
}
