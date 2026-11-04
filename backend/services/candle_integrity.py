"""candle_cache bütünlük denetimi — karışık beslemeyi bir daha sessiz bırakmamak için.

Vaka (2026-11-04, analyst_reports/candle_cache_karisik_besleme_2026-11-04.md): Yahoo
serisi aylarca broker satırlarının üstüne yazıldı, kaydedici geçmişi 60 dk kaydırdı;
ikisi de ancak bir araştırma denetiminde fark edildi.

Her saat son pencerede üç şeye bakar: (1) yabancı seri izi (>3 ondalık), (2) broker
satırına (indicator_snapshots) göre 60 dk kayma ve genel uyumsuzluk, (3) DataHub'ın
gün-içi kaynaklarının MT5 olması. Sorun çıkınca ERROR loglar, durum değişiminde Telegram
gönderir, sonucu /api/datahub/status altında `candle_integrity` olarak verir.
Fail-open: sinyal akışını hiçbir zaman durdurmaz.
"""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from utils.safe_supabase import safe_get_data, safe_get_error

logger = logging.getLogger(__name__)

SYMBOLS = ("NDX.INDX", "XAUUSD", "GDAXI.INDX", "USOIL.FOREX")
TIMEFRAMES = ("1m", "5m")
HUB_INTRADAY_TIMEFRAMES = ("1m", "5m", "1h")
HUB_REQUIRED_SOURCE_TAG = "mt5"
SHIFT_MINUTES = 60
WINDOW_HOURS = 6
#: Yeni barlar kaydedicide henüz iki tabloya yazılmamış olabilir
SETTLE_MINUTES = 10
INTERVAL_SECONDS = 3600
STARTUP_DELAY_SECONDS = 300
PAGE_LIMIT = 1000
PRICE_SCALE = 1000
PRICE_TOLERANCE = 1e-6
SERIES_TOLERANCE = 1e-6
MAX_SHIFTED_ROWS = 3
MAX_MISMATCH_RATIO = 0.02
#: Bu kadar karşılaştırılabilir satır yoksa oran anlamsız (piyasa kapalı)
MIN_COMPARABLE_ROWS = 30

_state: Dict[str, Any] = {"ok": None, "issues": [], "checked_at": None, "last_error": None, "detail": {}}


def has_foreign_decimals(price: float) -> bool:
    scaled = float(price) * PRICE_SCALE
    return abs(scaled - round(scaled)) > PRICE_TOLERANCE


def assess_series(cache: Dict[str, float], broker: Dict[str, float]) -> Dict[str, int]:
    """cache/broker: {epoch_sn (str): kapanış}. Satır sayımlarını döndürür."""
    shift_s = SHIFT_MINUTES * 60
    foreign = shifted = mismatch = comparable = 0
    for ts, close in cache.items():
        if has_foreign_decimals(close):
            foreign += 1
        same_time = broker.get(ts)
        if same_time is None:
            continue
        comparable += 1
        if abs(close - same_time) <= SERIES_TOLERANCE:
            continue
        mismatch += 1
        earlier = broker.get(str(int(ts) - shift_s))
        if earlier is not None and abs(close - earlier) <= SERIES_TOLERANCE:
            shifted += 1
    return {"rows": len(cache), "comparable": comparable, "foreign": foreign,
            "shifted": shifted, "mismatch": mismatch}


def series_issues(symbol: str, timeframe: str, counts: Dict[str, int]) -> List[str]:
    issues: List[str] = []
    label = f"{symbol}/{timeframe}"
    if counts["foreign"]:
        issues.append(f"{label}: {counts['foreign']} satırda yabancı seri izi")
    if counts["shifted"] > MAX_SHIFTED_ROWS:
        issues.append(f"{label}: {counts['shifted']} satır {SHIFT_MINUTES} dk kayık")
    comparable = counts["comparable"]
    if comparable >= MIN_COMPARABLE_ROWS and counts["mismatch"] / comparable > MAX_MISMATCH_RATIO:
        issues.append(f"{label}: {counts['mismatch']}/{comparable} satır broker'dan farklı")
    return issues


def hub_source_issues(candle_sources: Dict[str, Dict[str, Optional[str]]],
                      price_sources: Dict[str, Optional[str]]) -> List[str]:
    issues: List[str] = []
    for symbol in SYMBOLS:
        for tf in HUB_INTRADAY_TIMEFRAMES:
            source = (candle_sources.get(symbol) or {}).get(tf) or ""
            if HUB_REQUIRED_SOURCE_TAG not in source:
                issues.append(f"hub {symbol}/{tf}: kaynak {source or 'yok'}")
        price_source = price_sources.get(symbol) or ""
        if HUB_REQUIRED_SOURCE_TAG not in price_source:
            issues.append(f"hub {symbol}: fiyat kaynağı {price_source or 'yok'}")
    return issues


def _epoch_key(candle_time: str) -> str:
    parsed = datetime.fromisoformat(str(candle_time).replace("Z", "+00:00"))
    return str(int(parsed.timestamp()))


def _fetch_closes(db, table: str, symbol: str, timeframe: str,
                  since_iso: str, until_iso: str) -> Dict[str, float]:
    result = (db.table(table).select("candle_time,close")
              .eq("symbol", symbol).eq("timeframe", timeframe)
              .gte("candle_time", since_iso).lt("candle_time", until_iso)
              .order("candle_time", desc=True).limit(PAGE_LIMIT).execute())
    if safe_get_error(result):
        raise RuntimeError(f"{table} okunamadı")
    return {_epoch_key(r["candle_time"]): float(r["close"]) for r in (safe_get_data(result) or [])}


def run_check(db) -> Dict[str, Any]:
    from services.data_hub import get_hub_status

    now = datetime.now(timezone.utc)
    until_iso = (now - timedelta(minutes=SETTLE_MINUTES)).isoformat()
    cache_since = (now - timedelta(hours=WINDOW_HOURS)).isoformat()
    broker_since = (now - timedelta(hours=WINDOW_HOURS, minutes=SHIFT_MINUTES)).isoformat()
    issues: List[str] = []
    detail: Dict[str, Any] = {}
    for symbol in SYMBOLS:
        for tf in TIMEFRAMES:
            cache = _fetch_closes(db, "candle_cache", symbol, tf, cache_since, until_iso)
            broker = _fetch_closes(db, "indicator_snapshots", symbol, tf, broker_since, until_iso)
            counts = assess_series(cache, broker)
            detail[f"{symbol}/{tf}"] = counts
            issues.extend(series_issues(symbol, tf, counts))
    status = get_hub_status()
    issues.extend(hub_source_issues(status.get("candle_sources") or {}, status.get("price_sources") or {}))
    return {"ok": not issues, "issues": issues, "detail": detail, "checked_at": now.isoformat()}


async def _notify(result: Dict[str, Any]) -> None:
    try:
        from services.telegram_service import telegram_notifier
        message = "\n".join(result["issues"]) if result["issues"] else "Tüm kontroller temiz."
        await telegram_notifier.send_market_alert("candle_cache bütünlüğü", message[:3500])
    except Exception as exc:
        logger.warning("[candle-integrity] bildirim gönderilemedi: %s", exc)


async def start_candle_integrity_loop() -> None:
    if os.getenv("CANDLE_INTEGRITY_ENABLED", "1").strip().lower() in {"0", "false", "no", "off"}:
        return
    from database.supabase_client import get_supabase_client
    await asyncio.sleep(STARTUP_DELAY_SECONDS)   # besleme hub'ı doldursun
    while True:
        try:
            db = get_supabase_client()
            result = await asyncio.to_thread(run_check, db)
            previous_ok = _state.get("ok")
            _state.update(result, last_error=None)
            if result["issues"]:
                logger.error("[candle-integrity] %d sorun: %s", len(result["issues"]), result["issues"][:10])
            if previous_ok is not None and previous_ok != result["ok"] or (previous_ok is None and not result["ok"]):
                await _notify(result)
        except Exception as exc:
            _state["last_error"] = str(exc)[:300]
            logger.warning("[candle-integrity] denetim hatası: %s", exc)
        await asyncio.sleep(INTERVAL_SECONDS)


def get_integrity_status() -> Dict[str, Any]:
    return dict(_state)
