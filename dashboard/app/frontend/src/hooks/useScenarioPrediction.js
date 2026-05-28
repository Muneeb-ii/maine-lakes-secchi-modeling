import { useEffect, useMemo, useRef, useState } from "react";
import { API_URL, DEBOUNCE_MS } from "../lib/constants";
import {
  buildPayloadFeatures,
  parseApiError,
  parsePredictionResponse,
} from "../lib/contracts";
import {
  buildTrajectoryPoint,
  capTrajectoryHistory,
  detectChangedFeatures,
  formatLatestChange,
  shouldAppendPoint,
} from "../lib/trajectory";

export function useScenarioPrediction({ lakeId, baseline, features, featureConfig }) {
  const [forecast, setForecast] = useState(null);
  const [predictionError, setPredictionError] = useState("");
  const [isPredicting, setIsPredicting] = useState(false);
  const [chartHistory, setChartHistory] = useState([]);
  const previousFeaturesRef = useRef(null);
  const isFirstPointRef = useRef(true);

  useEffect(() => {
    if (!baseline || !featureConfig || Object.keys(features).length === 0) return;

    let cancelled = false;
    const timeoutId = setTimeout(async () => {
      try {
        setIsPredicting(true);
        setPredictionError("");
        const payloadFeatures = buildPayloadFeatures(features, baseline, featureConfig);
        const res = await fetch(`${API_URL}/predict_scenario`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            midas_id: lakeId,
            features: payloadFeatures,
            requested_outputs: ["prediction", "explainability"],
          }),
        });
        const rawData = await res.json();
        if (!res.ok) {
          throw new Error(parseApiError(rawData));
        }
        if (cancelled) return;

        const parsed = parsePredictionResponse(rawData);
        setForecast(parsed);

        const prediction = parsed.predictionMeters;
        const modelBaseline = parsed.explainability.base_value;
        const previousFeatures = previousFeaturesRef.current;
        const changedFeatures = previousFeatures
          ? detectChangedFeatures(previousFeatures, features, featureConfig)
          : [];

        setChartHistory((previous) => {
          const lastPrediction = previous.length ? previous[previous.length - 1].prediction : null;
          const isFirst = isFirstPointRef.current;

          if (!shouldAppendPoint(lastPrediction, prediction, isFirst)) {
            previousFeaturesRef.current = { ...features };
            return previous;
          }

          const step = previous.length + 1;
          const point = buildTrajectoryPoint({
            step,
            prediction,
            baseline: modelBaseline,
            changedFeatures,
            previousPrediction: lastPrediction,
            isStarting: isFirst,
          });

          isFirstPointRef.current = false;
          previousFeaturesRef.current = { ...features };
          return capTrajectoryHistory([...previous, point]);
        });
      } catch (error) {
        if (!cancelled) {
          setPredictionError(error.message || "Prediction failed.");
        }
      } finally {
        if (!cancelled) {
          setIsPredicting(false);
        }
      }
    }, DEBOUNCE_MS);

    return () => {
      cancelled = true;
      clearTimeout(timeoutId);
    };
  }, [features, baseline, featureConfig, lakeId]);

  const latestChange = useMemo(() => {
    if (chartHistory.length < 2) return null;
    return formatLatestChange(chartHistory[chartHistory.length - 1]);
  }, [chartHistory]);

  const resetChart = () => {
    setChartHistory([]);
    previousFeaturesRef.current = null;
    isFirstPointRef.current = true;
  };

  const clearForecast = () => setForecast(null);

  return {
    forecast,
    predictionError,
    setPredictionError,
    isPredicting,
    chartHistory,
    latestChange,
    resetChart,
    clearForecast,
  };
}
