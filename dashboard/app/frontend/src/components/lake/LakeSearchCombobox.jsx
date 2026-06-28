import { useId } from "react";
import { MapPin, Search } from "lucide-react";
import {
  SEARCH_ARIA_LABEL,
  SEARCH_LOADING,
  SEARCH_NO_MATCHES,
  SEARCH_PLACEHOLDER,
  SEARCH_RECENT_HEADING,
  formatLakeSearchDisplay,
} from "../../lib/copy";
import { useUnitSystem } from "../../context/UnitSystemContext";
import { formatQuantity } from "../../lib/units";

export function LakeSearchCombobox({
  lakeId,
  lakeName,
  searchQuery,
  onSearchQueryChange,
  searchResults,
  searchError,
  searchFocused,
  onSearchFocusedChange,
  isSearching,
  activeSuggestion,
  onActiveSuggestionChange,
  recentLakes,
  onSelectLake,
  onShowLakeOnMap,
  onSearchKeyDown,
}) {
  const { system } = useUnitSystem();
  const listboxId = useId();
  const activeOptionId =
    activeSuggestion >= 0 ? `${listboxId}-option-${activeSuggestion}` : undefined;
  const displayValue = searchFocused
    ? searchQuery
    : formatLakeSearchDisplay(lakeId, lakeName) || searchQuery;
  const formatLocation = (result) => {
    if (typeof result.latitude !== "number" || typeof result.longitude !== "number") {
      return "";
    }
    const coordinates = `${result.latitude.toFixed(4)}, ${result.longitude.toFixed(4)}`;
    if (typeof result.areaAcres === "number") {
      return `${coordinates} · ${formatQuantity(result.areaAcres, {
        canonicalUnit: "acres",
        system,
        decimals: 1,
      })}`;
    }
    return coordinates;
  };

  return (
    <div className="w-full relative">
      <Search className="absolute left-3 top-3.5 w-4 h-4 text-slate-500 pointer-events-none" aria-hidden />
      <input
        type="text"
        role="combobox"
        aria-expanded={searchFocused}
        aria-controls={listboxId}
        aria-activedescendant={activeOptionId}
        aria-autocomplete="list"
        aria-label={SEARCH_ARIA_LABEL}
        value={displayValue}
        onChange={(event) => {
          onSearchQueryChange(event.target.value);
          onActiveSuggestionChange(-1);
        }}
        onFocus={() => {
          onSearchFocusedChange(true);
          if (!searchQuery) {
            onSearchQueryChange(lakeName || "");
          }
        }}
        onBlur={() => setTimeout(() => onSearchFocusedChange(false), 150)}
        onKeyDown={onSearchKeyDown}
        placeholder={SEARCH_PLACEHOLDER}
        className="input-field"
      />
      {searchFocused && (
        <ul
          id={listboxId}
          role="listbox"
          className="absolute z-20 mt-2 w-full panel p-2 max-h-72 overflow-auto list-none m-0"
        >
          {isSearching && (
            <li className="p-2 text-base text-slate-700" role="status">
              {SEARCH_LOADING}
            </li>
          )}
          {searchError && (
            <li className="p-2 text-base text-delta-down" role="alert">
              {searchError}
            </li>
          )}
          {!isSearching &&
            searchResults.map((result, index) => (
              <li key={result.midasId} role="presentation">
                <div
                  className={`flex min-h-12 items-center gap-2 rounded-lg text-base transition ${
                    index === activeSuggestion
                      ? "bg-lake-accent/10 text-lake-accent"
                      : "hover:bg-slate-100"
                  }`}
                >
                  <button
                    type="button"
                    id={`${listboxId}-option-${index}`}
                    role="option"
                    aria-selected={index === activeSuggestion}
                    className="min-w-0 flex-1 px-3 py-2.5 text-left"
                    onMouseDown={() => onSelectLake(result.midasId, result.lakeName)}
                  >
                    <div className="font-medium">{result.lakeName}</div>
                    <div className="text-base text-slate-700">{result.midasId}</div>
                    {formatLocation(result) && (
                      <div className="text-sm font-medium text-slate-600">{formatLocation(result)}</div>
                    )}
                  </button>
                  {typeof result.latitude === "number" && typeof result.longitude === "number" && (
                    <button
                      type="button"
                      className="mr-2 inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-lg text-slate-600 transition hover:bg-white hover:text-lake-accent focus-visible:outline focus-visible:outline-2 focus-visible:outline-lake-accent"
                      aria-label={`Show ${result.lakeName} on map`}
                      onMouseDown={(event) => {
                        event.preventDefault();
                        event.stopPropagation();
                        onShowLakeOnMap?.(result);
                      }}
                    >
                      <MapPin className="h-4 w-4" aria-hidden />
                    </button>
                  )}
                </div>
              </li>
            ))}
          {!isSearching && searchResults.length === 0 && searchQuery.trim() && !searchError && (
            <li className="p-2 text-base text-slate-700">{SEARCH_NO_MATCHES}</li>
          )}
          {!searchQuery.trim() && recentLakes.length > 0 && (
            <li>
              <div className="px-2 py-1 text-base font-medium text-slate-700">{SEARCH_RECENT_HEADING}</div>
              <ul className="list-none m-0 p-0">
                {recentLakes.map((item) => (
                  <li key={item.midasId} role="presentation">
                    <button
                      type="button"
                      className="min-h-12 w-full rounded-lg px-3 py-2.5 text-left text-base transition hover:bg-slate-100"
                      onMouseDown={() => onSelectLake(item.midasId, item.lakeName)}
                    >
                      <div className="font-medium">{item.lakeName}</div>
                      <div className="text-base text-slate-700">{item.midasId}</div>
                    </button>
                  </li>
                ))}
              </ul>
            </li>
          )}
        </ul>
      )}
    </div>
  );
}
