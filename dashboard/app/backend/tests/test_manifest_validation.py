import json
import tempfile
import unittest
from pathlib import Path

from artifact_validation import validate_manifest


class ManifestValidationTests(unittest.TestCase):
    def test_validate_manifest_success(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            models_path = Path(temp_dir)
            artifact_file = models_path / "artifact.bin"
            artifact_file.write_bytes(b"artifact")

            manifest = {
                "feature_order": ["A", "B"],
                "artifacts": [
                    {
                        "name": "artifact",
                        "path": "artifact.bin",
                        "required": True,
                        "sha256": "c7c5c1d70c5dec4416ab6158afd0b223ef40c29b1dc1f97ed9428b94d4cadb1c",
                    }
                ],
            }

            ok, errors = validate_manifest(
                models_path=models_path,
                manifest=manifest,
                expected_feature_order=["A", "B"],
            )
            self.assertTrue(ok)
            self.assertEqual(errors, [])

    def test_validate_manifest_detects_mismatch(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            models_path = Path(temp_dir)
            manifest = {"feature_order": ["wrong"], "artifacts": []}
            ok, errors = validate_manifest(
                models_path=models_path,
                manifest=manifest,
                expected_feature_order=["A", "B"],
            )
            self.assertFalse(ok)
            self.assertTrue(any("feature_order" in err for err in errors))


if __name__ == "__main__":
    unittest.main()
