import { useEffect, useId, useMemo, useState } from "react";
import { Activity, Beaker, Droplet, Gauge, Thermometer } from "lucide-react";
import { SLIDER_STARTING_VALUE, SLIDER_VALUE_ERROR } from "../../lib/copy";
import { FEATURE_HELP_CONTENT, getFriendlyFeatureLabel } from "../../lib/featureLabels";
import { formatValueWithUnit } from "../../lib/formatters";
import { hasFiniteSliderValue, resolveSliderNumericValue } from "../../lib/playgroundGuards";
import { PARAMETER_ICON_COLORS } from "../../lib/theme";
import { SectionHelp } from "../ui/SectionHelp";

const iconMap = { Beaker, Droplet, Activity, Gauge, Thermometer };

function formatInputValue(value) {
  if (!hasFiniteSliderValue(value)) return "";
  return String(Number(value));
}

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
  const inputId = useId();
  const Icon = iconMap[config?.icon] || Beaker;
  const unit = config?.unit || "";
  const label = getFriendlyFeatureLabel(featureKey, config?.label);
  const numericValue = resolveSliderNumericValue(value, min);
  const displayValue = hasFiniteSliderValue(value) ? Number(value) : NaN;
  const [draftValue, setDraftValue] = useState(() => formatInputValue(value));
  const [inputError, setInputError] = useState("");
  const numericMin = Number(min);
  const numericMax = Number(max);
  const step = config?.slider?.step ?? 0.1;
  const errorMessage = useMemo(
    () => SLIDER_VALUE_ERROR(numericMin, numericMax, unit),
    [numericMin, numericMax, unit]
  );

  useEffect(() => {
    setDraftValue(formatInputValue(value));
    setInputError("");
  }, [value]);

  const validateDraft = (nextDraft) => {
    if (nextDraft.trim() === "") return errorMessage;
    const nextValue = Number(nextDraft);
    if (!Number.isFinite(nextValue) || nextValue < numericMin || nextValue > numericMax) {
      return errorMessage;
    }
    return "";
  };

  const applyTypedValue = (nextDraft, shouldCommit = false) => {
    const validationError = validateDraft(nextDraft);
    setInputError(validationError);
    if (validationError) return;
    onChange(featureKey, Number(nextDraft));
    if (shouldCommit) onCommit(featureKey);
  };
  const differsFromBaseline =
    baselineValue !== undefined &&
    hasFiniteSliderValue(value) &&
    Number.isFinite(Number(baselineValue)) &&
    Math.abs(Number(value) - Number(baselineValue)) > 0.001;
  const baselineText = differsFromBaseline
    ? `${SLIDER_STARTING_VALUE}: ${formatValueWithUnit(baselineValue, unit)}`
    : "\u00a0";
  const rangeSpan = numericMax - numericMin;
  const rangePercent =
    rangeSpan > 0 ? `${((numericValue - numericMin) / rangeSpan) * 100}%` : "0%";

  return (
    <div
      className={`parameter-slider-card slider-group slider-group-compact ${
        included ? "" : "opacity-70"
      } ${differsFromBaseline ? "parameter-slider-changed" : ""}`}
    >
      <div className="parameter-slider-header">
        <div className="flex min-w-0 items-start gap-1 sm:gap-2">
          <label className="touch-checkbox" data-claro-target="parameter-include">
            <input
              type="checkbox"
              className="h-4 w-4 accent-lake-accent"
              checked={included}
              onChange={(event) => onIncludedChange(featureKey, event.target.checked)}
            />
            <span className="sr-only">Include {label} in prediction</span>
          </label>
          <Icon
            className={`mt-2 h-4 w-4 shrink-0 sm:mt-0.5 ${
              PARAMETER_ICON_COLORS[config?.icon] || PARAMETER_ICON_COLORS.Beaker
            }`}
            aria-hidden
          />
          <div className="flex min-w-0 flex-1 items-start gap-0.5 pt-1.5 sm:pt-0">
            <span className="min-w-0 flex-1 text-base leading-6 text-slate-900">{label}</span>
            <span className="shrink-0">
              <SectionHelp
                content={FEATURE_HELP_CONTENT[featureKey]}
                placement="top"
                className="ml-0"
              />
            </span>
          </div>
        </div>
        <div className="parameter-slider-value">
          <input
            id={inputId}
            type="number"
            inputMode="decimal"
            min={numericMin}
            max={numericMax}
            step={step}
            value={draftValue}
            disabled={!included}
            aria-label={`${label} value${unit ? ` in ${unit}` : ""}`}
            aria-invalid={Boolean(inputError)}
            aria-describedby={inputError ? `${inputId}-error` : undefined}
            className={`parameter-slider-value-input ${
              inputError ? "border-delta-down" : "border-slate-300"
            }`}
            onChange={(event) => {
              const nextDraft = event.target.value;
              setDraftValue(nextDraft);
              applyTypedValue(nextDraft);
            }}
            onBlur={() => applyTypedValue(draftValue, true)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                applyTypedValue(draftValue, true);
              }
            }}
          />
          {unit && <span className="text-base text-slate-700">{unit}</span>}
        </div>
      </div>
      <input
        type="range"
        className={`mt-2 w-full ${differsFromBaseline ? "" : "range-default"}`}
        style={{ "--range-percent": rangePercent }}
        min={min}
        max={max}
        step={step}
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
      {inputError && (
        <p id={`${inputId}-error`} className="mt-2 text-base leading-snug text-delta-down">
          {inputError}
        </p>
      )}
      <p
        className={`parameter-slider-baseline ${differsFromBaseline ? "" : "invisible"}`}
        aria-hidden={!differsFromBaseline}
      >
        {baselineText}
      </p>
    </div>
  );
}
