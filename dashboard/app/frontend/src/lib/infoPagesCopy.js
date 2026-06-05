export const FOOTER_LINKS = {
  contributors: "Contributors",
  modeling: "Modeling process",
};

export const CONTRIBUTORS_PAGE = {
  eyebrow: "Contributors",
  title: "People and partners behind this dashboard",
  intro:
    "This tool was built at Colby College to make Maine lake clarity research easier to explore.",
  developers: {
    title: "Developers",
    names: [
      "Tahiya Chowdhury",
      "Muneeb Nafees",
      "Anthony Yeh",
      "Danielle Wain",
      "Bianca Hulub",
    ],
    affiliation: "Colby College",
  },
  partners: {
    title: "Collaboration & support",
    items: [
      {
        name: "7 Lakes Alliance",
        detail: "Collaborating partner supporting Maine lake monitoring and outreach.",
        href: "https://7lakesalliance.org/",
      },
      {
        name: "USGS funding",
        detail: "Research supported by U.S. Geological Survey funding.",
        href: "https://www.usgs.gov/",
      },
      {
        name: "Colby College",
        detail: "Academic home for the dashboard development and modeling research.",
        href: "https://www.colby.edu/",
      },
    ],
  },
};

export const MODELING_PAGE = {
  eyebrow: "Modeling process",
  title: "How we estimate Secchi depth",
  intro:
    "The Playground shows scenario predictions: if water conditions change for a lake, how might Secchi depth respond? This page explains where those estimates come from, what inputs they use, and how to interpret them responsibly.",
  sections: [
    {
      id: "secchi",
      title: "What Secchi depth measures",
      paragraphs: [
        "Secchi depth is a field measurement of water clarity. A disk is lowered into the lake until it disappears; the depth at that point is recorded in meters. Higher values generally mean clearer water.",
        "The dashboard does not replace field measurements. It offers a way to explore how clarity might shift when chemistry and related conditions change, using patterns learned from historical monitoring.",
      ],
    },
    {
      id: "data",
      title: "Data behind the model",
      paragraphs: [
        "Predictions are trained on a merged Maine lakes dataset that combines Secchi observations with chemistry, location, and lake morphology records. Lakes are identified by MIDAS IDs used throughout Maine monitoring programs.",
        "The active dashboard model uses lakes that pass quality filters: at least 100 observations after base filtering and chemical missingness at or below 90%. That policy keeps predictions focused on lakes with enough monitoring history to support stable estimates.",
      ],
      stats: [
        { label: "Lakes in dataset (after filtering)", value: "994" },
        { label: "Lakes with strong monitoring support", value: "187" },
        { label: "Monitoring records in supported set", value: "87,116" },
      ],
    },
    {
      id: "approach",
      title: "Modeling approach",
      paragraphs: [
        "The served model is a gradient-boosted tree regressor (CatBoost) tuned for Maine lakes. It learns nonlinear relationships between water measurements, lake characteristics, season, and observed Secchi depth.",
        "Chlorophyll (CHLA) is intentionally excluded from prediction features. Experiments showed that a no-CHLA feature set with native missing-value handling outperformed imputation-heavy alternatives for dashboard use.",
        "When you move sliders in the Playground, the model recomputes a prediction for your scenario. Locked inputs—year, month, location, and lake size—stay tied to the lake profile you selected.",
      ],
    },
    {
      id: "inputs",
      title: "Inputs used in each prediction",
      paragraphs: [
        "Fourteen measurements feed every forecast. Some are fixed for the lake you pick; others are editable in the Playground.",
      ],
      featureGroups: [
        {
          name: "Fixed for your lake",
          description: "Set from the lake profile and baseline scenario.",
          features: [
            "Year and month",
            "Latitude and longitude",
            "Surface area (acres)",
            "Maximum depth (ft)",
          ],
        },
        {
          name: "Adjustable in the Playground",
          description: "Water chemistry sliders you can change to explore scenarios.",
          features: [
            "Dissolved oxygen (max and min)",
            "Total phosphorus (epilimnion and bottom grab)",
            "pH",
            "Water color",
            "Conductivity",
            "Alkalinity",
          ],
        },
      ],
    },
    {
      id: "performance",
      title: "How well the model performs",
      paragraphs: [
        "On supported lakes, chronological evaluation (training on past years and testing on later years) shows the model captures most clarity variation in held-out data. Typical absolute error is a little under one meter on average.",
        "Performance is strongest for lakes in the supported monitoring set. For other lakes, the dashboard may still show predictions, but you should treat them as exploratory.",
      ],
      stats: [
        { label: "R² on supported lakes (chronological)", value: "0.72" },
        { label: "Typical absolute error (MAE)", value: "0.80 m" },
        { label: "Typical root error (RMSE)", value: "1.09 m" },
      ],
    },
    {
      id: "explainability",
      title: "Understanding prediction drivers",
      paragraphs: [
        "Each prediction includes a breakdown of which inputs most pushed the estimate toward clearer or murkier water. The dashboard highlights the top three factors and lets you expand the full list.",
        "Geographic and morphological features—especially depth, longitude, and latitude—often rank among the strongest global drivers. Chemistry sliders can move a single scenario meaningfully when you change them away from a lake’s usual profile.",
        "Driver values show direction and magnitude in meters of Secchi depth, not causal proof. They help you see what the model weighed most heavily for the scenario you built.",
      ],
    },
    {
      id: "limitations",
      title: "Limitations and responsible use",
      paragraphs: [
        "Scenario mode answers “what if” questions for adjusted water conditions. It does not forecast long-term trends across years—that capability is planned for the separate Trends workspace.",
        "Predictions depend on the quality and completeness of monitoring for each lake. Unsupported lakes, sparse chemistry, or statewide fallback profiles increase uncertainty.",
        "Saved scenarios stay in your browser only; they are not stored on a server. Use results to explore hypotheses and communicate patterns, not as a substitute for site-specific monitoring or management decisions.",
      ],
      list: [
        "Not a permit, remediation, or regulatory decision tool.",
        "Not validated for lakes outside the Maine training distribution.",
        "Does not model every driver of clarity (e.g., weather events, invasive species, watershed land use).",
        "Slider ranges may extend beyond values commonly observed for a lake—treat extreme settings cautiously.",
      ],
    },
    {
      id: "research",
      title: "Research trail",
      paragraphs: [
        "The active dashboard model traces to experiments 34, 35, 37, and 38 in this repository: CatBoost tuning without CHLA, leave-one-lake-out checks, imputation benchmarks, and quality-threshold support policy. Each experiment produced committed reports used to choose the served artifact.",
        "Model version 2026-05-28-exp34-exp38 is loaded from repository artifacts at deploy time, so the API and UI stay aligned with a single canonical feature contract.",
      ],
    },
  ],
};
