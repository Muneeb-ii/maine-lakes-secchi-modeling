import { Activity, Beaker, Droplet, Gauge, Thermometer } from "lucide-react";
import { SLIDER_STARTING_VALUE } from "../../lib/copy";
import { getFriendlyFeatureLabel } from "../../lib/featureLabels";
import { formatValueWithUnit } from "../../lib/formatters";
import { hasFiniteSliderValue, resolveSliderNumericValue } from "../../lib/playgroundGuards";

const iconMap = { Beaker, Droplet, Activity, Gauge, Thermometer };

export function ParameterSlider({
  featureKey,
  config,
  value,
  baselineValue,
  included = true,
  onChange,
  onCommit,
  onIncludedChange,
  min,
  max,
}) {
  const Icon = iconMap[config?.icon] || Beaker;
  const unit = config?.unit || "";
  const label = getFriendlyFeatureLabel(featureKey, config?.label);
  const numericValue = resolveSliderNumericValue(value, min);
  const displayValue = hasFiniteSliderValue(value) ? Number(value) : NaN;
  const differsFromBaseline =
    baselineValue !== undefined &&
    hasFiniteSliderValue(value) &&
    Number.isFinite(Number(baselineValue)) &&
    Math.abs(Number(value) - Number(baselineValue)) > 0.001;
  const baselineText = differsFromBaseline
    ? `${SLIDER_STARTING_VALUE}: ${formatValueWithUnit(baselineValue, unit)}`
    : "\u00a0";

  return (
    <div
      className={`parameter-slider-card slider-group slider-group-compact ${
        included ? "" : "opacity-70"
      }`}
    >
      <div className="parameter-slider-header">
        <div className="flex min-w-0 items-start gap-1 sm:gap-2">
          <label className="touch-checkbox">
            <input
              type="checkbox"
              className="h-4 w-4 accent-lake-accent"
              checked={included}
              onChange={(event) => onIncludedChange(featureKey, event.target.checked)}
            />
            <span className="sr-only">Include {label} in prediction</span>
          </label>
          <Icon className="mt-2 h-4 w-4 shrink-0 text-slate-600 sm:mt-0.5" aria-hidden />
          <span className="min-w-0 pt-1.5 text-sm leading-5 text-slate-900 sm:pt-0">{label}</span>
        </div>
        <div className="parameter-slider-value">
          {formatValueWithUnit(displayValue, unit)}
        </div>
      </div>
      <input
        type="range"
        className="mt-2 w-full"
        min={min}
        max={max}
        step={config?.slider?.step ?? 0.1}
        value={numericValue}
        aria-label={`${label}${unit ? ` in ${unit}` : ""}`}
        aria-valuemin={min}
        aria-valuemax={max}
        aria-valuenow={numericValue}
        aria-valuetext={formatValueWithUnit(displayValue, unit)}
        disabled={!included}
        onChange={(event) => onChange(featureKey, event.target.value)}
        onPointerUp={() => onCommit(featureKey)}
        onKeyUp={(event) => {
          if (event.key === "Enter" || event.key === " ") onCommit(featureKey);
        }}
      />
      <p
        className={`parameter-slider-baseline ${differsFromBaseline ? "" : "invisible"}`}
        aria-hidden={!differsFromBaseline}
      >
        {baselineText}
      </p>
    </div>
  );
}
