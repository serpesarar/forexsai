"""t.me/s açık önizleme sayfalarından kanal arşivi: ham metin + yayın damgası (jsonl, kaldığı yerden sürer).

Saygılı hız: istekler arası ≥2 sn; 429'da Retry-After kadar bekler; oturum/giriş kullanmaz.
"""
from __future__ import annotations
import html, json, re, sys, time, urllib.error, urllib.request
from pathlib import Path

HERE = Path(__file__).parent
UA = "ForexSAI-research"
POST = re.compile(r'data-post="[^"/]+/(\d+)"(.*?)(?=data-post="|\Z)', re.S)
TEXT = re.compile(r'tgme_widget_message_text[^>]*>(.*?)</div>', re.S)
WHEN = re.compile(r'<time datetime="([^"]+)"')
TAG = re.compile(r"<[^>]+>")
SLEEP_S = 2.0


def fetch(chan: str, before: int | None) -> str:
    url = f"https://t.me/s/{chan}" + (f"?before={before}" if before else "")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf8", "replace")
        except urllib.error.HTTPError as e:
            wait = int(e.headers.get("Retry-After") or 60) if e.code == 429 else 20 * (attempt + 1)
            print(f"{chan} HTTP {e.code}, {wait}s", flush=True)
            time.sleep(wait)
        except Exception as e:  # ağ hatası: geri çekil, sonra yeniden dene
            print(f"{chan} {type(e).__name__}, {20 * (attempt + 1)}s", flush=True)
            time.sleep(20 * (attempt + 1))
    raise RuntimeError(f"{chan} before={before} alınamadı")


def parse(page: str) -> list[dict]:
    out = []
    for m in POST.finditer(page):
        pid, body = int(m.group(1)), m.group(2)
        when, txt = WHEN.search(body), TEXT.search(body)
        if when and txt:
            text = html.unescape(TAG.sub(" ", txt.group(1).replace("<br/>", " "))).strip()
            out.append({"id": pid, "ts": when.group(1), "text": re.sub(r"\s+", " ", text)})
    return out


def main(chan: str, stop_iso: str, start: int | None = None, tag: str = "") -> None:
    path = HERE / "data" / f"tg_{chan}{tag}.jsonl"
    seen_min = start
    if path.exists():
        for line in path.open(encoding="utf8"):
            pid = json.loads(line)["id"]
            seen_min = pid if seen_min is None else min(seen_min, pid)
    before, empties = seen_min, 0
    with path.open("a", encoding="utf8") as f:
        while True:
            rows = parse(fetch(chan, before))
            time.sleep(SLEEP_S)
            if not rows:   # silinmiş/medya aralığı: id'yi atlayarak ilerle
                empties += 1
                if before is None or before <= 1 or empties > 200:
                    break
                before = max(1, before - 20)
                continue
            empties = 0
            for r in sorted(rows, key=lambda x: -x["id"]):
                if before is None or r["id"] < before:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
            f.flush()
            before = min(r["id"] for r in rows)
            if rows[0]["ts"][:10] <= stop_iso or before <= 1:
                break
    print(f"{chan} bitti before={before}", flush=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else None, sys.argv[4] if len(sys.argv) > 4 else "")
