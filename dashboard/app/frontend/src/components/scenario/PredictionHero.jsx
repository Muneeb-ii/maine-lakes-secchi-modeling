import { AnimatePresence, motion } from "framer-motion";
import { Minus, Plus } from "lucide-react";
import { METRIC_LABELS, SECTION_LABELS, SECCHI_DIRECTION_NOTE } from "../../lib/copy";
import { formatMeters, formatSignedMeters, getClarityBand } from "../../lib/formatters";
import { HELP_CONTENT } from "../../lib/helpContent";
import { useReducedMotion } from "../../lib/useReducedMotion";
import { SectionHelp } from "../ui/SectionHelp";

function DeltaValue({ value }) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return <span className="text-2xl font-medium text-slate-400">--</span>;
  }
  const isPositive = value > 0;
  const isNegative = value < 0;
  const Icon = isPositive ? Plus : isNegative ? Minus : null;
  const colorClass = isPositive ? "text-delta-up" : isNegative ? "text-delta-down" : "text-slate-300";

  return (
    <span className={`inline-flex items-center gap-1 text-2xl font-medium ${colorClass}`}>
      {Icon && <Icon className="w-5 h-5" aria-hidden />}
      {formatSignedMeters(value)}
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

  return (
    <div className="panel p-6 border-l-4 border-l-lake-accent/50">
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-6">
        <div className="min-w-0">
          <h2 className="section-heading text-slate-400">
            {SECTION_LABELS.prediction}
            <SectionHelp content={HELP_CONTENT.prediction} placement="bottom" />
          </h2>
          <div
            className={`mt-3 text-5xl sm:text-6xl lg:text-7xl font-semibold leading-none tabular-nums ${
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
          <p className="mt-2 text-sm text-slate-300">{SECCHI_DIRECTION_NOTE}</p>
          {clarityBand && forecast && (
            <div className="mt-4 flex flex-wrap items-center gap-2">
              <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-lake-accent/15 text-teal-200 border border-lake-accent/30">
                {clarityBand.label}
              </span>
              <span className="text-xs text-slate-500">{clarityBand.description}</span>
            </div>
          )}
        </div>

        <div className="flex flex-wrap gap-6 sm:gap-8 text-slate-300">
          <div>
            <div className="info-label">{METRIC_LABELS.modelBaseline}</div>
            <div className="text-2xl font-medium mt-1 tabular-nums">
              {forecast ? formatMeters(baseline) : "--"}
            </div>
          </div>
          <div>
            <div className="info-label">{METRIC_LABELS.deltaFromBaseline}</div>
            <div className="mt-1">
              <DeltaValue value={delta} />
            </div>
          </div>
        </div>
      </div>

      {isPredicting && (
        <p className="mt-4 text-xs text-slate-500" role="status">
          Updating prediction…
        </p>
      )}
      {predictionError && (
        <p className="mt-4 text-sm text-red-300" role="alert">
          {predictionError}
        </p>
      )}
    </div>
  );
}
