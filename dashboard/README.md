# Dashboard

The dashboard is a serving layer for finalized research artifacts. It is intentionally separated from the experiment workflow so the UI and API do not become the place where model selection happens.

## Layout

- `dashboard/app/backend/` contains the FastAPI API and backend contract tests.
- `dashboard/app/frontend/` contains the React + Vite frontend.
- `artifacts/models/` contains the active artifact set loaded by the backend.

## Local Development

### Backend

- `cd dashboard/app/backend`
- `pip install -r requirements.txt`
- `uvicorn main:app --reload --port 8000`

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
- Prediction feature set: no `CHLA`; uses the same 14-feature order as Experiment 34.
- Supported-lake policy: `n_obs >= 100` after base filtering and `pct_missing_chemical_overall <= 0.90`.
- Current coverage: 187 supported lakes out of 994 lakes after base filtering.
- Active proof trail: Experiments `34`, `35`, `37`, and `38`.

Why these experiments matter:

- `34` establishes tuned no-CHLA CatBoost as the strongest chronological model path.
- `35` shows unrestricted LOLO generalization is still weak.
- `37` shows MissForest imputation hurts CatBoost, so the dashboard keeps native missing-value handling.
- `38` shows the supported-lake policy improves confirmed 100-lake LOLO average R2 from the unrestricted baseline.

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

## Artifact Contract

- The backend loads its active model from `MODEL_ARTIFACTS_PATH`.
- Default local path is `artifacts/models/`.
- Required files are validated via `model_manifest.json` before the API reports itself as ready.
- Swapping models should be done by replacing or regenerating artifacts, not by editing the API code.
