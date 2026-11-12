"""box_spotcrude_carry_dump.py — MT5 kutusunda çalışır: PY-01 EK-2 (petrol carry, broker verisi) için ham veri.

Yalnız OKUR (symbol_info, copy_rates, history_deals); emir açmaz, canlı süreçlere dokunmaz. Sonuç hesaplamaz.

Parçalar (köprü çıktısı tavanlı olduğu için ayrı ayrı çağrılır):
  --part info   petrol benzeri tüm semboller + SpotCrude sözleşme/swap özellikleri (metin)
  --part d1     SpotCrude D1 tüm geçmiş (gzip+base64 CSV)
  --part h1     SpotCrude H1 son ~99k bar (gzip+base64 CSV)
  --part deals  hesap geçmişinde ticari olmayan tüm kayıtlar (düzeltme/swap/bakiye) + SpotCrude
                pozisyon kapanışlarının swap'ı (gzip+base64 CSV)

Zaman: bar/deal `time` ham BROKER saati olarak yazılır (`t_broker`, epoch sn); UTC'ye çevirme Mac tarafında.

Çalıştırma (kutuda):  python backend/research/box_spotcrude_carry_dump.py --part info
"""
from __future__ import annotations

import argparse
import base64
import csv
import gzip
import io
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "yeni deneme"))

try:
    import MetaTrader5 as mt5  # type: ignore
except ImportError:
    sys.exit("HATA: MetaTrader5 yok — bu script MT5 kutusunda çalışır.")
try:
    import config  # type: ignore
except Exception:  # pragma: no cover
    config = None  # type: ignore

SYMBOL = "SpotCrude"
MAX_BARS = 99_000
OIL_HINTS = ("crude", "oil", "wti", "brent", "cl", "xti", "xbr", "ukoil", "usoil")
INFO_FIELDS = ("name", "description", "path", "currency_base", "currency_profit", "digits", "point",
               "trade_contract_size", "trade_calc_mode", "trade_mode", "swap_mode", "swap_long",
               "swap_short", "swap_rollover3days", "spread", "expiration_time", "start_time",
               "trade_tick_value", "trade_tick_size", "volume_min", "margin_initial")
HISTORY_START = datetime(2015, 1, 1)


def connect() -> None:
    kw = {}
    if config is not None and getattr(config, "MT5_ACCOUNT", None):
        kw = dict(login=config.MT5_ACCOUNT, password=config.MT5_PASSWORD, server=config.MT5_SERVER)
    path = getattr(config, "MT5_TERMINAL_PATH", "") if config is not None else ""
    ok = mt5.initialize(path, **kw) if path else mt5.initialize(**kw)
    if not ok:
        sys.exit(f"mt5.initialize basarisiz: {mt5.last_error()}")
    a = mt5.account_info()
    print(f"hesap={getattr(a, 'login', 0)} sunucu={getattr(a, 'server', '')} para={getattr(a, 'currency', '')}")


def emit(tag: str, rows: list[list], header: list[str]) -> None:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(header)
    w.writerows(rows)
    blob = base64.b64encode(gzip.compress(buf.getvalue().encode())).decode()
    print(f"{tag}_ROWS={len(rows)} {tag}_B64_LEN={len(blob)}")
    print(f"{tag}_B64_BEGIN")
    for i in range(0, len(blob), 4000):
        print(blob[i:i + 4000])
    print(f"{tag}_B64_END")


def part_info() -> None:
    syms = mt5.symbols_get() or []
    print(f"sembol_sayisi={len(syms)}")
    for s in syms:
        nm = s.name.lower()
        if any(h in nm for h in OIL_HINTS) or any(h in (s.description or "").lower() for h in ("crude", "oil")):
            print(f"PETROL {s.name} | {s.description} | {s.path} | swap L={s.swap_long} S={s.swap_short} "
                  f"mode={s.swap_mode} exp={s.expiration_time}")
    mt5.symbol_select(SYMBOL, True)
    si = mt5.symbol_info(SYMBOL)
    if si is None:
        sys.exit(f"{SYMBOL} yok: {mt5.last_error()}")
    for f in INFO_FIELDS:
        print(f"INFO {f}={getattr(si, f, None)}")
    tk = mt5.symbol_info_tick(SYMBOL)
    print(f"INFO tick bid={getattr(tk, 'bid', None)} ask={getattr(tk, 'ask', None)} t_broker={getattr(tk, 'time', None)}")


def part_bars(tf: int, tag: str) -> None:
    mt5.symbol_select(SYMBOL, True)
    r = None
    for n in (MAX_BARS, 50_000, 20_000, 10_000, 5_000):
        r = mt5.copy_rates_from_pos(SYMBOL, tf, 0, n)
        if r is not None and len(r):
            break
    if r is None or not len(r):
        sys.exit(f"bar yok: {mt5.last_error()}")
    rows = [[int(x["time"]), float(x["open"]), float(x["high"]), float(x["low"]), float(x["close"]),
             int(x["tick_volume"]), int(x["spread"])] for x in r]
    print(f"{tag} ilk={datetime.utcfromtimestamp(rows[0][0])} son={datetime.utcfromtimestamp(rows[-1][0])} (broker saati)")
    emit(tag, rows, ["t_broker", "open", "high", "low", "close", "tick_volume", "spread_pts"])


def part_deals() -> None:
    deals = mt5.history_deals_get(HISTORY_START, datetime.now() + timedelta(days=2)) or []
    print(f"deal_toplam={len(deals)}")
    rows = []
    for d in deals:
        trade = d.type in (mt5.DEAL_TYPE_BUY, mt5.DEAL_TYPE_SELL)
        if trade and d.symbol != SYMBOL:
            continue
        if trade and d.entry == mt5.DEAL_ENTRY_IN:
            kind = "in"
        elif trade:
            kind = "out"
        else:
            kind = "nontrade"
        rows.append([int(d.time), int(d.position_id), d.symbol, int(d.type), int(d.entry), kind,
                     float(d.volume), float(d.price), round(float(d.profit), 2), round(float(d.swap), 2),
                     round(float(d.commission), 2), str(d.comment or "")])
    emit("DEALS", rows, ["t_broker", "position_id", "symbol", "type", "entry", "kind", "volume", "price",
                         "profit", "swap", "commission", "comment"])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", choices=["info", "d1", "h1", "deals"], required=True)
    a = ap.parse_args()
    connect()
    try:
        if a.part == "info":
            part_info()
        elif a.part == "d1":
            part_bars(mt5.TIMEFRAME_D1, "D1")
        elif a.part == "h1":
            part_bars(mt5.TIMEFRAME_H1, "H1")
        else:
            part_deals()
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    main()
