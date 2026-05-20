import hashlib
import json
from pathlib import Path
from typing import Dict, List, Tuple


def _sha256_for_file(file_path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with file_path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(manifest_path: Path) -> Dict[str, object]:
    with manifest_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_manifest(
    models_path: Path,
    manifest: Dict[str, object],
    expected_feature_order: List[str],
) -> Tuple[bool, List[str]]:
    errors: List[str] = []

    manifest_feature_order = manifest.get("feature_order")
    if manifest_feature_order != expected_feature_order:
        errors.append("Manifest feature_order does not match backend feature contract.")

    artifact_entries = manifest.get("artifacts", [])
    if not artifact_entries:
        errors.append("Manifest artifacts list is empty.")

    for artifact in artifact_entries:
        name = artifact.get("name", "unknown")
        relative_path = artifact.get("path")
        expected_hash = artifact.get("sha256")
        required = artifact.get("required", True)

        if not relative_path:
            errors.append(f"Artifact {name} is missing a path.")
            continue

        artifact_path = models_path / relative_path
        if not artifact_path.exists():
            if required:
                errors.append(f"Required artifact missing: {relative_path}")
            continue

        if expected_hash:
            observed_hash = _sha256_for_file(artifact_path)
            if observed_hash != expected_hash:
                errors.append(
                    f"Checksum mismatch for {relative_path}. Expected {expected_hash}, got {observed_hash}."
                )

    return len(errors) == 0, errors
