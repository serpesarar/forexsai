"""Read bounded public TradingView topic pages; do not claim a complete library export."""
from __future__ import annotations

import concurrent.futures
import json
from pathlib import Path
import re
from urllib.parse import urljoin
import urllib.request

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
TOPICS = ["editors-picks", "kdj", "bbi", "blackcat", "ichimokuclouds", "ehlers",
          "kalmanfilter", "marketprofile", "orderflow", "volumeprofile",
          "smartmoneyconcepts", "harmonicpatterns", "gold", "crudeoil", "dax",
          "nasdaq100", "wavetrend", "wyckoff", "gann", "squeeze", "machinelearning",
          "fractal", "renko", "pointandfigure"]
EXPLICIT = ["WhBzgfDu", "CnB3fSph", "CLk71Qgy", "Iko0E2kL", "amRCTgFw",
            "nqQ1DT5a", "2KE8wTuF", "TpUW4muw", "U1SJ8ubc", "n8ss8BID",
            "t2PFNKEf", "QmGxhXJ7", "4EpIOEMu", "HG385dBY", "SldE4p9a", "X67OSwqc", "AqXxNS7j"]


def soup(url: str) -> BeautifulSoup:
    req = urllib.request.Request(url, headers={"User-Agent": "ForexSAI-public-indicator-research"})
    with urllib.request.urlopen(req, timeout=35) as response:
        return BeautifulSoup(response.read(12_000_000), "html.parser")


def listing(topic: str) -> dict:
    url = f"https://www.tradingview.com/scripts/{topic}/"
    try:
        page = soup(url)
        records = {}
        for anchor in page.select('a[href*="/script/"]'):
            match = re.search(r"/script/([A-Za-z0-9]+)(?:-[^/?#]*)?/?", anchor.get("href", ""))
            if not match:
                continue
            ident = match[1]
            label = anchor.get_text(" ", strip=True)
            # Engagement/comment links also point at /script/; do not use their
            # numeric counts as publication titles.
            if not any(ch.isalpha() for ch in label) or "#" in anchor.get("href", ""):
                continue
            row = records.setdefault(ident, {"script_id": ident, "url": urljoin(url, anchor["href"]).split("?")[0], "title": "", "topics": [topic], "description_excerpt": ""})
            if label and (not row["title"] or len(label) < len(row["title"])):
                row["title"] = label[:300]
            if len(label) > len(row["description_excerpt"]):
                row["description_excerpt"] = " ".join(label.split()[:85])
        return {"topic": topic, "url": url, "records": list(records.values())}
    except Exception as exc:
        return {"topic": topic, "url": url, "error": f"{type(exc).__name__}: {exc}", "records": []}


def detail(ident: str) -> dict:
    url = f"https://www.tradingview.com/script/{ident}/"
    try:
        page = soup(url)
        h = page.find("h1")
        meta = page.find("meta", property="og:description") or page.find("meta", attrs={"name": "description"})
        text = page.get_text(" ", strip=True)
        status = "open_source_badge_seen" if "Open-source script" in text else "protected_or_invite_badge_seen" if any(s in text for s in ("Protected script", "Invite-only script")) else "not_verified"
        return {"script_id": ident, "url": url, "title": h.get_text(" ", strip=True) if h else "", "code_access": status,
                "description_excerpt": " ".join((meta.get("content", "") if meta else "").split()[:85]),
                "source_code_downloaded": False}
    except Exception as exc:
        return {"script_id": ident, "url": url, "error": f"{type(exc).__name__}: {exc}", "source_code_downloaded": False}


def main() -> None:
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        topics = list(pool.map(listing, TOPICS))
    records = {}
    for topic in topics:
        for row in topic["records"]:
            if row["script_id"] in records:
                records[row["script_id"]]["topics"].extend(row["topics"])
            else:
                records[row["script_id"]] = row
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        details = list(pool.map(detail, EXPLICIT))
    for row in details:
        old = records.get(row["script_id"], {})
        if "error" not in row:
            row["topics"] = old.get("topics", [])
            records[row["script_id"]] = row
    out = {"date": "2026-10-25", "scope": "First public page per topic, no pagination; curated pages checked separately. Listing entries are discovery metadata, not source-code audits.",
           "topics": [{k: v for k, v in x.items() if k != "records"} | {"count": len(x["records"])} for x in topics],
           "curated_details": details, "records": list(records.values())}
    (ROOT / "TRADINGVIEW_DISCOVERY.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print("Topic counts", [(x["topic"], len(x["records"]), x.get("error", "")) for x in topics])
    print("Unique publications", len(records))
    print("Curated pages", [(x.get("title"), x.get("code_access"), x.get("error")) for x in details])


if __name__ == "__main__":
    main()
