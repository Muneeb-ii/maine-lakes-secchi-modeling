import { useId } from "react";
import { Search } from "lucide-react";

export function LakeSearchCombobox({
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
        aria-label="Search lake by MIDAS ID or name"
        value={searchQuery}
        onChange={(event) => {
          onSearchQueryChange(event.target.value);
          onActiveSuggestionChange(-1);
        }}
        onFocus={() => onSearchFocusedChange(true)}
        onBlur={() => setTimeout(() => onSearchFocusedChange(false), 150)}
        onKeyDown={onSearchKeyDown}
        placeholder="Search by MIDAS or lake name..."
        className="input-field"
      />
      {searchFocused && (
        <ul
          id={listboxId}
          role="listbox"
          className="absolute z-20 mt-2 w-full panel p-2 max-h-72 overflow-auto list-none m-0"
        >
          {isSearching && (
            <li className="p-2 text-xs text-slate-400" role="status">
              Searching...
            </li>
          )}
          {searchError && (
            <li className="p-2 text-xs text-red-300" role="alert">
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
                  className={`w-full text-left px-3 py-2.5 rounded-lg text-sm transition ${
                    index === activeSuggestion
                      ? "bg-lake-accent/20 text-teal-100"
                      : "hover:bg-slate-800/80"
                  }`}
                  onMouseDown={() => onSelectLake(result.midasId, result.lakeName)}
                >
                  <div className="font-medium">{result.lakeName}</div>
                  <div className="text-xs text-slate-400">{result.midasId}</div>
                </button>
              </li>
            ))}
          {!isSearching && searchResults.length === 0 && searchQuery.trim() && !searchError && (
            <li className="p-2 text-xs text-slate-400">No matches found.</li>
          )}
          {!searchQuery.trim() && recentLakes.length > 0 && (
            <li>
              <div className="px-2 py-1 text-xs font-medium text-slate-500">Recent lakes</div>
              <ul className="list-none m-0 p-0">
                {recentLakes.map((item) => (
                  <li key={item.midasId} role="presentation">
                    <button
                      type="button"
                      className="w-full text-left px-3 py-2.5 rounded-lg text-sm hover:bg-slate-800/80 transition"
                      onMouseDown={() => onSelectLake(item.midasId, item.lakeName)}
                    >
                      <div className="font-medium">{item.lakeName}</div>
                      <div className="text-xs text-slate-400">{item.midasId}</div>
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
