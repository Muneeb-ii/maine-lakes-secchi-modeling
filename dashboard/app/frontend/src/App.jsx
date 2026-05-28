import { useEffect, useMemo, useRef, useState } from "react";
import {
  Area,
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
import {
  Activity,
  ArrowRight,
  Beaker,
  Bookmark,
  Gauge,
  MapPin,
  RotateCcw,
  Search,
  Sparkles,
  Thermometer,
  Droplet,
  Layers,
} from "lucide-react";
import {
  buildPayloadFeatures,
  parseApiError,
  parseLakeSearchResponse,
  parsePredictionResponse,
  validateFeatureConfig,
} from "./lib/contracts";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const RECENT_LAKES_KEY = "dashboardRecentLakes";
const SAVED_SCENARIOS_KEY = "dashboardSavedScenarios";

const iconMap = { Beaker, Droplet, Activity, Gauge, Thermometer };

function formatMeters(value) {
  if (typeof value !== "number" || Number.isNaN(value)) return "--";
  return `${value.toFixed(2)} m`;
}

function formatSignedMeters(value) {
  if (typeof value !== "number" || Number.isNaN(value)) return "--";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(2)} m`;
}

export default function App() {
  const explainabilityRef = useRef(null);
  const [bootState, setBootState] = useState("loading");
  const [bootError, setBootError] = useState("");
  const [featureConfig, setFeatureConfig] = useState(null);
  const [lakeId, setLakeId] = useState("C3420");
  const [lakeName, setLakeName] = useState("");
  const [baseline, setBaseline] = useState(null);
  const [features, setFeatures] = useState({});
  const [forecast, setForecast] = useState(null);
  const [predictionError, setPredictionError] = useState("");
  const [chartHistory, setChartHistory] = useState([]);

  const [searchQuery, setSearchQuery] = useState("C3420");
  const [searchResults, setSearchResults] = useState([]);
  const [searchError, setSearchError] = useState("");
  const [searchFocused, setSearchFocused] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [activeSuggestion, setActiveSuggestion] = useState(-1);
  const [recentLakes, setRecentLakes] = useState(() => {
    try {
      const cached = localStorage.getItem(RECENT_LAKES_KEY);
      return cached ? JSON.parse(cached) : [];
    } catch {
      return [];
    }
  });

  const [savedScenarios, setSavedScenarios] = useState(() => {
    try {
      const cached = localStorage.getItem(SAVED_SCENARIOS_KEY);
      return cached ? JSON.parse(cached) : [];
    } catch {
      return [];
    }
  });
  const [compareScenarioId, setCompareScenarioId] = useState("");
  const [expandedExplainability, setExpandedExplainability] = useState(false);

  useEffect(() => {
    const boot = async () => {
      try {
        const [healthRes, featureRes] = await Promise.all([
          fetch(`${API_URL}/`),
          fetch(`${API_URL}/config/features`),
        ]);
        const healthData = await healthRes.json();
        const featureData = await featureRes.json();

        if (!healthRes.ok) {
          throw new Error(parseApiError(healthData));
        }
        if (!featureRes.ok) {
          throw new Error(parseApiError(featureData));
        }

        validateFeatureConfig(featureData);
        if (!healthData.models_loaded) {
          throw new Error(
            healthData?.startup_errors?.[0] || "Model is unavailable. Check backend startup logs."
          );
        }

        setFeatureConfig(featureData);
        setBootState("ready");
        await loadLakeBaseline("C3420");
      } catch (error) {
        setBootError(error.message || "Failed to initialize dashboard.");
        setBootState("error");
      }
    };

    boot();
  }, []);

  useEffect(() => {
    if (!searchFocused) return;
    const query = searchQuery.trim();
    if (!query) {
      setSearchResults([]);
      setSearchError("");
      return;
    }

    const timeoutId = setTimeout(async () => {
      try {
        setIsSearching(true);
        setSearchError("");
        const res = await fetch(
          `${API_URL}/lakes/search?q=${encodeURIComponent(query)}&limit=8`
        );
        const payload = await res.json();
        if (!res.ok) {
          throw new Error(parseApiError(payload));
        }
        setSearchResults(parseLakeSearchResponse(payload));
      } catch (error) {
        setSearchError(error.message || "Failed to search lakes.");
        setSearchResults([]);
      } finally {
        setIsSearching(false);
      }
    }, 220);

    return () => clearTimeout(timeoutId);
  }, [searchQuery, searchFocused]);

  useEffect(() => {
    if (!baseline || !featureConfig || Object.keys(features).length === 0) return;

    const timeoutId = setTimeout(async () => {
      try {
        setPredictionError("");
        const payloadFeatures = buildPayloadFeatures(features, baseline, featureConfig);
        const res = await fetch(`${API_URL}/predict_scenario`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            midas_id: lakeId,
            features: payloadFeatures,
            requested_outputs: ["prediction", "explainability"],
          }),
        });
        const rawData = await res.json();
        if (!res.ok) {
          throw new Error(parseApiError(rawData));
        }
        const parsed = parsePredictionResponse(rawData);
        setForecast(parsed);
        setChartHistory((previous) => {
          const next = [
            ...previous,
            {
              index: previous.length + 1,
              timeLabel: new Date().toLocaleTimeString(),
              prediction: parsed.predictionMeters,
              baseline: parsed.explainability.base_value,
            },
          ];
          if (next.length > 40) {
            return next.slice(next.length - 40);
          }
          return next;
        });
      } catch (error) {
        setPredictionError(error.message || "Prediction failed.");
      }
    }, 220);

    return () => clearTimeout(timeoutId);
  }, [features, baseline, featureConfig, lakeId]);

  useEffect(() => {
    localStorage.setItem(RECENT_LAKES_KEY, JSON.stringify(recentLakes.slice(0, 6)));
  }, [recentLakes]);

  useEffect(() => {
    localStorage.setItem(SAVED_SCENARIOS_KEY, JSON.stringify(savedScenarios.slice(0, 12)));
  }, [savedScenarios]);

  const loadLakeBaseline = async (midasId, nameHint) => {
    try {
      setPredictionError("");
      const normalized = String(midasId || "").trim().toUpperCase();
      if (!normalized) {
        throw new Error("Please provide a MIDAS ID.");
      }
      const res = await fetch(`${API_URL}/lake/${normalized}`);
      const payload = await res.json();
      if (!res.ok) {
        throw new Error(parseApiError(payload));
      }

      setLakeId(normalized);
      setSearchQuery(normalized);
      setLakeName(nameHint || payload.lake_name || "Unknown Ecosystem");
      setBaseline(payload.baseline);
      setFeatures(payload.baseline);
      setForecast(null);
      setChartHistory([]);
      setSearchFocused(false);
      setActiveSuggestion(-1);
      setRecentLakes((previous) => {
        const deduped = previous.filter((item) => item.midasId !== normalized);
        return [{ midasId: normalized, lakeName: nameHint || payload.lake_name }, ...deduped];
      });
    } catch (error) {
      setPredictionError(error.message || "Failed to load lake profile.");
    }
  };

  const selectedCompareScenario = useMemo(
    () => savedScenarios.find((scenario) => scenario.id === compareScenarioId),
    [savedScenarios, compareScenarioId]
  );

  const scenarioDelta =
    selectedCompareScenario && forecast
      ? forecast.predictionMeters - selectedCompareScenario.predictionMeters
      : null;

  const topExplainability = useMemo(() => {
    if (!forecast?.explainability?.waterfall) return [];
    return [...forecast.explainability.waterfall]
      .sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution))
      .slice(0, 3);
  }, [forecast]);

  const chartData = useMemo(() => chartHistory.map((point) => ({ ...point })), [chartHistory]);

  const handleFeatureChange = (key, value) => {
    setFeatures((previous) => ({ ...previous, [key]: Number(value) }));
  };

  const handleSearchKeyDown = async (event) => {
    if (!searchFocused) return;

    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveSuggestion((previous) =>
        Math.min(previous + 1, Math.max(searchResults.length - 1, 0))
      );
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveSuggestion((previous) => Math.max(previous - 1, 0));
    } else if (event.key === "Enter") {
      event.preventDefault();
      if (activeSuggestion >= 0 && searchResults[activeSuggestion]) {
        const match = searchResults[activeSuggestion];
        await loadLakeBaseline(match.midasId, match.lakeName);
      } else {
        await loadLakeBaseline(searchQuery);
      }
    } else if (event.key === "Escape") {
      setSearchFocused(false);
      setActiveSuggestion(-1);
    }
  };

  const resetToBaseline = () => {
    if (!baseline) return;
    setFeatures({ ...baseline });
  };

  const saveScenario = () => {
    if (!forecast) return;
    const scenario = {
      id: `${Date.now()}`,
      lakeId,
      lakeName,
      predictionMeters: forecast.predictionMeters,
      timestamp: new Date().toISOString(),
      features,
    };
    setSavedScenarios((previous) => [scenario, ...previous.filter((item) => item.id !== scenario.id)]);
    setCompareScenarioId(scenario.id);
  };

  const scrollToExplainability = () => {
    explainabilityRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  if (bootState === "loading") {
    return (
      <div className="min-h-screen flex items-center justify-center dashboard-bg">
        <div className="panel px-8 py-10 text-center">
          <div className="text-xl font-semibold text-cyan-200">Connecting to Lake Inference Engine...</div>
          <div className="mt-3 text-sm text-slate-400">Loading model contract and feature definitions.</div>
        </div>
      </div>
    );
  }

  if (bootState === "error") {
    return (
      <div className="min-h-screen flex items-center justify-center dashboard-bg px-6">
        <div className="panel max-w-xl p-8">
          <h1 className="text-2xl font-semibold text-red-300">Dashboard Initialization Failed</h1>
          <p className="text-sm text-slate-300 mt-3">{bootError}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-bg min-h-screen text-slate-100">
      <div className="max-w-[1600px] mx-auto p-6 lg:p-8 space-y-6">
        <header className="panel p-6">
          <div className="flex flex-col gap-6 xl:flex-row xl:items-center xl:justify-between">
            <div>
              <h1 className="text-3xl lg:text-4xl font-semibold tracking-tight gradient-title">
                Lake Clarity Scenario Studio
              </h1>
              <p className="text-slate-300 mt-2">
                Decision-first simulation for {lakeId} {lakeName ? `• ${lakeName}` : ""}
              </p>
              <div className="mt-3 text-xs text-slate-400">
                Model {forecast?.modelId || featureConfig?.active_model?.model_id || "unknown"} • Version{" "}
                {forecast?.modelVersion || featureConfig?.active_model?.model_version || "unknown"}
              </div>
            </div>
            <div className="w-full xl:w-[420px] relative">
              <Search className="absolute left-3 top-3.5 w-4 h-4 text-slate-500" />
              <input
                type="text"
                value={searchQuery}
                onChange={(event) => {
                  setSearchQuery(event.target.value);
                  setActiveSuggestion(-1);
                }}
                onFocus={() => setSearchFocused(true)}
                onBlur={() => setTimeout(() => setSearchFocused(false), 120)}
                onKeyDown={handleSearchKeyDown}
                placeholder="Search by MIDAS or lake name..."
                className="w-full h-11 rounded-xl pl-10 pr-4 bg-slate-900/70 border border-slate-700/70 focus:ring-2 focus:ring-cyan-400/60 outline-none"
                aria-label="Search lake"
              />
              {searchFocused && (
                <div className="absolute z-20 mt-2 w-full panel p-2 max-h-72 overflow-auto">
                  {isSearching && <div className="p-2 text-xs text-slate-400">Searching...</div>}
                  {searchError && <div className="p-2 text-xs text-red-300">{searchError}</div>}
                  {!isSearching &&
                    searchResults.map((result, index) => (
                      <button
                        key={result.midasId}
                        className={`w-full text-left px-3 py-2 rounded-lg text-sm transition ${
                          index === activeSuggestion ? "bg-cyan-500/20 text-cyan-100" : "hover:bg-slate-800/80"
                        }`}
                        onMouseDown={() => loadLakeBaseline(result.midasId, result.lakeName)}
                      >
                        <div className="font-medium">{result.lakeName}</div>
                        <div className="text-xs text-slate-400">{result.midasId}</div>
                      </button>
                    ))}
                  {!isSearching && searchResults.length === 0 && searchQuery.trim() && !searchError && (
                    <div className="p-2 text-xs text-slate-400">No matches found.</div>
                  )}
                  {!searchQuery.trim() && recentLakes.length > 0 && (
                    <div className="pt-1">
                      <div className="px-2 py-1 text-xs uppercase tracking-wider text-slate-500">Recent Lakes</div>
                      {recentLakes.map((item) => (
                        <button
                          key={item.midasId}
                          className="w-full text-left px-3 py-2 rounded-lg text-sm hover:bg-slate-800/80 transition"
                          onMouseDown={() => loadLakeBaseline(item.midasId, item.lakeName)}
                        >
                          <div className="font-medium">{item.lakeName}</div>
                          <div className="text-xs text-slate-400">{item.midasId}</div>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </header>

        <section className="grid grid-cols-1 xl:grid-cols-12 gap-6">
          <div className="xl:col-span-8 space-y-6">
            <div className="panel p-6 relative overflow-hidden">
              <div className="absolute -top-20 -right-20 w-72 h-72 rounded-full blur-3xl bg-cyan-500/20 pointer-events-none" />
              <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-6 relative">
                <div>
                  <div className="text-xs uppercase tracking-[0.18em] text-slate-400">Current Prediction</div>
                  <div className="text-6xl lg:text-7xl font-semibold leading-none mt-3">
                    {forecast ? formatMeters(forecast.predictionMeters) : "--"}
                  </div>
                  <div className="mt-3 text-sm text-slate-300">Secchi depth target clarity</div>
                </div>
                <div className="flex items-center gap-5 text-slate-300">
                  <ArrowRight className="w-6 h-6 text-slate-500" />
                  <div>
                    <div className="text-xs uppercase tracking-[0.12em] text-slate-500">Model Baseline</div>
                    <div className="text-2xl font-medium mt-1">
                      {forecast ? formatMeters(forecast.explainability.base_value) : "--"}
                    </div>
                  </div>
                </div>
                <div>
                  <div className="text-xs uppercase tracking-[0.12em] text-slate-500">Delta vs Baseline</div>
                  <div className="text-2xl font-medium mt-1 text-cyan-300">
                    {forecast
                      ? formatSignedMeters(
                          forecast.predictionMeters - forecast.explainability.base_value
                        )
                      : "--"}
                  </div>
                </div>
              </div>
              {predictionError && <div className="mt-4 text-sm text-red-300">{predictionError}</div>}
            </div>

            <div className="panel p-4 flex flex-wrap items-center gap-3">
              <button className="action-button" onClick={resetToBaseline}>
                <RotateCcw className="w-4 h-4" /> Reset to Baseline
              </button>
              <button className="action-button" onClick={saveScenario} disabled={!forecast}>
                <Bookmark className="w-4 h-4" /> Save Scenario
              </button>
              <button className="action-button" onClick={scrollToExplainability}>
                <Sparkles className="w-4 h-4" /> Explain This Change
              </button>
              <div className="flex items-center gap-2 ml-auto min-w-[260px]">
                <Layers className="w-4 h-4 text-slate-400" />
                <select
                  value={compareScenarioId}
                  onChange={(event) => setCompareScenarioId(event.target.value)}
                  className="w-full h-10 rounded-lg bg-slate-900/70 border border-slate-700/70 px-3 text-sm focus:ring-2 focus:ring-cyan-400/50 outline-none"
                >
                  <option value="">Compare scenario...</option>
                  {savedScenarios.map((scenario) => (
                    <option key={scenario.id} value={scenario.id}>
                      {scenario.lakeId} • {new Date(scenario.timestamp).toLocaleTimeString()}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {selectedCompareScenario && (
              <div className="panel p-4 text-sm text-slate-200">
                <div>
                  Comparing against saved scenario from{" "}
                  {new Date(selectedCompareScenario.timestamp).toLocaleString()}.
                </div>
                <div className="mt-1 text-cyan-300">
                  Delta vs selected scenario: {formatSignedMeters(scenarioDelta)}
                </div>
              </div>
            )}

            <div className="panel p-6 h-[360px]">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-sm uppercase tracking-[0.15em] text-cyan-300 flex items-center gap-2">
                  <Activity className="w-4 h-4" /> Scenario Trajectory
                </h2>
                <div className="text-xs text-slate-400">
                  {chartData.length} points • Live updates
                </div>
              </div>
              <div className="h-[280px]">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={chartData}>
                    <defs>
                      <linearGradient id="predictionFill" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#22d3ee" stopOpacity={0.4} />
                        <stop offset="95%" stopColor="#22d3ee" stopOpacity={0.02} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.15)" />
                    <XAxis dataKey="index" tick={{ fill: "#94a3b8", fontSize: 11 }} />
                    <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} />
                    <RechartsTooltip
                      cursor={{ stroke: "#64748b", strokeDasharray: "4 4" }}
                      contentStyle={{
                        borderRadius: "12px",
                        borderColor: "rgba(56,189,248,0.35)",
                        backgroundColor: "#0b1220",
                      }}
                      formatter={(value, name) => [formatMeters(Number(value)), name]}
                      labelFormatter={(label) => `Sample #${label}`}
                    />
                    <ReferenceLine
                      y={forecast?.explainability?.base_value}
                      stroke="rgba(250, 204, 21, 0.8)"
                      strokeDasharray="5 5"
                      ifOverflow="extendDomain"
                    />
                    <Line
                      type="monotone"
                      dataKey="baseline"
                      stroke="#facc15"
                      strokeWidth={2}
                      dot={false}
                      name="Baseline"
                    />
                    <Area
                      type="monotone"
                      dataKey="prediction"
                      stroke="#22d3ee"
                      strokeWidth={2.8}
                      fill="url(#predictionFill)"
                      name="Prediction"
                      animationDuration={280}
                    />
                    {chartData[0] && (
                      <ReferenceDot
                        x={chartData[0].index}
                        y={chartData[0].prediction}
                        r={5}
                        stroke="#22d3ee"
                        fill="#0f172a"
                      />
                    )}
                    {chartData[chartData.length - 1] && (
                      <ReferenceDot
                        x={chartData[chartData.length - 1].index}
                        y={chartData[chartData.length - 1].prediction}
                        r={6}
                        stroke="#a78bfa"
                        fill="#a78bfa"
                      />
                    )}
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          <div className="xl:col-span-4 space-y-6">
            <div className="panel p-5 sticky top-4">
              <div className="flex items-center gap-2 text-cyan-300 text-sm uppercase tracking-[0.14em]">
                <MapPin className="w-4 h-4" /> Locked Lake Profile
              </div>
              <div className="mt-3 text-xs text-slate-400">
                Geographic fields are locked to the selected lake and cannot be edited.
              </div>
              {baseline && (
                <div className="grid grid-cols-2 gap-3 mt-4">
                  <div className="info-card">
                    <div className="info-label">Latitude</div>
                    <div className="info-value">{baseline.LATITUDE?.toFixed(4)}</div>
                  </div>
                  <div className="info-card">
                    <div className="info-label">Longitude</div>
                    <div className="info-value">{baseline.LONGITUDE?.toFixed(4)}</div>
                  </div>
                  <div className="info-card">
                    <div className="info-label">Area (Acres)</div>
                    <div className="info-value">{baseline.AREA_ACRES?.toLocaleString()}</div>
                  </div>
                  <div className="info-card">
                    <div className="info-label">Max Depth</div>
                    <div className="info-value">{baseline.DEPTH_MAX_FEET?.toFixed(1)} ft</div>
                  </div>
                </div>
              )}
            </div>

            <div className="panel p-5 max-h-[430px] overflow-y-auto">
              <h2 className="text-sm uppercase tracking-[0.14em] text-cyan-300 flex items-center gap-2">
                <Sparkles className="w-4 h-4" /> Tunable Parameters
              </h2>
              <div className="space-y-5 mt-4">
                {(featureConfig?.editable_features || []).map((key) => {
                  const config = featureConfig.features[key];
                  const val = features[key] !== undefined ? features[key] : 0;
                  let sMin = config?.slider?.min ?? 0;
                  let sMax = config?.slider?.max ?? 100;
                  if (baseline && baseline[key] > sMax) sMax = baseline[key] * 1.5;
                  if (baseline && baseline[key] < sMin) sMin = baseline[key] * 0.5;
                  const Icon = iconMap[config.icon] || Beaker;

                  return (
                    <div key={key} className="slider-group">
                      <div className="flex justify-between items-center text-sm">
                        <div className="flex items-center gap-2 text-slate-200">
                          <Icon className="w-4 h-4 text-slate-400" />
                          {config.label}
                        </div>
                        <div className="font-mono text-cyan-300">{val.toFixed(2)}</div>
                      </div>
                      <input
                        type="range"
                        className="w-full mt-2"
                        min={sMin}
                        max={sMax}
                        step={config?.slider?.step ?? 0.1}
                        value={val}
                        onChange={(event) => handleFeatureChange(key, event.target.value)}
                      />
                    </div>
                  );
                })}
              </div>
            </div>

            <div ref={explainabilityRef} className="panel p-5">
              <h2 className="text-sm uppercase tracking-[0.14em] text-cyan-300 flex items-center gap-2">
                <Gauge className="w-4 h-4" /> Explainability
              </h2>
              {forecast?.explainability?.waterfall?.length ? (
                <>
                  <div className="mt-4 space-y-3">
                    {topExplainability.map((item) => (
                      <div key={item.feature} className="info-card">
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-slate-200">{item.feature}</span>
                          <span
                            className={`text-sm font-medium ${
                              item.contribution >= 0 ? "text-cyan-300" : "text-rose-300"
                            }`}
                          >
                            {formatSignedMeters(item.contribution)}
                          </span>
                        </div>
                        <div className="mt-1 text-xs text-slate-400">
                          Input value:{" "}
                          {item.rendered_value === null ? "aggregate" : Number(item.rendered_value).toFixed(2)}
                        </div>
                      </div>
                    ))}
                  </div>
                  <button
                    className="mt-4 text-sm text-cyan-300 hover:text-cyan-200 transition"
                    onClick={() => setExpandedExplainability((previous) => !previous)}
                  >
                    {expandedExplainability ? "Hide technical breakdown" : "Show technical breakdown"}
                  </button>
                  {expandedExplainability && (
                    <div className="mt-4 space-y-2 max-h-56 overflow-y-auto pr-1">
                      {forecast.explainability.waterfall.map((item, index) => (
                        <div key={`${item.feature}-${index}`} className="text-xs text-slate-300 flex justify-between gap-4">
                          <span>{item.feature}</span>
                          <span>{formatSignedMeters(item.contribution)}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </>
              ) : (
                <div className="mt-4 text-sm text-amber-200">
                  Explainability data was not provided by the current model output.
                </div>
              )}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
