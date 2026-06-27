import { useMemo, useState } from "react";
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
} from "recharts";
import { Activity, RotateCcw } from "lucide-react";
import {
  METRIC_LABELS,
  SECTION_LABELS,
  TRAJECTORY_AXIS_SESSION,
  TRAJECTORY_CHART_EMPTY_SUMMARY,
  TRAJECTORY_EMPTY_PROMPT,
  TRAJECTORY_RESET_BUTTON,
  TRAJECTORY_RESET_CONFIRM,
  TRAJECTORY_SCALE_DETAIL,
  TRAJECTORY_SCALE_FULL,
  TRAJECTORY_SCALE_LABEL,
  TRAJECTORY_SCALE_NOTE_DETAIL,
  TRAJECTORY_STEP_NOTE,
  TRAJECTORY_TOOLTIP_VS_PREVIOUS,
  TRAJECTORY_TOOLTIP_VS_BASELINE,
  formatTrajectoryChartLiveSummary,
  formatTrajectorySteps,
  getTrajectoryAxisSecchi,
  getTrajectoryLegend,
  getTrajectoryScaleNoteFull,
} from "../../lib/copy";
import { TRAJECTORY_MAX_STEPS } from "../../lib/constants";
import { formatMeters, formatSignedMeters } from "../../lib/formatters";
import { HELP_CONTENT } from "../../lib/helpContent";
import {
  buildTrajectoryChangeRows,
  buildYAxisTicks,
  clampSecchiForChart,
  computeTrajectorySummary,
  computeYDomain,
  formatYAxisTick,
  isPlausibleSecchiMeters,
  needsResetConfirmation,
} from "../../lib/trajectory";
import { formatSecchiThreshold, SECTION_ACCENTS } from "../../lib/theme";
import { toDisplay } from "../../lib/units";
import { useReducedMotion } from "../../lib/useReducedMotion";
import { useUnitSystem } from "../../context/UnitSystemContext";
import { SectionHelp } from "../ui/SectionHelp";
import { SectionHeadingIcon } from "../ui/SectionHeadingIcon";

function TrajectoryTooltip({ active, payload, system }) {
  if (!active || !payload?.length) return null;
  const point = payload[0]?.payload;
  if (!point) return null;

  return (
    <div className="max-w-xs rounded-xl border border-lake-border bg-lake-panel px-3 py-2 text-base shadow-panel">
      <p className="font-medium text-slate-950">
        Change {point.step}: {point.label}
      </p>
      <p className="text-slate-700 mt-1">Secchi {formatMeters(point.prediction, system)}</p>
      <p className="text-slate-600 mt-0.5">
        {TRAJECTORY_TOOLTIP_VS_BASELINE}: {formatSignedMeters(point.deltaFromBaseline, { system })}
      </p>
      {typeof point.deltaFromPrevious === "number" && (
        <p className="text-slate-600 mt-0.5">
          {TRAJECTORY_TOOLTIP_VS_PREVIOUS}: {formatSignedMeters(point.deltaFromPrevious, { system })}
        </p>
      )}
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

function LegendSwatch({ label, color, dashed = false, dot = false }) {
  return (
    <span className="inline-flex items-center gap-2 text-base text-slate-700">
      <span className="relative inline-flex h-3 w-9 items-center" aria-hidden>
        <span
          className={`h-0.5 w-full ${dashed ? "border-t-2 border-dashed bg-transparent" : ""}`}
          style={dashed ? { borderColor: color } : { backgroundColor: color }}
        />
        {dot && (
          <span
            className="absolute left-1/2 h-2.5 w-2.5 -translate-x-1/2 rounded-full border-2 border-white"
            style={{ backgroundColor: color }}
          />
        )}
      </span>
      {label}
    </span>
  );
}

function ScenarioLegend({ hasCompare, showClarityReferences, system }) {
  const legend = getTrajectoryLegend(system);
  return (
    <div className="mb-3 flex flex-wrap gap-x-5 gap-y-2" aria-label="Chart legend">
      <LegendSwatch label={legend.prediction} color="#005AB5" dot />
      <LegendSwatch label={legend.baselineRef} color="#E69F00" dashed />
      {hasCompare && <LegendSwatch label={legend.compareRef} color="#CC79A7" dashed />}
      {showClarityReferences && (
        <LegendSwatch
          label={`${formatSecchiThreshold(2, system)} and ${formatSecchiThreshold(4, system)} clarity references`}
          color="#64748B"
          dashed
        />
      )}
    </div>
  );
}

function ChangeTone({ value, system }) {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    return <span className="text-slate-600">Start</span>;
  }
  const toneClass = value > 0 ? "text-delta-up" : value < 0 ? "text-delta-down" : "text-slate-600";
  return <span className={`font-medium ${toneClass}`}>{formatSignedMeters(value, { system })}</span>;
}

function TrajectoryChangeTable({ rows, system }) {
  if (!rows.length) {
    return (
      <div className="flex h-full min-h-[220px] flex-col justify-center rounded-lg border border-dashed border-lake-accent/35 bg-lake-accentSoft/50 px-4 text-center">
        <p className="text-base font-semibold text-slate-800">No changes recorded yet</p>
        <p className="mt-2 text-base leading-relaxed text-slate-700">
          Adjust a water condition and the same session points shown in the chart will appear here as rows.
        </p>
      </div>
    );
  }

  return (
    <div className="h-full overflow-hidden rounded-lg border border-lake-border bg-white">
      <div className="border-b border-slate-200 bg-slate-50 px-3 py-2">
        <h3 className="section-subheading text-base">Change log</h3>
        <p className="text-base leading-relaxed text-slate-600">Rows stay in sync with the chart points.</p>
      </div>
      <div className="max-h-[420px] overflow-auto">
        <table className="min-w-full text-left text-base">
          <thead className="sticky top-0 bg-white shadow-[0_1px_0_#e2e8f0]">
            <tr>
              <th scope="col" className="px-3 py-2 font-semibold text-slate-600">Step</th>
              <th scope="col" className="px-3 py-2 font-semibold text-slate-600">Change</th>
              <th scope="col" className="px-3 py-2 font-semibold text-slate-600">Secchi</th>
              <th scope="col" className="px-3 py-2 font-semibold text-slate-600">Move</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.step} className="border-b border-slate-100 last:border-0">
                <td className="px-3 py-2 font-semibold tabular-nums text-slate-900">{row.step}</td>
                <td className="px-3 py-2 text-slate-700">
                  <div className="font-medium text-slate-900">{row.label}</div>
                  <div className="text-sm leading-snug text-slate-600">
                    {row.value}
                    {row.extraChangeCount > 0 ? ` + ${row.extraChangeCount} more` : ""}
                  </div>
                </td>
                <td className="px-3 py-2 tabular-nums text-slate-900">{formatMeters(row.prediction, system)}</td>
                <td className="px-3 py-2 tabular-nums">
                  <ChangeTone value={row.deltaFromPrevious} system={system} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
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
  const { system } = useUnitSystem();
  const reducedMotion = useReducedMotion();
  const [scaleMode, setScaleMode] = useState("detail");
  const summary = useMemo(() => computeTrajectorySummary(chartData), [chartData]);
  const baseline = forecast?.explainability?.base_value;
  const compareValue = compareScenario?.predictionMeters;
  const chartBaseline = isPlausibleSecchiMeters(baseline) ? baseline : null;
  const chartCompareValue = isPlausibleSecchiMeters(compareValue) ? compareValue : null;
  const yDomain = useMemo(
    () => computeYDomain(chartData, chartBaseline, chartCompareValue, { mode: scaleMode }),
    [chartData, chartBaseline, chartCompareValue, scaleMode]
  );
  const yTicks = useMemo(
    () => buildYAxisTicks(yDomain[0], yDomain[1], scaleMode),
    [yDomain, scaleMode]
  );
  const plottedData = useMemo(
    () =>
      chartData.map((point) => ({
        ...point,
        chartPrediction: clampSecchiForChart(point.prediction),
      })),
    [chartData]
  );
  const changeRows = useMemo(() => buildTrajectoryChangeRows(chartData), [chartData]);
  const showClarityReferences = scaleMode === "full";

  const chartSummary = useMemo(() => {
    if (!chartData.length) {
      return TRAJECTORY_CHART_EMPTY_SUMMARY;
    }
    const latest = chartData[chartData.length - 1];
    return formatTrajectoryChartLiveSummary(
      chartData.length,
      formatMeters(latest.prediction, system),
      formatSignedMeters(latest.deltaFromBaseline, { system })
    );
  }, [chartData, system]);

  const handleClear = () => {
    if (needsResetConfirmation(chartData.length)) {
      if (!window.confirm(TRAJECTORY_RESET_CONFIRM)) return;
    }
    onClearTrajectory();
  };

  return (
    <div
      data-claro-target="trajectory-chart"
      className={`panel flex h-full flex-col p-4 sm:p-5 ${SECTION_ACCENTS.trajectory.panelAccentClass}`}
    >
      <div className="mb-3 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-start sm:justify-between">
        <div>
          <h2 className="section-heading">
            <SectionHeadingIcon section="trajectory" icon={Activity} />
            {SECTION_LABELS.trajectory}
            <SectionHelp content={HELP_CONTENT.trajectory} />
          </h2>
          <p className="mt-2 max-w-2xl body-copy leading-relaxed">
            The first dot is this lake’s typical condition. Each later dot is a meaningful
            slider adjustment you tried, so the line shows how your scenario changed predicted
            clarity.
          </p>
        </div>
        <div className="flex w-full flex-wrap items-center gap-3 sm:w-auto">
          <span className="text-base text-slate-700">
            {formatTrajectorySteps(chartData.length, TRAJECTORY_MAX_STEPS)}
          </span>
          {chartData.length > 0 && (
            <button
              type="button"
              className="action-button h-12 px-3 text-base sm:ml-auto"
              onClick={handleClear}
            >
              <RotateCcw className="w-3.5 h-3.5" aria-hidden />
              {TRAJECTORY_RESET_BUTTON}
            </button>
          )}
        </div>
      </div>

      {latestChange && (
        <div className="mb-3 rounded-lg border border-lake-accent/25 bg-lake-accent/8 px-3 py-2">
          <p className="info-label mb-1">{METRIC_LABELS.latestChange}</p>
          <p className="text-base text-lake-accent font-medium">{latestChange}</p>
        </div>
      )}

      {chartData.length > 0 && (
        <div className="mb-3 grid grid-cols-1 gap-2 text-base sm:grid-cols-2 xl:grid-cols-5">
          <div className="info-card">
            <div className="info-label">{METRIC_LABELS.steps}</div>
            <div className="info-value">{summary.stepCount}</div>
          </div>
          <div className="info-card">
            <div className="info-label">{METRIC_LABELS.latestSecchi}</div>
            <div className="info-value">{formatMeters(summary.latest, system)}</div>
          </div>
          <div className="info-card">
            <div className="info-label">{METRIC_LABELS.latestVsBaseline}</div>
            <div className="info-value">{formatSignedMeters(summary.latestDeltaFromBaseline, { system })}</div>
          </div>
          <div className="info-card">
            <div className="info-label">{METRIC_LABELS.latestVsPrevious}</div>
            <div className="info-value">
              {typeof summary.latestDeltaFromPrevious === "number"
                ? formatSignedMeters(summary.latestDeltaFromPrevious, { system })
                : "Start"}
            </div>
          </div>
          <div className="info-card">
            <div className="info-label">{METRIC_LABELS.largestMove}</div>
            <div className="info-value">
              {typeof summary.largestMove === "number"
                ? formatSignedMeters(summary.largestMove, { system })
                : "Start"}
            </div>
          </div>
        </div>
      )}

      <p className="sr-only" aria-live="polite">
        {chartSummary}
      </p>

      {chartData.length > 0 && (
        <div className="mb-3 flex flex-col gap-2 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="info-label">{TRAJECTORY_SCALE_LABEL}</p>
            <p className="text-base text-slate-700">
              {scaleMode === "detail"
                ? TRAJECTORY_SCALE_NOTE_DETAIL
                : getTrajectoryScaleNoteFull(system)}
            </p>
          </div>
          <div className="inline-grid grid-cols-2 rounded-lg border border-lake-border bg-white p-1">
            <button
              type="button"
              className={`rounded-md px-3 py-2 text-base font-semibold transition ${
                scaleMode === "detail"
                  ? "bg-lake-accent text-white"
                  : "text-lake-accent hover:bg-blue-50"
              }`}
              onClick={() => setScaleMode("detail")}
            >
              {TRAJECTORY_SCALE_DETAIL}
            </button>
            <button
              type="button"
              className={`rounded-md px-3 py-2 text-base font-semibold transition ${
                scaleMode === "full"
                  ? "bg-lake-accent text-white"
                  : "text-lake-accent hover:bg-blue-50"
              }`}
              onClick={() => setScaleMode("full")}
            >
              {TRAJECTORY_SCALE_FULL}
            </button>
          </div>
        </div>
      )}

      {chartData.length > 0 && (
        <ScenarioLegend
          hasCompare={typeof chartCompareValue === "number"}
          showClarityReferences={showClarityReferences}
          system={system}
        />
      )}

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(26rem,0.42fr)] xl:items-stretch">
        <div className="h-[340px] sm:h-[420px] xl:h-[460px]">
          {chartData.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-lake-accent/35 bg-lake-accentSoft/50 px-4 text-center text-base text-slate-600">
              <p>{TRAJECTORY_EMPTY_PROMPT}</p>
              <p className="max-w-md text-base text-slate-700">{TRAJECTORY_STEP_NOTE}</p>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart
                data={plottedData}
                margin={{ top: 12, right: 16, left: 8, bottom: 28 }}
              >
              <CartesianGrid strokeDasharray="3 3" stroke="#CBD5E1" />
              <XAxis
                dataKey="step"
                tick={{ fill: "#334155", fontSize: 13, fontWeight: 500 }}
                axisLine={{ stroke: "#94A3B8" }}
                tickLine={{ stroke: "#94A3B8" }}
                label={{
                  value: TRAJECTORY_AXIS_SESSION,
                  position: "insideBottom",
                  offset: -4,
                  fill: "#334155",
                  fontSize: 13,
                  fontWeight: 600,
                }}
              />
              <YAxis
                width={52}
                type="number"
                domain={[() => yDomain[0], () => yDomain[1]]}
                ticks={yTicks}
                allowDataOverflow
                tickFormatter={(value) => formatYAxisTick(toDisplay(value, "m", system), scaleMode)}
                tick={{ fill: "#334155", fontSize: 13, fontWeight: 600 }}
                axisLine={{ stroke: "#94A3B8" }}
                tickLine={{ stroke: "#94A3B8" }}
                label={{
                  value: getTrajectoryAxisSecchi(system),
                  angle: -90,
                  position: "insideLeft",
                  offset: 14,
                  fill: "#334155",
                  fontSize: 13,
                  fontWeight: 600,
                  style: { textAnchor: "middle" },
                }}
              />
              <RechartsTooltip content={<TrajectoryTooltip system={system} />} />
              {showClarityReferences && (
                <>
                  <ReferenceLine
                    y={2}
                    stroke="#64748B"
                    strokeDasharray="2 6"
                    ifOverflow="discard"
                    name="clarity2m"
                    label={{ value: formatSecchiThreshold(2, system), position: "insideRight", fill: "#475569", fontSize: 13 }}
                  />
                  <ReferenceLine
                    y={4}
                    stroke="#64748B"
                    strokeDasharray="2 6"
                    ifOverflow="discard"
                    name="clarity4m"
                    label={{ value: formatSecchiThreshold(4, system), position: "insideRight", fill: "#475569", fontSize: 13 }}
                  />
                </>
              )}
              {typeof chartBaseline === "number" && (
                <ReferenceLine
                  y={chartBaseline}
                  stroke="#E69F00"
                  strokeDasharray="5 5"
                  ifOverflow="discard"
                  name="baselineRef"
                  label={{
                    value: `${formatMeters(chartBaseline, system)} typical`,
                    position: "insideTopLeft",
                    fill: "#A16207",
                    fontSize: 12,
                    fontWeight: 600,
                  }}
                />
              )}
              {typeof chartCompareValue === "number" && (
                <ReferenceLine
                  y={chartCompareValue}
                  stroke="#CC79A7"
                  strokeDasharray="4 4"
                  ifOverflow="discard"
                  name="compareRef"
                />
              )}
              <Line
                type="monotone"
                dataKey="chartPrediction"
                stroke="#005AB5"
                strokeWidth={3.5}
                connectNulls={false}
                dot={{ r: 5, fill: "#005AB5", stroke: "#FFFFFF", strokeWidth: 2 }}
                activeDot={{ r: 8, fill: "#005AB5", stroke: "#FFFFFF", strokeWidth: 2 }}
                name="prediction"
                isAnimationActive={!reducedMotion}
                animationDuration={reducedMotion ? 0 : 280}
              />
              {plottedData[0]?.chartPrediction !== null && (
                <ReferenceDot
                  x={plottedData[0].step}
                  y={plottedData[0].chartPrediction}
                  r={5}
                  stroke="#005AB5"
                  fill="#FFFFFF"
                  ifOverflow="discard"
                />
              )}
              {plottedData.at(-1)?.chartPrediction !== null && (
                <ReferenceDot
                  x={plottedData.at(-1).step}
                  y={plottedData.at(-1).chartPrediction}
                  r={6}
                  stroke="#005AB5"
                  fill="#005AB5"
                  ifOverflow="discard"
                />
              )}
              </ComposedChart>
            </ResponsiveContainer>
          )}
        </div>
        <TrajectoryChangeTable rows={changeRows} system={system} />
      </div>
    </div>
  );
}
