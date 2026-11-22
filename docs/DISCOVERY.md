# Metadata-only discovery

The scheduled workflow scans only public GitHub repository metadata and recursive Git tree entries for repositories explicitly listed in `catalog/sources.json`.

- Resolves the default branch to an immutable commit SHA.
- Reads tree paths, modes, sizes, and Git blob SHAs only.
- Never fetches candidate file contents, clones repositories, installs packages, or executes candidate code.
- Ignores symlinks, unsafe paths, oversized files, and truncated trees.
- Uses read-only repository permissions and uploads reports as short-lived workflow artifacts; it never commits to the approved catalog.
- Every result remains `unreviewed_candidate`; discovery cannot approve or activate a skill.

The Git blob SHA is an exact duplicate hint. The normalized-path SHA-256 is a path identity hint, not a content digest. A later isolated review must hash the actual reviewed bytes and verify license, provenance, security, duplication, and consumer compatibility.

Run locally: `python scripts/discover_sources.py` followed by `python -m unittest discover -s tests -v`.
