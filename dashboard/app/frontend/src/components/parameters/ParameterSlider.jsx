import { Activity, Beaker, Droplet, Gauge, Thermometer } from "lucide-react";
import { SLIDER_STARTING_VALUE } from "../../lib/copy";
import { getFriendlyFeatureLabel } from "../../lib/featureLabels";
import { formatValueWithUnit } from "../../lib/formatters";

const iconMap = { Beaker, Droplet, Activity, Gauge, Thermometer };

export function ParameterSlider({ featureKey, config, value, baselineValue, onChange, min, max }) {
  const Icon = iconMap[config?.icon] || Beaker;
  const unit = config?.unit || "";
  const label = getFriendlyFeatureLabel(featureKey, config?.label);
  const differsFromBaseline =
    baselineValue !== undefined &&
    typeof value === "number" &&
    Math.abs(value - baselineValue) > 0.001;

  return (
    <div className="slider-group">
      <div className="flex justify-between items-start gap-3 text-base">
        <div className="flex items-center gap-2 text-slate-900 min-w-0">
          <Icon className="w-4 h-4 text-slate-600 shrink-0" aria-hidden />
          <span className="truncate">{label}</span>
        </div>
        <div className="font-mono text-lake-accent shrink-0 tabular-nums">
          {formatValueWithUnit(value, unit)}
        </div>
      </div>
      <input
        type="range"
        className="w-full mt-3"
        min={min}
        max={max}
        step={config?.slider?.step ?? 0.1}
        value={value}
        aria-label={`${label}${unit ? ` in ${unit}` : ""}`}
        aria-valuemin={min}
        aria-valuemax={max}
        aria-valuenow={value}
        aria-valuetext={formatValueWithUnit(value, unit)}
        onChange={(event) => onChange(featureKey, event.target.value)}
      />
      {differsFromBaseline && (
        <p className="mt-1.5 text-sm text-slate-600">
          {SLIDER_STARTING_VALUE}: {formatValueWithUnit(baselineValue, unit)}
        </p>
      )}
    </div>
  );
}
