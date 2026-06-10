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
    "This dashboard explores lake water clarity with machine learning across two workspaces. The Playground answers “what if” questions when you change water conditions for a lake. Trends will show how clarity has changed over time and what may lie ahead when that workspace launches.",
  playground: {
    summary:
      "Scenario predictions: if water conditions change for a lake, how might Secchi depth respond? The sections below explain where those estimates come from, what inputs they use, and how to interpret them responsibly.",
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
        "Chlorophyll (CHLA) is intentionally excluded from prediction features. During model selection, we found that leaving CHLA out and letting the model handle missing chemistry natively worked better than filling gaps with imputed values for interactive scenario use.",
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
        "Scenario mode answers “what if” questions for adjusted water conditions. It does not forecast long-term trends across years—that question is for the Trends workspace (in development; see below).",
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
      title: "How we chose the served model",
      paragraphs: [
        "The Playground model was not picked from a single offline score. We compared candidate setups on chronological splits, checked whether lakes held up under leave-one-lake-out validation, and benchmarked missing-chemistry strategies before settling on native missing-value handling without chlorophyll.",
        "We also defined the supported-lake policy from monitoring depth and data completeness so the tool prioritizes lakes with enough history for stable estimates. The dashboard loads one validated model package at deploy time, which keeps predictions, slider definitions, and explainability aligned.",
      ],
    },
    ],
  },
  trends: {
    summary: "Clarity over time for Maine lakes.",
    paragraphs: [
      "The Trends workspace will explore how clarity has changed over time and what may lie ahead for lakes you follow. It is built for temporal questions—not slider scenarios.",
      "Model selection, inputs, and performance details for trend forecasting will be documented here when the workspace launches. Until then, use the Playground to explore how water conditions affect Secchi depth for a lake you choose.",
    ],
    workspaceCta: "Visit the Trends workspace",
  },
};
