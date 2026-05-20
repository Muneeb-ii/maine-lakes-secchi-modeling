# Experiment Runbook

This runbook defines the expected workflow for rerunning or adding experiments. The goal is to keep the experiment system reproducible and predictable for both future maintenance and new collaborators.

## Stable Rules

- Keep the numeric experiment IDs stable forever.
- Every experiment script lives in `experiments/scripts/`.
- Every canonical experiment must have one registry entry in `experiments/registry.json`.
- Every canonical experiment must produce one committed markdown report in `reports/`.
- Supporting figures and tables should also be committed when they are part of the experiment output contract.

## Running Existing Experiments

- List available experiments with `python experiments/run.py list`.
- Run one experiment with `python experiments/run.py run 22`.
- Run all canonical experiments with `python experiments/run.py run-all`.
- Validate declared outputs with `python experiments/run.py validate`.

## Adding a New Experiment

1. Copy `experiments/templates/experiment_template.py` into `experiments/scripts/` and replace the placeholder ID, slug, and title.
2. Add a matching entry to `experiments/registry.json`.
3. Use the canonical report structure:
   - Objective
   - Method
   - Parameters
   - Results
   - Next Step
4. Write outputs into `reports/` using stable filenames prefixed by the experiment ID.
5. Commit the script, registry update, report, and any supporting figures together.

## Report Expectations

- Reports are generated outputs, not final interpretation essays.
- Reports should state what was tested, how it was run, what parameters were used, and what metrics or figures resulted.
- Keep product implications, deployment implications, and long-form interpretation out of the generated report body.
- Put research progression and cross-experiment interpretation in `experiments/README.md`.

## Supporting Utilities

- `experiments/scripts/experiment_utils.py` is the shared utility layer for loading canonical data, writing reports, and rendering tables.
- `artifacts/models/train_dashboard_model.py` is the artifact export path for dashboard-serving assets, not a replacement for the experiment workflow.
- `data/lake_missingness.csv` is a derived support file used by some later experiments and should be regenerated intentionally.
