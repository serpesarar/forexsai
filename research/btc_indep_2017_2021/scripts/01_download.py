"""data.binance.vision indirici (SHA256 .CHECKSUM doğrulamalı) — bağımsız dönem.

btc_5y_20261021/scripts/01_download_binance.py + btc_scalp_20261021/scripts/01_download.py mantığı (fetch/get aynen);
yalnız tarih aralıkları ve veri setleri değişti. Zip içeriği ÇALIŞTIRILMAZ.
Kullanım: python -I -B 01_download.py <raw_dir>
"""
from __future__ import annotations

import hashlib
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BASE = "https://data.binance.vision/"
SPOT = ("data/spot/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-{ym}.zip", "2017-08", "2021-05")
UM = {
    "um_klines": "data/futures/um/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-{ym}.zip",
    "um_premium": "data/futures/um/monthly/premiumIndexKlines/BTCUSDT/1m/BTCUSDT-1m-{ym}.zip",
    "um_mark": "data/futures/um/monthly/markPriceKlines/BTCUSDT/1m/BTCUSDT-1m-{ym}.zip",
    "um_index": "data/futures/um/monthly/indexPriceKlines/BTCUSDT/1m/BTCUSDT-1m-{ym}.zip",
    "um_funding": "data/futures/um/monthly/fundingRate/BTCUSDT/BTCUSDT-fundingRate-{ym}.zip",
}
UM_RANGE = ("2020-01", "2021-05")


def months(a: str, b: str):
    y, m = int(a[:4]), int(a[5:])
    y1, m1 = int(b[:4]), int(b[5:])
    while (y, m) <= (y1, m1):
        yield f"{y:04d}-{m:02d}"
        m += 1
        if m == 13:
            y, m = y + 1, 1


def fetch(url: str, retries: int = 5) -> bytes:
    for i in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            if i == retries - 1:
                raise
            print(f"  retry {url}: {e}", flush=True)
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


def run(name: str, keys: list[str], raw: Path) -> None:
    out = raw / name
    out.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(6) as ex:
        res = list(ex.map(lambda k: (k, get(k, out / k.rsplit("/", 1)[-1])), keys))
    bad = [r for r in res if r[1] not in ("ok", "cached-ok")]
    (out / "download_log.tsv").write_text("".join(f"{k.rsplit('/', 1)[-1]}\t{s}\n" for k, s in res))
    print(f"{name}: {len(res)} dosya, sorunlu {len(bad)} {bad[:5]}", flush=True)


def main() -> None:
    raw = Path(sys.argv[1])
    tpl, a, b = SPOT
    run("spot_klines", [tpl.format(ym=ym) for ym in months(a, b)], raw)
    for name, tpl in UM.items():
        run(name, [tpl.format(ym=ym) for ym in months(*UM_RANGE)], raw)


if __name__ == "__main__":
    main()
