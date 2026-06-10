import { useCallback, useEffect, useMemo, useState } from "react";
import { SAVED_SCENARIOS_KEY } from "../lib/constants";
import {
  buildSavedScenario,
  countOtherLakeScenarios,
  migrateSavedScenarios,
  prependSavedScenario,
  sanitizeCompareId,
  scenariosForLake,
} from "../lib/savedScenarios";

function readSavedScenarios() {
  try {
    const cached = localStorage.getItem(SAVED_SCENARIOS_KEY);
    const parsed = cached ? JSON.parse(cached) : [];
    return migrateSavedScenarios(parsed);
  } catch {
    return [];
  }
}

export function useSavedScenarios() {
  const [savedScenarios, setSavedScenarios] = useState(readSavedScenarios);
  const [compareScenarioId, setCompareScenarioId] = useState("");

  useEffect(() => {
    localStorage.setItem(SAVED_SCENARIOS_KEY, JSON.stringify(savedScenarios));
  }, [savedScenarios]);

  useEffect(() => {
    setCompareScenarioId((current) => sanitizeCompareId(savedScenarios, current));
  }, [savedScenarios]);

  const selectedCompareScenario = useMemo(() => {
    const validId = sanitizeCompareId(savedScenarios, compareScenarioId);
    if (!validId) return null;
    return savedScenarios.find((scenario) => scenario.id === validId) ?? null;
  }, [savedScenarios, compareScenarioId]);

  const saveScenario = useCallback(
    ({ lakeId, lakeName, forecast, features, includedFeatures, label }) => {
      const scenario = buildSavedScenario({
        lakeId,
        lakeName,
        forecast,
        features,
        includedFeatures,
        label,
      });
      if (!scenario) return false;
      setSavedScenarios((previous) => prependSavedScenario(previous, scenario));
      return true;
    },
    []
  );

  const deleteScenario = useCallback(
    (scenarioId = compareScenarioId) => {
      if (!scenarioId) return false;
      const exists = savedScenarios.some((scenario) => scenario.id === scenarioId);
      if (!exists) return false;
      setSavedScenarios((previous) =>
        previous.filter((scenario) => scenario.id !== scenarioId)
      );
      setCompareScenarioId((current) => (current === scenarioId ? "" : current));
      return true;
    },
    [compareScenarioId, savedScenarios]
  );

  const scenariosForCurrentLake = useCallback(
    (lakeId) => scenariosForLake(savedScenarios, lakeId),
    [savedScenarios]
  );

  const otherLakeScenarioCount = useCallback(
    (lakeId) => countOtherLakeScenarios(savedScenarios, lakeId),
    [savedScenarios]
  );

  return {
    savedScenarios,
    compareScenarioId,
    setCompareScenarioId,
    selectedCompareScenario,
    saveScenario,
    deleteScenario,
    scenariosForCurrentLake,
    otherLakeScenarioCount,
  };
}
