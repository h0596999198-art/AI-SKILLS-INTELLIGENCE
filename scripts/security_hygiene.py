#!/usr/bin/env python3
"""Fail closed on secret-like files and high-confidence credential material.

This scanner never prints matched values or file contents. It is a guardrail,
not a substitute for a dedicated secret-scanning service or credential rotation.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", "__pycache__", ".venv", "node_modules"}
SECRET_NAMES = {".env", "id_rsa", "id_ed25519", "credentials.json"}
SECRET_SUFFIXES = {".pem", ".p12", ".pfx", ".key"}
MAX_BYTES = 2_000_000
PATTERNS = [
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{24,}\b"),
]


def scan():
    findings = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.name in SECRET_NAMES or path.suffix.lower() in SECRET_SUFFIXES or path.name.startswith(".env."):
            if path.name != ".env.example":
                findings.append((path.relative_to(ROOT).as_posix(), "secret-like filename"))
            continue
        try:
            if path.stat().st_size > MAX_BYTES:
                continue
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for pattern in PATTERNS:
            if pattern.search(content):
                findings.append((path.relative_to(ROOT).as_posix(), "high-confidence secret pattern"))
                break
    return findings


if __name__ == "__main__":
    findings = scan()
    if findings:
        for path, reason in findings:
            print(f"BLOCKED: {path}: {reason}", file=sys.stderr)
        raise SystemExit(1)
    print("Secret hygiene scan passed (high-confidence patterns only).")
