import { Minus, Plus, Waves } from "lucide-react";
import {
  METRIC_LABELS,
  PREDICTION_DELTA_NOTE,
  PREDICTION_SCALE_LABEL,
  PREDICTION_TYPICAL_NOTE,
  PREDICTION_UPDATING,
  SECTION_LABELS,
  SECCHI_DIRECTION_NOTE,
  TYPICAL_PREDICTION_MAE_METERS,
} from "../../lib/copy";
import { formatMeters, formatSignedMeters, getClarityBand } from "../../lib/formatters";
import { HELP_CONTENT } from "../../lib/helpContent";
import { formatSecchiThreshold, getClarityDescription, SECTION_ACCENTS } from "../../lib/theme";
import { displayUnitFor, toDisplay } from "../../lib/units";
import { useUnitSystem } from "../../context/UnitSystemContext";
import { ClarityScaleBar } from "../layout/ClarityScaleBar";
import { SectionHelp } from "../ui/SectionHelp";
import { SectionHeading } from "../ui/SectionHeading";

function DeltaValue({ value, system }) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return <span className="text-2xl font-semibold tabular-nums text-slate-600">--</span>;
  }
  const isPositive = value > 0;
  const isNegative = value < 0;
  const Icon = isPositive ? Plus : isNegative ? Minus : null;
  const colorClass = isPositive ? "text-delta-up" : isNegative ? "text-delta-down" : "text-slate-900";

  return (
    <span className={`inline-flex items-center gap-1 text-2xl font-semibold tabular-nums ${colorClass}`}>
      {Icon && <Icon className="h-4 w-4" aria-hidden />}
      {formatSignedMeters(value, { absolute: true, system })}
    </span>
  );
}

function PredictedValue({ meters, system, isPredicting }) {
  if (!Number.isFinite(meters)) {
    return <span className={isPredicting ? "opacity-70" : undefined}>--</span>;
  }
  const display = toDisplay(meters, "m", system);
  const unit = displayUnitFor("m", system);
  return (
    <span className={`inline-flex items-baseline gap-2 ${isPredicting ? "opacity-70" : ""}`}>
      <span>{display.toFixed(2)}</span>
      <span className="text-[0.4em] font-semibold tracking-normal text-slate-600">{unit}</span>
    </span>
  );
}

function depthContext(predictionMeters, maxDepthFeet, system) {
  if (!Number.isFinite(predictionMeters) || !Number.isFinite(maxDepthFeet) || maxDepthFeet <= 0) {
    return null;
  }
  const depthMeters = toDisplay(maxDepthFeet, "ft", "metric");
  const percent = (predictionMeters / depthMeters) * 100;
  const depthLabel = `${toDisplay(maxDepthFeet, "ft", system).toFixed(1)} ${displayUnitFor("ft", system)}`;
  if (percent >= 100) {
    return `At or beyond this lake’s recorded maximum depth (${depthLabel})`;
  }
  return `${Math.round(percent)}% of this lake’s maximum depth (${depthLabel})`;
}

export function PredictionHero({ forecast, predictionError, isPredicting, baseline }) {
  const { system } = useUnitSystem();
  const prediction = forecast?.predictionMeters;
  const typical = forecast?.explainability?.base_value;
  const hasPrediction = Number.isFinite(prediction);
  const delta =
    forecast && hasPrediction && typeof typical === "number" ? prediction - typical : null;
  const clarityBand = hasPrediction ? getClarityBand(prediction) : null;
  const heroWashClass = clarityBand?.heroWashClass || "hero-wash-prediction";
  const vsDepth = depthContext(prediction, baseline?.DEPTH_MAX_FEET, system);
  const maeNote = `Typical error on supported lakes is about ${formatSecchiThreshold(
    TYPICAL_PREDICTION_MAE_METERS,
    system
  )}.`;

  return (
    <div
      data-claro-target="prediction-card"
      className={`panel flex h-full flex-col p-4 sm:p-5 ${heroWashClass} ${SECTION_ACCENTS.prediction.panelAccentClass}`}
    >
      <SectionHeading section="prediction" icon={Waves} help={HELP_CONTENT.prediction}>
        {SECTION_LABELS.prediction}
      </SectionHeading>

      <div
        data-claro-target="prediction-metrics"
        className="mt-4 flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between lg:gap-8"
      >
        <div className="min-w-0">
          <div
            className="text-7xl font-semibold leading-none tracking-tight tabular-nums sm:text-8xl"
            aria-live="polite"
            aria-atomic="true"
          >
            <PredictedValue meters={prediction} system={system} isPredicting={isPredicting} />
          </div>
          {clarityBand ? (
            <div className="mt-4 flex flex-wrap items-center gap-x-3 gap-y-1">
              <span className={clarityBand.pillClass}>{clarityBand.label}</span>
              <span className="text-lg text-slate-700">{getClarityDescription(clarityBand, system)}</span>
            </div>
          ) : (
            <p className="body-copy mt-4">{SECCHI_DIRECTION_NOTE}</p>
          )}
        </div>

        <dl className="grid min-w-[14rem] shrink-0 grid-cols-2 gap-x-6 gap-y-4 sm:grid-cols-2 lg:grid-cols-1 lg:border-l lg:border-slate-200 lg:pl-6">
          <div>
            <dt className="info-label inline-flex items-center">
              {METRIC_LABELS.modelBaseline}
              <SectionHelp content={HELP_CONTENT.modelBaseline} placement="bottom" />
            </dt>
            <dd className="mt-1 text-2xl font-semibold tabular-nums">
              {forecast ? formatMeters(typical, system) : "--"}
            </dd>
            <p className="mt-0.5 text-sm text-slate-600 sm:text-base">{PREDICTION_TYPICAL_NOTE}</p>
          </div>
          <div>
            <dt className="info-label inline-flex items-center">
              {METRIC_LABELS.deltaFromBaseline}
              <SectionHelp content={HELP_CONTENT.deltaFromBaseline} placement="bottom" />
            </dt>
            <dd className="mt-1">
              <DeltaValue value={delta} system={system} />
            </dd>
            <p className="mt-0.5 text-sm text-slate-600 sm:text-base">{PREDICTION_DELTA_NOTE}</p>
          </div>
        </dl>
      </div>

      <div className="mt-auto border-t border-slate-200 pt-4">
        <p className="info-label">{PREDICTION_SCALE_LABEL}</p>
        <ClarityScaleBar compact className="mt-2" valueMeters={hasPrediction ? prediction : undefined} />
        <p className="mt-3 text-base text-slate-700">
          {vsDepth ? `${vsDepth}. ` : null}
          {maeNote}
        </p>
      </div>

      {isPredicting && (
        <p className="mt-3 text-base text-slate-700" role="status">
          {PREDICTION_UPDATING}
        </p>
      )}
      {predictionError && (
        <p className="mt-3 text-base text-delta-down" role="alert">
          {predictionError}
        </p>
      )}
    </div>
  );
}
