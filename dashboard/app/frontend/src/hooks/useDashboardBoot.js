import { useCallback, useEffect, useState } from "react";
import { API_URL } from "../lib/constants";
import { UNKNOWN_LAKE_NAME } from "../lib/copy";
import { parseApiError, validateFeatureConfig } from "../lib/contracts";

export function useDashboardBoot({ onLakeLoaded }) {
  const [bootState, setBootState] = useState("loading");
  const [bootError, setBootError] = useState("");
  const [featureConfig, setFeatureConfig] = useState(null);

  const loadLakeBaseline = useCallback(
    async (midasId, nameHint) => {
      const normalized = String(midasId || "").trim().toUpperCase();
      if (!normalized) {
        throw new Error("Please provide a MIDAS ID.");
      }
      const res = await fetch(`${API_URL}/lake/${normalized}`);
      const payload = await res.json();
      if (!res.ok) {
        throw new Error(parseApiError(payload));
      }

      const rawName = nameHint || payload.lake_name || "";
      const name =
        rawName && rawName !== UNKNOWN_LAKE_NAME ? rawName : payload.lake_name || "";

      const lakeSupport = {
        supported: Boolean(payload.supported),
        status: payload.status || "success",
        isFallback: payload.status === "fallback",
      };

      onLakeLoaded(normalized, name, payload.baseline, lakeSupport);
      return { normalized, name, lakeSupport };
    },
    [onLakeLoaded]
  );

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
  }, [loadLakeBaseline]);

  return { bootState, bootError, featureConfig, loadLakeBaseline };
}
