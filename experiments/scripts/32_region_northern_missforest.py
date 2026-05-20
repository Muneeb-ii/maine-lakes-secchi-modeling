"""Experiment 32: Northern region — MissForest + RF (Parts 1–3)."""

from experiment_utils import write_markdown_report
from region_experiment_common import build_region_report_sections

REPORT_NAME = "32_region_northern_missforest.md"


def main() -> None:
    title, sections = build_region_report_sections(region_key="northern", experiment_num=32)
    path = write_markdown_report(REPORT_NAME, title, sections)
    print(f"Report written to {path}")


if __name__ == "__main__":
    main()
