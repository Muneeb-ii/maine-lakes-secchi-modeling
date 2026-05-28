import { useEffect, useState } from "react";
import { API_URL, DEBOUNCE_MS, RECENT_LAKES_KEY } from "../lib/constants";
import { parseApiError, parseLakeSearchResponse } from "../lib/contracts";

function readRecentLakes() {
  try {
    const cached = localStorage.getItem(RECENT_LAKES_KEY);
    return cached ? JSON.parse(cached) : [];
  } catch {
    return [];
  }
}

export function useLakeSearch() {
  const [searchQuery, setSearchQuery] = useState("C3420");
  const [searchResults, setSearchResults] = useState([]);
  const [searchError, setSearchError] = useState("");
  const [searchFocused, setSearchFocused] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [activeSuggestion, setActiveSuggestion] = useState(-1);
  const [recentLakes, setRecentLakes] = useState(readRecentLakes);

  useEffect(() => {
    localStorage.setItem(RECENT_LAKES_KEY, JSON.stringify(recentLakes.slice(0, 6)));
  }, [recentLakes]);

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
    }, DEBOUNCE_MS);

    return () => clearTimeout(timeoutId);
  }, [searchQuery, searchFocused]);

  const pushRecentLake = (midasId, lakeName) => {
    setRecentLakes((previous) => {
      const deduped = previous.filter((item) => item.midasId !== midasId);
      return [{ midasId, lakeName }, ...deduped];
    });
  };

  return {
    searchQuery,
    setSearchQuery,
    searchResults,
    searchError,
    searchFocused,
    setSearchFocused,
    isSearching,
    activeSuggestion,
    setActiveSuggestion,
    recentLakes,
    pushRecentLake,
  };
}
