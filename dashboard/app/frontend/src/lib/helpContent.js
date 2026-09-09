export const HELP_CONTENT = {
  lakeProfile: {
    title: "About this lake",
    body: "Location, area, and maximum depth for the lake you picked, plus its typical pH, color, conductivity, and alkalinity averaged over its monitoring history. They stay the same while you explore different water conditions.",
  },
  parameters: {
    title: "Water conditions",
    body: "Change measured oxygen, temperature, and phosphorus values to see how Secchi depth might respond. Location, lake size, and typical chemistry stay tied to your selection. If this lake has thin slider history, the amber note means those effects lean on other lakes.",
  },
  prediction: {
    title: "Predicted Secchi depth",
    body: "The depth the model expects for your current slider settings. Typical for this lake is the estimate at this lake’s usual measurements. Change from typical updates as you move sliders. The scale shows where the prediction sits among Maine clarity bands, and the comparison to maximum depth is this lake’s recorded basin depth—not a model output.",
  },
  modelBaseline: {
    title: "Typical for this lake",
    body: "The Secchi depth the model predicts for this lake’s usual water conditions, based on typical measurements recorded for this lake. This reference stays fixed while you adjust sliders.",
  },
  deltaFromBaseline: {
    title: "Change from typical",
    body: "How far your current predicted Secchi depth is above or below that reference. Positive means clearer; negative means murkier.",
  },
  trajectory: {
    title: "Scenario history",
    body: "This chart records how predicted clarity changes as you make slider adjustments. The first dot is the lake’s typical condition; each later dot is a meaningful change you tried.",
  },
  explainability: {
    title: "What influenced this prediction",
    body: "How this lake’s fixed traits and the water measurements you changed pushed the estimate toward clearer or murkier water. Green-leaning values tend toward clearer; orange-red toward murkier.",
  },
  scenarioActions: {
    title: "Save & compare",
    body: "Save bookmarks a snapshot of your current sliders and predicted Secchi depth in this browser only — you can add an optional name. Selecting a snapshot compares it on the chart as a reference line. Load restores that snapshot’s sliders. Restore lake defaults resets sliders and clears chart history; saved snapshots stay in the menu. Delete removes the selected snapshot.",
  },
};
