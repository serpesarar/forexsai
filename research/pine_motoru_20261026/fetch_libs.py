"""Eksik kütüphaneleri indir: scriptlerin import ettiği ama tarama listesinde olmayan kütüphaneler.

Yol: `pubscripts-suggest-json/?search=<ad>` → kind=library sonucunun scriptIdPart'ı → pine-facade kaynağı.
Yazar adı değişmiş olabilir (ör. import TFlab/…, yayıncı TradingFinder): önce yazar+ad, yoksa yalnız ad eşleşmesi.
Kütüphanelerin kendi importları da (geçişli) çözülür.
Çıktı: data/src/libs_extra.jsonl.gz + data/lib_index_v2.json (eski indeks + ekler; ad→kaynak).
Kullanım: python fetch_libs.py
"""
from __future__ import annotations

import gzip
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pine_src  # noqa: E402

SEARCH = "https://www.tradingview.com/pubscripts-suggest-json/?search={}"
GET = "https://pine-facade.tradingview.com/pine-facade/get/{}/last"
OUT = HERE / "data/src/libs_extra.jsonl.gz"
IDX_OLD = HERE / "data/lib_index.json"
IDX_NEW = HERE / "data/lib_index_v2.json"
IMPORT_RE = re.compile(r"^\s*import\s+([\w\-]+)/([\w\-]+)/(\d+)", re.M)
TITLE_RE = re.compile(r'^\s*library\(\s*(?:title\s*=\s*)?["\']([^"\']+)["\']', re.M)
PAUSE_S = 0.6
UA = {"User-Agent": "Mozilla/5.0"}


def _get_json(url: str):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


def find(user: str, name: str):
    """→ (scriptIdPart, yayıncı) ya da None."""
    res = _get_json(SEARCH.format(urllib.parse.quote(name))).get("results") or []
    libs = [x for x in res if (x.get("extra") or {}).get("kind") == "library"
            and (x.get("title") or "").lower() == name.lower()]
    if not libs:
        return None
    best = next((x for x in libs if (x.get("author") or {}).get("username", "").lower() == user.lower()), libs[0])
    return best["scriptIdPart"], (best.get("author") or {}).get("username", "")


def wanted(sources, have: set) -> dict:
    """İmport edilen ama indekste olmayan kütüphaneler: 'yazar/ad' (küçük harf) → (yazar, ad) asıl yazımı."""
    out = {}
    for src in sources:
        for u, n, _ in IMPORT_RE.findall(src):
            k = f"{u}/{n}".lower()
            if k not in have and n.lower() not in have:
                out.setdefault(k, (u, n))
    return out


def main():
    idx = json.loads(IDX_OLD.read_text())
    names = {k.split("/", 1)[1] for k in idx}
    extra = []
    if OUT.exists():
        with gzip.open(OUT, "rt") as f:
            extra = [json.loads(line) for line in f]
    for r in extra:
        idx[r["key"]] = r["source"]
        names.add(r["key"].split("/", 1)[1])
    tried = {r["want"] for r in extra}
    srcs = [r["source"] for r in pine_src.iter_sources(True) if r.get("type") != "library"]
    rounds = 0
    while True:
        need = {k: v for k, v in wanted(srcs + list(idx.values()), set(idx) | names).items() if k not in tried}
        if not need:
            break
        rounds += 1
        print(f"tur {rounds}: {len(need)} kütüphane aranıyor", flush=True)
        for k, (u, n) in need.items():
            tried.add(k)
            try:
                hit = find(u, n)
                time.sleep(PAUSE_S)
                if not hit:
                    continue
                sid, pub = hit
                src = _get_json(GET.format(urllib.parse.quote(sid, safe=""))).get("source") or ""
                time.sleep(PAUSE_S)
            except Exception as e:                       # ağ hatası: kaydet, devam
                print("  hata", k, type(e).__name__, str(e)[:80], flush=True)
                continue
            m = TITLE_RE.search(src)
            if not m:
                continue
            key = f"{pub.lower()}/{m.group(1).lower()}"
            rec = dict(want=k, key=key, sid=sid, author=pub, type="library", source=src)
            extra.append(rec)
            idx[key] = src
            names.add(m.group(1).lower())
            with gzip.open(OUT, "at") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"  toplam ek kütüphane {len(extra)}", flush=True)
    IDX_NEW.write_text(json.dumps(idx))
    left = wanted(srcs, set(idx) | names)
    print(f"bitti: {len(extra)} ek kütüphane; çözülemeyen {len(left)}", flush=True)


if __name__ == "__main__":
    main()
