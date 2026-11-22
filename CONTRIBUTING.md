# Contributing

## Candidate intake
- Submit metadata and source references; do not vendor or execute candidate code during discovery.
- Use an immutable upstream Git commit SHA (40 hexadecimal characters).
- Record the exact skill path and SHA-256 digest of the reviewed content.
- Record license evidence and explicit redistribution permission.
- Include security, compatibility, and duplicate-check evidence.

## Approval
A candidate remains `discovered` or `under_review` until every gate passes. Only an authorized reviewer may set `approved`, with reviewer identity and UTC timestamp.

## Security
- Never commit credentials, access tokens, private keys, cookies, or real `.env` files.
- Do not execute untrusted candidate scripts in CI.
- Pin GitHub Actions to full commit SHAs.
- Keep CI permissions read-only.

## Quality
Run `python scripts/validate_catalog.py` and `python -m unittest discover -s tests -v`.
