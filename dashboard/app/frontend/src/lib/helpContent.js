export const HELP_CONTENT = {
  lakeProfile: {
    title: "Lake profile",
    body: "Geographic fields for the lake you selected. These values are fixed for the scenario and cannot be changed with sliders.",
  },
  parameters: {
    title: "Parameters",
    body: "Adjust water chemistry and temperature to explore how conditions affect predicted Secchi depth. Lake location and size stay tied to the lake you selected.",
  },
  prediction: {
    title: "Predicted Secchi depth",
    body: "Predicted Secchi depth for your current slider settings. The baseline prediction uses the lake’s default profile; your scenario shows how far you have moved from that starting point.",
  },
  trajectory: {
    title: "Scenario trajectory",
    body: "Each meaningful slider change adds a step on this chart so you can see how clarity shifts during your session. " +
      "A step is recorded when predicted Secchi changes by at least 0.02 m; tiny movements may not appear.",
  },
  explainability: {
    title: "Prediction drivers",
    body: "The model’s top contributors for the current prediction. Positive values tend to push Secchi up (clearer); negative values tend to push it down.",
  },
  scenarioActions: {
    title: "Scenario actions",
    body: "Reset sliders to the lake baseline, save a scenario to compare later in this browser session, or overlay a saved scenario on the trajectory chart.",
  },
};
