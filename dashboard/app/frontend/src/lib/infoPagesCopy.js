export const FOOTER_LINKS = {
  contributors: "Contributors",
  modeling: "Modeling process",
};

export const CONTRIBUTORS_PAGE = {
  eyebrow: "Contributors",
  title: "People and partners behind this dashboard",
  intro:
    "This dashboard reflects an interdisciplinary collaboration between Colby faculty and student researchers working across lake science, machine learning, and software development.",
  developers: {
    title: "Project contributors",
    sections: [
      {
        title: "Faculty leadership",
        accent: "lake",
        people: [
          {
            name: "Dr. Tahiya Chowdhury",
            role: "Clare Boothe Luce Assistant Professor of Computer Science",
            detail:
              "Led the computer science direction and supervised student modeling and dashboard development.",
          },
          {
            name: "Dr. Danielle Wain",
            role: "Lake Science Director; Research Scientist, Colby College",
            detail:
              "Leads lake science contributions, curates the lake dataset, and supervised student modeling and dashboard development.",
          },
          {
            name: "Dr. Whitney King",
            role: "Frank and Theodora Miselis Professor of Chemistry",
            detail:
              "Advised the original dataset development and contributed to the project design.",
          },
        ],
      },
      {
        title: "Student research and development",
        accent: "drivers",
        people: [
          {
            name: "Muneeb Nafees",
            role: "Dashboard development and initial modeling",
            detail:
              "Developed the dashboard experience and contributed early modeling work for interactive lake clarity prediction.",
          },
          {
            name: "Adrian Gellert",
            role: "Dataset development",
            detail:
              "Generated the first version of the lake science dataset used by the project.",
          },
          {
            name: "Gent Maksutaj",
            role: "Water quality forecasting",
            detail:
              "Contributed to early versions of the water quality forecasting models.",
          },
          {
            name: "Rishit Chatterjee",
            role: "Water quality forecasting",
            detail:
              "Contributed to early versions of the water quality forecasting models.",
          },
          {
            name: "Anthony Yeh",
            role: "Dashboard development",
            detail: "Contributed to early dashboard development.",
          },
          {
            name: "Bianca Hulub",
            role: "Dashboard development",
            detail: "Contributed to early dashboard development.",
          },
        ],
      },
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
    "This dashboard explores lake water clarity across two workspaces. The Playground answers “what if” questions when you change water conditions for a lake. Trends shows monitored summer clarity over time and a five-year baseline outlook for lakes with enough recent history.",
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
        "The active model uses lakes with at least 100 observations after base filtering. Typical water chemistry is filled with lake-level averages in this snapshot. Lakes with few oxygen, temperature, or phosphorus measurements stay selectable, but the Playground warns that their slider effects rely more on other lakes.",
      ],
      stats: [
        { label: "Lakes in model data (after filtering)", value: "1,011" },
        { label: "Lakes meeting the support policy", value: "360" },
        { label: "Of those, thin slider history", value: "152" },
        { label: "Monitoring records in supported set", value: "151,686" },
      ],
    },
    {
      id: "approach",
      title: "Modeling approach",
      paragraphs: [
        "The served model is a gradient-boosted tree regressor (CatBoost) tuned for Maine lakes. It learns nonlinear relationships between water measurements, lake characteristics, season, and observed Secchi depth.",
        "Chlorophyll (CHLA) is intentionally excluded from prediction features. During model selection, we found that leaving CHLA out and letting the model handle missing chemistry natively worked better than filling gaps with imputed values for interactive scenario use.",
        "When you move sliders in the Playground, the model recomputes a prediction for your scenario. Year, month, location, lake size, and typical chemistry stay tied to the lake profile you selected.",
      ],
    },
    {
      id: "inputs",
      title: "Inputs used in each prediction",
      paragraphs: [
        "Sixteen inputs feed every prediction. Some are fixed for the lake you pick; others are editable in the Playground.",
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
            "Typical pH, water color, conductivity, and alkalinity (lake-level averages)",
          ],
        },
        {
          name: "Adjustable in the Playground",
          description: "Directly measured water conditions you can change to explore scenarios.",
          features: [
            "Dissolved oxygen (max and min)",
            "Water temperature (max and min)",
            "Total phosphorus (epicore and bottom grab)",
          ],
        },
      ],
    },
    {
      id: "performance",
      title: "How well the model performs",
      paragraphs: [
        "On supported lakes, chronological evaluation trains on earlier years and tests on later years. Those holdout scores describe accuracy, not the exact weights in the live Playground. The served model is refit on all supported monitoring so current years are included.",
        "Performance is strongest for lakes in the supported monitoring set. For other lakes, the dashboard may still show predictions, but you should treat them as exploratory.",
      ],
      stats: [
        { label: "R² on supported lakes (chronological)", value: "0.73" },
        { label: "Typical absolute error (MAE)", value: "0.79 m" },
        { label: "Typical root error (RMSE)", value: "1.08 m" },
      ],
    },
    {
      id: "explainability",
      title: "Understanding prediction drivers",
      paragraphs: [
        "Each prediction includes a breakdown of which inputs most pushed the estimate toward clearer or murkier water. The dashboard highlights the top three factors and lets you expand the full list.",
        "Geographic and morphological features, especially depth, longitude, and latitude, often rank among the strongest global drivers. Chemistry sliders can still move one scenario when you change them from a lake’s usual profile.",
        "Driver values show direction and magnitude in meters of Secchi depth, not causal proof. They help you see what the model weighed most heavily for the scenario you built.",
      ],
    },
    {
      id: "limitations",
      title: "Limitations and responsible use",
      paragraphs: [
        "Scenario mode answers “what if” questions for adjusted water conditions. It does not forecast long-term trends. That question belongs in the Trends workspace.",
        "Predictions depend on the quality and completeness of monitoring for each lake. Unsupported lakes, sparse chemistry, or statewide fallback profiles increase uncertainty.",
        "Saved scenarios stay in your browser only; they are not stored on a server. Use results to explore hypotheses and communicate patterns, not as a substitute for site-specific monitoring or management decisions.",
      ],
      list: [
        "Not a permit, remediation, or regulatory decision tool.",
        "Not validated for lakes outside the Maine training distribution.",
        "Does not model every driver of clarity (e.g., weather events, invasive species, watershed land use).",
        "Slider ranges may extend beyond values commonly observed for a lake. Treat extreme settings cautiously.",
      ],
    },
    {
      id: "research",
      title: "How we chose the served model",
      paragraphs: [
        "The Playground model was not picked from a single offline score. Hyperparameters and the decision to skip chlorophyll and imputation come from the 2025 experiments. The June 2026 snapshot then fixed which fields are editable versus locked lake chemistry, and kept lakes with sparse slider measurements selectable with a warning.",
        "Leave-one-lake-out scores remain weak, so treat a single lake’s slider response as an exploration tool, not a guarantee that the same pattern would hold if that lake had never been seen. The dashboard loads one model package at deploy time so predictions, sliders, and explainability stay aligned.",
      ],
    },
    ],
  },
  trends: {
    summary:
      "Observed summer clarity through 2024, plus a cautious five-year baseline outlook for lakes with enough recent history.",
    sections: [
      {
        id: "trends-data",
        title: "What the Trends workspace shows",
        paragraphs: [
          "Trends starts with observed summer Secchi depth for each lake. It shows the monitored record through 2024 and, when support is strong enough, a reference outlook from 2025 to 2029.",
          "The outlook is not a scenario model. It does not change water chemistry or explain what would cause clarity to move. It answers a narrower question: if a lake’s recent level is the best guide we have, what level is reasonable to carry forward?",
        ],
        stats: [
          { label: "Lakes in the Trends dataset", value: "1,084" },
          { label: "Lakes with a five-year outlook", value: "352" },
          { label: "Outlook years", value: "2025 to 2029" },
        ],
      },
      {
        id: "trends-method",
        title: "How the baseline outlook is calculated",
        paragraphs: [
          "For each lake, the model treats the annual summer value as a noisy measurement of an underlying clarity level. It estimates that level from the full observed history, smoothing one-year jumps while updating as new observations arrive.",
          "The local-level state-space model then carries the latest estimated level forward for five years. Because this is a persistence outlook, its point estimate does not automatically rise or fall over time.",
          "The shaded 80% and 95% ranges come from errors in earlier backtests. They show how far a future observation has typically landed from the baseline, rather than pretending the point estimate is exact.",
        ],
      },
      {
        id: "trends-selection",
        title: "How we checked the baseline",
        paragraphs: [
          "Experiment 45 asked whether any model beat simple baselines enough to publish a skillful five-year forecast. None did, including the more complex Bayesian, CatBoost, and GAM attempts.",
          "Experiment 46 asked whether a labeled persistence outlook with empirical ranges could be shown responsibly. The local-level model had lower five-year error than a recent five-year mean on 2020 to 2024 outcomes. Its interval coverage was close to the intended 80% and 95% levels. Later simple-model checks may look slightly better on historical error, but they do not replace this baseline until a later dataset includes years after 2024.",
        ],
        stats: [
          { label: "Five-year MAE on full support", value: "0.64 m" },
          { label: "Observed within 80% range", value: "78%" },
          { label: "Observed within 95% range", value: "95%" },
        ],
      },
      {
        id: "trends-support",
        title: "Which lakes receive an outlook",
        paragraphs: [
          "A lake receives a five-year outlook only when its record has enough recent support: at least 10 annual summer observations and at least one observation in 2022, 2023, or 2024.",
          "Lakes that do not meet this policy still keep their observed history in Trends. They are shown as history-only so the dashboard does not imply more forecast confidence than the data support.",
        ],
        list: [
          "Full support: at least 10 observed summer years and a latest observation in 2022 or later.",
          "History only: the record is still available, but the outlook is withheld when history or recency is limited.",
        ],
      },
      {
        id: "trends-limitations",
        title: "How to read it responsibly",
        paragraphs: [
          "Start with the observed record and look for the latest measured value, the length of the history, and whether an outlook is available. Treat the point estimate as a baseline, not a promise.",
          "The ranges are empirical backtest ranges, not formal guarantees. They do not include every source of future change, such as weather, watershed conditions, invasive species, or management actions. Continued monitoring remains the best way to learn what is happening in a lake.",
        ],
      },
    ],
  },
};
