import { useId } from "react";
import { Search } from "lucide-react";
import {
  SEARCH_ARIA_LABEL,
  SEARCH_LOADING,
  SEARCH_NO_MATCHES,
  SEARCH_PLACEHOLDER,
  SEARCH_RECENT_HEADING,
  formatLakeSearchDisplay,
} from "../../lib/copy";

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
  onSearchKeyDown,
}) {
  const listboxId = useId();
  const activeOptionId =
    activeSuggestion >= 0 ? `${listboxId}-option-${activeSuggestion}` : undefined;
  const displayValue = searchFocused
    ? searchQuery
    : formatLakeSearchDisplay(lakeId, lakeName) || searchQuery;

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
                <button
                  type="button"
                  id={`${listboxId}-option-${index}`}
                  role="option"
                  aria-selected={index === activeSuggestion}
                  className={`min-h-12 w-full rounded-lg px-3 py-2.5 text-left text-base transition ${
                    index === activeSuggestion
                      ? "bg-lake-accent/10 text-lake-accent"
                      : "hover:bg-slate-100"
                  }`}
                  onMouseDown={() => onSelectLake(result.midasId, result.lakeName)}
                >
                  <div className="font-medium">{result.lakeName}</div>
                  <div className="text-base text-slate-700">{result.midasId}</div>
                </button>
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
