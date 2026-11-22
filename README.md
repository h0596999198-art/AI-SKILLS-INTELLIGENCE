# AI-SKILLS-INTELLIGENCE

**A governed, security-first registry for reusable AI skills.**

This repository discovers skill metadata, records immutable provenance, evaluates licensing and security evidence, detects duplicates, and publishes an approved catalog. It is designed to serve multiple independent projects through a **read-only catalog contract**.

## What this repository is — and is not

- It is a catalog, review system, provenance ledger, and compatibility registry.
- It is not a runtime, code executor, package installer, secrets store, or project backup.
- Discovery never executes candidate code or installs candidate dependencies.
- A source repository or skill collection is untrusted until each skill is independently reviewed.
- An empty approved catalog is intentional. No skill is approved by default.

## Consumers

ORION and FLIRA may consume the same approved catalog independently. The integration contract is documented in [integrations/README.md](integrations/README.md).

**Data boundary:** consumers may fetch approved public metadata and, only where licensing permits, the reviewed skill artifact. Consumers must never upload project files, prompts, customer data, logs, environment variables, credentials, private source code, database exports, or runtime memory to this registry. No consumer telemetry is required.

Each consumer keeps its own credentials, configuration, data stores, runtime, permissions, and approval decisions. Registry approval does not grant a skill permission to access consumer systems.

## Approval lifecycle

`discovered → under_review → approved | rejected`

Approval requires all of the following:
1. HTTPS source and immutable 40-character upstream commit.
2. Exact reviewed content SHA-256 and source path.
3. Verifiable license evidence and explicit redistribution permission.
4. Security review result `pass`.
5. Compatibility review result `pass` for declared targets.
6. Duplicate review result `pass`.
7. Named reviewer and UTC review timestamp.

A failed, missing, or unknown gate blocks approval. Review evidence is metadata; it does not replace legal review or sandbox testing by the consuming project.

## Repository map

- `catalog/`: registry index, categories, and untrusted source list.
- `schemas/`: machine-readable record contract.
- `policies/`: approval and security invariants.
- `integrations/`: consumer isolation and read-only integration contracts.
- `scripts/`: standard-library validators and secret hygiene checks.
- `.github/workflows/`: read-only CI checks.

## Local validation

Requires Python 3.12+; no third-party packages are needed.

```bash
python scripts/validate_catalog.py
python scripts/security_hygiene.py
python -m unittest discover -s tests -v
```

## Security reporting

Do not publish exploit details or secrets in an issue. Report suspected exposure privately to the repository owner and rotate any credential that may have been exposed. Removing a secret from the latest commit does not erase it from Git history; revoke/rotate first, then perform a history cleanup if necessary.

## Governance

Changes to approval policy, schemas, workflows, or integration contracts require review. CI uses read-only repository permissions, pinned GitHub Actions, and never executes candidate skill code.
