# Commit Checklist

Use this checklist before committing repository changes.

## Repository Hygiene

- Local-only directories such as `.venv/`, `.cache/`, `.codex/`, `.cursor/`, and frontend `node_modules/` are not part of the commit.
- Generated reports and figures are committed only when they are part of the canonical experiment contract.
- Temporary debug files, notebooks, or ad hoc exports are either removed or explicitly documented before commit.

## Experiment Layer

- Any changed canonical experiment script has a matching entry in `experiments/registry.json`.
- `python experiments/run.py validate` passes.
- `python experiments/verify_reports.py` passes.
- If experiment outputs changed intentionally, the matching report and figures in `reports/` were regenerated in the same change set.

## Documentation

- `README.md` still reflects the real top-level structure.
- `experiments/README.md` matches the current experiment storyline and report status.
- `experiments/RUNBOOK.md` still matches the actual experiment workflow.
- Dashboard or hosting docs are updated when artifact paths, runtime assumptions, or deployment behavior change.

## Dashboard Layer

- Model artifact changes are reflected in `artifacts/models/`.
- The dashboard still reads artifacts through the manifest and feature contract rather than hard-coded experiment assumptions.
- Any backend or frontend contract change is paired with the relevant tests or build verification.

## Recommended Verification

- `python experiments/run.py validate`
- `python experiments/verify_reports.py`
- backend tests
- frontend build/tests

The goal is not to commit a perfectly finished research repo. The goal is to commit a repo whose current state is deliberate, reproducible, and easy for the next collaborator to understand.
