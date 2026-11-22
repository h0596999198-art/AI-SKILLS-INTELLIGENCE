#!/usr/bin/env python3
"""Validate registry invariants using only the Python standard library."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATUSES = {"discovered", "under_review", "approved", "rejected"}
SHA40 = re.compile(r"^[0-9a-fA-F]{40}$")
SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")


def load(path):
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def validate():
    errors = []
    try:
        catalog = load(ROOT / "catalog/index.json")
        categories_doc = load(ROOT / "catalog/categories.json")
    except (OSError, json.JSONDecodeError) as exc:
        return [f"Unable to load registry input: {exc}"]
    if catalog.get("schema_version") != "1.0":
        errors.append("catalog.schema_version must be '1.0'")
    if catalog.get("registry") != "AI-SKILLS-INTELLIGENCE":
        errors.append("catalog.registry must be AI-SKILLS-INTELLIGENCE")
    categories = set(categories_doc.get("categories", []))
    skills = catalog.get("skills")
    if not isinstance(skills, list):
        return errors + ["catalog.skills must be an array"]
    seen = set()
    for i, skill in enumerate(skills):
        p = f"skills[{i}]"
        if not isinstance(skill, dict):
            errors.append(f"{p} must be an object")
            continue
        sid = skill.get("id")
        if not isinstance(sid, str) or not re.fullmatch(r"[a-z0-9][a-z0-9._-]{2,79}", sid):
            errors.append(f"{p}.id is invalid")
        elif sid in seen:
            errors.append(f"duplicate skill id: {sid}")
        else:
            seen.add(sid)
        if not isinstance(skill.get("name"), str) or not skill["name"].strip():
            errors.append(f"{p}.name is required")
        if skill.get("category") not in categories:
            errors.append(f"{p}.category is not registered")
        source = skill.get("source")
        if not isinstance(source, dict) or not str(source.get("url", "")).startswith("https://"):
            errors.append(f"{p}.source.url must use HTTPS")
        elif not source.get("path"):
            errors.append(f"{p}.source.path is required")
        if not isinstance(skill.get("revision"), str) or not SHA40.fullmatch(skill["revision"]):
            errors.append(f"{p}.revision must be a full 40-character commit SHA")
        if not isinstance(skill.get("content_sha256"), str) or not SHA256.fullmatch(skill["content_sha256"]):
            errors.append(f"{p}.content_sha256 must be a 64-character SHA-256")
        status = skill.get("status")
        if status not in STATUSES:
            errors.append(f"{p}.status is invalid")
        if status == "approved":
            lic = skill.get("license") or {}
            sec = skill.get("security") or {}
            comp = skill.get("compatibility") or {}
            dup = skill.get("duplicate_check") or {}
            approval = skill.get("approval") or {}
            if not lic.get("evidence_url"):
                errors.append(f"{p}: license evidence_url required")
            if lic.get("redistribution_permitted") is not True:
                errors.append(f"{p}: redistribution permission required")
            if sec.get("result") != "pass":
                errors.append(f"{p}: security review must pass")
            if comp.get("result") != "pass":
                errors.append(f"{p}: compatibility review must pass")
            if dup.get("result") != "pass":
                errors.append(f"{p}: duplicate review must pass")
            if not approval.get("reviewer") or not approval.get("reviewed_at_utc"):
                errors.append(f"{p}: reviewer and UTC timestamp required")
    return errors


if __name__ == "__main__":
    problems = validate()
    if problems:
        print("\n".join("ERROR: " + p for p in problems), file=sys.stderr)
        raise SystemExit(1)
    print("Catalog validation passed.")
