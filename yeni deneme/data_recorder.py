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


# ── MT5 SUNUCU SAATİ → GERÇEK UTC (2026-07-28 düzeltmesi) ───────────────────
# MT5'in copy_rates/tick `time` alanı epoch GİBİ görünür ama BROKER SUNUCU
# saatindedir (IC Markets: kış UTC+2, ABD-yaz UTC+3). Bunu doğrudan
# `fromtimestamp(..., tz=utc)` ile yazmak barları 2-3 saat İLERİ etiketler.
#
# Bulunan hasar (research/ndx_buy_lab/RAPOR.md §1): candle_cache'e 3 saat kaymış
# damgalar yazılıyordu → (a) sinyal↔mum eşleşmesi bozuk, (b) bayatlık kontrolleri
# "gelecekten gelen bar" gördüğü için hep taze sanıyor, (c) backend'in Redis
# köprüsü DOĞRU UTC yazdığı için bu script periyodik toplu yazımda doğru
# satırların ÜZERİNE kaymış veri basıyordu.
#
# Çözüm: offset'i çalışma anında ÖLÇ (sunucu tick zamanı − gerçek UTC), 15 dk'ya
# yuvarla. Böylece DST geçişleri ve broker değişiklikleri kendiliğinden çözülür.
_SERVER_OFFSET_SEC = 0


def detect_server_offset() -> int:
    """MT5 sunucu saati ile gerçek UTC arasındaki farkı saniye olarak ölç."""
    import time as _time
    best = None
    for sym in list(config.RECORDER_SYMBOLS.values()):
        try:
            if not mt5.symbol_select(sym, True):
                continue
            tick = mt5.symbol_info_tick(sym)
            if not tick or not tick.time:
                continue
            delta = tick.time - _time.time()
            # 15 dk'ya yuvarla (tick gecikmesi/saat sapması gürültüsünü at)
            snapped = round(delta / 900.0) * 900
            if best is None or abs(delta - snapped) < abs(best[1] - best[0]):
                best = (snapped, delta)
        except Exception:
            continue
    if best is None:
        log.warning("sunucu saat offset'i ölçülemedi — 0 varsayılıyor "
                    "(barlar broker saatinde kalabilir!)")
        return 0
    snapped, raw = best
    log.info("MT5 sunucu saat offset'i: %+.1f dk (ham %+.1f) → UTC'ye çevriliyor",
             snapped / 60.0, raw / 60.0)
    return int(snapped)


def _iso(epoch: int) -> str:
    """Broker sunucu epoch'unu GERÇEK UTC ISO damgasına çevir."""
    return datetime.fromtimestamp(epoch - _SERVER_OFFSET_SEC, tz=timezone.utc).isoformat()


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

    global _SERVER_OFFSET_SEC
    _SERVER_OFFSET_SEC = detect_server_offset()

    try:
        loops = 0
        while True:
            log.info("─── kayıt @ %s ───", datetime.now(timezone.utc).strftime("%H:%M:%S"))
            # DST geçişi / broker değişikliği: offset'i saatte bir tazele
            loops += 1
            if loops % max(1, int(3600 / max(config.RECORDER_POLL, 1))) == 0:
                new_off = detect_server_offset()
                if new_off != _SERVER_OFFSET_SEC:
                    log.warning("sunucu offset'i değişti: %+d dk → %+d dk",
                                _SERVER_OFFSET_SEC // 60, new_off // 60)
                    _SERVER_OFFSET_SEC = new_off
                    last_seen.clear()   # damgalar yeniden hesaplanmalı
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
