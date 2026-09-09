# Data provenance

`catalog.json` is the source of truth for dataset IDs, file paths, hashes, lineage, and the active research snapshot.

## Layout

- `raw/` contains provider files exactly as received. Never edit them.
- `processed/<dataset-id>/` contains a merged modeling dataset, its metadata, and its build summary.
- `derived/<dataset-id>/` contains outputs that are valid only for that processed dataset.
- `pipeline/` contains reproducible processing code.

Snapshot IDs use the provider release date: `secchi-YYYY-MM-DD`. Processed IDs add the merge revision: `secchi-merged-YYYY-MM-DD-rN`. Increase `rN` only when processing the same raw release differently.

## Current datasets

- `secchi-merged-2025-04-17-r1` is the immutable historical input for experiments `01`–`38`.
- `secchi-merged-2026-06-29-r1` is the active input for new research and the current dashboard artifacts. The June delivery supersedes April; both contain measurements through 2024-12-03.

In the active snapshot, `PH`, `COLOR`, `CONDUCT`, and `ALK` are fixed lake-level means derived from legacy station-date observations. Future interfaces must join these values by `MIDAS`, not expose them as user-editable inputs. The playground follows this: they are locked lake descriptors (Experiment 47).

The LOLO seed lists under `derived/secchi-merged-2026-06-29-r1/` are the same lake lists as the 2025 snapshot seeds so leave-one-lake-out results stay comparable across snapshots.

Regenerate a snapshot's lake-missingness matrix with:

```bash
SECCHI_DATASET_ID=secchi-merged-2026-06-29-r1 python experiments/scripts/calculate_lake_missingness.py
```

The script writes only the chemistry and profile columns present on that dataset, so the same command works for `secchi-merged-2025-04-17-r1`.

Rebuild the active processed snapshot with:

```bash
python data/pipeline/build_secchi_merged.py --dataset-id secchi-merged-2026-06-29-r1
```

## Adding a delivery

1. Place unchanged provider files in `raw/<source>/<source-YYYY-MM-DD>/`.
2. Add paths and SHA-256 hashes to `catalog.json`.
3. Create a new processed ID and builder revision; never overwrite an existing snapshot.
4. Store dataset-dependent summaries and seeds under `derived/<processed-dataset-id>/`.
5. Record the exact processed dataset ID in each new experiment's registry entry.
