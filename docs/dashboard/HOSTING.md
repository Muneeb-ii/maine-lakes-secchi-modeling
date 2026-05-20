# Dashboard Hosting Notes

This dashboard is prepared for generic container hosting first so it can later be placed on Colby-managed infrastructure with minimal changes.

## Current Readiness Targets

- FastAPI backend served by Uvicorn.
- React frontend built to static assets and served through Nginx.
- Artifact-driven model loading from `artifacts/models/`.
- Environment-variable configuration for CORS and artifact location.

## Required Environment Variables

- `MODEL_ARTIFACTS_PATH` points to the artifact directory that contains `model_manifest.json` and the required serialized files.
- `API_ALLOWED_ORIGINS` controls frontend origins that may call the backend.
- `VITE_API_URL` is used at frontend build time to point the UI at the backend base URL.

## Minimal Go-Live Checklist

- Confirm container image builds succeed for frontend and backend.
- Confirm backend health endpoint reports `models_loaded=true`.
- Confirm the frontend can reach the backend with the production URL and production CORS policy.
- Confirm artifact replacement can happen without code changes.
- Confirm restart policy, logs, and TLS are handled by the eventual host.
