"""Experiment 30: Coastal region — MissForest + RF (Parts 1–3)."""

from experiment_utils import write_markdown_report
from region_experiment_common import build_region_report_sections

REPORT_NAME = "30_region_coastal_missforest.md"


def main() -> None:
    title, sections = build_region_report_sections(region_key="coastal", experiment_num=30)
    path = write_markdown_report(REPORT_NAME, title, sections)
    print(f"Report written to {path}")


if __name__ == "__main__":
    main()
