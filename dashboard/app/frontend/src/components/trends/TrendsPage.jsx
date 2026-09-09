import { useEffect, useMemo, useState } from "react";
import { BarChart3, Map, Search, Waves } from "lucide-react";
import { ClaroGuide } from "../claro/ClaroGuide";
import { InfoPageNav } from "../layout/InfoPageNav";
import { PageFrame } from "../layout/PageFrame";
import { UnitSystemToggle } from "../layout/UnitSystemToggle";
import { SectionHeadingIcon } from "../ui/SectionHeadingIcon";
import { LakeMapPicker } from "../lake/LakeMapPicker";
import { LakeSearchCombobox } from "../lake/LakeSearchCombobox";
import { TrendsChart } from "./TrendsChart";
import { useTrendsData } from "../../hooks/useTrendsData";
import { API_URL, RECENT_LAKES_KEY } from "../../lib/constants";
import { parseLakeSearchResponse } from "../../lib/contracts";
import { PAGE_CONTAINER } from "../../lib/layoutClasses";
import { stepSearchSuggestion } from "../../lib/playgroundGuards";
import { getClaroRouteId } from "../../lib/claroTourContent";
import { ROUTES } from "../../lib/routes";
import { SECTION_ACCENTS } from "../../lib/theme";
import { formatQuantity } from "../../lib/units";
import { useUnitSystem } from "../../context/UnitSystemContext";

function readRecentLakes() {
  try {
    const cached = localStorage.getItem(RECENT_LAKES_KEY);
    const parsed = cached ? JSON.parse(cached) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function LakeDirectory({ lakes, selectedId, onSelect, isMapOpen, mapFocusLake, onOpenMap, onCloseMap }) {
  const [query, setQuery] = useState("");
  const [searchFocused, setSearchFocused] = useState(false);
  const [activeSuggestion, setActiveSuggestion] = useState(-1);
  const [recentLakes, setRecentLakes] = useState(readRecentLakes);
  const [lakeLocations, setLakeLocations] = useState({});
  const selectedLake = lakes.find((lake) => lake.midas_id === selectedId);

  useEffect(() => {
    let cancelled = false;
    fetch(`${API_URL}/lakes/locations`)
      .then((response) => (response.ok ? response.json() : null))
      .then((payload) => {
        if (cancelled || !payload) return;
        const next = {};
        parseLakeSearchResponse(payload).forEach((lake) => {
          next[lake.midasId.toLowerCase()] = lake;
        });
        setLakeLocations(next);
      })
      .catch(() => {
        // The directory remains usable without optional map-focus metadata.
      });
    return () => {
      cancelled = true;
    };
  }, []);
  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return lakes.filter((lake) => !needle || `${lake.lake_name} ${lake.midas_id}`.toLowerCase().includes(needle));
  }, [lakes, query]);
  const searchResults = useMemo(
    () =>
      filtered.slice(0, 8).map((lake) => ({
        midasId: lake.midas_id,
        lakeName: lake.lake_name,
        latitude: lakeLocations[lake.midas_id]?.latitude,
        longitude: lakeLocations[lake.midas_id]?.longitude,
        areaAcres: lakeLocations[lake.midas_id]?.areaAcres,
      })),
    [filtered, lakeLocations]
  );

  const selectLake = (midasId, lakeName) => {
    const normalized = String(midasId || "").toLowerCase();
    const selected = lakes.find((lake) => lake.midas_id === normalized || lake.midas_id === midasId);
    if (!selected) return;
    const name = lakeName || selected.lake_name;
    onSelect(selected.midas_id);
    setQuery("");
    setSearchFocused(false);
    setActiveSuggestion(-1);
    setRecentLakes((previous) => {
      const next = [
        { midasId: selected.midas_id, lakeName: name },
        ...previous.filter((item) => item.midasId !== selected.midas_id),
      ].slice(0, 6);
      try {
        localStorage.setItem(RECENT_LAKES_KEY, JSON.stringify(next));
      } catch {
        // Recent lakes are a convenience; selection should still work if storage is unavailable.
      }
      return next;
    });
  };

  const handleSearchKeyDown = (event) => {
    if (!searchFocused) return;
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveSuggestion((previous) => stepSearchSuggestion(previous, "down", searchResults.length));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveSuggestion((previous) => stepSearchSuggestion(previous, "up", searchResults.length));
    } else if (event.key === "Enter") {
      event.preventDefault();
      const match =
        searchResults[activeSuggestion] ||
        (searchResults.length === 1 ? searchResults[0] : undefined);
      if (match) selectLake(match.midasId, match.lakeName);
    } else if (event.key === "Escape") {
      setSearchFocused(false);
      setActiveSuggestion(-1);
    }
  };

  return (
    <aside className={`panel flex min-h-0 flex-col p-4 sm:p-5 ${SECTION_ACCENTS.trends.panelAccentClass}`}>
      <h2 className="section-heading"><Search className="h-5 w-5 text-lake-amber" aria-hidden />Find a lake</h2>
      <div className="relative z-20 mt-3 flex items-start gap-2" data-claro-target="trends-lake-search">
        <LakeSearchCombobox
          lakeId={selectedId}
          lakeName={selectedLake?.lake_name || ""}
          searchQuery={query}
          onSearchQueryChange={setQuery}
          searchResults={searchResults}
          searchError=""
          searchFocused={searchFocused}
          onSearchFocusedChange={setSearchFocused}
          isSearching={false}
          activeSuggestion={activeSuggestion}
          onActiveSuggestionChange={setActiveSuggestion}
          recentLakes={recentLakes}
          onSelectLake={selectLake}
          onShowLakeOnMap={(lake) => {
            onOpenMap(lake);
          }}
          onSearchKeyDown={handleSearchKeyDown}
          workspace="trends"
        />
        <button
          type="button"
          className="workspace-action-button workspace-action-button-trends h-12 w-12 shrink-0 px-0"
          data-claro-target="lake-map-button"
          onClick={() => {
            onOpenMap(null);
          }}
          aria-label="Choose a lake from map"
        >
          <Map className="h-5 w-5" aria-hidden />
        </button>
      </div>
      <p className="mt-2 text-sm text-slate-600">{filtered.length.toLocaleString()} of {lakes.length.toLocaleString()} lakes</p>
      <div className="mt-4 flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm leading-5 text-amber-950">
        <BarChart3 className="mt-0.5 h-4 w-4 shrink-0 text-lake-amber" aria-hidden />
        <p>Forecasts are available only for lakes meeting the full-support policy: at least 10 observed years and no more than a two-year gap to the latest observation.</p>
      </div>
      <div
        className="mt-3 min-h-[8rem] max-h-[28rem] overflow-auto rounded-lg border border-slate-200 bg-white xl:max-h-[52rem]"
        aria-label="Maine lakes"
        data-claro-target="trends-lake-list"
      >
        {filtered.length === 0 ? <p className="p-4 text-base text-slate-700">No lakes match that search.</p> : filtered.map((lake) => (
          <button key={lake.midas_id} type="button" aria-current={lake.midas_id === selectedId ? "true" : undefined} onClick={() => selectLake(lake.midas_id, lake.lake_name)} className={`w-full border-b border-slate-100 px-3 py-3 text-left last:border-0 focus-visible:relative focus-visible:z-10 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-lake-amber ${lake.midas_id === selectedId ? "bg-amber-50" : "hover:bg-slate-50"}`}>
            <span className="block font-medium text-slate-950">{lake.lake_name}</span>
            <span className="block text-sm text-slate-600">{lake.midas_id} · {lake.region || "Maine"}</span>
            <span className={`mt-1 inline-block text-xs font-semibold ${lake.forecast_available ? "text-emerald-700" : "text-slate-500"}`}>{lake.forecast_available ? "Forecast available" : "History only"}</span>
          </button>
        ))}
      </div>
      <LakeMapPicker
        isOpen={isMapOpen}
        initialLake={mapFocusLake}
        currentLakeId={String(selectedId || "").toUpperCase()}
        workspace="trends"
        onClose={onCloseMap}
        onSelectLake={selectLake}
      />
    </aside>
  );
}

function LakeTrendDetail({ detail, metadata, isLoading, error, onRetry }) {
  const { system } = useUnitSystem();
  if (isLoading) {
    return (
      <div className="panel p-6 text-slate-700" role="status" data-claro-target="trends-detail">
        Loading lake trend…
      </div>
    );
  }
  if (error) {
    return (
      <div className="panel p-6" role="alert" data-claro-target="trends-detail">
        <p className="text-delta-down">{error}</p>
        <button type="button" className="action-button mt-4" onClick={onRetry}>
          Try again
        </button>
      </div>
    );
  }
  if (!detail) {
    return <div className="panel p-6 text-slate-700" data-claro-target="trends-detail">Choose a lake to view its monitored history.</div>;
  }
  const latest = detail.history.at(-1);
  const end = detail.forecast.at(-1);
  return (
    <section className={`panel p-5 sm:p-6 ${SECTION_ACCENTS.trends.panelAccentClass}`} data-claro-target="trends-detail">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-lake-amber">
            {detail.region || "Maine"} · {detail.midas_id}
          </p>
          <h2 className="display-title mt-1 text-2xl sm:text-3xl">{detail.lake_name}</h2>
        </div>
        {detail.forecast_available ? (
          <span className="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-sm font-semibold text-emerald-950">
            Full-support outlook
          </span>
        ) : (
          <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-sm font-semibold text-slate-950">
            History only
          </span>
        )}
      </div>
      {!detail.forecast_available ? (
        <div className="mt-6 rounded-lg border border-amber-200 bg-amber-50 p-4 text-base leading-7 text-amber-950">
          {detail.unavailable_reason || "There is not enough recent history for the five-year baseline outlook."}
        </div>
      ) : (
        <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-3">
          <div className="rounded-lg bg-slate-50 p-3">
            <p className="text-sm text-slate-600">Latest observed</p>
            <p className="mt-1 text-xl font-semibold">
              {latest ? formatQuantity(latest.secchi_m, { canonicalUnit: "m", system, decimals: 2 }) : "—"}
            </p>
            <p className="text-sm text-slate-600">{latest?.year ?? "—"}</p>
          </div>
          <div className="rounded-lg bg-amber-50 p-3">
            <p className="text-sm text-amber-950">{end?.year ?? metadata.forecast_years.at(-1)} outlook</p>
            <p className="mt-1 text-xl font-semibold text-amber-950">
              {end ? formatQuantity(end.secchi_m, { canonicalUnit: "m", system, decimals: 2 }) : "—"}
            </p>
          </div>
          <div className="rounded-lg bg-slate-50 p-3">
            <p className="text-sm text-slate-600">Observed history</p>
            <p className="mt-1 text-xl font-semibold">{detail.history_years} years</p>
            <p className="text-sm text-slate-600">through {detail.latest_year}</p>
          </div>
        </div>
      )}
      <div className="mt-6">
        <TrendsChart detail={detail} />
      </div>
      <p className="mt-5 text-sm leading-6 text-slate-600">
        The observed record and baseline outlook use separate scales so each remains readable. The baseline is a reference scenario, not a claim that the lake will improve or decline.
      </p>
    </section>
  );
}

export function TrendsPage() {
  const { metadata, selectedId, setSelectedId, detail, isLoading, isDetailLoading, error, detailError, retry, retryDetail } = useTrendsData();
  const [isMapOpen, setIsMapOpen] = useState(false);
  const [mapFocusLake, setMapFocusLake] = useState(null);

  const openLakeMap = (lake = null) => {
    setMapFocusLake(lake);
    setIsMapOpen(true);
  };

  const closeLakeMap = () => setIsMapOpen(false);

  const handleClaroStepExit = (step) => {
    if (step?.id === "trends-map") closeLakeMap();
  };

  return (
    <PageFrame
      footerAddon={(
        <ClaroGuide
          routeId={getClaroRouteId(ROUTES.trends)}
          onStepExit={handleClaroStepExit}
          isMapOpen={isMapOpen}
        />
      )}
    >
      <section className={`${PAGE_CONTAINER} py-6 sm:py-10`} data-claro-target="trends-page">
        <InfoPageNav eyebrow="Trends · Maine lakes" eyebrowTone="amber" eyebrowIcon={Waves} actions={<UnitSystemToggle workspace="trends" />} />
        <header
          className={`panel p-6 sm:p-8 ${SECTION_ACCENTS.trends.panelAccentClass}`}
          style={{ backgroundImage: "linear-gradient(135deg, rgba(230, 159, 0, 0.08) 0%, #ffffff 55%)" }}
        >
          <h1 className="display-title flex items-center gap-3 text-3xl sm:text-4xl">
            <SectionHeadingIcon section="trends" icon={BarChart3} />
            Maine lake trends
          </h1>
          <p className="body-copy mt-3 max-w-3xl">
            Explore monitored summer Secchi depth through 2024 and a five-year baseline outlook for lakes with enough recent history.
          </p>
        </header>
        {isLoading ? (
          <div className="panel mt-5 p-6" role="status">Loading Maine lake trends…</div>
        ) : error ? (
          <div className="panel mt-5 p-6" role="alert">
            <p className="text-delta-down">{error}</p>
            <button type="button" className="action-button mt-4" onClick={retry}>Try again</button>
          </div>
        ) : (
          <div className="mt-5 grid grid-cols-1 items-start gap-5 xl:grid-cols-[minmax(260px,0.34fr)_minmax(0,0.66fr)]">
            <LakeDirectory
              lakes={metadata.lakes}
              selectedId={selectedId}
              onSelect={setSelectedId}
              isMapOpen={isMapOpen}
              mapFocusLake={mapFocusLake}
              onOpenMap={openLakeMap}
              onCloseMap={closeLakeMap}
            />
            <LakeTrendDetail detail={detail} metadata={metadata} isLoading={isDetailLoading} error={detailError} onRetry={retryDetail} />
          </div>
        )}
      </section>
    </PageFrame>
  );
}
