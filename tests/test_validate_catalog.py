import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_catalog.py"
SPEC = importlib.util.spec_from_file_location("validate_catalog", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)

CATEGORIES = {"categories": ["coding", "security", "other"]}


def candidate(**overrides):
    record = {
        "id": "safe-skill",
        "name": "Safe skill",
        "category": "coding",
        "source": {"url": "https://github.com/example/repo", "path": "skills/safe/SKILL.md"},
        "revision": "a" * 40,
        "content_sha256": "b" * 64,
        "status": "discovered"
    }
    record.update(overrides)
    return record


def catalog(*records):
    return {"schema_version": "1.0", "registry": "AI-SKILLS-INTELLIGENCE", "skills": list(records)}


class CatalogValidationTests(unittest.TestCase):
    def test_empty_bootstrap_catalog_is_valid(self):
        self.assertEqual(MODULE.validate_data(catalog(), CATEGORIES), [])

    def test_valid_discovered_candidate_is_allowed(self):
        self.assertEqual(MODULE.validate_data(catalog(candidate()), CATEGORIES), [])

    def test_duplicate_ids_are_rejected(self):
        errors = MODULE.validate_data(catalog(candidate(), candidate()), CATEGORIES)
        self.assertTrue(any("duplicate skill id" in error for error in errors))

    def test_parent_path_is_rejected(self):
        item = candidate(source={"url": "https://github.com/example/repo", "path": "../secret"})
        errors = MODULE.validate_data(catalog(item), CATEGORIES)
        self.assertTrue(any("safe relative path" in error for error in errors))

    def test_approved_record_requires_every_gate(self):
        item = candidate(status="approved")
        errors = MODULE.validate_data(catalog(item), CATEGORIES)
        self.assertGreaterEqual(len(errors), 5)

    def test_approved_record_passes_with_evidence(self):
        item = candidate(
            status="approved",
            license={"evidence_url": "https://opensource.org/license/mit", "redistribution_permitted": True},
            security={"result": "pass", "reviewed_at_utc": "2026-11-22T08:00:00Z"},
            compatibility={"result": "pass", "targets": ["ORION", "FLIRA"]},
            duplicate_check={"result": "pass", "fingerprint": "c" * 64},
            approval={"reviewer": "maintainer", "reviewed_at_utc": "2026-11-22T08:10:00Z"}
        )
        self.assertEqual(MODULE.validate_data(catalog(item), CATEGORIES), [])

    def test_duplicate_fingerprints_are_rejected(self):
        first = candidate(duplicate_check={"result": "pass", "fingerprint": "d" * 64})
        second = candidate(id="another-skill", duplicate_check={"result": "pass", "fingerprint": "d" * 64})
        errors = MODULE.validate_data(catalog(first, second), CATEGORIES)
        self.assertTrue(any("duplicate content fingerprint" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
