# Maine Lakes Secchi Depth

This repository is used to iterate on Secchi-depth modeling experiments and keep a deployment-ready dashboard layer that serves the selected model artifacts.

## Repository Map

- `data/` contains the canonical research inputs, especially `Merged_Dataset.csv` and `Merged_Dataset_Metadata.csv`.
- `experiments/` contains the stable experiment registry, runner, template, and the numbered experiment scripts that generate reports.
- `reports/` contains the committed canonical report outputs and figure artifacts produced by experiments.
- `artifacts/models/` contains dashboard-facing model artifacts, the manifest, and the model training/export script.
- `dashboard/` contains the frontend and backend application used to serve the active CatBoost model.
- `docs/` contains hosting and workflow documentation that is not tied to a single experiment run.

## Core Workflows

### 1. Understand the dataset and experiment storyline

- Read `experiments/README.md` for the chronological research narrative.
- Use `python experiments/run.py list` to inspect the stable experiment registry.
- Open `reports/` when you need the canonical run outputs for a specific experiment ID.

### 2. Rerun or add experiments

- Run one experiment with `python experiments/run.py run 22`.
- Validate the committed output contract with `python experiments/run.py validate`.
- Use `experiments/templates/experiment_template.py` and `experiments/RUNBOOK.md` when adding a new experiment.
- Use `docs/COMMIT_CHECKLIST.md` before committing larger repo changes.

### 3. Train or swap dashboard model artifacts

- Rebuild dashboard artifacts with `python artifacts/models/train_dashboard_model.py`.
- The backend reads the active model from `artifacts/models/` using `model_manifest.json`.
- Model replacement should happen through artifact regeneration or artifact swap, not backend code edits.

## Current Research Status

- The experiment system is the source of truth for model exploration (38 canonical experiments, `01`–`38`).
- Reports are committed outputs, not final interpretation documents.
- The dashboard is intentionally downstream of model selection and serves one active artifact set today.
- A tuned native-missing CatBoost model is live in the playground; trend forecasting remains a future workspace.

## Dashboard and Model Selection

The dashboard is not treated as the research environment. It is a serving layer that depends on:

- a validated artifact manifest
- compatible serialized model assets
- a stable feature contract shared by backend and frontend

Local UI entry is `/` (landing); the scenario explorer runs at `/playground`. See `dashboard/README.md` for dev and deployment setup.

As the served model changes, regenerate or replace the contents of `artifacts/models/`, verify backend startup, and update the dashboard UI only when the product surface needs to change.