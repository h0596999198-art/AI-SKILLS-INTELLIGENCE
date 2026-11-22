import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_catalog.py"
SPEC = importlib.util.spec_from_file_location("validate_catalog", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class CatalogValidationTests(unittest.TestCase):
    def test_empty_bootstrap_catalog_is_valid(self):
        self.assertEqual(MODULE.validate(), [])

    def test_commit_sha_pattern_is_strict(self):
        self.assertIsNotNone(MODULE.SHA40.fullmatch("a" * 40))
        self.assertIsNone(MODULE.SHA40.fullmatch("a" * 39))

    def test_sha256_pattern_is_strict(self):
        self.assertIsNotNone(MODULE.SHA256.fullmatch("b" * 64))
        self.assertIsNone(MODULE.SHA256.fullmatch("b" * 63))


if __name__ == "__main__":
    unittest.main()
