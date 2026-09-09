import { useCallback, useEffect, useState } from "react";
import { API_URL } from "../lib/constants";
import { parseApiError } from "../lib/contracts";

function parseIndex(payload) {
  if (!payload || !Array.isArray(payload.lakes)) throw new Error("Trend lake index was incomplete.");
  return payload;
}

function parseDetail(payload) {
  if (!payload || !payload.midas_id || !Array.isArray(payload.history) || !Array.isArray(payload.forecast)) {
    throw new Error("Trend details were incomplete.");
  }
  return payload;
}

async function getJson(path, signal) {
  const response = await fetch(`${API_URL}${path}`, { signal });
  const payload = await response.json().catch(() => null);
  if (!response.ok) throw new Error(parseApiError(payload));
  return payload;
}

export function useTrendsData() {
  const [requestedLakeId] = useState(() => {
    const value = new URLSearchParams(window.location.search).get("lake");
    return String(value || "").trim().toLowerCase();
  });
  const [metadata, setMetadata] = useState(null);
  const [selectedId, setSelectedId] = useState("");
  const [detail, setDetail] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isDetailLoading, setIsDetailLoading] = useState(false);
  const [error, setError] = useState("");
  const [detailError, setDetailError] = useState("");
  const [detailRetry, setDetailRetry] = useState(0);

  const loadIndex = useCallback(async (signal) => {
    setIsLoading(true);
    setError("");
    try {
      const next = parseIndex(await getJson("/trends", signal));
      setMetadata(next);
      const requested = requestedLakeId
        ? next.lakes.find((lake) => String(lake.midas_id).toLowerCase() === requestedLakeId)
        : null;
      const first = requested || next.lakes.find((lake) => lake.forecast_available) || next.lakes[0];
      setSelectedId((current) => current || first?.midas_id || "");
    } catch (caught) {
      if (caught.name !== "AbortError") setError(caught.message || "Trend data could not be loaded.");
    } finally {
      if (!signal.aborted) setIsLoading(false);
    }
  }, [requestedLakeId]);

  useEffect(() => {
    const controller = new AbortController();
    loadIndex(controller.signal);
    return () => controller.abort();
  }, [loadIndex]);

  useEffect(() => {
    if (!selectedId) return undefined;
    const controller = new AbortController();
    setIsDetailLoading(true);
    setDetailError("");
    getJson(`/trends/lakes/${encodeURIComponent(selectedId)}`, controller.signal)
      .then((payload) => setDetail(parseDetail(payload)))
      .catch((caught) => {
        if (caught.name !== "AbortError") {
          setDetail(null);
          setDetailError(caught.message || "This lake’s trend could not be loaded.");
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setIsDetailLoading(false);
      });
    return () => controller.abort();
  }, [selectedId, detailRetry]);

  return {
    metadata,
    selectedId,
    setSelectedId,
    detail,
    isLoading,
    isDetailLoading,
    error,
    detailError,
    retryDetail: () => setDetailRetry((value) => value + 1),
    retry: () => {
      const controller = new AbortController();
      loadIndex(controller.signal);
    },
  };
}
