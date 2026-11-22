#!/usr/bin/env python3
"""Validate catalog records and approval gates using only the standard library."""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATUSES = {"discovered", "under_review", "approved", "rejected"}
CATEGORIES_PATH = ROOT / "catalog/categories.json"
CATALOG_PATH = ROOT / "catalog/index.json"
ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,79}$")
SHA40 = re.compile(r"^[0-9a-fA-F]{40}$")
SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")


def load(path):
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def is_utc_timestamp(value):
    if not isinstance(value, str) or not value.endswith("Z"):
        return False
    try:
        datetime.fromisoformat(value[:-1] + "+00:00")
        return True
    except ValueError:
        return False


def validate_data(catalog, categories_doc):
    errors = []
    if not isinstance(catalog, dict):
        return ["catalog root must be an object"]
    if catalog.get("schema_version") != "1.0":
        errors.append("catalog.schema_version must be '1.0'")
    if catalog.get("registry") != "AI-SKILLS-INTELLIGENCE":
        errors.append("catalog.registry must be AI-SKILLS-INTELLIGENCE")
    categories = categories_doc.get("categories", []) if isinstance(categories_doc, dict) else []
    if not isinstance(categories, list) or not all(isinstance(x, str) for x in categories):
        errors.append("categories.categories must be an array of strings")
        categories = []
    skills = catalog.get("skills")
    if not isinstance(skills, list):
        return errors + ["catalog.skills must be an array"]

    seen_ids, seen_fingerprints = set(), set()
    for i, skill in enumerate(skills):
        p = f"skills[{i}]"
        if not isinstance(skill, dict):
            errors.append(f"{p} must be an object")
            continue
        sid = skill.get("id")
        if not isinstance(sid, str) or not ID_RE.fullmatch(sid):
            errors.append(f"{p}.id is invalid")
        elif sid in seen_ids:
            errors.append(f"duplicate skill id: {sid}")
        else:
            seen_ids.add(sid)

        name = skill.get("name")
        if not isinstance(name, str) or not name.strip() or len(name) > 160:
            errors.append(f"{p}.name must be a non-empty string up to 160 characters")
        if skill.get("category") not in categories:
            errors.append(f"{p}.category is not registered")

        source = skill.get("source")
        if not isinstance(source, dict):
            errors.append(f"{p}.source must be an object")
        else:
            url, path = source.get("url"), source.get("path")
            if not isinstance(url, str) or not url.startswith("https://") or any(c.isspace() for c in url):
                errors.append(f"{p}.source.url must be a valid HTTPS-style URL")
            if not isinstance(path, str) or not path or path.startswith("/") or ".." in path.split("/"):
                errors.append(f"{p}.source.path must be a safe relative path")

        revision = skill.get("revision")
        if not isinstance(revision, str) or not SHA40.fullmatch(revision):
            errors.append(f"{p}.revision must be a full 40-character commit SHA")
        digest = skill.get("content_sha256")
        if not isinstance(digest, str) or not SHA256.fullmatch(digest):
            errors.append(f"{p}.content_sha256 must be a 64-character SHA-256")

        status = skill.get("status")
        if status not in STATUSES:
            errors.append(f"{p}.status is invalid")
        if status == "approved":
            lic = skill.get("license")
            sec = skill.get("security")
            comp = skill.get("compatibility")
            dup = skill.get("duplicate_check")
            approval = skill.get("approval")
            if not isinstance(lic, dict) or not isinstance(lic.get("evidence_url"), str) or not lic["evidence_url"].startswith("https://"):
                errors.append(f"{p}: HTTPS license evidence_url required")
            if not isinstance(lic, dict) or lic.get("redistribution_permitted") is not True:
                errors.append(f"{p}: explicit redistribution permission required")
            if not isinstance(sec, dict) or sec.get("result") != "pass" or not is_utc_timestamp(sec.get("reviewed_at_utc")):
                errors.append(f"{p}: security pass and UTC review timestamp required")
            if not isinstance(comp, dict) or comp.get("result") != "pass" or not isinstance(comp.get("targets"), list) or not comp["targets"]:
                errors.append(f"{p}: compatibility pass and at least one target required")
            elif any(target not in {"ORION", "FLIRA", "generic"} for target in comp["targets"]):
                errors.append(f"{p}: compatibility target is invalid")
            if not isinstance(dup, dict) or dup.get("result") != "pass":
                errors.append(f"{p}: duplicate review must pass")
            elif dup.get("fingerprint") is not None and (not isinstance(dup["fingerprint"], str) or not SHA256.fullmatch(dup["fingerprint"])):
                errors.append(f"{p}: duplicate fingerprint must be SHA-256")
            if not isinstance(approval, dict) or not isinstance(approval.get("reviewer"), str) or not approval["reviewer"].strip() or not is_utc_timestamp(approval.get("reviewed_at_utc")):
                errors.append(f"{p}: reviewer and UTC approval timestamp required")

        dup = skill.get("duplicate_check")
        if isinstance(dup, dict) and isinstance(dup.get("fingerprint"), str) and SHA256.fullmatch(dup["fingerprint"]):
            if dup["fingerprint"] in seen_fingerprints:
                errors.append(f"{p}: duplicate content fingerprint")
            seen_fingerprints.add(dup["fingerprint"])
    return errors


def validate():
    try:
        return validate_data(load(CATALOG_PATH), load(CATEGORIES_PATH))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"Unable to load registry input: {exc}"]


if __name__ == "__main__":
    problems = validate()
    if problems:
        print("\n".join("ERROR: " + problem for problem in problems), file=sys.stderr)
        raise SystemExit(1)
    print("Catalog validation passed.")
