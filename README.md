# Lake Secchi Research and Dashboard

This repository is organized around one core task: understand the lake monitoring dataset, iterate on Secchi-depth modeling experiments, and keep a deployment-ready dashboard layer that can consume the final model artifacts once the research path is settled.

## Repository Map

- `data/` contains the canonical research inputs, especially `Merged_Dataset.csv` and `Merged_Dataset_Metadata.csv`.
- `experiments/` contains the stable experiment registry, runner, template, and the numbered experiment scripts that generate reports.
- `reports/` contains the committed canonical report outputs and figure artifacts produced by experiments.
- `artifacts/models/` contains dashboard-facing model artifacts, the manifest, and the model training/export script.
- `dashboard/` contains the frontend and backend application used to serve the final selected model.
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

- The experiment system is the source of truth for model exploration.
- Reports are committed outputs, not final interpretation documents.
- The dashboard is intentionally downstream of model selection and is structured to accept a single active artifact set today.
- Multiple production models are not exposed yet, but the artifact-driven contract keeps that extension path open.

## Dashboard and Model Selection

The dashboard is not treated as the research environment. It is a serving layer that depends on:

- a validated artifact manifest
- compatible serialized model assets
- a stable feature contract shared by backend and frontend

As the final model changes, the intended workflow is to regenerate or replace the contents of `artifacts/models/`, verify backend startup, and then refine the dashboard only when the research path is stable enough to justify product/UI effort.
