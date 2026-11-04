"""data.binance.vision zip indirici (SHA256 .CHECKSUM doğrulamalı, paralel).

Kullanım: python -I 01_download.py <listing_json> <raw_dir>
00_list_s3.py'nin ürettiği listeden aşağıdaki DATASETS tanımına göre seçilen
zip'leri <raw_dir>/<ad>/ altına indirir. Zip içeriği ÇALIŞTIRILMAZ.
Sonuç: <raw_dir>/<ad>/download_log.tsv (dosya, durum).
"""
from __future__ import annotations
import hashlib, json, re, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BASE = "https://data.binance.vision/"
M0, M1 = "2021-06", "2026-09"          # aylık dosya aralığı
D0, D1 = "2026-10-01", "2026-10-20"    # Ekim günlük
DATASETS = {
    # ad: [(prefix, from, to)]
    "um_klines": [("data/futures/um/monthly/klines/BTCUSDT/1m/", M0, M1), ("data/futures/um/daily/klines/BTCUSDT/1m/", D0, D1)],
    "um_premium": [("data/futures/um/monthly/premiumIndexKlines/BTCUSDT/1m/", M0, M1), ("data/futures/um/daily/premiumIndexKlines/BTCUSDT/1m/", D0, D1)],
    "um_mark": [("data/futures/um/monthly/markPriceKlines/BTCUSDT/1m/", M0, M1), ("data/futures/um/daily/markPriceKlines/BTCUSDT/1m/", D0, D1)],
    "um_index": [("data/futures/um/monthly/indexPriceKlines/BTCUSDT/1m/", M0, M1), ("data/futures/um/daily/indexPriceKlines/BTCUSDT/1m/", D0, D1)],
    "um_funding": [("data/futures/um/monthly/fundingRate/BTCUSDT/", M0, M1)],
    "um_metrics": [("data/futures/um/daily/metrics/BTCUSDT/", "2021-06-01", D1)],
    "um_bookdepth": [("data/futures/um/daily/bookDepth/BTCUSDT/", "2023-01-01", D1)],
    "cm_liq": [("data/futures/cm/daily/liquidationSnapshot/BTCUSD_PERP/", "2000-01-01", D1)],
}


def fetch(url: str, retries: int = 5) -> bytes:
    for i in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            if i == retries - 1:
                raise
            time.sleep(2 * (i + 1))
    raise RuntimeError


def get(key: str, dest: Path) -> str:
    try:
        ck = fetch(BASE + key + ".CHECKSUM").decode().split()[0].strip()
        if dest.exists() and hashlib.sha256(dest.read_bytes()).hexdigest() == ck:
            return "cached-ok"
        data = fetch(BASE + key)
        h = hashlib.sha256(data).hexdigest()
        if h != ck:
            return f"CHECKSUM-MISMATCH {h} != {ck}"
        dest.write_bytes(data)
        return "ok"
    except Exception as e:  # noqa: BLE001
        return f"ERROR {e}"


def stamp(key: str) -> str:
    m = re.search(r"(\d{4}-\d{2}(?:-\d{2})?)\.zip$", key)
    return m.group(1) if m else ""


def main() -> None:
    listing = json.load(open(sys.argv[1]))
    raw = Path(sys.argv[2])
    only = sys.argv[3:] or list(DATASETS)
    for name in only:
        out = raw / name
        out.mkdir(parents=True, exist_ok=True)
        jobs = []
        for prefix, a, b in DATASETS[name]:
            for it in listing[prefix]:
                s = stamp(it["key"])
                if a <= s[: len(a)] and s[: len(b)] <= b:
                    jobs.append(it["key"])
        with ThreadPoolExecutor(8) as ex:
            res = list(ex.map(lambda k: (k, get(k, out / k.rsplit("/", 1)[-1])), jobs))
        bad = [r for r in res if r[1] not in ("ok", "cached-ok")]
        (out / "download_log.tsv").write_text("".join(f"{k.rsplit('/',1)[-1]}\t{s}\n" for k, s in res))
        print(f"{name}: {len(res)} dosya, sorunlu {len(bad)} {bad[:5]}", flush=True)


if __name__ == "__main__":
    main()
