import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { formatQuantity, toDisplay } from "../../lib/units";
import { useUnitSystem } from "../../context/UnitSystemContext";

const CHART_COLORS = {
  observed: "#005ab5",
  forecast: "#b47700",
  range80: "#f59e0b",
  range95: "#fef3c7",
  grid: "#e2e8f0",
  axis: "#64748b",
};

function observedRows(detail) {
  return detail.history.map((row) => ({
    year: row.year,
    observed: row.secchi_m,
    nReadings: row.n_readings,
  }));
}

function forecastRows(detail) {
  return detail.forecast.map((row) => ({
    year: row.year,
    forecast: row.secchi_m,
    lower80: row.lower_80,
    upper80: row.upper_80,
    lower95: row.lower_95,
    upper95: row.upper_95,
  }));
}

function paddedDomain(values) {
  const finiteValues = values.filter((value) => Number.isFinite(value));
  if (!finiteValues.length) return [0, 1];
  const min = Math.min(...finiteValues);
  const max = Math.max(...finiteValues);
  const span = Math.max(max - min, 0.6);
  const lower = Math.max(0, min - span * 0.12);
  const upper = max + span * 0.12;
  return [lower, upper];
}

function chartDomain(rows, keys) {
  return paddedDomain(rows.flatMap((row) => keys.map((key) => row[key])));
}

function niceStep(span) {
  const rawStep = Math.max(span / 5, 0.2);
  const magnitude = 10 ** Math.floor(Math.log10(rawStep));
  const normalized = rawStep / magnitude;
  const multiple = normalized <= 1 ? 1 : normalized <= 2 ? 2 : normalized <= 5 ? 5 : 10;
  return multiple * magnitude;
}

function axisSpec(domain) {
  const step = niceStep(domain[1] - domain[0]);
  const start = Math.max(0, Math.floor(domain[0] / step) * step);
  const end = Math.ceil(domain[1] / step) * step;
  const ticks = [];
  for (let value = start; value <= end + step * 0.001; value += step) {
    ticks.push(Number(value.toFixed(10)));
  }
  return { domain: [start, end], ticks };
}

function RangeTooltip({ active, payload, system, mode }) {
  if (!active || !payload?.length) return null;
  const point = payload[0]?.payload;
  if (!point) return null;

  return (
    <div className="rounded-lg border border-lake-border bg-white px-3 py-2 text-sm shadow-panel">
      <p className="font-semibold text-slate-950">{point.year}</p>
      {mode === "history" && point.observed != null && (
        <p className="text-slate-700">
          Observed: {formatQuantity(point.observed, { canonicalUnit: "m", system, decimals: 2 })}
        </p>
      )}
      {mode === "history" && point.nReadings != null && (
        <p className="text-slate-600">{point.nReadings} monitoring readings</p>
      )}
      {mode === "forecast" && point.forecast != null && (
        <p className="font-medium text-amber-950">
          Baseline: {formatQuantity(point.forecast, { canonicalUnit: "m", system, decimals: 2 })}
        </p>
      )}
      {mode === "forecast" && point.lower80 != null && (
        <p className="text-slate-600">
          80% range: {formatQuantity(point.lower80, { canonicalUnit: "m", system, decimals: 2 })}–
          {formatQuantity(point.upper80, { canonicalUnit: "m", system, decimals: 2 })}
        </p>
      )}
      {mode === "forecast" && point.lower95 != null && (
        <p className="text-slate-600">
          95% range: {formatQuantity(point.lower95, { canonicalUnit: "m", system, decimals: 2 })}–
          {formatQuantity(point.upper95, { canonicalUnit: "m", system, decimals: 2 })}
        </p>
      )}
    </div>
  );
}

function ChartFrame({ rows, axis, system, mode, children, ariaLabel }) {
  const unit = system === "imperial" ? "ft" : "m";
  return (
    <div className="mt-4 w-full" aria-label={ariaLabel} role="img">
      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart data={rows} margin={{ top: 14, right: 12, left: 2, bottom: 8 }}>
          <CartesianGrid stroke={CHART_COLORS.grid} strokeDasharray="3 3" />
          <XAxis
            dataKey="year"
            tick={{ fontSize: 12, fill: CHART_COLORS.axis }}
            tickLine={false}
            axisLine={{ stroke: CHART_COLORS.grid }}
            minTickGap={24}
          />
          <YAxis
            domain={axis.domain}
            ticks={axis.ticks}
            allowDataOverflow
            tick={{ fontSize: 12, fill: CHART_COLORS.axis }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(value) => toDisplay(value, "m", system).toFixed(1)}
            label={{ value: unit, angle: -90, position: "insideLeft", offset: 8, fill: CHART_COLORS.axis }}
          />
          <Tooltip content={<RangeTooltip system={system} mode={mode} />} />
          {children}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

function LegendItem({ className, label }) {
  return (
    <span className="inline-flex items-center gap-2">
      <span className={`inline-block h-2.5 w-7 rounded-sm ${className}`} aria-hidden />
      {label}
    </span>
  );
}

function HistoryChart({ detail, system }) {
  const rows = observedRows(detail);
  const axis = axisSpec(chartDomain(rows, ["observed"]));
  const firstYear = rows[0]?.year;
  const lastYear = rows.at(-1)?.year;
  const totalReadings = rows.reduce((sum, row) => sum + (Number(row.nReadings) || 0), 0);

  return (
    <section data-claro-target="trends-history-chart" aria-labelledby="observed-record-heading">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h3 id="observed-record-heading" className="section-subheading">Observed record</h3>
        <span className="text-sm font-medium text-slate-600">
          {firstYear}–{lastYear} · {rows.length} monitored years
        </span>
      </div>
      <p className="mt-1 text-sm text-slate-600">
        Measured summer Secchi depth. {totalReadings.toLocaleString()} monitoring readings in this record.
      </p>
      <ChartFrame
        rows={rows}
        axis={axis}
        system={system}
        mode="history"
        ariaLabel="Observed summer Secchi depth by year"
      >
        <Line
          isAnimationActive={false}
          dataKey="observed"
          stroke={CHART_COLORS.observed}
          strokeWidth={2.5}
          dot={{ r: 2.5, fill: CHART_COLORS.observed }}
          activeDot={{ r: 4 }}
          name="Observed"
        />
      </ChartFrame>
      <div className="mt-1 flex flex-wrap gap-x-5 gap-y-2 text-sm text-slate-700" aria-label="Observed record legend">
        <LegendItem className="bg-lake-accent" label="Observed Secchi depth" />
      </div>
    </section>
  );
}

function ForecastChart({ detail, system }) {
  const rows = forecastRows(detail);
  const axis = axisSpec(chartDomain(rows, ["lower95", "upper95", "forecast"]));
  const firstYear = rows[0]?.year;
  const lastYear = rows.at(-1)?.year;

  return (
    <section
      data-claro-target="trends-forecast-chart"
      className="border-t border-amber-200 pt-6"
      aria-labelledby="baseline-outlook-heading"
    >
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h3 id="baseline-outlook-heading" className="section-subheading">Baseline outlook</h3>
        <span className="text-sm font-medium text-amber-900">
          {firstYear}–{lastYear} · modeled reference range
        </span>
      </div>
      <p className="mt-1 max-w-3xl text-sm text-slate-600">
        The center line holds the lake near its recent clarity level. The shaded bands show how wide the historical uncertainty range is around that baseline.
      </p>
      <ChartFrame
        rows={rows}
        axis={axis}
        system={system}
        mode="forecast"
        ariaLabel="Baseline Secchi depth outlook with empirical uncertainty ranges"
      >
        <Area
          dataKey={(row) => (row.lower95 == null ? null : [row.lower95, row.upper95])}
          stroke="none"
          fill={CHART_COLORS.range95}
          fillOpacity={0.95}
          isAnimationActive={false}
        />
        <Area
          dataKey={(row) => (row.lower80 == null ? null : [row.lower80, row.upper80])}
          stroke="none"
          fill={CHART_COLORS.range80}
          fillOpacity={0.42}
          isAnimationActive={false}
        />
        <Line
          isAnimationActive={false}
          dataKey="forecast"
          stroke={CHART_COLORS.forecast}
          strokeWidth={3}
          dot={{ r: 4, fill: CHART_COLORS.forecast, stroke: "#ffffff", strokeWidth: 1.5 }}
          activeDot={{ r: 5 }}
          name="Baseline outlook"
        />
      </ChartFrame>
      <div className="mt-1 flex flex-wrap gap-x-5 gap-y-2 text-sm text-slate-700" aria-label="Forecast legend">
        <LegendItem className="bg-[#b47700]" label="Baseline outlook" />
        <LegendItem className="bg-amber-300" label="80% empirical range" />
        <LegendItem className="bg-amber-100" label="95% empirical range" />
      </div>
    </section>
  );
}

export function TrendsChart({ detail }) {
  const { system } = useUnitSystem();
  const hasHistory = detail.history.length > 0;
  const hasForecast = detail.forecast.length > 0;

  if (!hasHistory && !hasForecast) {
    return <p className="mt-6 text-sm text-slate-600">No chartable observations are available for this lake.</p>;
  }

  return (
    <div className="mt-6 space-y-7" aria-label="Lake clarity trends">
      {hasHistory && <HistoryChart detail={detail} system={system} />}
      {hasForecast && <ForecastChart detail={detail} system={system} />}
    </div>
  );
}
