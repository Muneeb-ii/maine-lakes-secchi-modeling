from __future__ import annotations

import json
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = PROJECT_ROOT / "experiments" / "registry.json"
REPORT_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
HEADING_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)

CANONICAL_HEADINGS = {"Objective", "Method", "Parameters", "Results", "Next Step"}


def load_registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def audit_entry(entry: dict) -> dict:
    report_path = PROJECT_ROOT / entry["report"]
    issues: list[str] = []
    headings: list[str] = []
    image_refs: list[str] = []

    if not report_path.exists():
        return {
            "id": entry["id"],
            "report": entry["report"],
            "status": "missing_report",
            "issues": ["report file missing"],
            "headings": [],
            "image_refs": [],
        }

    text = report_path.read_text(encoding="utf-8")
    headings = HEADING_RE.findall(text)
    image_refs = REPORT_IMAGE_RE.findall(text)

    if not text.startswith("# "):
        issues.append("missing top-level markdown title")

    for image_ref in image_refs:
        asset_path = report_path.parent / image_ref
        if not asset_path.exists():
            issues.append(f"missing referenced image: {image_ref}")

    declared_artifacts = {Path(path).name for path in entry.get("artifacts", [])}
    referenced_images = {Path(path).name for path in image_refs}
    missing_declared_refs = sorted(declared_artifacts - referenced_images)
    for artifact in missing_declared_refs:
        issues.append(f"declared artifact not referenced in report: {artifact}")

    canonical_overlap = CANONICAL_HEADINGS.intersection(headings)
    if entry["id"] in {"01", "10", "22"} and canonical_overlap != CANONICAL_HEADINGS:
        issues.append("expected canonical report headings not fully present")

    return {
        "id": entry["id"],
        "report": entry["report"],
        "status": "ok" if not issues else "issues",
        "issues": issues,
        "headings": headings,
        "image_refs": image_refs,
    }


def main() -> int:
    registry = load_registry()["experiments"]
    audits = [audit_entry(entry) for entry in registry]

    issue_count = 0
    for audit in audits:
        if audit["status"] == "ok":
            print(f"OK   {audit['id']} {audit['report']}")
            continue
        issue_count += 1
        print(f"FAIL {audit['id']} {audit['report']}")
        for issue in audit["issues"]:
            print(f"  - {issue}")

    print(f"\nAudited {len(audits)} reports; {issue_count} report(s) with issues.")
    return 1 if issue_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
