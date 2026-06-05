import { Minus, Plus } from "lucide-react";
import {
  CONTRIBUTOR_AGGREGATE_VALUE,
  CONTRIBUTOR_CURRENT_VALUE,
} from "../../lib/copy";
import { getFriendlyFeatureLabel } from "../../lib/featureLabels";
import { formatSignedMeters, formatValueWithUnit } from "../../lib/formatters";
import { getContributionDisplay } from "../../lib/playgroundGuards";

const CONTRIBUTION_ICONS = { plus: Plus, minus: Minus };

export function ContributorCard({ item, label, unit = "" }) {
  const { icon, tone } = getContributionDisplay(item.contribution);
  const Icon = icon ? CONTRIBUTION_ICONS[icon] : null;
  const colorClass =
    tone === "up"
      ? "text-delta-up"
      : tone === "down"
        ? "text-delta-down"
        : "text-slate-600";
  const displayLabel = getFriendlyFeatureLabel(item.feature, label);

  return (
    <div className="info-card">
      <div className="flex justify-between items-center gap-3">
        <span className="text-base text-slate-900">{displayLabel}</span>
        <span className={`inline-flex items-center gap-1 text-base font-medium ${colorClass}`}>
          {Icon ? <Icon className="w-3.5 h-3.5" aria-hidden /> : null}
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
