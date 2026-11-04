"""Statically index pinned source; never import or execute vendor indicator code."""
from __future__ import annotations

import ast
from collections import Counter
import hashlib
import html
import json
from pathlib import Path
import re
from urllib.parse import quote
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
MANIFEST = json.loads((ROOT / "SOURCE_MANIFEST.json").read_text())
META = {r["repository"]: r for r in MANIFEST if "error" not in r}
ROWS: list[dict] = []


def add(repo: str, path: Path, name: str, family: str, description: str = "", line: int = 1,
        signature: str = "", kind: str = "indicator_implementation", body: str = "") -> None:
    base = ROOT / "vendor" / repo.replace("/", "__")
    rel = str(path.relative_to(base))
    triggers = []
    for label, pattern in [
        ("negative_shift_or_future_alignment", r"\.shift\(\s*-"),
        ("centered_rolling_window", r"center\s*=\s*True"),
        ("lookahead_setting_requires_review", r"lookahead\s*="),
        ("pivot_or_fractal_confirmation", r"(?i)pivot|fractal|swing_highs_lows"),
        ("explicit_unimplemented_marker", r"NotImplementedError"),
    ]:
        if re.search(pattern, body):
            triggers.append(label)
    stub = bool(re.search(r"raise\s+NotImplementedError", body))
    if "mpquant/MyTT" == repo:
        license_text = "README says GPL; version and full license text not supplied"
    elif "waditu/czsc" == repo:
        license_text = "Apache-2.0 notice in root LICENSE; API says NOASSERTION; Rust subcrate terms require review"
    else:
        license_text = META[repo]["license_api"]
    ROWS.append({"repository": repo, "commit": META[repo]["commit"], "name": name,
                 "family": family, "record_kind": kind, "language": path.suffix.lstrip("."),
                 "description_from_source": description[:2400], "signature": signature,
                 "local_path": str(path.relative_to(ROOT)), "line": line,
                 "source_url": f"https://github.com/{repo}/blob/{META[repo]['commit']}/{quote(rel)}#L{line}",
                 "license": license_text, "status": "unimplemented_marker" if stub else "source_indexed_not_runtime_validated",
                 "temporal_review_triggers": triggers})


def python_functions(repo: str, path: Path, mode: str, family: str = "") -> None:
    text = path.read_text(errors="replace")
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return
    nodes = []
    if mode in ("module", "mytt", "chan"):
        nodes = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    elif mode in ("finta", "smc"):
        for cls in tree.body:
            if isinstance(cls, ast.ClassDef) and cls.name in ("TA", "smc"):
                nodes.extend(n for n in cls.body if isinstance(n, ast.FunctionDef))
    elif mode == "ta":
        nodes = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name.endswith("Indicator")]
    for node in nodes:
        if node.name.startswith("_"):
            continue
        if mode == "module" and node.name != path.stem:
            continue
        body = ast.get_source_segment(text, node) or ""
        doc = ast.get_docstring(node) or ""
        if not doc:
            comments = [x.strip().lstrip("# ") for x in body.splitlines()[:4] if "#" in x]
            doc = " ".join(comments)
        kind = "indicator_implementation"
        if mode == "mytt" and node.lineno < 144 and path.name == "MyTT.py":
            kind = "formula_helper"
        if mode == "chan":
            kind = "chan_signal_or_structural_component"
        if mode == "smc":
            kind = "market_structure_component"
        signature = f"{node.name}({ast.unparse(node.args)})" if isinstance(node, ast.FunctionDef) else node.name
        add(repo, path, node.name, family or path.parent.name, doc, node.lineno, signature, kind, body)


def build() -> None:
    repo = "TA-Lib/ta-lib"
    base = ROOT / "vendor" / repo.replace("/", "__")
    for node in ET.parse(base / "ta_func_api.xml").getroot().findall("FinancialFunction"):
        name = node.findtext("Abbreviation")
        path = base / "src/ta_func" / f"ta_{name}.c"
        if not path.exists():
            continue
        inputs = [n.findtext("Name", "") for n in node.findall("RequiredInputArguments/RequiredInputArgument")]
        opts = {n.findtext("Name", ""): n.findtext("DefaultValue") for n in node.findall("OptionalInputArguments/OptionalInputArgument")}
        kind = "math_or_statistical_function" if node.findtext("GroupId") in ("Math Operators", "Math Transform", "Statistic Functions", "Price Transform") else "indicator_implementation"
        add(repo, path, name, node.findtext("GroupId", ""), node.findtext("ShortDescription", ""), signature=json.dumps({"inputs": inputs, "defaults": opts}), kind=kind)

    repo = "xgboosted/pandas-ta-classic"
    base = ROOT / "vendor" / repo.replace("/", "__") / "pandas_ta_classic"
    for path in sorted(base.glob("*/*.py")):
        if path.parent.name not in ("utils",) and not path.name.startswith("_"):
            python_functions(repo, path, "module")
    for repo, mode, pattern in [
        ("peerchemist/finta", "finta", "finta/finta.py"),
        ("bukosabino/ta", "ta", "ta/*.py"),
        ("mpquant/MyTT", "mytt", "MyTT.py"),
        ("mpquant/MyTT", "mytt", "MyTT_plus.py"),
        ("joshyattridge/smart-money-concepts", "smc", "smartmoneyconcepts/smc.py"),
        ("waditu/czsc", "chan", "czsc/signals/*.py"),
    ]:
        for path in sorted((ROOT / "vendor" / repo.replace("/", "__")).glob(pattern)):
            python_functions(repo, path, mode)

    repo = "everget/tradingview-pinescript-indicators"
    for path in sorted((ROOT / "vendor" / repo.replace("/", "__")).rglob("*.pine")):
        text = path.read_text()
        title = re.search(r'(?:study|indicator|strategy)\(\s*(?:title\s*=\s*)?[\'"]([^\'"]+)', text)
        family = path.parent.name
        kind = "utility_or_visual_script" if family in ("research", "utils", "highlighters") else "indicator_implementation"
        add(repo, path, title[1] if title else path.stem, family, "", kind=kind, body=text)

    repo = "TulipCharts/tulipindicators"
    base = ROOT / "vendor" / repo.replace("/", "__")
    for match in re.finditer(r'\{"([^"\n]+)",\s*"([^"\n]+)",\s*ti_\w+_start,[^{}]*?TI_TYPE_(\w+)', (base / "indicators.c").read_text()):
        path = base / "indicators" / (match[1] + ".c")
        if path.exists():
            kind = "math_or_statistical_function" if match[3] in ("SIMPLE", "MATH") else "indicator_implementation"
            add(repo, path, match[1], match[3], match[2], kind=kind)

    repo = "DaveSkender/Stock.Indicators"
    base = ROOT / "vendor" / repo.replace("/", "__")
    for folder in sorted((base / "src/Indicators").glob("*/*")):
        if not folder.is_dir():
            continue
        sources = sorted(folder.glob("*.Series.cs")) or sorted(folder.glob("*.cs"))
        if sources:
            path = sources[0]
            add(repo, path, folder.name, "stock_indicator", "", body=path.read_text())

    repo = "joshuaulrich/TTR"
    for path in sorted((ROOT / "vendor" / repo.replace("/", "__") / "R").glob("*.R")):
        text = path.read_text(errors="replace")
        for match in re.finditer(r'^[\'"]?([A-Za-z][\w.]*)[\'"]?\s*(?:<-|=)\s*function\s*\(', text, re.M):
            add(repo, path, match[1], "R_TTR_function", "", line=text[:match.start()].count("\n") + 1,
                kind="indicator_or_helper_function")

    repo = "anandanand84/technicalindicators"
    for path in sorted((ROOT / "vendor" / repo.replace("/", "__") / "src").glob("*/*.ts")):
        text = path.read_text()
        classes = re.findall(r'export\s+class\s+(\w+)\s+extends\s+(?:Indicator|CandlestickFinder)\b', text)
        for name in classes:
            add(repo, path, name, path.parent.name, "", body=text)

    repo = "QuantConnect/Lean"
    base = ROOT / "vendor" / repo.replace("/", "__")
    for path in sorted((base / "Indicators").rglob("*.cs")):
        text = path.read_text()
        match = re.search(r'(?:public|abstract)\s+(?:class|sealed\s+class)\s+(\w+)', text)
        if not match or match[1] in ("IndicatorDataPoint", "IndicatorResult", "IndicatorBase", "WindowIndicator", "IndicatorExtensions", "Indicator", "BarIndicator", "TradeBarIndicator"):
            continue
        prefix = text[:match.start()]
        summaries = re.findall(r'<summary>(.*?)</summary>', prefix, re.S)
        desc = re.sub(r'\s+', ' ', re.sub(r'///\s*|<[^>]+>', ' ', summaries[-1])) if summaries else ""
        kind = "candlestick_pattern" if "CandlestickPatterns" in str(path) else "indicator_or_statistical_component"
        add(repo, path, match[1], path.parent.name, desc, line=text[:match.start()].count("\n")+1, kind=kind, body=text)

    # Rust Chan components are indexed as modules, not inflated into independent indicators.
    repo = "waditu/czsc"
    base = ROOT / "vendor" / repo.replace("/", "__")
    for path in sorted((base / "crates/czsc-signals/src").glob("*.rs")):
        add(repo, path, path.stem, "chan_rust_signal_module", kind="chan_signal_module")
    for i, row in enumerate(ROWS):
        row["id"] = f"SRC-{i+1:04}"
    (ROOT / "IMPLEMENTATIONS.json").write_text(json.dumps(ROWS, ensure_ascii=False, indent=2))

    counts = Counter(r["repository"] for r in ROWS)
    stats = {"records": len(ROWS), "repositories": len(META), "by_repository": dict(counts),
             "by_kind": dict(Counter(r["record_kind"] for r in ROWS)),
             "source_files": sum(r["file_count"] for r in META.values()),
             "pine_files": sum(r["language"] == "pine" for r in ROWS),
             "unimplemented_markers": [r["id"] + " " + r["repository"] + " " + r["name"] for r in ROWS if r["status"] == "unimplemented_marker"]}
    (ROOT / "COUNTS.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2))
    lines = ["# Source implementation index\n\n", "These are implementation records, not unique indicators. Formula helpers, statistical operations, patterns and signal components are explicitly typed. Vendor code was statically parsed, not executed or certified. Temporal flags are review triggers, not confirmed defects.\n\n"]
    for repo in META:
        lines.append(f"## {repo} — {counts[repo]} records\n\n| ID | Name | Type / family | Source code | Description / status |\n|---|---|---|---|---|\n")
        for row in ROWS:
            if row["repository"] != repo:
                continue
            description = re.sub(r'\s+', ' ', row['description_from_source'])[:230].replace('|', '/')
            flags = ', '.join(row['temporal_review_triggers'])
            lines.append(f"| {row['id']} | {row['name']} | {row['record_kind']} / {row['family']} | [local]({row['local_path']}#L{row['line']}) · [upstream]({row['source_url']}) | {description or 'See linked formula/source.'} {flags} |\n")
        lines.append("\n")
    (ROOT / "IMPLEMENTATIONS.md").write_text(''.join(lines))

    checks = []
    for repo, meta in META.items():
        base = ROOT / "vendor" / repo.replace("/", "__")
        for info in meta['files']:
            path = base / info['path']
            assert path.is_file(), path
            assert hashlib.sha256(path.read_bytes()).hexdigest() == info['sha256'], path
            checks.append(path)
    for row in ROWS:
        path = ROOT / row['local_path']
        assert path.exists() and row['line'] <= len(path.read_text(errors='replace').splitlines()), row['id']
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    print(f"Verified {len(checks)} source-file hashes and {len(ROWS)} local source references.")


if __name__ == "__main__":
    build()
