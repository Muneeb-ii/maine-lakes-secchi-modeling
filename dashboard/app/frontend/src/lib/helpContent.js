export const HELP_CONTENT = {
  lakeProfile: {
    title: "About this lake",
    body: "Latitude, longitude, area, and maximum depth for the lake you picked. They stay the same while you explore different water conditions.",
  },
  parameters: {
    title: "Water conditions",
    body: "Change chemistry and related measurements to see how Secchi depth might respond. Location and lake size stay tied to your selection.",
  },
  prediction: {
    title: "Predicted Secchi depth",
    body: "The depth the model expects for your current slider settings.",
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
    body: "Restore sliders to the lake’s usual values, save your current slider settings, compare with a saved scenario, or delete the selected saved scenario.",
  },
};
