"""
MT5 1m bar recovery — tek adımda ÇEK + YÜKLE (2026-06-12).

Eksik 1m mumları MT5 terminalinden çeker ve doğrudan ForexSAI backend'ine
yükler (candle_cache'e işlenir). Ayrı curl adımı YOK.

NEDEN GEREKLI: MT5 köprüsü Redis'e yalnızca 5m/1h/1d bar yayınlıyor; `mt5:bar:1m`
stream'i opsiyonel ve bu köprüde yok (mt5_redis_client.py:211). Yani 1m candle_cache
canlı GÜNCELLENMEZ — sadece bu script'le elle doldurulur. Endeksler en son
2026-05-21'de doldurulmuş; bu yüzden donmuş görünüyor.

NEREDE ÇALIŞTIRILIR: MT5 terminalinin kurulu olduğu Windows kutusunda.
    pip install MetaTrader5 requests
    python mt5_pull_missing_1m.py                       # varsayılan: 05-20'den bugüne, 4 sembol
    python mt5_pull_missing_1m.py --symbols USTEC DE40  # sadece donmuş endeksler
    python mt5_pull_missing_1m.py --since 2026-05-20 --no-upload --out gap.json

Sembol eşlemesi (MT5 → ForexSAI), upload endpoint'i otomatik yapar:
    USTEC → NDX.INDX,  DE40 → GDAXI.INDX,  XTIUSD → USOIL.FOREX,  XAUUSD → XAUUSD
Üst üste binen aralık sorun değil: sunucu timestamp'e göre upsert eder (dedupe).
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

API = "https://upbeat-flow-production.up.railway.app"
MT5_SYMBOLS = ["XAUUSD", "USTEC", "DE40", "XTIUSD"]
DEFAULT_SINCE = "2026-05-20"   # son başarılı dökümle çakıştır → boşluk kalmasın


def pull(symbols, since, until, chunk_days):
    try:
        import MetaTrader5 as mt5  # type: ignore
    except ImportError:
        print("HATA: pip install MetaTrader5", file=sys.stderr); sys.exit(1)

    if not mt5.initialize():
        print(f"HATA: mt5.initialize() basarisiz: {mt5.last_error()}", file=sys.stderr)
        sys.exit(1)
    try:
        total = 0
        per_symbol = {}
        for sym in symbols:
            info = mt5.symbol_info(sym)
            if info is None:
                print(f"UYARI: {sym} MT5'te bulunamadi — atlaniyor")
                per_symbol[sym] = {"count": 0, "bars": [], "error": "symbol_not_found"}
                continue
            if not info.visible:
                mt5.symbol_select(sym, True)

            bars = []
            cursor = since
            while cursor < until:
                end = min(cursor + timedelta(days=chunk_days), until)
                rates = mt5.copy_rates_range(sym, mt5.TIMEFRAME_M1, cursor, end)
                if rates is not None and len(rates) > 0:
                    for r in rates:
                        bars.append({
                            "t": int(r["time"]),                 # unix sec, MT5 API = UTC
                            "o": float(r["open"]), "h": float(r["high"]),
                            "l": float(r["low"]),  "c": float(r["close"]),
                            "v": float(r["tick_volume"]) if "tick_volume" in r.dtype.names else 0.0,
                        })
                cursor = end

            seen = {b["t"]: b for b in bars}           # boundary çakışmalarını dedupe et
            clean = sorted(seen.values(), key=lambda x: x["t"])
            per_symbol[sym] = {"count": len(clean), "bars": clean}
            total += len(clean)
            fb = datetime.fromtimestamp(clean[0]["t"], tz=timezone.utc).isoformat() if clean else "—"
            lb = datetime.fromtimestamp(clean[-1]["t"], tz=timezone.utc).isoformat() if clean else "—"
            print(f"  {sym:8s} {len(clean):>7d} bar   ({fb} → {lb})")

        return {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "since": since.isoformat(), "until": until.isoformat(),
            "timeframe": "1m", "total_bars": total, "symbols": per_symbol,
        }
    finally:
        mt5.shutdown()


def upload(payload, purge):
    try:
        import requests  # type: ignore
    except ImportError:
        print("HATA: pip install requests  (ya da --no-upload kullan)", file=sys.stderr); sys.exit(1)
    url = f"{API}/api/mt5/upload-1m-bars"
    params = {"purge_existing": "true"} if purge else {}
    print(f"\nYukleniyor → {url} ...")
    files = {"file": ("mt5_1m_bars.json", json.dumps(payload), "application/json")}
    r = requests.post(url, files=files, params=params, timeout=600)
    print(f"  HTTP {r.status_code}")
    try:
        print("  " + json.dumps(r.json(), ensure_ascii=False)[:2000])
    except Exception:
        print("  " + r.text[:2000])
    r.raise_for_status()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default=DEFAULT_SINCE, help="YYYY-MM-DD (vars. 2026-05-20)")
    ap.add_argument("--until", default=None, help="YYYY-MM-DD (vars. su an)")
    ap.add_argument("--symbols", nargs="+", default=MT5_SYMBOLS)
    ap.add_argument("--chunk-days", type=int, default=10)
    ap.add_argument("--out", default="mt5_1m_bars.json", help="JSON yedek dosyasi")
    ap.add_argument("--no-upload", action="store_true", help="Sadece JSON yaz, yukleme")
    ap.add_argument("--purge", action="store_true",
                    help="Yuklemeden ONCE o sembolun tum 1m satirlarini sil (tz duzeltme icin)")
    args = ap.parse_args()

    since = datetime.fromisoformat(args.since).replace(tzinfo=timezone.utc)
    until = (datetime.fromisoformat(args.until).replace(tzinfo=timezone.utc)
             if args.until else datetime.now(timezone.utc))
    if until <= since:
        print("HATA: --until, --since'den sonra olmali", file=sys.stderr); sys.exit(1)

    print(f"MT5 1m cekiliyor  {since.date()} → {until.date()}  sembol={args.symbols}")
    payload = pull(args.symbols, since, until, args.chunk_days)

    Path(args.out).write_text(json.dumps(payload))
    print(f"\nYedek yazildi: {Path(args.out).absolute()}  ({payload['total_bars']} bar)")

    if args.no_upload:
        print("\n--no-upload: yukleme atlandi. Sonra elle:")
        print(f"  curl -X POST -F 'file=@{Path(args.out).absolute()}' {API}/api/mt5/upload-1m-bars")
    else:
        upload(payload, args.purge)
        print("\nBitti. Dogrulama: candle_cache'te 1m 'last' tarihleri guncellenmis olmali.")


if __name__ == "__main__":
    main()
