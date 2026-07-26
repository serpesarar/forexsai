"""
data_recorder.py — SÜREKLI OHLC + indicator kaydedici  (MT5 kutusunda, botla paralel)
====================================================================================
NEDEN: MT5 bridge 1m yayınlamıyor ve diğer TF'ler de ~periyodik donuyor. Bu script
MT5'ten DOĞRUDAN çekip Supabase'e yazar → veri donması KALICI biter, üstüne her
mum için TÜM indicator değerleri kaydedilir (gelişim/forensik analiz için).

Yazılan tablolar:
  • candle_cache         (OHLC, mevcut tablo — bot/paneller bunu okur)
  • indicator_snapshots  (her kapalı mum için tam indicator seti, ind JSONB)

Zaman: MT5 Python API time'ı UTC kabul edilir (offset 0 — backend/candle_cache
konvansiyonuyla birebir aynı).

Çalıştırma:  python data_recorder.py
Ayar:        config.py  (RECORDER_SYMBOLS / RECORDER_TIMEFRAMES / SUPABASE_*)
"""
from __future__ import annotations
import sys
import time
import logging
from datetime import datetime, timezone

import config
from indicators import compute_all

try:
    import MetaTrader5 as mt5
except ImportError:
    print("HATA: MetaTrader5 yok. Bu script MT5 kutusunda çalışır."); sys.exit(1)
try:
    from supabase import create_client
except ImportError:
    print("HATA: pip install supabase"); sys.exit(1)

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)s  %(message)s",
                    handlers=[logging.StreamHandler(),
                              logging.FileHandler("data_recorder.log", encoding="utf-8")])
log = logging.getLogger("recorder")

TF_MAP = {"1m": mt5.TIMEFRAME_M1, "5m": mt5.TIMEFRAME_M5, "15m": mt5.TIMEFRAME_M15,
          "30m": mt5.TIMEFRAME_M30, "1h": mt5.TIMEFRAME_H1}
HIST_BARS = 320           # steady-state pencere (ema200 + pay)
CC_CHUNK = 1000           # candle_cache upsert batch boyutu


def connect_mt5() -> bool:
    # LOGIN modu / ATTACH modu (MT5_ACCOUNT boş → açık terminale bağlan).
    # 2026-07-26: attach kurulumunda login=0 → '(-2, Invalid params)'.
    if config.MT5_ACCOUNT:
        kw = dict(login=config.MT5_ACCOUNT, password=config.MT5_PASSWORD,
                  server=config.MT5_SERVER)
        ok = (mt5.initialize(config.MT5_TERMINAL_PATH, **kw)
              if config.MT5_TERMINAL_PATH else mt5.initialize(**kw))
    else:
        ok = (mt5.initialize(config.MT5_TERMINAL_PATH)
              if config.MT5_TERMINAL_PATH else mt5.initialize())
    if not ok:
        log.error("mt5.initialize başarısız: %s", mt5.last_error()); return False
    info = mt5.account_info()
    log.info("MT5 bağlı | hesap=%s broker=%s", getattr(info, "login", "?"),
             getattr(info, "company", "?"))
    return True


def supa():
    if not config.SUPABASE_URL or not config.SUPABASE_SERVICE_KEY:
        log.error("config.SUPABASE_URL / SUPABASE_SERVICE_KEY boş — doldur."); sys.exit(1)
    return create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_KEY)


def _iso(epoch: int) -> str:
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()


def record(client, fx_symbol: str, mt5_symbol: str, tf_name: str, tf_const,
           last_seen: dict) -> None:
    key = (fx_symbol, tf_name)
    count = (config.RECORDER_BACKFILL_BARS.get(tf_name, HIST_BARS)  # ilk koşu: derin backfill
             if key not in last_seen else HIST_BARS)                # sonra: küçük pencere
    rates = mt5.copy_rates_from_pos(mt5_symbol, tf_const, 1, count)  # 1 = forming'i atla
    if rates is None or len(rates) < 30:
        return
    o = [float(r["open"]) for r in rates]; h = [float(r["high"]) for r in rates]
    l = [float(r["low"]) for r in rates];  c = [float(r["close"]) for r in rates]
    v = [float(r["tick_volume"]) for r in rates]
    t = [int(r["time"]) for r in rates]
    prev = last_seen.get(key, 0)
    new_idx = [i for i in range(len(t)) if t[i] > prev]
    if not new_idx:
        return

    now = datetime.now(timezone.utc).isoformat()
    # 1) candle_cache — tüm yeni kapalı barlar (chunk'lı: backfill binlerce satır olabilir)
    cc_rows = [{"symbol": fx_symbol, "timeframe": tf_name, "candle_time": _iso(t[i]),
                "open": o[i], "high": h[i], "low": l[i], "close": c[i],
                "volume": v[i], "fetched_at": now} for i in new_idx]
    for j in range(0, len(cc_rows), CC_CHUNK):
        try:
            client.table("candle_cache").upsert(
                cc_rows[j:j + CC_CHUNK], on_conflict="symbol,timeframe,candle_time").execute()
        except Exception as e:
            log.warning("%s %s candle_cache upsert hata: %s", fx_symbol, tf_name, e)

    # 2) indicator_snapshots — yeni barlar (poll başına tavan; gap OHLC olarak dolar,
    #    indicator istenirse candle_cache'ten sonradan yeniden hesaplanabilir)
    ind_rows = []
    for i in new_idx[-config.RECORDER_MAX_IND_PER_POLL:]:
        if i < 30:
            continue
        ind = compute_all(o[:i + 1], h[:i + 1], l[:i + 1], c[:i + 1], v[:i + 1])
        ind_rows.append({"symbol": fx_symbol, "timeframe": tf_name, "candle_time": _iso(t[i]),
                         "open": o[i], "high": h[i], "low": l[i], "close": c[i],
                         "volume": v[i], "ind": ind})
    if ind_rows:
        try:
            client.table("indicator_snapshots").upsert(
                ind_rows, on_conflict="symbol,timeframe,candle_time").execute()
        except Exception as e:
            log.warning("%s %s indicator upsert hata: %s", fx_symbol, tf_name, e)

    last_seen[key] = t[-1]
    log.info("  %-12s %-3s: +%d bar (son %s)", fx_symbol, tf_name, len(new_idx),
             _iso(t[-1])[11:16])


def resolve(mt5_symbol: str) -> str | None:
    if mt5.symbol_info(mt5_symbol) is not None:
        mt5.symbol_select(mt5_symbol, True)
        return mt5_symbol
    log.warning("%s MT5'te bulunamadı — atlandı", mt5_symbol)
    return None


def main():
    log.info("=" * 60)
    log.info("data_recorder başlıyor — semboller=%s TF=%s",
             list(config.RECORDER_SYMBOLS), config.RECORDER_TIMEFRAMES)
    log.info("=" * 60)
    if not connect_mt5():
        sys.exit(1)
    client = supa()
    last_seen: dict = {}
    resolved = {fx: resolve(m) for fx, m in config.RECORDER_SYMBOLS.items()}

    try:
        while True:
            log.info("─── kayıt @ %s ───", datetime.now(timezone.utc).strftime("%H:%M:%S"))
            for fx, mt5_symbol in config.RECORDER_SYMBOLS.items():
                rs = resolved.get(fx)
                if not rs:
                    continue
                for tf_name in config.RECORDER_TIMEFRAMES:
                    tf_const = TF_MAP.get(tf_name)
                    if tf_const is None:
                        continue
                    try:
                        record(client, fx, rs, tf_name, tf_const, last_seen)
                    except Exception as e:
                        log.exception("%s %s kayıt hata: %s", fx, tf_name, e)
            time.sleep(config.RECORDER_POLL)
    except KeyboardInterrupt:
        log.info("Durduruldu (Ctrl+C).")
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    main()
