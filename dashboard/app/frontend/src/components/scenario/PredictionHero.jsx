import { AnimatePresence, motion } from "framer-motion";
import { Minus, Plus, Waves } from "lucide-react";
import {
  METRIC_LABELS,
  PREDICTION_UPDATING,
  SECTION_LABELS,
  SECCHI_DIRECTION_NOTE,
} from "../../lib/copy";
import { formatMeters, formatSignedMeters, getClarityBand } from "../../lib/formatters";
import { HELP_CONTENT } from "../../lib/helpContent";
import { SECTION_ACCENTS } from "../../lib/theme";
import { useReducedMotion } from "../../lib/useReducedMotion";
import { SectionHelp } from "../ui/SectionHelp";
import { SectionHeadingIcon } from "../ui/SectionHeadingIcon";

function DeltaValue({ value }) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return <span className="text-2xl font-medium text-slate-600">--</span>;
  }
  const isPositive = value > 0;
  const isNegative = value < 0;
  const Icon = isPositive ? Plus : isNegative ? Minus : null;
  const colorClass = isPositive ? "text-delta-up" : isNegative ? "text-delta-down" : "text-slate-700";

  return (
    <span className={`inline-flex items-center gap-1 text-xl font-medium sm:text-2xl ${colorClass}`}>
      {Icon && <Icon className="w-5 h-5" aria-hidden />}
      {formatSignedMeters(value, { absolute: true })}
    </span>
  );
}

export function PredictionHero({ forecast, predictionError, isPredicting }) {
  const reducedMotion = useReducedMotion();
  const prediction = forecast?.predictionMeters;
  const baseline = forecast?.explainability?.base_value;
  const delta =
    forecast && typeof prediction === "number" && typeof baseline === "number"
      ? prediction - baseline
      : null;
  const clarityBand = getClarityBand(prediction);
  const heroWashClass = clarityBand?.heroWashClass || "hero-wash-prediction";

  return (
    <div
      data-claro-target="prediction-card"
      className={`panel p-4 sm:p-5 lg:p-6 ${heroWashClass} ${SECTION_ACCENTS.prediction.panelAccentClass}`}
    >
      <div className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between lg:gap-6">
        <div className="min-w-0">
          <h2 className="section-heading text-slate-700">
            <SectionHeadingIcon section="prediction" icon={Waves} />
            {SECTION_LABELS.prediction}
            <SectionHelp content={HELP_CONTENT.prediction} placement="bottom" />
          </h2>
          <div
            className={`mt-3 text-4xl font-semibold leading-none tabular-nums sm:text-5xl lg:text-7xl ${
              isPredicting ? "opacity-70" : ""
            }`}
            aria-live="polite"
            aria-atomic="true"
          >
            <AnimatePresence mode="wait">
              <motion.span
                key={prediction ?? "empty"}
                initial={reducedMotion ? false : { opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={reducedMotion ? undefined : { opacity: 0, y: -8 }}
                transition={{ duration: 0.25 }}
              >
                {forecast ? formatMeters(prediction) : "--"}
              </motion.span>
            </AnimatePresence>
          </div>
          <p className="body-copy mt-2">{SECCHI_DIRECTION_NOTE}</p>
          {clarityBand && forecast && (
            <div className="mt-4 flex flex-wrap items-center gap-2">
              <span className={clarityBand.pillClass}>{clarityBand.label}</span>
              <span className="body-copy">{clarityBand.description}</span>
            </div>
          )}
        </div>

        <div
          data-claro-target="prediction-metrics"
          className="grid grid-cols-2 gap-3 text-slate-700 sm:flex sm:flex-wrap sm:gap-8"
        >
          <div className="min-w-0">
            <div className="info-label inline-flex items-center">
              {METRIC_LABELS.modelBaseline}
              <SectionHelp content={HELP_CONTENT.modelBaseline} placement="bottom" />
            </div>
            <div className="mt-1 text-xl font-medium tabular-nums sm:text-2xl">
              {forecast ? formatMeters(baseline) : "--"}
            </div>
          </div>
          <div className="min-w-0">
            <div className="info-label inline-flex items-center">
              {METRIC_LABELS.deltaFromBaseline}
              <SectionHelp content={HELP_CONTENT.deltaFromBaseline} placement="bottom" />
            </div>
            <div className="mt-1">
              <DeltaValue value={delta} />
            </div>
          </div>
        </div>
      </div>

      {isPredicting && (
        <p className="mt-4 text-base text-slate-700" role="status">
          {PREDICTION_UPDATING}
        </p>
      )}
      {predictionError && (
        <p className="mt-4 text-base text-delta-down" role="alert">
          {predictionError}
        </p>
      )}
    </div>
  );
}
