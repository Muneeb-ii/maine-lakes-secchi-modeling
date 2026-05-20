from __future__ import annotations

from experiment_utils import CanonicalReport, load_data, write_canonical_report


EXPERIMENT_ID = "XX"
REPORT_FILENAME = "XX_experiment_slug.md"
REPORT_TITLE = "Experiment XX: Replace With Final Title"


def main() -> None:
    df = load_data().frame

    report = CanonicalReport(
        objective=(
            "State the exact question being tested and the reason this experiment exists "
            "relative to the prior baseline."
        ),
        method=(
            "Describe the data subset, train/test split, feature policy, model family, "
            "and any major preprocessing or validation decisions."
        ),
        parameters=(
            "List the key tunable settings, feature groups, and any external inputs or "
            "supporting artifacts used during the run."
        ),
        results=(
            f"Record the core tables, metrics, and figure references here. "
            f"Loaded rows for reference: {len(df):,}."
        ),
        next_step=(
            "State the immediate follow-on experiment or decision this result unlocked. "
            "Keep this brief and workflow-oriented."
        ),
    )

    path = write_canonical_report(REPORT_FILENAME, REPORT_TITLE, report)
    print(f"Wrote report to {path}")


if __name__ == "__main__":
    main()
