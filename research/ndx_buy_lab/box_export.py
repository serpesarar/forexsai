"""box_export.py — MT5 kutusunda çalışır: derin bar geçmişi + tam işlem geçmişi.

NDX BUY araştırması (2026-07-28) için veri toplar. Canlı süreçlere DOKUNMAZ,
yalnız okur ve Supabase'e yazar.

1) Derin bar geçmişi → candle_cache upsert (mevcut şema, mevcut sembol adları).
   Amaç: 1 aylık pencere yerine YILLARCA veri → rejim filtrelerini birden fazla
   piyasa rejiminde test edebilmek (tek rejimde bulunan "edge" sahtedir).
2) Tam MT5 deal geçmişi → pozisyonlara birleştirilir → gzip+base64 olarak
   stdout'a basılır (ajan çıktı limiti 60k; sıkıştırılmış hali ~20-40k).

Çalıştırma (kutuda):  python research/ndx_buy_lab/box_export.py
"""
from __future__ import annotations

import base64
import gzip
import io
import csv
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "yeni deneme"))

try:
    import MetaTrader5 as mt5
except ImportError:
    print("HATA: MetaTrader5 yok — bu script MT5 kutusunda çalışır.")
    sys.exit(1)

import config  # type: ignore

try:
    from supabase import create_client
except ImportError:
    print("HATA: pip install supabase")
    sys.exit(1)


# ── Ne kadar geçmiş isteniyor (MT5 terminalinin verdiği kadarı gelir) ──────────
# 1m ARAŞTIRMADA replay çözünürlüğü için gerekli; Supabase'de 2026-02-11'den beri
# var, bu yüzden burada daha derinini istiyoruz ama ilk öncelik üst TF'ler.
DEEP_REQUEST = {
    "1h":  60000,   # ~10 yıl
    "30m": 60000,   # ~5 yıl
    "15m": 80000,   # ~3.5 yıl
    "5m":  120000,  # ~1.7 yıl
    "1m":  200000,  # ~1 yıl (seans saatleri)
}
TF_MAP = {
    "1m": mt5.TIMEFRAME_M1, "5m": mt5.TIMEFRAME_M5, "15m": mt5.TIMEFRAME_M15,
    "30m": mt5.TIMEFRAME_M30, "1h": mt5.TIMEFRAME_H1, "1d": mt5.TIMEFRAME_D1,
}
DEEP_REQUEST["1d"] = 6000

# ForexSAI adı → broker sembolü. config.SYMBOL_MAP kutunun gerçeğidir; broker
# değişmiş olabilir (USTEC → NAS100), o yüzden config'ten okuyup doğruluyoruz.
SYMBOLS = dict(getattr(config, "RECORDER_SYMBOLS", None)
               or getattr(config, "SYMBOL_MAP", {}))

CHUNK = 1000


# ── MT5 sunucu saati → gerçek UTC (bkz. RAPOR.md §1) ────────────────────────
# MT5'in `time` alanı epoch GİBİ görünür ama BROKER saatindedir (UTC+2/+3).
# Bu düzeltme olmadan yazılan her bar 2-3 saat ileri damgalanır.
_OFFSET_SEC = 0


def detect_offset() -> int:
    import time as _t
    for sym in list(SYMBOLS.values()):
        try:
            if not mt5.symbol_select(sym, True):
                continue
            tk = mt5.symbol_info_tick(sym)
            if tk and tk.time:
                return int(round((tk.time - _t.time()) / 900.0) * 900)
        except Exception:
            continue
    return 0


def to_utc(epoch: int) -> datetime:
    return datetime.fromtimestamp(int(epoch) - _OFFSET_SEC, tz=timezone.utc)


def connect() -> bool:
    if getattr(config, "MT5_ACCOUNT", None):
        kw = dict(login=config.MT5_ACCOUNT, password=config.MT5_PASSWORD,
                  server=config.MT5_SERVER)
        ok = (mt5.initialize(config.MT5_TERMINAL_PATH, **kw)
              if getattr(config, "MT5_TERMINAL_PATH", "") else mt5.initialize(**kw))
    else:
        ok = (mt5.initialize(config.MT5_TERMINAL_PATH)
              if getattr(config, "MT5_TERMINAL_PATH", "") else mt5.initialize())
    if not ok:
        print("mt5.initialize başarısız:", mt5.last_error())
    return bool(ok)


def sb():
    return create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_KEY)


def resolve_symbol(broker_sym: str) -> str | None:
    """Broker sembolünü doğrula; yoksa yakın adayları dene."""
    if mt5.symbol_info(broker_sym) is not None:
        mt5.symbol_select(broker_sym, True)
        return broker_sym
    for cand in mt5.symbols_get() or []:
        if cand.name.upper() == broker_sym.upper():
            mt5.symbol_select(cand.name, True)
            return cand.name
    return None


def backfill_bars(client, fx_symbol: str, broker_sym: str) -> None:
    real = resolve_symbol(broker_sym)
    if not real:
        print(f"  ! {fx_symbol}: broker sembolü bulunamadı ({broker_sym})")
        return
    for tf, want in DEEP_REQUEST.items():
        rates = mt5.copy_rates_from_pos(real, TF_MAP[tf], 0, want)
        if rates is None or len(rates) == 0:
            print(f"  {fx_symbol} {tf}: veri yok ({mt5.last_error()})")
            continue
        rows = []
        for r in rates:
            ts = to_utc(r["time"])
            rows.append({
                "symbol": fx_symbol, "timeframe": tf,
                "candle_time": ts.isoformat(),
                "open": float(r["open"]), "high": float(r["high"]),
                "low": float(r["low"]), "close": float(r["close"]),
                "volume": float(r["tick_volume"]),
            })
        first, last = rows[0]["candle_time"][:10], rows[-1]["candle_time"][:10]
        wrote = 0
        for i in range(0, len(rows), CHUNK):
            try:
                client.table("candle_cache").upsert(
                    rows[i:i + CHUNK], on_conflict="symbol,timeframe,candle_time"
                ).execute()
                wrote += len(rows[i:i + CHUNK])
            except Exception as e:
                print(f"  ! upsert hata {fx_symbol} {tf} @{i}: {e}")
                break
        print(f"  {fx_symbol} {tf}: {wrote}/{len(rows)} bar  {first} → {last}")


def export_deals() -> str:
    """Tüm deal geçmişini pozisyonlara birleştirip CSV döndür."""
    frm = datetime(2026, 1, 1, tzinfo=timezone.utc)
    to = datetime.now(timezone.utc) + timedelta(days=1)
    deals = mt5.history_deals_get(frm, to)
    if deals is None:
        print("history_deals_get None:", mt5.last_error())
        return ""
    ins: dict[int, list] = {}
    outs: dict[int, list] = {}
    for d in deals:
        if d.entry == mt5.DEAL_ENTRY_IN:
            ins.setdefault(d.position_id, []).append(d)
        elif d.entry in (mt5.DEAL_ENTRY_OUT, mt5.DEAL_ENTRY_OUT_BY):
            outs.setdefault(d.position_id, []).append(d)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["position_id", "symbol", "direction", "magic", "comment_in",
                "comment_out", "open_time", "open_price", "close_time",
                "close_price", "volume", "profit", "commission", "swap"])
    n = 0
    for pid, il in sorted(ins.items()):
        i0 = il[0]
        ol = outs.get(pid) or []
        if not ol:
            continue
        o_last = ol[-1]
        profit = sum(x.profit for x in ol)
        comm = sum(x.commission for x in ol) + sum(x.commission for x in il)
        swap = sum(x.swap for x in ol)
        w.writerow([
            pid, i0.symbol, "BUY" if i0.type == mt5.DEAL_TYPE_BUY else "SELL",
            i0.magic, i0.comment, o_last.comment,
            to_utc(i0.time).isoformat(),
            i0.price,
            to_utc(o_last.time).isoformat(),
            o_last.price, i0.volume, round(profit, 2), round(comm, 2), round(swap, 2),
        ])
        n += 1
    print(f"  pozisyon sayısı: {n}")
    return buf.getvalue()


def main() -> None:
    if not connect():
        sys.exit(1)
    global _OFFSET_SEC
    _OFFSET_SEC = detect_offset()
    print(f"MT5 sunucu offset'i: {_OFFSET_SEC/60:+.0f} dk -> UTC'ye cevriliyor")
    print("== BAR BACKFILL ==")
    print("  semboller:", SYMBOLS)
    client = sb()
    for fx, brk in SYMBOLS.items():
        backfill_bars(client, fx, brk)
    print("== DEAL EXPORT ==")
    csv_text = export_deals()
    if csv_text:
        blob = base64.b64encode(gzip.compress(csv_text.encode())).decode()
        print(f"DEALS_B64_LEN={len(blob)}")
        print("DEALS_B64_BEGIN")
        for i in range(0, len(blob), 4000):
            print(blob[i:i + 4000])
        print("DEALS_B64_END")
    mt5.shutdown()


if __name__ == "__main__":
    main()
