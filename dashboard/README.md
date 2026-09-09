# Dashboard

The dashboard is a serving layer for finalized research artifacts. It is intentionally separated from the experiment workflow so the UI and API do not become the place where model selection happens.

## Layout

- `dashboard/app/backend/` contains the FastAPI API and backend contract tests.
- `dashboard/app/frontend/` contains the React + Vite frontend.
- `artifacts/models/` contains the active artifact set loaded by the backend.

## Local Development

### Backend

From the repository root, use the project virtualenv so CatBoost and other backend deps resolve correctly:

- `python -m venv .venv && source .venv/bin/activate` (first time only)
- `pip install -r dashboard/app/backend/requirements.txt`
- `cd dashboard/app/backend`
- `python -m uvicorn main:app --reload --port 8000`

Use `python -m uvicorn` (not a global `uvicorn` on your PATH). A global install often runs without CatBoost and the API will report `models_loaded: false`.

### Frontend

- `cd dashboard/app/frontend`
- `npm ci`
- `npm run dev`

## Docker Workflow

- Build and run the full stack with `docker compose up --build`.
- Backend listens on `http://localhost:8000`.
- Frontend listens on `http://localhost:5173`.


## Active Model Policy

The current dashboard artifact set serves the tuned native-missing CatBoost model selected from the later experiment sequence.

- Model family: `CatBoostRegressor`
- Prediction feature set: no `CHLA`; 16 features per Experiment 47 — six editable measured inputs (`DOMAX`, `DOMIN`, `TMAX`, `TMIN`, `TPEC`, `TPBG`) plus locked lake context (`year`, `month`, geography, and the fixed lake-level `PH`, `COLOR`, `CONDUCT`, `ALK`).
- Supported-lake policy: `n_obs >= 100` after base filtering. The inherited 2025 chemistry-missingness cutoff remains in the artifact but is nearly inert on the June snapshot (Experiment 47).
- Current coverage: 360 supported lakes out of 1,011 lakes after base filtering (152 of those supported lakes are flagged `thin_history`).
- Published Playground metrics are a chronological 80/20 holdout. The served CatBoost is a separate fit on all supported rows.
- Active proof trail: Experiments `34`, `35`, `37`, `38` (2025 snapshot decisions) and `47` (June contract and support rule).
- Support tiers: `supported` (`n_obs >= 100`) drives selectability; `thin_history` (supported but measured slider fields missing > 90%) only drives the amber warning in the playground header (`LakeSupportNote`).

Why these experiments matter:

- `34` (2025) chose the CatBoost hyperparameters transferred to June.
- `35` (2025) shows unrestricted LOLO generalization is still weak.
- `37` (2025) shows MissForest imputation hurts CatBoost, so the dashboard keeps native missing-value handling.
- `38` (2025) chose the `n_obs >= 100` cutoff. Its chemistry-missingness rule does not do meaningful work on June data.
- `47` (June) is the served feature contract, the thin-history warning, and the June chronological/LOLO check.

The detailed artifact-level report is `artifacts/models/dashboard_model_report.md`, and the machine-readable support metadata is `artifacts/models/supported_lakes_policy.json`.


## Render Deployment

The Render deployment uses one free Docker web service so the frontend and backend ship together:

- `render.yaml` defines the Render Blueprint service.
- `dashboard/render.Dockerfile` builds the React frontend with `VITE_API_URL=/api`, installs the FastAPI backend, and copies the committed model artifacts into the image.
- `dashboard/nginx.render.conf.template` serves the static frontend and proxies `/api/*` to FastAPI on `127.0.0.1:8000`.
- `dashboard/start-render.sh` starts both Uvicorn and Nginx inside the Render container.
- Render health checks use `/api/`, which is proxied to the FastAPI root endpoint.

Recommended Render setup:

1. Create a new Blueprint from this GitHub repo and select `render.yaml`.
2. Keep `autoDeployTrigger: checksPass` so Render deploys only after GitHub Actions passes.
3. Use the generated `https://<service>.onrender.com` URL first; add a custom domain later if needed.
4. To update the deployed model, regenerate and commit the files under `artifacts/models/`, including `model_manifest.json` and `catboost_predictor.joblib`.

The GitHub Actions workflow at `.github/workflows/dashboard-ci.yml` runs backend tests, frontend contract/build checks, report validation, and Docker image build checks before Render deploys.

## API rate limiting

The FastAPI backend applies per-IP sliding-window limits (60-second window):

| Env var | Default | Applies to |
|---------|---------|------------|
| `API_RATE_LIMIT_PER_MINUTE` | `180` | All API routes (health, config, lake lookup, search, predict) |
| `PREDICT_RATE_LIMIT_PER_MINUTE` | `60` | `POST /predict_scenario` only (stricter; counts toward the API total too) |

Set either variable to `0` to disable that limit (not recommended in production). Over-limit responses return HTTP `429` with a `Retry-After` header (seconds).

Behind Render/Nginx, limits use the client IP from `X-Forwarded-For`.

## Artifact Contract

- The backend loads its active model from `MODEL_ARTIFACTS_PATH`.
- Default local path is `artifacts/models/`.
- Required files are validated via `model_manifest.json` before the API reports itself as ready.
- Swapping models should be done by replacing or regenerating artifacts, not by editing the API code.

## Trends

Trends uses the June 2026 dataset: summer observations through 2024 for 1,084 lakes. Experiment 45 withholds a skillful multi-year forecast. Experiment 46 supports a labeled local-level baseline outlook for 2025–2029, with empirical 80% and 95% ranges. Experiment 48 is a simple-model challenger; Experiment 49 is the replacement test and does not swap the served model until post-2024 outcomes exist.

Forecasts require at least 10 observed summer years and an observation in 2022 or later; other lakes retain historical charts. Rebuild the separate serving artifact with `.venv/bin/python artifacts/models/build_trends_artifact.py` after the Experiment 46 assessment and calibration outputs are finalized. Restart the API after rebuilding.

`GET /trends` serves the index and validation metadata; `GET /trends/lakes/{midas_id}` serves one lake's history and available outlook. The API reads `artifacts/models/trends_artifact.json` without running research code.
