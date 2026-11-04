"""Collect pinned public indicator source snapshots without importing vendor code."""
from __future__ import annotations

import concurrent.futures
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parent
REPOSITORIES = [
    "TA-Lib/ta-lib", "xgboosted/pandas-ta-classic",
    "TulipCharts/tulipindicators", "DaveSkender/Stock.Indicators",
    "peerchemist/finta", "bukosabino/ta", "joshuaulrich/TTR",
    "mpquant/MyTT", "everget/tradingview-pinescript-indicators",
    "anandanand84/technicalindicators", "joshyattridge/smart-money-concepts",
    "waditu/czsc",
    "QuantConnect/Lean",
]


def get(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "ForexSAI-indicator-source-research"})
    with urllib.request.urlopen(request, timeout=90) as response:
        return response.read(100_000_000)


def keep(repo: str, path: str) -> bool:
    p = PurePosixPath(path)
    name = p.name.lower()
    if name.startswith(("license", "copying", "notice", "authors")) or path in ("README.md", "readme.md"):
        return True
    if repo == "TA-Lib/ta-lib":
        return path.startswith(("src/ta_func/", "include/")) and p.suffix in (".c", ".h") or path == "ta_func_api.xml"
    if repo == "xgboosted/pandas-ta-classic":
        return path.startswith("pandas_ta_classic/") and p.suffix == ".py"
    if repo == "TulipCharts/tulipindicators":
        return path.startswith("indicators/") and p.suffix == ".c" or path in ("indicators.h", "indicators.c")
    if repo == "DaveSkender/Stock.Indicators":
        return path.startswith("src/") and p.suffix in (".cs", ".csproj")
    if repo == "peerchemist/finta":
        return path.startswith("finta/") and p.suffix == ".py"
    if repo == "bukosabino/ta":
        return path.startswith("ta/") and p.suffix == ".py"
    if repo == "joshuaulrich/TTR":
        return path.startswith(("R/", "src/", "man/")) and p.suffix in (".R", ".c", ".h", ".Rd")
    if repo == "mpquant/MyTT":
        return p.suffix == ".py"
    if repo == "everget/tradingview-pinescript-indicators":
        return p.suffix in (".pine", ".pinescript")
    if repo == "anandanand84/technicalindicators":
        return path.startswith("src/") and p.suffix == ".ts"
    if repo == "joshyattridge/smart-money-concepts":
        return path.startswith("smartmoneyconcepts/") and p.suffix == ".py"
    if repo == "waditu/czsc":
        return path.startswith(("czsc/signals/", "czsc/utils/ta", "czsc/objects", "crates/")) and p.suffix in (".py", ".rs")
    return False


def collect(repo: str) -> dict:
    result = {"repository": repo}
    try:
        metadata = json.loads(get(f"https://api.github.com/repos/{repo}"))
        branch = metadata["default_branch"]
        commit = json.loads(get(f"https://api.github.com/repos/{repo}/commits/{branch}"))
        sha = commit["sha"]
        result.update(default_branch=branch, commit=sha,
                      commit_date=commit["commit"]["committer"]["date"],
                      license_api=(metadata.get("license") or {}).get("spdx_id", "UNSPECIFIED"),
                      source_url=f"https://github.com/{repo}/tree/{sha}")
        if repo == "QuantConnect/Lean":
            entries = []
            for folder in ("Indicators", "Indicators/CandlestickPatterns"):
                listing = json.loads(get(f"https://api.github.com/repos/{repo}/contents/{folder}?ref={sha}"))
                entries.extend(x["path"] for x in listing if x["type"] == "file" and x["name"].endswith(".cs"))
            entries.append("LICENSE")
            dest = ROOT / "vendor" / repo.replace("/", "__")
            def fetch_file(path: str) -> dict:
                data = get(f"https://raw.githubusercontent.com/{repo}/{sha}/{path}")
                target = dest / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
                return {"path": path, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
                files = list(pool.map(fetch_file, entries))
            result.update(files=files, file_count=len(files), license_files=["LICENSE"],
                          snapshot_scope="Indicators/*.cs and CandlestickPatterns/*.cs; not the whole LEAN engine")
            return result
        content = get(f"https://codeload.github.com/{repo}/tar.gz/{sha}")
        result["archive_sha256"] = hashlib.sha256(content).hexdigest()
        dest = ROOT / "vendor" / repo.replace("/", "__")
        files = []
        with tarfile.open(fileobj=io.BytesIO(content), mode="r:gz") as archive:
            for member in archive.getmembers():
                if not member.isfile() or member.size > 3_000_000:
                    continue
                relative = PurePosixPath(*PurePosixPath(member.name).parts[1:])
                if relative.is_absolute() or ".." in relative.parts or not keep(repo, str(relative)):
                    continue
                data = archive.extractfile(member).read()
                target = dest / str(relative)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
                files.append({"path": str(relative), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        result["files"] = files
        result["file_count"] = len(files)
        result["license_files"] = [x["path"] for x in files if PurePosixPath(x["path"]).name.lower().startswith(("license", "copying", "notice"))]
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def main() -> None:
    import sys
    selected = sys.argv[1:] or REPOSITORIES
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(collect, selected))
    existing = ROOT / "SOURCE_MANIFEST.json"
    if existing.exists() and sys.argv[1:]:
        results = [x for x in json.loads(existing.read_text()) if x["repository"] not in selected] + results
    (ROOT / "SOURCE_MANIFEST.json").write_text(json.dumps(results, ensure_ascii=False, indent=2))
    for result in results:
        print(result["repository"], result.get("commit", "")[:12], result.get("license_api"), result.get("file_count"), result.get("error", ""), flush=True)


if __name__ == "__main__":
    main()
