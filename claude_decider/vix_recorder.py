"""
vix_recorder.py — Pepperstone CANLI VIX → Supabase (bulut sistemin canlı takibi için).
=============================================================================
NEDEN: Bulut backend (Railway) senin yerel Pepperstone MT5'ine bağlanamaz. Bu recorder
Windows'ta Pepperstone terminalinin yanında çalışır, VIX'i her 60s okuyup Supabase
`vix_live` tablosuna UPSERT eder. Backend `macro_data_service` oradan canlı okuyup
TÜM VIX-modellerine (bot VIX-regime scope, meta engine Layer4b, scheduler vol-sizing)
dağıtır. Recorder kapalıysa backend yfinance'e düşer — hiçbir şey kırılmaz.

NOT: decider (run_decider) VIX'i zaten kendi Pepperstone bağlantısından okur; bu recorder
AYRI amaç → BULUT sistemini beslemek. İkisi de salt-okuma, aynı terminali paylaşabilir.

KURULUM (Windows):
  1. decider_config.py'de SUPABASE_URL + SUPABASE_SERVICE_KEY'i doldur (bot config'inden kopyala).
  2. Supabase'de vix_live tablosunu oluştur (supabase/migrations/..._vix_live.sql çalıştır).
  3. python claude_decider/vix_recorder.py --terminal "C:/.../Pepperstone MetaTrader 5/terminal64.exe"
     (Windows yolunu kendi kurulumuna göre ver; ileri/geri slash ikisi de olur.)
"""
from __future__ import annotations
import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import decider_config as cfg  # noqa: E402
import MetaTrader5 as mt5  # noqa: E402
import requests  # noqa: E402


def find_vix_symbol(preferred: str | None) -> str | None:
    for s in ([preferred] if preferred else []) + cfg.VIX_CANDIDATES:
        if mt5.symbol_info(s) is not None:
            mt5.symbol_select(s, True)
            return s
    allsyms = mt5.symbols_get() or []
    matches = [x.name for x in allsyms if "vix" in x.name.lower() or "volat" in x.name.lower()]
    if matches:
        print("⚠️  Tam eşleşme yok, aday:", matches); mt5.symbol_select(matches[0], True)
        return matches[0]
    return None


def read_vix(symbol: str) -> float | None:
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        return None
    for v in (getattr(tick, "last", 0.0), getattr(tick, "bid", 0.0), getattr(tick, "ask", 0.0)):
        if v and v > 0:
            return float(v)
    return None


def upsert_supabase(value: float, symbol: str) -> bool:
    url, key = cfg.SUPABASE_URL.strip(), cfg.SUPABASE_SERVICE_KEY.strip()
    if not url or not key:
        print("❌ decider_config'te SUPABASE_URL/SUPABASE_SERVICE_KEY boş — doldur."); return False
    try:
        r = requests.post(
            f"{url.rstrip('/')}/rest/v1/vix_live",
            headers={"apikey": key, "Authorization": f"Bearer {key}",
                     "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates"},
            json={"symbol": "VIX", "value": round(value, 4),
                  "ts_utc": datetime.now(timezone.utc).isoformat(), "source": f"pepperstone:{symbol}"},
            timeout=10)
        if r.status_code in (200, 201, 204):
            return True
        print(f"  supabase {r.status_code}: {r.text[:150]}"); return False
    except Exception as e:
        print("  supabase yazılamadı:", e); return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--terminal", required=True, help="Pepperstone terminal64.exe yolu")
    ap.add_argument("--symbol", default=None, help="VIX sembolü (boşsa otomatik bul)")
    ap.add_argument("--interval", type=float, default=60.0, help="okuma/yazma aralığı sn")
    args = ap.parse_args()

    if not mt5.initialize(args.terminal):
        print("❌ Pepperstone'a bağlanılamadı:", mt5.last_error()); return
    print(f"✓ Pepperstone bağlı | {getattr(mt5.account_info(),'company','')}")
    symbol = find_vix_symbol(args.symbol)
    if not symbol:
        print("❌ VIX sembolü yok — --symbol ile ver."); mt5.shutdown(); return
    print(f"✓ VIX '{symbol}' → Supabase vix_live (her {args.interval:.0f}s)")

    ok_count = 0
    try:
        while True:
            v = read_vix(symbol)
            if v is not None and upsert_supabase(v, symbol):
                ok_count += 1
                if ok_count % 10 == 1:
                    print(f"  [{datetime.now():%H:%M:%S}] VIX={v:.2f} → Supabase ✓")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nRecorder durduruldu.")
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    main()
