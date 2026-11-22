#!/usr/bin/env python3
"""Metadata-only discovery of public SKILL.md files in explicitly allowlisted GitHub repositories."""
import argparse, hashlib, json, re, sys, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "catalog" / "sources.json"
MAX_FILE_BYTES = 262144
MAX_CANDIDATES = 250
UA = "AI-SKILLS-INTELLIGENCE/1.0 metadata-only"
def github_repo(url):
    p = urllib.parse.urlparse(url)
    parts = [x for x in p.path.strip("/").split("/") if x]
    if p.scheme != "https" or p.netloc.lower() != "github.com" or len(parts) != 2:
        raise ValueError("source must be an HTTPS GitHub owner/repository URL")
    if any(not re.fullmatch(r"[A-Za-z0-9_.-]+", x) for x in parts):
        raise ValueError("invalid GitHub repository identifier")
    return parts[0], parts[1]
def safe_path(path):
    if not isinstance(path, str) or not path or path.startswith("/") or "\\" in path:
        return False
    return all(part not in {"", ".", ".."} for part in PurePosixPath(path).parts)
def normalized_path(path):
    return "/".join(x.lower() for x in PurePosixPath(path).parts if x not in {"", "."})
def api_get(url, opener=urllib.request.urlopen):
    req = urllib.request.Request(url, headers={"Accept":"application/vnd.github+json","User-Agent":UA,"X-GitHub-Api-Version":"2022-11-28"})
    with opener(req, timeout=20) as response:
        if response.status != 200:
            raise RuntimeError(f"GitHub API HTTP {response.status}")
        raw = response.read(4000001)
    if len(raw) > 4000000:
        raise RuntimeError("GitHub metadata response exceeds 4 MB")
    return json.loads(raw.decode("utf-8"))
def discover_repository(source, getter=api_get):
    owner, name = github_repo(source["url"])
    repo = f"{owner}/{name}"
    meta = getter(f"https://api.github.com/repos/{repo}")
    branch = meta.get("default_branch")
    if not isinstance(branch, str) or not branch:
        raise ValueError("default branch is unavailable")
    commit = getter(f"https://api.github.com/repos/{repo}/commits/{urllib.parse.quote(branch, safe='')}")
    revision = commit.get("sha")
    if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("immutable source revision unavailable")
    tree = getter(f"https://api.github.com/repos/{repo}/git/trees/{revision}?recursive=1")
    if tree.get("truncated") is True:
        raise ValueError("recursive source tree is truncated")
    entries = tree.get("tree")
    if not isinstance(entries, list):
        raise ValueError("malformed source tree")
    found = []
    for entry in entries:
        path = entry.get("path")
        if not safe_path(path) or PurePosixPath(path).name.lower() != "skill.md":
            continue
        if entry.get("type") != "blob" or entry.get("mode") != "100644":
            continue
        size, blob = entry.get("size"), entry.get("sha")
        if not isinstance(size, int) or not 0 <= size <= MAX_FILE_BYTES:
            continue
        if not isinstance(blob, str) or not re.fullmatch(r"[0-9a-f]{40}", blob):
            continue
        found.append({
            "source_repository": repo.lower(),
            "source_revision": revision,
            "source_path": path,
            "file_size_bytes": size,
            "git_blob_sha": blob,
            "exact_content_dedup_key": blob,
            "normalized_path_dedup_key": hashlib.sha256(f"{repo.lower()}:{normalized_path(path)}".encode()).hexdigest(),
            "review_status": "unreviewed_candidate",
            "content_fetched": False,
            "code_executed": False
        })
    found.sort(key=lambda x: (x["source_repository"], x["source_path"].lower()))
    return found[:MAX_CANDIDATES], revision
def build_report(source_doc, getter=api_get):
    report = {"report_version":"1.0","generated_at_utc":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
      "discovery_mode":"metadata_only","candidate_content_fetched":False,"candidate_code_executed":False,
      "automatic_approval":False,"sources":[],"candidates":[],"errors":[]}
    seen = set()
    for source in source_doc.get("sources", []):
        if not isinstance(source, dict) or not isinstance(source.get("url"), str):
            report["errors"].append("Malformed source entry"); continue
        try:
            owner, name = github_repo(source["url"]); key = f"{owner.lower()}/{name.lower()}"
            if key in seen: continue
            seen.add(key)
            candidates, revision = discover_repository(source, getter)
            report["sources"].append({"repository":key,"revision":revision,"candidate_count":len(candidates),"result":"scanned"})
            report["candidates"].extend(candidates)
        except (ValueError, RuntimeError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            report["errors"].append({"source":str(source.get("id","unknown")),"reason":str(exc)[:200]})
    exact, paths = {}, {}
    for item in report["candidates"]:
        exact.setdefault(item["exact_content_dedup_key"], []).append(item)
        paths.setdefault(item["normalized_path_dedup_key"], []).append(item)
    report["deduplication"] = {"exact_blob_groups":sum(len(v)>1 for v in exact.values()),"normalized_path_groups":sum(len(v)>1 for v in paths.values())}
    report["summary"] = {"sources_scanned":len(report["sources"]),"candidates_found":len(report["candidates"]),"source_errors":len(report["errors"]),"approval_count":0}
    return report
def markdown(report):
    rows = ["# Public skill discovery report","",f"- Generated UTC: {report['generated_at_utc']}","- Mode: metadata only",
      f"- Sources scanned: {report['summary']['sources_scanned']}",f"- Candidates found: {report['summary']['candidates_found']}",
      f"- Source errors: {report['summary']['source_errors']}","- Automatically approved: 0","- Candidate contents fetched: no","- Candidate code executed: no","",
      "| Repository | Path | Revision | Size | Status |","|---|---|---|---:|---|"]
    for x in report["candidates"]:
        rows.append(f"| {x['source_repository']} | {x['source_path']} | {x['source_revision'][:12]} | {x['file_size_bytes']} | unreviewed |")
    if not report["candidates"]: rows.append("| — | — | — | — | none found |")
    for err in report["errors"]: rows.append(f"- Source error ({err['source']}): {err['reason']}")
    rows.extend(["","> Discovery is not approval. Review provenance, license, content, security, duplicates, and compatibility before catalog admission.",""])
    return "\n".join(rows)
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources",default=str(SOURCES)); parser.add_argument("--json-out",default="discovery-report.json"); parser.add_argument("--markdown-out",default="discovery-report.md")
    args=parser.parse_args()
    try:
        with open(args.sources,encoding="utf-8") as f: sources=json.load(f)
        report=build_report(sources)
        with open(args.json_out,"w",encoding="utf-8") as f: json.dump(report,f,indent=2,ensure_ascii=False); f.write("\n")
        with open(args.markdown_out,"w",encoding="utf-8") as f: f.write(markdown(report))
        print(f"Discovery: {report['summary']['sources_scanned']} sources, {report['summary']['candidates_found']} candidates, {report['summary']['source_errors']} errors; metadata only.")
        return 0 if report["summary"]["sources_scanned"] else 1
    except (OSError,json.JSONDecodeError,ValueError) as exc:
        print(f"Discovery failed: {exc}",file=sys.stderr); return 1
if __name__ == "__main__": raise SystemExit(main())
