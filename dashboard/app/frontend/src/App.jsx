import { useCallback, useState } from "react";
import { AppShell } from "./components/layout/AppShell";
import { BootScreen } from "./components/layout/BootScreen";
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
import { UNKNOWN_LAKE_NAME } from "./lib/copy";

export default function App() {
  const [lakeId, setLakeId] = useState("C3420");
  const [lakeName, setLakeName] = useState("");
  const [baseline, setBaseline] = useState(null);
  const [features, setFeatures] = useState({});
  const [lakeSupport, setLakeSupport] = useState(null);

  const handleLakeLoaded = useCallback((normalized, name, lakeBaseline, support) => {
    setLakeId(normalized);
    setLakeName(name === UNKNOWN_LAKE_NAME ? "" : name);
    setBaseline(lakeBaseline);
    setFeatures(lakeBaseline);
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
  } = useScenarioPrediction({ lakeId, baseline, features, featureConfig });

  const {
    savedScenarios,
    compareScenarioId,
    setCompareScenarioId,
    selectedCompareScenario,
    saveScenario,
  } = useSavedScenarios();

  const scenarioDelta =
    selectedCompareScenario && forecast
      ? forecast.predictionMeters - selectedCompareScenario.predictionMeters
      : null;

  const selectLake = async (midasId, nameHint) => {
    try {
      setPredictionError("");
      const result = await loadLakeBaseline(midasId, nameHint);
      if (!result) return;
      const { normalized, name, lakeSupport: support } = result;
      lakeSearch.setSearchQuery(normalized);
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
        Math.min(previous + 1, Math.max(lakeSearch.searchResults.length - 1, 0))
      );
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      lakeSearch.setActiveSuggestion((previous) => Math.max(previous - 1, 0));
    } else if (event.key === "Enter") {
      event.preventDefault();
      if (lakeSearch.activeSuggestion >= 0 && lakeSearch.searchResults[lakeSearch.activeSuggestion]) {
        const match = lakeSearch.searchResults[lakeSearch.activeSuggestion];
        await selectLake(match.midasId, match.lakeName);
      } else {
        await selectLake(lakeSearch.searchQuery);
      }
    } else if (event.key === "Escape") {
      lakeSearch.setSearchFocused(false);
      lakeSearch.setActiveSuggestion(-1);
    }
  };

  const handleFeatureChange = (key, value) => {
    setFeatures((previous) => ({ ...previous, [key]: Number(value) }));
  };

  const resetToBaseline = () => {
    if (!baseline) return;
    setFeatures({ ...baseline });
  };

  if (bootState !== "ready") {
    return <BootScreen state={bootState} error={bootError} />;
  }

  return (
    <AppShell
      header={
        <DashboardHeader
          lakeId={lakeId}
          lakeName={lakeName}
          lakeSupport={lakeSupport}
          searchProps={{
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
      }
      lakeSection={<LakeProfileCard baseline={baseline} />}
      parametersSection={
        <ParameterPanel
          featureConfig={featureConfig}
          features={features}
          baseline={baseline}
          onFeatureChange={handleFeatureChange}
        />
      }
      resultsSection={
        <>
          <PredictionHero
            forecast={forecast}
            predictionError={predictionError}
            isPredicting={isPredicting}
          />
          <ScenarioActionBar
            onReset={resetToBaseline}
            onSave={() => saveScenario({ lakeId, lakeName, forecast, features })}
            canSave={Boolean(forecast)}
            savedScenarios={savedScenarios}
            compareScenarioId={compareScenarioId}
            onCompareChange={setCompareScenarioId}
          />
          <ScenarioCompareBanner scenario={selectedCompareScenario} delta={scenarioDelta} />
          <TrajectoryChart
            chartData={chartHistory}
            forecast={forecast}
            compareScenario={selectedCompareScenario}
            latestChange={latestChange}
            onClearTrajectory={resetChart}
          />
        </>
      }
      driversSection={
        <ExplainabilityPanel forecast={forecast} featureConfig={featureConfig} />
      }
    />
  );
}
