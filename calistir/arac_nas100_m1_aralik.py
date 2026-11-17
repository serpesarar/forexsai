"""Kutuda çalışır — SALT OKUMA: NAS100 M1'i tarih aralığıyla, ay ay çeker (copy_rates_range).

Terminal ayarına dokunmaz. 'Grafikteki azami bar' (100.000) en son N barı sınırlıyor; diskte history/NAS100/*.hcc
yıl dosyaları 2017'ye kadar M1 tutuyor. Bu betik o geçmişin aralık sorgusuyla okunup okunamadığını dener.
  python calistir/arac_nas100_m1_aralik.py dene              → birkaç örnek ayın bar sayısı
  python calistir/arac_nas100_m1_aralik.py yukle 2017 2026    → ay ay çeker, tfy_m1_aralik_<YYYY>.csv.gz yükler
`t` = MT5 sunucu duvar saati (NY+7).
"""
from __future__ import annotations

import datetime as dt
import gzip
import io
import sys

sys.path.insert(0, "remote_agent")
import agent_config as cfg  # noqa: E402
import MetaTrader5 as mt5  # noqa: E402

SYMBOL, BUCKET = "NAS100", "research-xfer"


def month_range(y: int, m: int) -> tuple[dt.datetime, dt.datetime]:
    a = dt.datetime(y, m, 1, tzinfo=dt.timezone.utc)
    b = dt.datetime(y + (m == 12), m % 12 + 1, 1, tzinfo=dt.timezone.utc)
    return a, b


def fetch(y: int, m: int):
    a, b = month_range(y, m)
    r = mt5.copy_rates_range(SYMBOL, mt5.TIMEFRAME_M1, a, b)
    return [] if r is None else r


def main() -> None:
    if not mt5.initialize(getattr(cfg, "MT5_TERMINAL_PATH", None)):
        raise SystemExit(f"MT5 başlatılamadı: {mt5.last_error()}")
    acc = mt5.account_info()
    if acc is None or "Pepperstone" not in (acc.server or ""):
        raise SystemExit("beklenmeyen hesap")
    mt5.symbol_select(SYMBOL, True)
    mode = sys.argv[1] if len(sys.argv) > 1 else "dene"
    if mode == "dene":
        for y, m in ((2017, 3), (2019, 3), (2022, 6), (2025, 3), (2026, 4)):
            r = fetch(y, m)
            print(y, m, len(r), (str(dt.datetime.utcfromtimestamp(int(r[0]["time"]))) if len(r) else "-"), mt5.last_error())
    else:
        import requests
        y0, y1 = int(sys.argv[2]), int(sys.argv[3])
        url, key = cfg.SUPABASE_URL.rstrip("/"), cfg.SUPABASE_SERVICE_KEY
        h = {"Authorization": f"Bearer {key}", "apikey": key, "x-upsert": "true", "Content-Type": "application/gzip"}
        for y in range(y0, y1 + 1):
            buf = io.BytesIO()
            n = 0
            with gzip.GzipFile(fileobj=buf, mode="wb") as g:
                g.write(b"t,o,h,l,c,v,sp\n")
                for m in range(1, 13):
                    for x in fetch(y, m):
                        g.write(f"{int(x['time'])},{x['open']},{x['high']},{x['low']},{x['close']},{x['tick_volume']},{x['spread']}\n".encode())
                        n += 1
            r = requests.post(f"{url}/storage/v1/object/{BUCKET}/tfy_m1_aralik_{y}.csv.gz", headers=h, data=buf.getvalue(), timeout=600)
            print(y, n, r.status_code, flush=True)
    mt5.shutdown()


if __name__ == "__main__":
    main()
