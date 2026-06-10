# Project Context

Agent-oriented map of the Maine Lakes Secchi-depth modeling repository. Read this first before making changes.

## Snapshot (current state)

| Area | Status |
|------|--------|
| Experiments | **38 canonical** experiments (`01`–`38`), all registered in `experiments/registry.json` |
| Research narrative | Phases 1–4 complete through CatBoost tuning, imputation benchmarks, and LOLO quality thresholds |
| Active dashboard model | **Tuned native-missing CatBoost** (no `CHLA`), version `2026-05-28-exp34-exp38` |
| Supported lakes | **187 of 994** lakes after base filtering (`n_obs >= 100`, chemistry missingness `<= 0.90`) |
| Deployment | Render Blueprint (`render.yaml`); CI gates deploy via `checksPass` |
| Python | **3.11** (backend + experiments) |
| Frontend | React 18 + Vite 6 + Tailwind; client-side routes at `/`, `/playground`, `/trends`, `/contributors`, `/modeling-process` |

**Research is done in `experiments/`; serving is done in `dashboard/`.** Model selection happens in experiments and artifact export — not in dashboard code.

Current dashboard UX:

- `/` — landing page with hero copy, clarity bands, and workspace destination cards.
- `/playground` — CatBoost scenario explorer (sliders, trajectory, SHAP drivers).
- `/trends` — Trend Following placeholder (model in development).
- `/contributors` and `/modeling-process` — static info pages linked from the shared footer.
- Light, WCAG-oriented theme with semantic section accents (`lib/theme.js`), clarity-band theming, 18 px base type, and colorblind-safe status colors (`dashboard/DESIGN.md`).
- **Claro** — mint-green guided tour on `/playground` (`components/claro/`, `lib/claroTourContent.js`); `data-claro-target` anchors on key panels.
- **Save & compare** — labeled snapshots in `localStorage` (`lib/savedScenarios.js`, schema v1); lake-scoped compare, load, delete; trajectory chart + change-log table share `chartHistory`.
- Playground supports **per-feature include toggles**; excluded chemistry fields are sent as `null` so CatBoost uses native missing-value handling.
- **Brand mark** — lake + Secchi disk logo (`components/brand/DashboardLogo.jsx`, `SiteBrand.jsx`); favicon at `app/frontend/public/favicon.svg`; primary blue `#005AB5` (`theme-color` in `index.html`). Distinct from the green Claro mascot.
- **Site chrome** — `InfoPageNav` shows logo + optional page eyebrow; playground/trends use eyebrows instead of duplicate header pills.
- **Info pages** — contributors and modeling-process show `PageInProgressNotice` while copy evolves (`lib/siteStatus.js` toggle).
- Partner logos in `dashboard/app/frontend/src/assets/logos/`; copy in `lib/copy.js`, `lib/infoPagesCopy.js`, `lib/featureLabels.js`.
- Routing uses `history.pushState` + `popstate` (no router package); Render/Nginx serves `index.html` for all paths.

## Two-layer architecture

```
experiments/ + reports/     →  research, exploration, committed outputs
         ↓
artifacts/models/           →  manifest + serialized model (boundary)
         ↓
dashboard/                  →  FastAPI backend + React frontend (serving only)
```

Do not embed experiment logic in the dashboard. Do not hard-code model assumptions in the dashboard when the manifest or feature contract already define them.

## Directory map

| Path | Purpose | Touch when |
|------|---------|------------|
| `data/` | Canonical inputs: `Merged_Dataset.csv`, `Merged_Dataset_Metadata.csv`, plus source exports | Dataset or metadata changes |
| `experiments/` | Registry, runner (`run.py`), scripts (`scripts/`), utils, RUNBOOK | Adding/rerunning experiments |
| `experiments/registry.json` | Source of truth for experiment IDs, scripts, reports, artifacts, dependencies | Any new or changed experiment |
| `reports/` | Committed markdown reports and PNG figures from experiments | After intentional experiment reruns |
| `artifacts/models/` | Dashboard model: manifest, joblib, lake policy JSON, training script | Swapping or retraining the served model |
| `dashboard/app/backend/` | FastAPI API, feature contract, model adapters, tests | API, prediction, or contract changes |
| `dashboard/app/frontend/` | React UI, hooks, contract tests, landing/playground/trends pages | UI/UX or client-side contract changes |
| `docs/` | Commit checklist, hosting, report style | Workflow or deployment doc updates |
| `.github/workflows/` | `dashboard-ci.yml` (primary gate), `ci.yml` (lighter) | CI behavior changes |

**Not committed:** `.venv/`, `.cache/`, `node_modules/`, `.cursor/`, `.codex/`.

## Active model contract

The backend loads artifacts from `MODEL_ARTIFACTS_PATH` (default: repo-root `artifacts/models/`).

Key files:

- `model_manifest.json` — schema version, feature order, artifact checksums, metrics, proof-experiment trail
- `catboost_predictor.joblib` — serialized `CatBoostRegressor`
- `supported_lakes_policy.json` — which lakes the dashboard will serve
- `baseline_lakes_summary.json`, `lake_names.json` — lake metadata for the UI
- `dashboard_model_report.md` — human-readable artifact summary

Feature order (14 features, **no `CHLA`**): `year`, `month`, `LATITUDE`, `LONGITUDE`, `AREA_ACRES`, `DEPTH_MAX_FEET`, `DOMAX`, `DOMIN`, `TPEC`, `TPBG`, `PH`, `COLOR`, `CONDUCT`, `ALK`.

Shared definitions live in:

- `artifacts/models/model_manifest.json` → `feature_order`
- `dashboard/app/backend/feature_contract.py` → `CANONICAL_FEATURE_ORDER`
- `dashboard/app/frontend/src/lib/contracts.js` → must stay aligned (`buildPayloadFeatures` supports `null` excluded features)

Proof trail for the current model: experiments **34**, **35**, **37**, **38** (see manifest `proof_experiments` and `dashboard/README.md`).

To retrain or swap the served model:

```bash
python artifacts/models/train_dashboard_model.py
```

Then verify manifest checksums, backend startup, and tests before committing.

## Experiment sequence (high level)

Full narrative: `experiments/README.md`. Registry metadata: `experiments/registry.json`.

| Phase | IDs | Focus |
|-------|-----|-------|
| 1 — Dataset shape | `01`–`08` | Missingness, distributions, correlations, temporal/spatial structure |
| 2 — Baselines & generalization | `09`–`18` | Depth/type splits, RF baseline, LOLO, chemical features, temporal validation |
| 3 — Trees & MissForest | `19`–`26` | Spatial features, XGB/LGBM/CatBoost, MissForest chronology and elimination |
| 4 — Deep learning & CatBoost follow-ups | `27`–`38` | MLP/TabNet/FT-Transformer, regional benchmarks, tuned CatBoost, imputation benchmark, LOLO quality thresholds |

Latest experiments (`36`–`38`) cover imputation comparison and supported-lake policy selection for the dashboard.

## Task routing (for agents)

| If you need to… | Start here |
|-----------------|------------|
| Understand the research storyline | `experiments/README.md`, then `reports/<id>_*.md` |
| List or run an experiment | `python experiments/run.py list` / `run <id>` |
| Add a new experiment | `experiments/templates/experiment_template.py`, `experiments/RUNBOOK.md`, update `registry.json` |
| Check committed outputs exist | `python experiments/run.py validate` |
| Validate report structure/content | `python experiments/verify_reports.py` |
| Change the served model | `artifacts/models/train_dashboard_model.py`, then manifest + policy JSON |
| Change prediction inputs or API shape | `feature_contract.py`, `contracts.py`, frontend `contracts.js` + tests |
| Work on UI or routes | `dashboard/app/frontend/src/`, `lib/routes.js`, then `dashboard/DESIGN.md` |
| Change landing/info copy | `lib/copy.js`, `lib/infoPagesCopy.js`, `lib/featureLabels.js` |
| Change dashboard logo / favicon | `components/brand/`, `app/frontend/public/favicon.svg`, `dashboard/DESIGN.md` |
| Change info-page draft banner | `lib/siteStatus.js`, `PageInProgressNotice.jsx` |
| Change Claro tour | `lib/claroTourContent.js`, `components/claro/ClaroGuide.jsx` |
| Change save/compare snapshots | `lib/savedScenarios.js`, `hooks/useSavedScenarios.js`, `ScenarioActionBar.jsx` |
| Change rate limits | `dashboard/app/backend/rate_limit.py`, `dashboard/README.md` |
| Work on API | `dashboard/app/backend/main.py`, adapters in `model_adapters.py` |
| Deploy or host | `docs/dashboard/HOSTING.md`, `render.yaml`, `dashboard/render.Dockerfile` |
| Pre-commit review | `docs/COMMIT_CHECKLIST.md` |

## Commands

Run from **repository root** unless noted.

### Experiments

```bash
pip install -r experiments/requirements.txt

python experiments/run.py list
python experiments/run.py validate
python experiments/verify_reports.py
python experiments/run.py run 38          # single experiment
python experiments/run.py run-all         # all canonical (long-running)
```

### Dashboard — local dev

```bash
# Backend
cd dashboard/app/backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend (separate terminal)
cd dashboard/app/frontend
npm ci
npm run dev
```

Copy `.env.example` for local env vars (`VITE_API_URL`, `API_ALLOWED_ORIGINS`, `MODEL_ARTIFACTS_PATH`).

### Dashboard — Docker

```bash
docker compose up --build    # backend :8000, frontend :5173
```

### Dashboard — verification

```bash
# Backend tests
cd dashboard/app/backend && python -m unittest discover -s tests

# Frontend contract tests + build
cd dashboard/app/frontend && npm run test:contracts && npm run build
```

## API surface (backend)

Base path locally: `http://localhost:8000`. On Render, proxied at `/api/*`.

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/` | Health / readiness (validates artifacts) |
| `GET` | `/config/features` | Feature schema for the UI |
| `GET` | `/lake/{midas_id}` | Lake profile and support status |
| `GET` | `/lakes/search` | Lake search |
| `POST` | `/predict_scenario` | Scenario prediction + explainability; editable features may be `null` when excluded in the UI |

Rate limits (sliding 60 s window, per client IP): `API_RATE_LIMIT_PER_MINUTE` default **180** on all routes; `PREDICT_RATE_LIMIT_PER_MINUTE` default **60** on predict (counts toward the API total). Over-limit → HTTP `429` with `Retry-After`. See `dashboard/README.md` and `rate_limit.py`.

## CI and deployment

- **`dashboard-ci.yml`** (primary): backend tests + pip-audit, frontend contract tests + build, `verify_reports.py`, Docker image builds. Runs on push/PR to `main`/`master`. Render uses `autoDeployTrigger: checksPass`.
- **`ci.yml`**: lighter workflow (backend tests, `run.py validate`, frontend tests/build, Docker builds on all pushes/PRs).

Render ships one combined image (`dashboard/render.Dockerfile`): Nginx serves the built frontend and proxies `/api/*` to Uvicorn. Artifacts are copied into the image at build time.

## Development rules

1. **Prefer existing conventions** — experiment runner, registry, templates, report naming (`reports/<id>_<slug>.md`).
2. **Registry first** — new/changed canonical experiments require `experiments/registry.json` updates and regenerated reports when outputs change intentionally.
3. **Artifact-driven dashboard** — swap models via `artifacts/models/`, not backend hard-coding.
4. **Keep contracts aligned** — backend `feature_contract.py`, frontend `contracts.js`, and manifest `feature_order` must match.
5. **Dashboard theme consistency** — keep the light accessible palette, semantic accents from `lib/theme.js` + `index.css`, clarity-band colors aligned across routes, 18 px base text, `text-base` or larger body/control copy, visible focus states, and shared `AppFooter` consistent across all frontend routes.
6. **Feature inclusion contract** — excluded editable features must be `null` in the predict payload (frontend `buildPayloadFeatures`, backend `_prediction_features` → `NaN` for CatBoost).
7. **Minimal verification** — run the smallest check set that covers your change (see below).
8. **Surgical diffs** — do not refactor unrelated code; match surrounding style.

## Verification matrix

| Change type | Run |
|-------------|-----|
| Experiment script or registry | `python experiments/run.py validate` + `python experiments/verify_reports.py` |
| Report outputs intentionally changed | Regenerate reports/figures, then both validators above |
| Model artifacts | `train_dashboard_model.py`, backend tests, manual API startup |
| Backend | `python -m unittest discover -s tests` in `dashboard/app/backend` |
| Frontend | `npm run test:contracts` + `npm run build` in `dashboard/app/frontend` |
| Docker / deploy | `docker compose up --build` or CI Docker job |

## Further reading

- `README.md` — top-level repo map
- `experiments/README.md` — full experiment narrative by phase
- `experiments/RUNBOOK.md` — how to add and run experiments
- `dashboard/README.md` — local dev, model policy, Render setup
- `dashboard/DESIGN.md` — dashboard UI/UX, layout, design system, frontend architecture
- `docs/COMMIT_CHECKLIST.md` — pre-commit checklist
- `docs/dashboard/HOSTING.md` — hosting details
- `docs/experiments/REPORT_STYLE.md` — report formatting conventions
