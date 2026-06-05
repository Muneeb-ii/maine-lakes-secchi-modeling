import { useMemo } from "react";
import {
  CartesianGrid,
  ComposedChart,
  Line,
  ReferenceDot,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip as RechartsTooltip,
  XAxis,
  YAxis,
  Legend,
} from "recharts";
import { Activity, RotateCcw } from "lucide-react";
import {
  METRIC_LABELS,
  SECTION_LABELS,
  TRAJECTORY_AXIS_SECCHI,
  TRAJECTORY_AXIS_SESSION,
  TRAJECTORY_CHART_EMPTY_SUMMARY,
  TRAJECTORY_EMPTY_PROMPT,
  TRAJECTORY_LEGEND,
  TRAJECTORY_RESET_BUTTON,
  TRAJECTORY_RESET_CONFIRM,
  TRAJECTORY_STEP_NOTE,
  TRAJECTORY_TOOLTIP_VS_BASELINE,
  formatTrajectoryChartLiveSummary,
  formatTrajectorySteps,
} from "../../lib/copy";
import { TRAJECTORY_MAX_STEPS } from "../../lib/constants";
import { formatMeters, formatSignedMeters } from "../../lib/formatters";
import { HELP_CONTENT } from "../../lib/helpContent";
import { computeTrajectorySummary, computeYDomain, needsResetConfirmation } from "../../lib/trajectory";
import { useReducedMotion } from "../../lib/useReducedMotion";
import { SectionHelp } from "../ui/SectionHelp";

function TrajectoryTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const point = payload[0]?.payload;
  if (!point) return null;

  return (
    <div className="rounded-xl border border-lake-border bg-lake-panel px-3 py-2 text-sm shadow-panel max-w-xs">
      <p className="font-medium text-slate-950">
        Step {point.step}: {point.label}
      </p>
      <p className="text-slate-700 mt-1">Secchi {formatMeters(point.prediction)}</p>
      <p className="text-slate-600 mt-0.5">
        {TRAJECTORY_TOOLTIP_VS_BASELINE}: {formatSignedMeters(point.deltaFromBaseline)}
      </p>
      {point.changedFeatures?.length > 0 && (
        <ul className="mt-2 space-y-0.5 text-slate-600 list-none m-0 p-0">
          {point.changedFeatures.map((f) => (
            <li key={f.key}>
              {f.label}: {f.value}
              {f.unit ? ` ${f.unit}` : ""}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function TrajectoryChart({
  chartData,
  forecast,
  compareScenario,
  latestChange,
  onClearTrajectory,
}) {
  const reducedMotion = useReducedMotion();
  const summary = useMemo(() => computeTrajectorySummary(chartData), [chartData]);
  const baseline = forecast?.explainability?.base_value;
  const compareValue = compareScenario?.predictionMeters;
  const yDomain = useMemo(
    () => computeYDomain(chartData, baseline, compareValue),
    [chartData, baseline, compareValue]
  );

  const chartSummary = useMemo(() => {
    if (!chartData.length) {
      return TRAJECTORY_CHART_EMPTY_SUMMARY;
    }
    const latest = chartData[chartData.length - 1];
    return formatTrajectoryChartLiveSummary(
      chartData.length,
      formatMeters(latest.prediction),
      formatSignedMeters(latest.deltaFromBaseline)
    );
  }, [chartData]);

  const handleClear = () => {
    if (needsResetConfirmation(chartData.length)) {
      if (!window.confirm(TRAJECTORY_RESET_CONFIRM)) return;
    }
    onClearTrajectory();
  };

  return (
    <div className="panel p-6">
      <div className="flex flex-wrap items-start justify-between gap-3 mb-4">
        <h2 className="section-heading">
          <Activity className="w-4 h-4" aria-hidden />
          {SECTION_LABELS.trajectory}
          <SectionHelp content={HELP_CONTENT.trajectory} />
        </h2>
        <div className="flex items-center gap-3">
          <span className="text-sm text-slate-600">
            {formatTrajectorySteps(chartData.length, TRAJECTORY_MAX_STEPS)}
          </span>
          {chartData.length > 0 && (
            <button
              type="button"
              className="action-button h-10 px-3 text-sm"
              onClick={handleClear}
            >
              <RotateCcw className="w-3.5 h-3.5" aria-hidden />
              {TRAJECTORY_RESET_BUTTON}
            </button>
          )}
        </div>
      </div>

      {latestChange && (
        <div className="mb-4 rounded-lg border border-lake-accent/25 bg-lake-accent/8 px-4 py-3">
          <p className="info-label mb-1">{METRIC_LABELS.latestChange}</p>
          <p className="text-base text-lake-accent font-medium">{latestChange}</p>
        </div>
      )}

      {chartData.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-4 text-sm">
          <div className="info-card">
            <div className="info-label">{METRIC_LABELS.steps}</div>
            <div className="info-value">{summary.stepCount}</div>
          </div>
          <div className="info-card">
            <div className="info-label">{METRIC_LABELS.sessionRange}</div>
            <div className="info-value">
              {formatMeters(summary.min)} to {formatMeters(summary.max)}
            </div>
          </div>
          <div className="info-card col-span-2 sm:col-span-1">
            <div className="info-label">{METRIC_LABELS.latestVsBaseline}</div>
            <div className="info-value">{formatSignedMeters(summary.latestDeltaFromBaseline)}</div>
          </div>
        </div>
      )}

      <p className="sr-only" aria-live="polite">
        {chartSummary}
      </p>

      <div className="h-[220px] md:h-[280px] lg:h-[320px]">
        {chartData.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center px-4 gap-2 text-base text-slate-600 border border-dashed border-slate-300 rounded-lg">
            <p>{TRAJECTORY_EMPTY_PROMPT}</p>
            <p className="text-sm text-slate-600 max-w-md">{TRAJECTORY_STEP_NOTE}</p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#CBD5E1" />
              <XAxis
                dataKey="step"
                tick={{ fill: "#4B5563", fontSize: 13 }}
                label={{
                  value: TRAJECTORY_AXIS_SESSION,
                  position: "insideBottom",
                  offset: -2,
                  fill: "#4B5563",
                  fontSize: 12,
                }}
              />
              <YAxis
                domain={yDomain}
                tick={{ fill: "#4B5563", fontSize: 13 }}
                label={{
                  value: TRAJECTORY_AXIS_SECCHI,
                  angle: -90,
                  position: "insideLeft",
                  fill: "#4B5563",
                  fontSize: 12,
                }}
              />
              <RechartsTooltip content={<TrajectoryTooltip />} />
              <Legend
                verticalAlign="top"
                align="right"
                wrapperStyle={{ fontSize: 13, paddingBottom: 8 }}
                formatter={(value) => TRAJECTORY_LEGEND[value] || value}
              />
              <ReferenceLine
                y={2}
                stroke="#94A3B8"
                strokeDasharray="2 6"
                ifOverflow="extendDomain"
                name="clarity2m"
              />
              <ReferenceLine
                y={4}
                stroke="#94A3B8"
                strokeDasharray="2 6"
                ifOverflow="extendDomain"
                name="clarity4m"
              />
              {typeof baseline === "number" && (
                <ReferenceLine
                  y={baseline}
                  stroke="#E69F00"
                  strokeDasharray="5 5"
                  ifOverflow="extendDomain"
                  name="baselineRef"
                />
              )}
              {typeof compareValue === "number" && (
                <ReferenceLine
                  y={compareValue}
                  stroke="#CC79A7"
                  strokeDasharray="4 4"
                  ifOverflow="extendDomain"
                  name="compareRef"
                />
              )}
              <Line
                type="monotone"
                dataKey="prediction"
                stroke="#005AB5"
                strokeWidth={2.5}
                dot={{ r: 3, fill: "#005AB5" }}
                name="prediction"
                isAnimationActive={!reducedMotion}
                animationDuration={reducedMotion ? 0 : 280}
              />
              {chartData[0] && (
                <ReferenceDot
                  x={chartData[0].step}
                  y={chartData[0].prediction}
                  r={5}
                  stroke="#005AB5"
                  fill="#FFFFFF"
                />
              )}
              {chartData[chartData.length - 1] && (
                <ReferenceDot
                  x={chartData[chartData.length - 1].step}
                  y={chartData[chartData.length - 1].prediction}
                  r={6}
                  stroke="#005AB5"
                  fill="#005AB5"
                />
              )}
            </ComposedChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
