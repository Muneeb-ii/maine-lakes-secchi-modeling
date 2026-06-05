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
    body: "The depth the model expects for your current slider settings. “Typical for this lake” is the estimate using that lake’s usual profile; the difference shows how far your scenario moved from that starting point.",
  },
  trajectory: {
    title: "Changes you tried",
    body: "Each meaningful slider change adds a point so you can see how clarity shifted as you explored. Small changes under 0.02 m may not add a new point.",
  },
  explainability: {
    title: "What influenced this prediction",
    body: "Which measurements most pushed the estimate toward clearer or murkier water. Green-leaning values tend toward clearer; orange-red toward murkier.",
  },
  scenarioActions: {
    title: "Save & compare",
    body: "Restore sliders to the lake’s usual values, save a scenario to revisit later in this browser, or compare a saved scenario on the changes chart.",
  },
};
