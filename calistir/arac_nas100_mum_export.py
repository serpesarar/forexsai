"""Kutuda çalışır — NAS100 mumlarını MT5'ten SALT OKUNUR çeker, özel 'research-xfer' deposuna yükler.

Emir göndermez, sembol/terminal ayarına dokunmaz (yalnız symbol_select). Panel tarafındaki tüketici:
research/ndx_tf_yapilandirma_20261117 (2/3/90/210 dk mum üretimi). Dosya adları `tfy_` önekli,
mevcut `NAS100_*.csv.gz` dosyalarının üzerine yazmaz.

Çalıştırma (panelden): python3 scripts/remote.py sh "python calistir/arac_nas100_mum_export.py"
`t` sütunu MT5 sunucu duvar saatidir (sunucu = New York + 7 sa, yeni deneme/broker_time.py).
"""
from __future__ import annotations

import datetime as dt
import gzip
import io
import json
import sys

sys.path.insert(0, "remote_agent")
import agent_config as cfg  # noqa: E402
import MetaTrader5 as mt5  # noqa: E402
import requests  # noqa: E402

SYMBOL = "NAS100"
TFS = ("M1", "M5", "M15", "M30", "H1")
CHUNK = 99_000
EXPECTED_SERVER = "Pepperstone"
BUCKET = "research-xfer"
PREFIX = "tfy_"


def pull(tf: str) -> list:
    pos, parts = 1, []
    while True:
        r = mt5.copy_rates_from_pos(SYMBOL, getattr(mt5, "TIMEFRAME_" + tf), pos, CHUNK)
        if r is None or len(r) == 0:
            break
        parts.append(r)
        pos += len(r)
        if len(r) < CHUNK:
            break
    return sorted({int(x["time"]): x for p in parts for x in p}.items())


def upload(name: str, data: bytes, ctype: str) -> int:
    url = cfg.SUPABASE_URL.rstrip("/")
    key = cfg.SUPABASE_SERVICE_KEY
    h = {"Authorization": f"Bearer {key}", "apikey": key, "x-upsert": "true", "Content-Type": ctype}
    return requests.post(f"{url}/storage/v1/object/{BUCKET}/{name}", headers=h, data=data, timeout=300).status_code


def main() -> None:
    if not mt5.initialize(getattr(cfg, "MT5_TERMINAL_PATH", None)):
        raise SystemExit(f"MT5 başlatılamadı: {mt5.last_error()}")
    acc = mt5.account_info()
    if acc is None or EXPECTED_SERVER not in (acc.server or ""):
        raise SystemExit(f"beklenmeyen terminal/hesap: {getattr(acc, 'server', None)}")
    mt5.symbol_select(SYMBOL, True)
    meta = {"symbol": SYMBOL, "login": acc.login, "server": acc.server,
            "exported_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "files": {}}
    for tf in TFS:
        rows = pull(tf)
        buf = io.BytesIO()
        with gzip.GzipFile(fileobj=buf, mode="wb") as g:
            g.write(b"t,o,h,l,c,v,sp\n")
            for t, x in rows:
                g.write(f"{t},{x['open']},{x['high']},{x['low']},{x['close']},{x['tick_volume']},{x['spread']}\n".encode())
        name = f"{PREFIX}{SYMBOL}_{tf}.csv.gz"
        code = upload(name, buf.getvalue(), "application/gzip")
        meta["files"][name] = {"rows": len(rows), "first_server_t": rows[0][0] if rows else None,
                               "last_server_t": rows[-1][0] if rows else None, "http": code}
        print(name, len(rows), code, flush=True)
    tick = mt5.symbol_info_tick(SYMBOL)
    meta["srv_minus_utc_s"] = int(round((tick.time - dt.datetime.now(dt.timezone.utc).timestamp()) / 900) * 900)
    print(upload(f"{PREFIX}meta.json", json.dumps(meta).encode(), "application/json"), json.dumps(meta))
    mt5.shutdown()


if __name__ == "__main__":
    main()
