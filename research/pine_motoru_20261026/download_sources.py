"""TradingView topluluk scriptlerinin Pine kaynak kodunu indir (kaynağı açık olanlar).

Girdi : research/indicator_atlas_20261025/topluluk_taramasi/data/ids_{tags,search}.jsonl (script_id_part'lı liste)
Uç    : https://pine-facade.tradingview.com/pine-facade/get/<PUB;id>/last  → {"source": ...}
Çıktı : data/src/sources.jsonl.gz — her satır {id, sid, name, author, type, boosts, created_at, version, ok, source}
        Kaynağı gelmeyen (korumalı/davetli/silinmiş) satırlar ok=False ile yazılır. Devam ettirilebilir.
Kullanım: python download_sources.py [limit]
"""
from __future__ import annotations

import gzip
import json
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIST_DIR = HERE.parents[0] / "indicator_atlas_20261025/topluluk_taramasi/data"
OUT = HERE / "data/src/sources.jsonl.gz"
URL = "https://pine-facade.tradingview.com/pine-facade/get/{}/last"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"
WORKERS = 4
DELAY_S = 0.3


def scripts() -> dict:
    """Benzersiz script_id_part → liste metadata'sı (en yüksek boost'lu satır)."""
    out: dict = {}
    for name in ("ids_tags.jsonl", "ids_search.jsonl"):
        p = LIST_DIR / name
        if not p.exists():
            continue
        for line in p.open():
            r = json.loads(line)
            sid = r.get("script_id_part")
            if not sid:
                continue
            cur = out.get(sid)
            if cur is None or (r.get("boosts") or 0) > (cur.get("boosts") or 0):
                out[sid] = r
    return out


def done_ids() -> set:
    if not OUT.exists():
        return set()
    with gzip.open(OUT, "rt") as f:
        return {json.loads(line)["sid"] for line in f}


def fetch(sid: str) -> tuple[bool, str]:
    url = URL.format(urllib.parse.quote(sid, safe=""))
    for i in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                j = json.loads(r.read().decode("utf-8", "ignore"))
            src = j.get("source") or ""
            return bool(src), src
        except Exception as e:
            code = getattr(e, "code", None)
            if code in (403, 404):
                return False, ""
            time.sleep(3 * (i + 1) if code == 429 else 1 + i)
    return False, ""


def main(limit: int | None = None) -> None:
    meta = scripts()
    done = done_ids()
    todo = [s for s in sorted(meta, key=lambda s: -(meta[s].get("boosts") or 0)) if s not in done]
    if limit:
        todo = todo[:limit]
    print(f"benzersiz {len(meta)}, indirilecek {len(todo)}", flush=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)

    def one(sid):
        time.sleep(DELAY_S)
        return sid, fetch(sid)

    n_ok = 0
    with gzip.open(OUT, "at") as f, ThreadPoolExecutor(WORKERS) as ex:
        for k, (sid, (ok, src)) in enumerate(ex.map(one, todo), 1):
            m = meta[sid]
            f.write(json.dumps(dict(id=m.get("id"), sid=sid, name=m.get("name"), author=m.get("author"),
                                    type=m.get("type"), boosts=m.get("boosts"), created_at=m.get("created_at"),
                                    version=m.get("version"), ok=ok, source=src), ensure_ascii=False) + "\n")
            n_ok += ok
            if k % 500 == 0:
                f.flush()
                print(f"{k}/{len(todo)} indirildi, kaynaklı {n_ok}", flush=True)
    print(f"bitti: {len(todo)} istek, kaynaklı {n_ok}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else None)
