import { Minus, Plus } from "lucide-react";
import {
  CONTRIBUTOR_AGGREGATE_VALUE,
  CONTRIBUTOR_CURRENT_VALUE,
} from "../../lib/copy";
import { getFriendlyFeatureLabel } from "../../lib/featureLabels";
import { formatSignedMeters, formatValueWithUnit } from "../../lib/formatters";

export function ContributorCard({ item, label, unit = "" }) {
  const isPositive = item.contribution >= 0;
  const Icon = isPositive ? Plus : Minus;
  const colorClass = isPositive ? "text-delta-up" : "text-delta-down";
  const displayLabel = getFriendlyFeatureLabel(item.feature, label);

  return (
    <div className="info-card">
      <div className="flex justify-between items-center gap-3">
        <span className="text-base text-slate-900">{displayLabel}</span>
        <span className={`inline-flex items-center gap-1 text-base font-medium ${colorClass}`}>
          <Icon className="w-3.5 h-3.5" aria-hidden />
          {formatSignedMeters(item.contribution, { absolute: true })}
        </span>
      </div>
      <p className="mt-1 text-sm text-slate-600">
        {CONTRIBUTOR_CURRENT_VALUE}:{" "}
        {item.rendered_value === null
          ? CONTRIBUTOR_AGGREGATE_VALUE
          : formatValueWithUnit(Number(item.rendered_value), unit)}
      </p>
    </div>
  );
}
