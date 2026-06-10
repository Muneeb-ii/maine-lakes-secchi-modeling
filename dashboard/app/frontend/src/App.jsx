import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { BarChart3, FlaskConical, Waves } from "lucide-react";
import { ClaroGuide } from "./components/claro/ClaroGuide";
import { AppFooter } from "./components/layout/AppFooter";
import { AppShell } from "./components/layout/AppShell";
import { BootScreen } from "./components/layout/BootScreen";
import { ContributorsPage } from "./components/layout/ContributorsPage";
import { InfoPageNav } from "./components/layout/InfoPageNav";
import { LandingPage } from "./components/layout/LandingPage";
import { ModelingProcessPage } from "./components/layout/ModelingProcessPage";
import { PageFrame } from "./components/layout/PageFrame";
import { DashboardHeader } from "./components/lake/DashboardHeader";
import { LakeProfileCard } from "./components/lake/LakeProfileCard";
import { ExplainabilityPanel } from "./components/explainability/ExplainabilityPanel";
import { ParameterPanel } from "./components/parameters/ParameterPanel";
import { PredictionHero } from "./components/scenario/PredictionHero";
import { ScenarioActionBar } from "./components/scenario/ScenarioActionBar";
import { ScenarioCompareBanner } from "./components/scenario/ScenarioCompareBanner";
import { TrajectoryChart } from "./components/scenario/TrajectoryChart";
import { useDashboardBoot } from "./hooks/useDashboardBoot";
import { useLakeSearch } from "./hooks/useLakeSearch";
import { useSavedScenarios } from "./hooks/useSavedScenarios";
import { useScenarioPrediction } from "./hooks/useScenarioPrediction";
import {
  LANDING_DESTINATIONS,
  LANDING_TRENDS_PAGE_NOTE,
  PLAYGROUND_EYEBROW,
  SCENARIO_DELETED_STATUS,
  SCENARIO_DELETE_CONFIRM,
  SCENARIO_LOAD_CONFIRM,
  SCENARIO_LOADED_STATUS,
  SCENARIO_SAVED_STATUS,
  UNKNOWN_LAKE_NAME,
  parseLakeSearchInput,
} from "./lib/copy";
import { PAGE_CONTAINER } from "./lib/layoutClasses";
import { stepSearchSuggestion } from "./lib/playgroundGuards";
import { ROUTES, navigateTo } from "./lib/routes";
import { getClaroRouteId } from "./lib/claroTourContent";
import {
  buildFeaturesFromSnapshot,
  compareIdForLake,
  filterIncludedFeaturesForConfig,
  hasChangesFromSnapshot,
  hasScenarioChangesFromBaseline,
  isCompareScenarioActive,
} from "./lib/savedScenarios";
import { SECTION_ACCENTS } from "./lib/theme";
import { SectionHeadingIcon } from "./components/ui/SectionHeadingIcon";

const SLIDER_IDLE_COMMIT_MS = 700;

function finiteEditableFeatures(featureConfig, values) {
  return (featureConfig?.editable_features || []).filter((key) => Number.isFinite(Number(values?.[key])));
}

function defaultValueForFeature(featureConfig, key) {
  const slider = featureConfig?.features?.[key]?.slider || {};
  const min = Number(slider.min ?? 0);
  const max = Number(slider.max ?? 100);
  return (min + max) / 2;
}

function useCurrentPath() {
  const [path, setPath] = useState(() => window.location.pathname);

  useEffect(() => {
    const handlePopState = () => setPath(window.location.pathname);
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  return path;
}

function TrendsPage() {
  return (
    <PageFrame>
      <section className={`${PAGE_CONTAINER} flex min-h-[calc(100vh-96px)] flex-col justify-center py-12`}>
        <InfoPageNav
          eyebrow={LANDING_DESTINATIONS.trends.title}
          eyebrowTone="amber"
        />
        <div
          data-claro-target="trends-page"
          className={`panel p-8 ${SECTION_ACCENTS.trends.panelAccentClass}`}
          style={{
            backgroundImage:
              "linear-gradient(135deg, rgba(230, 159, 0, 0.08) 0%, #ffffff 55%)",
          }}
        >
          <h1 className="display-title flex items-center gap-3 text-4xl">
            <SectionHeadingIcon section="trends" icon={BarChart3} />
            {LANDING_DESTINATIONS.trends.status}
          </h1>
          <p className="mt-4 max-w-2xl text-lg leading-8 text-slate-700">
            {LANDING_DESTINATIONS.trends.description} {LANDING_TRENDS_PAGE_NOTE}
          </p>
          <button
            type="button"
            onClick={() => navigateTo(ROUTES.playground)}
            className="action-button-primary mt-8"
          >
            <FlaskConical className="h-4 w-4" aria-hidden />
            {LANDING_DESTINATIONS.playground.cta}
          </button>
        </div>
      </section>
    </PageFrame>
  );
}

function PlaygroundPage() {
  const [lakeId, setLakeId] = useState("C3420");
  const [lakeName, setLakeName] = useState("");
  const [baseline, setBaseline] = useState(null);
  const [features, setFeatures] = useState({});
  const [includedFeatures, setIncludedFeatures] = useState([]);
  const [featureCommitVersion, setFeatureCommitVersion] = useState(0);
  const [lakeSupport, setLakeSupport] = useState(null);
  const [scenarioActionStatus, setScenarioActionStatus] = useState("");
  const featureCommitTimerRef = useRef(null);

  const handleLakeLoaded = useCallback((normalized, name, lakeBaseline, support, config) => {
    if (featureCommitTimerRef.current) {
      window.clearTimeout(featureCommitTimerRef.current);
      featureCommitTimerRef.current = null;
    }
    setLakeId(normalized);
    setLakeName(name === UNKNOWN_LAKE_NAME ? "" : name);
    setBaseline(lakeBaseline);
    setFeatures(lakeBaseline);
    if (config) {
      setIncludedFeatures(finiteEditableFeatures(config, lakeBaseline));
    }
    setFeatureCommitVersion(0);
    setLakeSupport(support);
    return { normalized, name };
  }, []);

  const { bootState, bootError, featureConfig, loadLakeBaseline } = useDashboardBoot({
    onLakeLoaded: handleLakeLoaded,
  });

  const lakeSearch = useLakeSearch();
  const {
    forecast,
    predictionError,
    setPredictionError,
    isPredicting,
    chartHistory,
    latestChange,
    resetChart,
    clearForecast,
  } = useScenarioPrediction({
    lakeId,
    baseline,
    features,
    featureConfig,
    includedFeatures,
    featureCommitVersion,
  });

  const {
    savedScenarios,
    compareScenarioId,
    setCompareScenarioId,
    saveScenario,
    deleteScenario,
    scenariosForCurrentLake,
    otherLakeScenarioCount,
  } = useSavedScenarios();

  const lakeSavedScenarios = scenariosForCurrentLake(lakeId);
  const otherLakeSaveCount = otherLakeScenarioCount(lakeId);
  const lakeCompareScenarioId = compareIdForLake(savedScenarios, compareScenarioId, lakeId);
  const activeCompareScenario = useMemo(() => {
    if (!lakeCompareScenarioId) return null;
    return savedScenarios.find((scenario) => scenario.id === lakeCompareScenarioId) ?? null;
  }, [lakeCompareScenarioId, savedScenarios]);

  const canSave =
    Boolean(forecast) &&
    hasScenarioChangesFromBaseline(baseline, features, featureConfig, includedFeatures);

  const scenarioDelta =
    isCompareScenarioActive(activeCompareScenario, lakeId, forecast) && forecast
      ? forecast.predictionMeters - activeCompareScenario.predictionMeters
      : null;

  const handleSaveScenario = (label) => {
    const saved = saveScenario({
      lakeId,
      lakeName,
      forecast,
      features,
      includedFeatures,
      label,
    });
    if (saved) {
      setScenarioActionStatus(SCENARIO_SAVED_STATUS);
    }
    return saved;
  };

  const handleLoadScenario = () => {
    if (!activeCompareScenario || !baseline) return;
    if (
      hasChangesFromSnapshot(features, includedFeatures, activeCompareScenario, featureConfig) &&
      !window.confirm(SCENARIO_LOAD_CONFIRM)
    ) {
      return;
    }
    if (featureCommitTimerRef.current) {
      window.clearTimeout(featureCommitTimerRef.current);
      featureCommitTimerRef.current = null;
    }
    setFeatures(
      buildFeaturesFromSnapshot(activeCompareScenario, baseline, featureConfig)
    );
    setIncludedFeatures(
      filterIncludedFeaturesForConfig(activeCompareScenario.includedFeatures, featureConfig)
    );
    setFeatureCommitVersion((previous) => previous + 1);
    setScenarioActionStatus(SCENARIO_LOADED_STATUS);
  };

  const handleDeleteScenario = () => {
    if (!lakeCompareScenarioId) return;
    if (!window.confirm(SCENARIO_DELETE_CONFIRM)) return;
    const deleted = deleteScenario(lakeCompareScenarioId);
    if (deleted) {
      setScenarioActionStatus(SCENARIO_DELETED_STATUS);
    }
  };

  const selectLake = async (midasId, nameHint) => {
    try {
      setPredictionError("");
      const result = await loadLakeBaseline(midasId, nameHint, featureConfig);
      if (!result) return;
      const { normalized, name, lakeSupport: support } = result;
      lakeSearch.setSearchQuery("");
      lakeSearch.setSearchFocused(false);
      lakeSearch.setActiveSuggestion(-1);
      lakeSearch.pushRecentLake(normalized, name);
      setLakeSupport(support);
      clearForecast();
      resetChart();
    } catch (error) {
      setPredictionError(error.message || "Failed to load lake profile.");
    }
  };

  const handleSearchKeyDown = async (event) => {
    if (!lakeSearch.searchFocused) return;

    if (event.key === "ArrowDown") {
      event.preventDefault();
      lakeSearch.setActiveSuggestion((previous) =>
        stepSearchSuggestion(previous, "down", lakeSearch.searchResults.length)
      );
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      lakeSearch.setActiveSuggestion((previous) =>
        stepSearchSuggestion(previous, "up", lakeSearch.searchResults.length)
      );
    } else if (event.key === "Enter") {
      event.preventDefault();
      if (lakeSearch.activeSuggestion >= 0 && lakeSearch.searchResults[lakeSearch.activeSuggestion]) {
        const match = lakeSearch.searchResults[lakeSearch.activeSuggestion];
        await selectLake(match.midasId, match.lakeName);
      } else {
        const { midasId, nameHint } = parseLakeSearchInput(lakeSearch.searchQuery);
        await selectLake(midasId || lakeSearch.searchQuery, nameHint);
      }
    } else if (event.key === "Escape") {
      lakeSearch.setSearchFocused(false);
      lakeSearch.setActiveSuggestion(-1);
    }
  };

  const handleFeatureChange = (key, value) => {
    setFeatures((previous) => ({ ...previous, [key]: Number(value) }));
    if (featureCommitTimerRef.current) {
      window.clearTimeout(featureCommitTimerRef.current);
    }
    featureCommitTimerRef.current = window.setTimeout(() => {
      setFeatureCommitVersion((previous) => previous + 1);
      featureCommitTimerRef.current = null;
    }, SLIDER_IDLE_COMMIT_MS);
  };

  const handleFeatureCommit = () => {
    if (featureCommitTimerRef.current) {
      window.clearTimeout(featureCommitTimerRef.current);
      featureCommitTimerRef.current = null;
    }
    setFeatureCommitVersion((previous) => previous + 1);
  };

  const handleFeatureIncludedChange = (key, included) => {
    setIncludedFeatures((previous) => {
      const next = new Set(previous);
      if (included) {
        next.add(key);
      } else {
        next.delete(key);
      }
      return [...next];
    });

    if (included && !Number.isFinite(Number(features[key]))) {
      setFeatures((previous) => ({
        ...previous,
        [key]: defaultValueForFeature(featureConfig, key),
      }));
    }

    setFeatureCommitVersion((previous) => previous + 1);
  };

  const resetToBaseline = () => {
    if (!baseline) return;
    if (featureCommitTimerRef.current) {
      window.clearTimeout(featureCommitTimerRef.current);
      featureCommitTimerRef.current = null;
    }
    setFeatures({ ...baseline });
    setIncludedFeatures(finiteEditableFeatures(featureConfig, baseline));
    setFeatureCommitVersion((previous) => previous + 1);
    resetChart({ ...baseline });
  };

  const clearTrajectory = () => {
    resetChart();
  };

  useEffect(() => {
    return () => {
      if (featureCommitTimerRef.current) {
        window.clearTimeout(featureCommitTimerRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (!scenarioActionStatus) return undefined;
    const timer = window.setTimeout(() => setScenarioActionStatus(""), 4000);
    return () => window.clearTimeout(timer);
  }, [scenarioActionStatus]);

  if (bootState !== "ready") {
    return <BootScreen state={bootState} error={bootError} />;
  }

  return (
    <AppShell
      footer={
        <>
          <AppFooter />
          <ClaroGuide routeId={getClaroRouteId(ROUTES.playground)} />
        </>
      }
      header={
        <>
          <InfoPageNav
            className="mb-4"
            eyebrow={PLAYGROUND_EYEBROW}
            eyebrowIcon={Waves}
          />
          <DashboardHeader
            lakeSupport={lakeSupport}
            searchProps={{
              lakeId,
              lakeName,
              searchQuery: lakeSearch.searchQuery,
              onSearchQueryChange: lakeSearch.setSearchQuery,
              searchResults: lakeSearch.searchResults,
              searchError: lakeSearch.searchError,
              searchFocused: lakeSearch.searchFocused,
              onSearchFocusedChange: lakeSearch.setSearchFocused,
              isSearching: lakeSearch.isSearching,
              activeSuggestion: lakeSearch.activeSuggestion,
              onActiveSuggestionChange: lakeSearch.setActiveSuggestion,
              recentLakes: lakeSearch.recentLakes,
              onSelectLake: selectLake,
              onSearchKeyDown: handleSearchKeyDown,
            }}
          />
        </>
      }
      lakeSection={<LakeProfileCard baseline={baseline} />}
      parametersSection={
        <ParameterPanel
          featureConfig={featureConfig}
          features={features}
          baseline={baseline}
          includedFeatures={includedFeatures}
          onFeatureChange={handleFeatureChange}
          onFeatureCommit={handleFeatureCommit}
          onFeatureIncludedChange={handleFeatureIncludedChange}
        />
      }
      predictionSection={
        <PredictionHero
          forecast={forecast}
          predictionError={predictionError}
          isPredicting={isPredicting}
        />
      }
      scenarioSection={
        <ScenarioActionBar
          onReset={resetToBaseline}
          onSave={handleSaveScenario}
          onLoad={handleLoadScenario}
          canSave={canSave}
          lakeSavedScenarios={lakeSavedScenarios}
          otherLakeSaveCount={otherLakeSaveCount}
          compareScenarioId={lakeCompareScenarioId}
          onCompareChange={setCompareScenarioId}
          onDeleteScenario={handleDeleteScenario}
          actionStatus={scenarioActionStatus}
        />
      }
      trajectorySection={
        <div className="space-y-4">
          <ScenarioCompareBanner
            scenario={activeCompareScenario}
            delta={scenarioDelta}
            lakeName={lakeName || lakeId}
          />
          <TrajectoryChart
            chartData={chartHistory}
            forecast={forecast}
            compareScenario={activeCompareScenario}
            latestChange={latestChange}
            onClearTrajectory={clearTrajectory}
          />
        </div>
      }
      driversSection={
        <ExplainabilityPanel forecast={forecast} featureConfig={featureConfig} lakeId={lakeId} />
      }
    />
  );
}

export default function App() {
  const path = useCurrentPath();

  if (path === ROUTES.playground) return <PlaygroundPage />;
  if (path === ROUTES.trends) return <TrendsPage />;
  if (path === ROUTES.contributors) return <ContributorsPage />;
  if (path === ROUTES.modeling) return <ModelingProcessPage />;
  return <LandingPage />;
}
