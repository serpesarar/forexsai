"""MT5 kutu kaydedicisi → DataHub beslemesi (Supabase `indicator_snapshots` üzerinden).

Neden (2026-09-30): Railway'deki MT5→Redis köprüsü 2026-06-25'ten beri veri almıyor
(kutuda yayıncı çalışmıyor). `hybrid` modda DataHub MT5'i hiç "taze" görmediği için
her sembolde Yahoo'ya düşüyordu. USOIL için Yahoo `CL=F` (ön ay vadeli) broker
SpotCrude'dan 0,1–4,7$ farklı → panel sinyalleri başka bir enstrümandan üretiliyor,
Yahoo mumları `candle_cache`'teki doğru satırların üstüne yazılıyordu.
Kutudaki `yeni deneme/data_recorder.py` broker barlarını dakikada bir
`indicator_snapshots`'a yazıyor; bu servis onları okuyup `mt5_recorder` kaynağıyla
DataHub'a alır → hybrid mod MT5'i taze görür, Yahoo atlanır.

Kapsam: MT5_RECORDER_FEED_SYMBOLS (varsayılan yalnız USOIL.FOREX).
Hata olursa fail-open: besleme durur, DataHub'ın mevcut yedeği devam eder.
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

TABLE = "indicator_snapshots"
TF_MS = {"1m": 60_000, "5m": 300_000, "1h": 3_600_000}
# İlk turda geçmişi değiştirmek için çekilecek bar sayısı (≈2g 1m, ≈5g 5m, ≈6h 1h)
INITIAL_BARS = {"1m": 3000, "5m": 1500, "1h": 1000}
PAGE = 1000
OVERLAP_BARS = 3            # geç güncellenen son barları da yakala
MAX_PRICE_AGE_SEC = 600     # en yeni 1m bar bundan eskiyse fiyat verme (kaydedici durmuş)

_state: Dict[str, Any] = {"running": False, "symbols": {}, "cycles": 0, "errors": 0,
                          "last_error": None, "started_at": None}


def feed_enabled() -> bool:
    return os.getenv("MT5_RECORDER_FEED_ENABLED", "1").strip().lower() not in {"0", "false", "no", "off"}


def feed_symbols() -> List[str]:
    raw = os.getenv("MT5_RECORDER_FEED_SYMBOLS", "USOIL.FOREX")
    return [s.strip() for s in raw.split(",") if s.strip()]


def feed_interval() -> float:
    try:
        return max(10.0, float(os.getenv("MT5_RECORDER_FEED_INTERVAL", "30")))
    except ValueError:
        return 30.0


def row_to_candle(row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Supabase satırı → DataHub mum sözlüğü (timestamp ms, UTC)."""
    ts = row.get("candle_time")
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    try:
        return {"timestamp": int(dt.timestamp() * 1000),
                "open": float(row["open"]), "high": float(row["high"]),
                "low": float(row["low"]), "close": float(row["close"]),
                "volume": float(row.get("volume") or 0)}
    except (KeyError, TypeError, ValueError):
        return None


def latest_price(candles_1m: List[Dict[str, Any]], now_s: float) -> Optional[tuple]:
    """En yeni kapanmış 1m bardan (fiyat, kapanış zamanı sn). Bayatsa None."""
    if not candles_1m:
        return None
    last = max(candles_1m, key=lambda c: c["timestamp"])
    close_s = last["timestamp"] / 1000 + 60
    if now_s - close_s > MAX_PRICE_AGE_SEC:
        return None
    return last["close"], close_s


def _fetch(db, symbol: str, tf: str, since_iso: Optional[str], n: int) -> List[Dict[str, Any]]:
    """Son n bar (ya da since_iso'dan beri) — eski→yeni sıralı."""
    rows: List[Dict[str, Any]] = []
    start = 0
    while len(rows) < n:
        q = (db.table(TABLE).select("candle_time,open,high,low,close,volume")
             .eq("symbol", symbol).eq("timeframe", tf))
        if since_iso:
            q = q.gte("candle_time", since_iso)
        res = q.order("candle_time", desc=True).range(start, start + min(PAGE, n - len(rows)) - 1).execute()
        batch = getattr(res, "data", None) or []
        rows.extend(batch)
        if len(batch) < PAGE:
            break
        start += PAGE
    out = [c for c in (row_to_candle(r) for r in reversed(rows)) if c]
    return out


async def _cycle(db) -> None:
    from services import data_hub as hub
    now_s = time.time()
    for symbol in feed_symbols():
        st = _state["symbols"].setdefault(symbol, {"seeded": False, "last_ts": {}, "bars": {}})
        c1m: List[Dict[str, Any]] = []
        for tf, ms in TF_MS.items():
            if not st["seeded"]:
                candles = await asyncio.to_thread(_fetch, db, symbol, tf, None, INITIAL_BARS[tf])
                n = hub.replace_candles(symbol, tf, candles, hub.MT5_RECORDER_SOURCE) if candles else 0
            else:
                last = st["last_ts"].get(tf)
                since = (datetime.fromtimestamp((last - OVERLAP_BARS * ms) / 1000, tz=timezone.utc).isoformat()
                         if last else None)
                candles = await asyncio.to_thread(_fetch, db, symbol, tf, since, 500)
                n = await hub.ingest_candles(symbol, tf, candles, source=hub.MT5_RECORDER_SOURCE) if candles else 0
            if candles:
                st["last_ts"][tf] = candles[-1]["timestamp"]
                st["bars"][tf] = n
            if tf == "1m":
                c1m = candles
        # Sahiplik (Yahoo'yu kapatma) YALNIZ gerçekten broker verisi geldiyse:
        # okuma boş dönerse (RLS / kaydedici durmuş) yedek eskisi gibi çalışsın.
        got = all(st["bars"].get(tf) for tf in TF_MS)
        if not st["seeded"]:
            st["seeded"] = got
            if not got:
                st["empty_reads"] = st.get("empty_reads", 0) + 1
                logger.warning("[recorder-feed] %s: %s tablosundan veri okunamadı "
                               "(RLS/anahtar?) → Yahoo yedeği sürüyor", symbol, TABLE)
                continue
        lp = latest_price(c1m, now_s)
        if lp:
            await hub.ingest_live_price(symbol, lp[0], timestamp=lp[1], source=hub.MT5_RECORDER_SOURCE)
            st["price"], st["price_ts"] = lp
        else:
            st["price_stale"] = True
        st["checked_at"] = now_s


async def start_mt5_recorder_feed() -> None:
    """Arka plan döngüsü (main.py lifespan). Kapalıysa hemen döner."""
    if not feed_enabled() or not feed_symbols():
        logger.info("[recorder-feed] kapalı")
        return
    try:
        from database.supabase_client import get_supabase_client
        db = get_supabase_client()
    except Exception as exc:
        logger.warning("[recorder-feed] Supabase yok, başlamadı: %s", exc)
        return
    if db is None:
        logger.warning("[recorder-feed] Supabase istemcisi yok, başlamadı")
        return
    _state.update(running=True, started_at=time.time())
    logger.info("[recorder-feed] başladı: %s (her %.0fs)", feed_symbols(), feed_interval())
    while True:
        try:
            await _cycle(db)
            _state["cycles"] += 1
        except Exception as exc:                       # fail-open: DataHub yedeği sürer
            _state["errors"] += 1
            _state["last_error"] = str(exc)[:300]
            logger.warning("[recorder-feed] tur hatası: %s", exc)
        await asyncio.sleep(feed_interval())


def get_feed_status() -> Dict[str, Any]:
    return {"enabled": feed_enabled(), "symbols_cfg": feed_symbols(), **_state}
