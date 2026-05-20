from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from tqdm.auto import tqdm


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = PROJECT_ROOT / "experiments" / "registry.json"
RUNNABLE_STATUSES = {"canonical", "script_only"}
VALIDATION_STATUSES = {"canonical"}


def load_registry() -> dict:
    with REGISTRY_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def experiments_by_id() -> dict[str, dict]:
    registry = load_registry()
    return {entry["id"]: entry for entry in registry["experiments"]}


def list_experiments() -> int:
    for entry in load_registry()["experiments"]:
        report = entry["report"]
        print(f"{entry['id']} [{entry['status']}] {entry['title']} -> {report}")
    return 0


def run_experiment(entry: dict) -> None:
    status = entry.get("status", "")
    if status not in RUNNABLE_STATUSES:
        raise RuntimeError(f"Experiment {entry['id']} is not runnable: status={status}")

    script_path = PROJECT_ROOT / entry["script"]
    if not script_path.exists():
        raise FileNotFoundError(f"Missing script for experiment {entry['id']}: {script_path}")

    env = os.environ.copy()
    env.setdefault("MPLCONFIGDIR", str(PROJECT_ROOT / ".cache" / "matplotlib"))
    env.setdefault("MPLBACKEND", "Agg")
    env.setdefault("OBJC_DISABLE_INITIALIZE_FORK_SAFETY", "YES")
    env.setdefault("OMP_NUM_THREADS", "1")
    env.setdefault("OPENBLAS_NUM_THREADS", "1")
    env.setdefault("MKL_NUM_THREADS", "1")
    env.setdefault("NUMEXPR_NUM_THREADS", "1")
    Path(env["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)

    print(f"Running experiment {entry['id']}: {entry['title']}")
    subprocess.run([sys.executable, str(script_path)], cwd=PROJECT_ROOT, env=env, check=True)


def validate_outputs(include_script_only: bool = False) -> int:
    failures: list[str] = []
    statuses = VALIDATION_STATUSES | ({"script_only"} if include_script_only else set())

    for entry in load_registry()["experiments"]:
        if entry.get("status") not in statuses:
            continue

        expected_paths = [entry["report"], *entry.get("artifacts", [])]
        missing = [path for path in expected_paths if not (PROJECT_ROOT / path).exists()]
        if missing:
            failures.append(f"{entry['id']}: missing {', '.join(missing)}")

    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        return 1

    print("All declared experiment outputs are present.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run or validate Lake Secchi experiments.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List experiment metadata.")

    run_parser = subparsers.add_parser("run", help="Run a single experiment by stable ID.")
    run_parser.add_argument("experiment_id", help="Stable two-digit experiment identifier.")

    run_all_parser = subparsers.add_parser("run-all", help="Run all canonical experiments in order.")
    run_all_parser.add_argument(
        "--include-script-only",
        action="store_true",
        help="Include script-only experiments that do not currently have canonical outputs.",
    )

    validate_parser = subparsers.add_parser("validate", help="Validate declared outputs exist.")
    validate_parser.add_argument(
        "--include-script-only",
        action="store_true",
        help="Also validate script-only experiments.",
    )

    args = parser.parse_args()

    if args.command == "list":
        return list_experiments()

    if args.command == "validate":
        return validate_outputs(include_script_only=args.include_script_only)

    registry = load_registry()["experiments"]
    lookup = {entry["id"]: entry for entry in registry}

    if args.command == "run":
        entry = lookup.get(args.experiment_id)
        if entry is None:
            raise KeyError(f"Unknown experiment ID: {args.experiment_id}")
        run_experiment(entry)
        return 0

    if args.command == "run-all":
        allowed_statuses = {"canonical"}
        if args.include_script_only:
            allowed_statuses.add("script_only")
        selected = [entry for entry in registry if entry.get("status") in allowed_statuses]
        for entry in tqdm(selected, desc="Experiments", unit="exp"):
            run_experiment(entry)
        return 0

    raise RuntimeError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
