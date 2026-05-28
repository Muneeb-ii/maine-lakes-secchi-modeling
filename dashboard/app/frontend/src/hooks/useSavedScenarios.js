import { useEffect, useMemo, useState } from "react";
import { SAVED_SCENARIOS_KEY } from "../lib/constants";

function readSavedScenarios() {
  try {
    const cached = localStorage.getItem(SAVED_SCENARIOS_KEY);
    return cached ? JSON.parse(cached) : [];
  } catch {
    return [];
  }
}

export function useSavedScenarios() {
  const [savedScenarios, setSavedScenarios] = useState(readSavedScenarios);
  const [compareScenarioId, setCompareScenarioId] = useState("");

  useEffect(() => {
    localStorage.setItem(SAVED_SCENARIOS_KEY, JSON.stringify(savedScenarios.slice(0, 12)));
  }, [savedScenarios]);

  const selectedCompareScenario = useMemo(
    () => savedScenarios.find((scenario) => scenario.id === compareScenarioId),
    [savedScenarios, compareScenarioId]
  );

  const saveScenario = ({ lakeId, lakeName, forecast, features }) => {
    if (!forecast) return;
    const scenario = {
      id: `${Date.now()}`,
      lakeId,
      lakeName,
      predictionMeters: forecast.predictionMeters,
      timestamp: new Date().toISOString(),
      features,
    };
    setSavedScenarios((previous) => [
      scenario,
      ...previous.filter((item) => item.id !== scenario.id),
    ]);
    setCompareScenarioId(scenario.id);
  };

  return {
    savedScenarios,
    compareScenarioId,
    setCompareScenarioId,
    selectedCompareScenario,
    saveScenario,
  };
}
