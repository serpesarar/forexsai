"""Kutuda çalışır — SALT OKUMA: NAS100 tik geçmişini broker sunucusundan çeker (copy_ticks_range).

'Grafikteki azami bar' sınırı tiklere uygulanmaz; tikten kurulan M1, 2026.hcc'nin terminal dökümü olmayan dönemini (2026-01 →
05-06) dakika dakika sınamak için kullanılır. Terminal ayarına, emre dokunmaz.
  python calistir/arac_nas100_tik.py dene                       → örnek günlerde tik sayısı
  python calistir/arac_nas100_tik.py yukle 2026-01-01 2026-05-07 → gün gün çeker, tfy_tik_<YYYYMMDD>.csv.gz yükler
Zaman: tik `time_msc` UTC epoch ms (MT5 tik zamanı sunucu duvar saatidir; dönüşüm panel tarafında yapılır).
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


def day_ticks(d: dt.date):
    a = dt.datetime(d.year, d.month, d.day, tzinfo=dt.timezone.utc)
    r = mt5.copy_ticks_range(SYMBOL, a, a + dt.timedelta(days=1), mt5.COPY_TICKS_ALL)
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
        for s in ("2016-06-01", "2017-03-01", "2019-03-05", "2025-03-04", "2026-02-03", "2026-08-04"):
            r = day_ticks(dt.date.fromisoformat(s))
            print(s, len(r), (int(r[0]["time"]), int(r[-1]["time"])) if len(r) else "-", mt5.last_error(), flush=True)
    else:
        import requests
        url, key = cfg.SUPABASE_URL.rstrip("/"), cfg.SUPABASE_SERVICE_KEY
        h = {"Authorization": f"Bearer {key}", "apikey": key, "x-upsert": "true", "Content-Type": "application/gzip"}
        d, end = dt.date.fromisoformat(sys.argv[2]), dt.date.fromisoformat(sys.argv[3])
        while d < end:
            r = day_ticks(d)
            if len(r):
                buf = io.BytesIO()
                with gzip.GzipFile(fileobj=buf, mode="wb") as g:
                    g.write(b"msc,bid,ask,last,vol,flags\n")
                    for x in r:
                        g.write(f"{int(x['time_msc'])},{x['bid']},{x['ask']},{x['last']},{int(x['volume'])},{int(x['flags'])}\n".encode())
                rr = requests.post(f"{url}/storage/v1/object/{BUCKET}/tfy_tik_{d:%Y%m%d}.csv.gz", headers=h, data=buf.getvalue(), timeout=600)
                print(d, len(r), rr.status_code, flush=True)
            d += dt.timedelta(days=1)
    mt5.shutdown()


if __name__ == "__main__":
    main()
