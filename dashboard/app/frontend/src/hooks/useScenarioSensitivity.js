import { useEffect, useMemo, useRef, useState } from "react";
import { API_URL, DEBOUNCE_MS } from "../lib/constants";
import {
  buildPayloadFeatures,
  parseApiError,
  parseSensitivityResponse,
} from "../lib/contracts";

export function useScenarioSensitivity({
  lakeId,
  baseline,
  features,
  featureConfig,
  includedFeatures,
  featureCommitVersion = 0,
}) {
  const [sensitivityByFeature, setSensitivityByFeature] = useState({});
  const [sensitivityError, setSensitivityError] = useState("");
  const [isCheckingSensitivity, setIsCheckingSensitivity] = useState(false);
  const featuresRef = useRef(features);
  const requestIdRef = useRef(0);

  useEffect(() => {
    featuresRef.current = features;
  }, [features]);

  const includedKey = useMemo(
    () => (includedFeatures || []).slice().sort().join("|"),
    [includedFeatures]
  );

  useEffect(() => {
    if (
      !baseline ||
      !featureConfig ||
      !includedFeatures?.length ||
      Object.keys(featuresRef.current || {}).length === 0
    ) {
      setSensitivityByFeature({});
      setSensitivityError("");
      setIsCheckingSensitivity(false);
      return undefined;
    }

    let cancelled = false;
    const requestId = requestIdRef.current + 1;
    requestIdRef.current = requestId;

    const timeoutId = setTimeout(async () => {
      try {
        setIsCheckingSensitivity(true);
        setSensitivityError("");
        const payloadFeatures = buildPayloadFeatures(
          featuresRef.current,
          baseline,
          featureConfig,
          includedFeatures
        );
        const res = await fetch(`${API_URL}/predict_scenario/sensitivity`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            midas_id: lakeId,
            features: payloadFeatures,
            requested_outputs: ["prediction"],
          }),
        });
        const rawData = await res.json();
        if (!res.ok) {
          throw new Error(parseApiError(rawData));
        }
        if (cancelled || requestId !== requestIdRef.current) return;

        const parsed = parseSensitivityResponse(rawData);
        setSensitivityByFeature(
          Object.fromEntries(parsed.items.map((item) => [item.feature, item]))
        );
      } catch (error) {
        if (!cancelled && requestId === requestIdRef.current) {
          setSensitivityError(error.message || "Sensitivity check failed.");
        }
      } finally {
        if (!cancelled && requestId === requestIdRef.current) {
          setIsCheckingSensitivity(false);
        }
      }
    }, DEBOUNCE_MS);

    return () => {
      cancelled = true;
      clearTimeout(timeoutId);
    };
  }, [baseline, featureConfig, featureCommitVersion, includedFeatures, includedKey, lakeId]);

  return {
    sensitivityByFeature,
    sensitivityError,
    isCheckingSensitivity,
  };
}
