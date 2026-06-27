import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { UNIT_SYSTEM_KEY } from "../lib/constants.js";
import { DEFAULT_UNIT_SYSTEM, normalizeUnitSystem, UNIT_SYSTEMS } from "../lib/units.js";

const UnitSystemContext = createContext(null);

function readStoredSystem() {
  if (typeof window === "undefined") return DEFAULT_UNIT_SYSTEM;
  try {
    const stored = window.localStorage.getItem(UNIT_SYSTEM_KEY);
    return stored ? normalizeUnitSystem(stored) : DEFAULT_UNIT_SYSTEM;
  } catch {
    return DEFAULT_UNIT_SYSTEM;
  }
}

export function UnitSystemProvider({ children }) {
  const [system, setSystemState] = useState(readStoredSystem);

  const setSystem = useCallback((next) => {
    setSystemState(normalizeUnitSystem(next));
  }, []);

  const toggleSystem = useCallback(() => {
    setSystemState((current) =>
      current === UNIT_SYSTEMS.US ? UNIT_SYSTEMS.METRIC : UNIT_SYSTEMS.US
    );
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      window.localStorage.setItem(UNIT_SYSTEM_KEY, system);
    } catch {
      // Persistence is best-effort; ignore storage failures.
    }
  }, [system]);

  const value = useMemo(
    () => ({ system, setSystem, toggleSystem }),
    [system, setSystem, toggleSystem]
  );

  return <UnitSystemContext.Provider value={value}>{children}</UnitSystemContext.Provider>;
}

// Returns the active unit system plus setters. Falls back to the default
// system when no provider is mounted so components stay render-safe.
export function useUnitSystem() {
  const context = useContext(UnitSystemContext);
  if (!context) {
    return { system: DEFAULT_UNIT_SYSTEM, setSystem: () => {}, toggleSystem: () => {} };
  }
  return context;
}
