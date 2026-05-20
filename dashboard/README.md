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

## Artifact Contract

- The backend loads its active model from `MODEL_ARTIFACTS_PATH`.
- Default local path is `artifacts/models/`.
- Required files are validated via `model_manifest.json` before the API reports itself as ready.
- Swapping models should be done by replacing or regenerating artifacts, not by editing the API code.
