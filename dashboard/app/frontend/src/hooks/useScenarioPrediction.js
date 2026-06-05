import { useEffect, useMemo, useRef, useState } from "react";
import { API_URL, DEBOUNCE_MS } from "../lib/constants";
import {
  buildPayloadFeatures,
  parseApiError,
  parsePredictionResponse,
} from "../lib/contracts";
import { resolveModelBaseline } from "../lib/playgroundGuards";
import {
  buildTrajectoryPoint,
  capTrajectoryHistory,
  detectChangedFeatures,
  featuresMatchForPrediction,
  formatLatestChange,
  shouldAppendPoint,
} from "../lib/trajectory";

export function useScenarioPrediction({
  lakeId,
  baseline,
  features,
  featureConfig,
  includedFeatures,
  featureCommitVersion = 0,
}) {
  const [forecast, setForecast] = useState(null);
  const [baselinePrediction, setBaselinePrediction] = useState(null);
  const [predictionError, setPredictionError] = useState("");
  const [isPredicting, setIsPredicting] = useState(false);
  const [chartHistory, setChartHistory] = useState([]);
  const previousFeaturesRef = useRef(null);
  const lastRecordedCommitRef = useRef(featureCommitVersion);
  const baselinePredictionRef = useRef(baselinePrediction);
  const lastPredictedFeaturesRef = useRef(null);
  const featuresRef = useRef(features);
  const predictRequestIdRef = useRef(0);

  useEffect(() => {
    featuresRef.current = features;
  }, [features]);

  useEffect(() => {
    baselinePredictionRef.current = baselinePrediction;
  }, [baselinePrediction]);

  useEffect(() => {
    if (typeof baselinePrediction !== "number" || !Number.isFinite(baselinePrediction)) {
      return;
    }
    setForecast((previous) => {
      if (!previous) return previous;
      if (previous.explainability?.base_value === baselinePrediction) return previous;
      return {
        ...previous,
        explainability: {
          ...previous.explainability,
          base_value: baselinePrediction,
        },
      };
    });
  }, [baselinePrediction]);

  useEffect(() => {
    previousFeaturesRef.current =
      baseline && Object.keys(baseline).length > 0 ? { ...baseline } : null;
    lastRecordedCommitRef.current = featureCommitVersion;
    setChartHistory([]);
    lastPredictedFeaturesRef.current = null;
  }, [baseline]);

  useEffect(() => {
    setBaselinePrediction(null);
    if (!baseline || !featureConfig || !includedFeatures?.length) return;

    let cancelled = false;
    const loadBaselinePrediction = async () => {
      try {
        const baselineFeatures = buildPayloadFeatures(
          baseline,
          baseline,
          featureConfig,
          includedFeatures
        );
        const res = await fetch(`${API_URL}/predict_scenario`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            midas_id: lakeId,
            features: baselineFeatures,
            requested_outputs: ["prediction"],
          }),
        });
        const rawData = await res.json();
        if (!res.ok) {
          throw new Error(parseApiError(rawData));
        }
        if (!cancelled) {
          const parsed = parsePredictionResponse(rawData);
          setBaselinePrediction(parsed.predictionMeters);
        }
      } catch (error) {
        if (!cancelled) {
          setBaselinePrediction(undefined);
        }
      }
    };

    loadBaselinePrediction();

    return () => {
      cancelled = true;
    };
  }, [baseline, featureConfig, lakeId, includedFeatures]);

  useEffect(() => {
    const currentFeatures = featuresRef.current;
    if (
      !baseline ||
      !featureConfig ||
      !includedFeatures?.length ||
      Object.keys(currentFeatures).length === 0
    ) {
      return;
    }

    let cancelled = false;
    const requestId = predictRequestIdRef.current + 1;
    predictRequestIdRef.current = requestId;

    const timeoutId = setTimeout(async () => {
      try {
        setIsPredicting(true);
        setPredictionError("");
        const payloadFeatures = buildPayloadFeatures(
          featuresRef.current,
          baseline,
          featureConfig,
          includedFeatures
        );
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
        if (cancelled || requestId !== predictRequestIdRef.current) return;

        const parsed = parsePredictionResponse(rawData);
        const modelBaseline = resolveModelBaseline(
          baselinePredictionRef.current,
          parsed.explainability.base_value
        );
        parsed.explainability.base_value = modelBaseline;
        setForecast(parsed);
        lastPredictedFeaturesRef.current = { ...featuresRef.current };
      } catch (error) {
        if (!cancelled && requestId === predictRequestIdRef.current) {
          setPredictionError(error.message || "Prediction failed.");
        }
      } finally {
        if (!cancelled && requestId === predictRequestIdRef.current) {
          setIsPredicting(false);
        }
      }
    }, DEBOUNCE_MS);

    return () => {
      cancelled = true;
      clearTimeout(timeoutId);
    };
  }, [featureCommitVersion, baseline, featureConfig, includedFeatures, lakeId]);

  useEffect(() => {
    if (!forecast || !baseline || !featureConfig || isPredicting || predictionError) {
      return;
    }
    if (lastRecordedCommitRef.current === featureCommitVersion) {
      return;
    }

    const editableKeys = featureConfig.editable_features || [];
    if (!featuresMatchForPrediction(lastPredictedFeaturesRef.current, features, editableKeys)) {
      return;
    }

    const previousFeatures = previousFeaturesRef.current;
    if (!previousFeatures) {
      previousFeaturesRef.current =
        baseline && Object.keys(baseline).length > 0 ? { ...baseline } : { ...features };
      lastRecordedCommitRef.current = featureCommitVersion;
      return;
    }

    const changedFeatures = detectChangedFeatures(previousFeatures, features, featureConfig);
    if (changedFeatures.length === 0) {
      previousFeaturesRef.current = { ...features };
      lastRecordedCommitRef.current = featureCommitVersion;
      return;
    }

    const prediction = forecast.predictionMeters;
    const modelBaseline = forecast.explainability.base_value;

    setChartHistory((previous) => {
      if (previous.length === 0) {
        const startingPoint = buildTrajectoryPoint({
          step: 1,
          prediction: modelBaseline,
          baseline: modelBaseline,
          changedFeatures: [],
          previousPrediction: null,
          isStarting: true,
        });
        const changedPoint = buildTrajectoryPoint({
          step: 2,
          prediction,
          baseline: modelBaseline,
          changedFeatures,
          previousPrediction: modelBaseline,
        });

        previousFeaturesRef.current = { ...features };
        lastRecordedCommitRef.current = featureCommitVersion;
        return capTrajectoryHistory([startingPoint, changedPoint]);
      }

      const lastPrediction = previous[previous.length - 1].prediction;

      if (!shouldAppendPoint(lastPrediction, prediction, false)) {
        previousFeaturesRef.current = { ...features };
        lastRecordedCommitRef.current = featureCommitVersion;
        return previous;
      }

      const step = previous.length + 1;
      const point = buildTrajectoryPoint({
        step,
        prediction,
        baseline: modelBaseline,
        changedFeatures,
        previousPrediction: lastPrediction,
      });

      previousFeaturesRef.current = { ...features };
      lastRecordedCommitRef.current = featureCommitVersion;
      return capTrajectoryHistory([...previous, point]);
    });
  }, [
    baseline,
    featureCommitVersion,
    featureConfig,
    features,
    forecast,
    isPredicting,
    predictionError,
  ]);

  const latestChange = useMemo(() => {
    if (chartHistory.length < 2) return null;
    return formatLatestChange(chartHistory[chartHistory.length - 1]);
  }, [chartHistory]);

  const resetChart = (seedFeatures = features) => {
    setChartHistory([]);
    previousFeaturesRef.current =
      seedFeatures && Object.keys(seedFeatures).length > 0 ? { ...seedFeatures } : null;
    lastRecordedCommitRef.current = featureCommitVersion;
  };

  const clearForecast = () => {
    setForecast(null);
    setBaselinePrediction(null);
    previousFeaturesRef.current = null;
    lastRecordedCommitRef.current = featureCommitVersion;
    lastPredictedFeaturesRef.current = null;
  };

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
};
