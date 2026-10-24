"""
Market Event Service — mum bazlı "Ne oldu?" motoru.

Bir mumun (candle) zaman aralığındaki TÜM açıklayıcı bağlamı tek çatıda toplar:
  1. Mum istatistikleri + teknik anomali (ATR oranı, hacim oranı, gap, percentile)
  2. Makro bağlam (DXY/VIX/US10Y/... saatlik hareketler, sembole özel yorum)
  3. Seans bağlamı (Londra/NY açılışı, premarket, tatil/yarım gün — DST doğru)
  4. Ekonomik takvim olayları (şablon üreteci — NFP/CPI/FOMC geçmiş oluşumları)
  5. Haber (enriched_news — varsa; yoksa sessizce atlanır, fail-open)

Canlı haber akışı OLMADAN da anlamlı açıklama üretir; haber geldiğinde
(Telegram dedektörü) aynı boru hattına otomatik eklenir.

Public API (hepsi fail-open — hata durumunda boş/nötr döner, asla raise etmez):
    await get_candle_context(symbol, timestamp_s, timeframe, lang)
    await get_event_markers(symbol, hours, timeframe, max_markers)

LLM KULLANMAZ — açıklamalar deterministik kurallarla üretilir (dürüstlük ilkesi:
uydurma neden yok; kanıt yoksa "teknik akış" der). İsteğe bağlı AI cilası
router katmanında ayrıca çağrılabilir.
"""
from __future__ import annotations

import logging
import re
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ── In-memory TTL cache ───────────────────────────────────────────────────────
# Marker/context hesapları (takvim üretimi + makro tarama + 500-mum anomali
# taraması) her çağrıda tekrarlanmasın; frontend 5dk'da bir yeniler + her
# sembol/timeframe geçişinde çağırır. Kapalı mumların bağlamı değişmez.
_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}
_MARKERS_TTL_S = 60.0
_CONTEXT_TTL_S = 30.0
_CACHE_MAX_ENTRIES = 256


def _cache_get(key: str, ttl: float) -> Optional[Dict[str, Any]]:
    entry = _CACHE.get(key)
    if not entry:
        return None
    stored_at, value = entry
    if time.monotonic() - stored_at > ttl:
        _CACHE.pop(key, None)
        return None
    return value


def _cache_put(key: str, value: Dict[str, Any]) -> None:
    if len(_CACHE) >= _CACHE_MAX_ENTRIES:
        # En eskiyi at — büyümeyi sınırla (basit, kilit gerektirmez)
        oldest = min(_CACHE, key=lambda k: _CACHE[k][0])
        _CACHE.pop(oldest, None)
    _CACHE[key] = (time.monotonic(), value)


def _headline_key(title: Optional[str]) -> str:
    """Haber başlığını dedup anahtarına indirger.

    Telegram + RSS aynı haberi farklı ID/timestamp ile getirebilir ("haber
    çakışması"). Normalize edilmiş ilk 8 anlamlı kelime aynıysa aynı haber
    sayılır.
    """
    text = re.sub(r"[^a-z0-9ğüşıöçâî ]", " ", (title or "").lower())
    words = [w for w in text.split() if len(w) > 2][:8]
    return " ".join(words)


_URGENCY_WEIGHT: Dict[str, int] = {"breaking": 4, "high": 3, "medium": 2, "low": 1}


def _dedupe_news_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Başlık-benzerliği ile haber dedup — en yüksek aciliyet/skorlu kopya kalır."""
    best: Dict[str, Dict[str, Any]] = {}
    passthrough: List[Dict[str, Any]] = []
    for item in items:
        key = _headline_key(item.get("title") or item.get("headline"))
        if not key:
            passthrough.append(item)
            continue
        rank = (
            _URGENCY_WEIGHT.get(str(item.get("impact") or item.get("urgency") or ""), 0),
            float(item.get("score") or 0),
        )
        existing = best.get(key)
        if existing is None or rank > existing["_rank"]:
            best[key] = {**item, "_rank": rank}
    deduped = [{k: v for k, v in item.items() if k != "_rank"} for item in best.values()]
    return passthrough + deduped

# ── Sembol kanonikleştirme ────────────────────────────────────────────────────
SYMBOL_ALIASES: Dict[str, str] = {
    "XAUUSD": "XAUUSD", "XAU": "XAUUSD", "GOLD": "XAUUSD",
    "NDX": "NDX.INDX", "NDX.INDX": "NDX.INDX", "NASDAQ": "NDX.INDX",
    "DAX": "GDAXI.INDX", "GDAXI": "GDAXI.INDX", "GDAXI.INDX": "GDAXI.INDX",
    "USOIL": "USOIL.FOREX", "USOIL.FOREX": "USOIL.FOREX", "WTI": "USOIL.FOREX",
}

SYMBOL_DISPLAY: Dict[str, str] = {
    "XAUUSD": "Altın (XAU/USD)",
    "NDX.INDX": "NASDAQ 100",
    "GDAXI.INDX": "DAX 40",
    "USOIL.FOREX": "WTI Ham Petrol",
}

TIMEFRAME_MINUTES: Dict[str, int] = {
    "1m": 1, "5m": 5, "15m": 15, "30m": 30, "1h": 60, "4h": 240, "1d": 1440,
}

# ── Makro ilişki haritası ─────────────────────────────────────────────────────
# relation: +1 → makro yükselince sembol için yukarı baskı (direct)
#           -1 → makro yükselince sembol için aşağı baskı (inverse)
# threshold_pct: saatlik değişim bu eşiği aşarsa "anlamlı" sayılır
# weight: sürücü sıralamasında görece önem
_MACRO_RELATIONS: Dict[str, List[Dict[str, Any]]] = {
    "XAUUSD": [
        {"key": "DXY", "label": "Dolar Endeksi (DXY)", "relation": -1, "threshold_pct": 0.22, "weight": 1.0,
         "note_tr": "Dolar {dir_tr} — altın üzerinde {press_tr} baskı",
         "note_en": "Dollar {dir_en} — {press_en} pressure on gold"},
        {"key": "US10Y", "label": "ABD 10Y Tahvil Faizi", "relation": -1, "threshold_pct": 1.2, "weight": 0.9,
         "note_tr": "10 yıllık faiz {dir_tr} — faiz getirmeyen altın için {press_tr}",
         "note_en": "10-year yield {dir_en} — {press_en} for non-yielding gold"},
        {"key": "VIX", "label": "VIX (Korku Endeksi)", "relation": 1, "threshold_pct": 3.0, "weight": 0.8,
         "note_tr": "VIX {dir_tr} — güvenli liman talebi {press2_tr}",
         "note_en": "VIX {dir_en} — safe-haven demand {press2_en}"},
    ],
    "NDX.INDX": [
        {"key": "VIX", "label": "VIX (Korku Endeksi)", "relation": -1, "threshold_pct": 3.0, "weight": 1.0,
         "note_tr": "VIX {dir_tr} — risk iştahı {press2_ters_tr}, teknoloji hisselerine {press_tr} baskı",
         "note_en": "VIX {dir_en} — risk appetite {press2_ters_en}, {press_en} pressure on tech"},
        {"key": "US10Y", "label": "ABD 10Y Tahvil Faizi", "relation": -1, "threshold_pct": 1.2, "weight": 0.9,
         "note_tr": "10 yıllık faiz {dir_tr} — büyüme hisseleri için {press_tr}",
         "note_en": "10-year yield {dir_en} — {press_en} for growth stocks"},
        {"key": "SPX", "label": "S&P 500", "relation": 1, "threshold_pct": 0.35, "weight": 0.7,
         "note_tr": "Geniş endeks (S&P 500) {dir_tr} — piyasa geneli {dir2_tr} yönlü",
         "note_en": "Broad market (S&P 500) {dir_en} — overall tape {dir2_en}"},
        {"key": "USDJPY", "label": "USD/JPY (Carry)", "relation": 1, "threshold_pct": 0.45, "weight": 0.5,
         "note_tr": "USD/JPY {dir_tr} — carry-trade akışı {dir2_tr} yönde",
         "note_en": "USD/JPY {dir_en} — carry-trade flow {dir2_en}"},
    ],
    "GDAXI.INDX": [
        {"key": "STOXX", "label": "Euro Stoxx 50", "relation": 1, "threshold_pct": 0.35, "weight": 1.0,
         "note_tr": "Avrupa endeksleri (Stoxx 50) {dir_tr} — bölgesel akış {dir2_tr}",
         "note_en": "European indices (Stoxx 50) {dir_en} — regional flow {dir2_en}"},
        {"key": "VIX", "label": "VIX (Korku Endeksi)", "relation": -1, "threshold_pct": 3.0, "weight": 0.8,
         "note_tr": "VIX {dir_tr} — küresel risk iştahı {press2_ters_tr}",
         "note_en": "VIX {dir_en} — global risk appetite {press2_ters_en}"},
        {"key": "EURUSD", "label": "EUR/USD", "relation": -1, "threshold_pct": 0.28, "weight": 0.6,
         "note_tr": "Euro {dir_tr} — ihracatçı ağırlıklı DAX için {press_tr}",
         "note_en": "Euro {dir_en} — {press_en} for export-heavy DAX"},
        {"key": "SPX", "label": "S&P 500", "relation": 1, "threshold_pct": 0.35, "weight": 0.6,
         "note_tr": "ABD piyasası (S&P 500) {dir_tr} — küresel sentiment {dir2_tr}",
         "note_en": "US market (S&P 500) {dir_en} — global sentiment {dir2_en}"},
    ],
    "USOIL.FOREX": [
        {"key": "DXY", "label": "Dolar Endeksi (DXY)", "relation": -1, "threshold_pct": 0.22, "weight": 0.9,
         "note_tr": "Dolar {dir_tr} — dolarla fiyatlanan petrol için {press_tr}",
         "note_en": "Dollar {dir_en} — {press_en} for dollar-priced oil"},
        {"key": "COPPER", "label": "Bakır (Büyüme Vekili)", "relation": 1, "threshold_pct": 0.6, "weight": 0.7,
         "note_tr": "Bakır {dir_tr} — küresel talep beklentisi {dir2_tr}",
         "note_en": "Copper {dir_en} — global demand outlook {dir2_en}"},
        {"key": "SPX", "label": "S&P 500", "relation": 1, "threshold_pct": 0.35, "weight": 0.6,
         "note_tr": "Risk iştahı (S&P 500) {dir_tr} — emtia talebine {dir2_tr} yansıma",
         "note_en": "Risk appetite (S&P 500) {dir_en} — {dir2_en} read-through to commodities"},
        {"key": "VIX", "label": "VIX (Korku Endeksi)", "relation": -1, "threshold_pct": 3.5, "weight": 0.5,
         "note_tr": "VIX {dir_tr} — riskli varlıklardan {press2_ters_tr} kaçış",
         "note_en": "VIX {dir_en} — risk-asset flows {press2_ters_en}"},
    ],
}

# Büyüklük sınıflandırma eşikleri (range/ATR oranı)
_MAGNITUDE_LEVELS: List[Tuple[float, str, str, str]] = [
    (3.0, "extreme", "olağandışı büyük", "exceptionally large"),
    (2.0, "big", "büyük", "large"),
    (1.3, "notable", "belirgin", "notable"),
    (0.0, "minor", "olağan", "ordinary"),
]

_SESSION_META: Dict[str, Dict[str, str]] = {
    "us_regular": {"emoji": "🇺🇸", "tr": "New York Seansı", "en": "New York Session"},
    "us_premarket": {"emoji": "🌅", "tr": "ABD Premarket", "en": "US Pre-Market"},
    "us_afterhours": {"emoji": "🌙", "tr": "ABD Kapanış Sonrası", "en": "US After-Hours"},
    "london": {"emoji": "🇬🇧", "tr": "Londra Seansı", "en": "London Session"},
    "asia": {"emoji": "🌏", "tr": "Asya Seansı", "en": "Asia Session"},
    "closed": {"emoji": "🔒", "tr": "Piyasa Kapalı", "en": "Market Closed"},
}


def canonical_symbol(symbol: str) -> str:
    """Frontend/legacy sembol adlarını DataHub kanonik adına çevirir."""
    return SYMBOL_ALIASES.get((symbol or "").strip().upper(), (symbol or "").strip().upper())


def _timeframe_minutes(timeframe: str) -> int:
    return TIMEFRAME_MINUTES.get((timeframe or "1h").strip().lower(), 60)


def _classify_magnitude(range_vs_atr: Optional[float]) -> Tuple[str, str, str]:
    """(kod, tr, en) — mum büyüklüğü sınıfı."""
    value = range_vs_atr if range_vs_atr is not None else 0.0
    for threshold, code, label_tr, label_en in _MAGNITUDE_LEVELS:
        if value >= threshold:
            return code, label_tr, label_en
    return "minor", "olağan", "ordinary"


def _find_candle_index(candles: List[Dict[str, Any]], target_ms: int, tf_minutes: int) -> int:
    """Hedef zaman damgasının düştüğü mumun index'i; bulunamazsa -1."""
    tf_ms = tf_minutes * 60_000
    best_idx, best_dist = -1, None
    for idx, candle in enumerate(candles):
        ts = int(candle.get("timestamp", 0) or 0)
        if ts <= 0:
            continue
        if ts <= target_ms < ts + tf_ms:
            return idx
        dist = abs(ts - target_ms)
        if best_dist is None or dist < best_dist:
            best_idx, best_dist = idx, dist
    # Tam bucket bulunamadıysa en yakın mumu kabul et (yarım timeframe toleransla)
    if best_idx >= 0 and best_dist is not None and best_dist <= tf_ms:
        return best_idx
    return -1


def _true_range(candle: Dict[str, Any], prev_close: Optional[float]) -> float:
    high = float(candle.get("high", 0) or 0)
    low = float(candle.get("low", 0) or 0)
    if prev_close is None or prev_close <= 0:
        return max(0.0, high - low)
    return max(high - low, abs(high - prev_close), abs(low - prev_close))


def _compute_technicals(candles: List[Dict[str, Any]], idx: int) -> Dict[str, Any]:
    """Seçili mumun teknik anomali istatistikleri (ATR20, hacim, gap, percentile)."""
    candle = candles[idx]
    open_p = float(candle.get("open", 0) or 0)
    high_p = float(candle.get("high", 0) or 0)
    low_p = float(candle.get("low", 0) or 0)
    close_p = float(candle.get("close", 0) or 0)
    volume = float(candle.get("volume", 0) or 0)

    change_pct = ((close_p - open_p) / open_p * 100) if open_p else 0.0
    range_pct = ((high_p - low_p) / open_p * 100) if open_p else 0.0

    # ATR(20) — seçili mumdan ÖNCEKİ 20 mum (kendisi dahil edilmez: sızıntısız)
    atr = None
    lookback = candles[max(0, idx - 20):idx]
    if len(lookback) >= 5:
        trs: List[float] = []
        for j, c in enumerate(lookback):
            prev_close = float(lookback[j - 1].get("close", 0) or 0) if j > 0 else None
            trs.append(_true_range(c, prev_close))
        if trs:
            atr = sum(trs) / len(trs)

    candle_range = max(0.0, high_p - low_p)
    range_vs_atr = (candle_range / atr) if atr and atr > 0 else None

    # Range percentile — önceki 100 muma göre
    range_percentile = None
    window = candles[max(0, idx - 100):idx]
    if len(window) >= 20:
        ranges = sorted(
            max(0.0, float(c.get("high", 0) or 0) - float(c.get("low", 0) or 0))
            for c in window
        )
        below = sum(1 for r in ranges if r <= candle_range)
        range_percentile = round(below / len(ranges) * 100)

    # Hacim oranı — önceki 20 mum ortalamasına göre
    volume_ratio = None
    vol_window = [float(c.get("volume", 0) or 0) for c in candles[max(0, idx - 20):idx]]
    vol_window = [v for v in vol_window if v > 0]
    if vol_window and volume > 0:
        avg_vol = sum(vol_window) / len(vol_window)
        if avg_vol > 0:
            volume_ratio = round(volume / avg_vol, 2)

    # Gap — önceki kapanışa göre açılış farkı
    gap_pct = None
    if idx > 0:
        prev_close = float(candles[idx - 1].get("close", 0) or 0)
        if prev_close > 0 and open_p > 0:
            gap_pct = round((open_p - prev_close) / prev_close * 100, 3)

    body = abs(close_p - open_p)
    body_ratio = round(body / candle_range, 2) if candle_range > 0 else None

    magnitude_code, magnitude_tr, magnitude_en = _classify_magnitude(range_vs_atr)

    return {
        "open": open_p, "high": high_p, "low": low_p, "close": close_p,
        "volume": volume,
        "change_pct": round(change_pct, 3),
        "range_pct": round(range_pct, 3),
        "direction": "up" if change_pct > 0 else "down" if change_pct < 0 else "flat",
        "atr20": round(atr, 5) if atr else None,
        "range_vs_atr": round(range_vs_atr, 2) if range_vs_atr is not None else None,
        "range_percentile": range_percentile,
        "volume_ratio": volume_ratio,
        "gap_pct": gap_pct,
        "body_ratio": body_ratio,
        "magnitude": magnitude_code,
        "magnitude_tr": magnitude_tr,
        "magnitude_en": magnitude_en,
        "is_significant": bool(
            (range_vs_atr is not None and range_vs_atr >= 1.3)
            or abs(change_pct) >= 0.5
            or (volume_ratio is not None and volume_ratio >= 2.0)
        ),
    }


def _macro_window_change(
    df: Any, start_utc: datetime, end_utc: datetime
) -> Tuple[Optional[float], List[float]]:
    """Makro H1 serisinden [start, end] penceresi % değişimi + sparkline noktaları."""
    try:
        if df is None or df.empty:
            return None, []
        closes = df["close"]
        idx = df.index
        # Referans = pencere başlangıcından ÖNCEKİ son kapanış.
        # Pencere = [start, end) — bar-start etiketli H1 serilerde mumun kendi
        # saatindeki bar dahil edilir (dışlanırsa overnight gap'ler kaçar).
        before_mask = idx < start_utc
        window_mask = (idx >= start_utc) & (idx < end_utc)
        if not before_mask.any():
            return None, []
        ref = float(closes[before_mask].iloc[-1])
        if ref == 0:
            return None, []
        in_window = closes[window_mask]
        last = float(in_window.iloc[-1]) if len(in_window) else ref
        change = (last - ref) / ref * 100

        # Sparkline: pencere + öncesinden toplam ~12 nokta
        spark_mask = (idx > start_utc - timedelta(hours=9)) & (idx < end_utc)
        spark = [round(float(v), 4) for v in closes[spark_mask].tail(12)]
        return round(change, 3), spark
    except Exception:
        logger.debug("[MarketEvent] macro window change failed", exc_info=True)
        return None, []


def _build_macro_context(
    symbol: str, start_utc: datetime, end_utc: datetime
) -> List[Dict[str, Any]]:
    """Sembole özel makro sürücü listesi — pencere içi hareket + etki yorumu."""
    relations = _MACRO_RELATIONS.get(symbol, [])
    if not relations:
        return []

    try:
        from services import macro_data_service
    except Exception:
        return []

    results: List[Dict[str, Any]] = []
    for rel in relations:
        try:
            df = macro_data_service.get_history(rel["key"], "H1")
            change_pct, spark = _macro_window_change(df, start_utc, end_utc)
            if change_pct is None:
                continue

            significant = abs(change_pct) >= rel["threshold_pct"]
            if change_pct == 0:
                # Bayat/yatay seri — yanıltıcı "geriledi" metni üretme
                continue
            rising = change_pct > 0
            # Sembole etkisi: relation * hareket yönü (ham işaret metin kalıplarında,
            # eşik-altı hareket etki alanında "neutral" olarak raporlanır)
            impact_sign = rel["relation"] * (1 if rising else -1)
            raw_impact = "bullish" if impact_sign > 0 else "bearish" if impact_sign < 0 else "neutral"
            impact = raw_impact
            if abs(change_pct) < rel["threshold_pct"] * 0.4:
                impact = "neutral"

            fmt = {
                "dir_tr": "yükseldi" if rising else "geriledi",
                "dir_en": "rose" if rising else "fell",
                "dir2_tr": "pozitif" if rising else "negatif",
                "dir2_en": "positive" if rising else "negative",
                "press_tr": "aşağı yönlü" if raw_impact == "bearish" else "yukarı yönlü",
                "press_en": "downward" if raw_impact == "bearish" else "upward",
                "press2_tr": "arttı" if raw_impact == "bullish" else "azaldı",
                "press2_en": "increased" if raw_impact == "bullish" else "decreased",
                "press2_ters_tr": "azaldı" if raw_impact == "bearish" else "arttı",
                "press2_ters_en": "decreased" if raw_impact == "bearish" else "increased",
            }
            results.append({
                "key": rel["key"],
                "label": rel["label"],
                "change_pct": change_pct,
                "direction": "up" if rising else "down",
                "impact_on_symbol": impact,
                "is_significant": significant,
                "weight": rel["weight"],
                "note_tr": rel["note_tr"].format(**fmt),
                "note_en": rel["note_en"].format(**fmt),
                "sparkline": spark,
            })
        except Exception:
            logger.debug("[MarketEvent] macro relation %s failed", rel.get("key"), exc_info=True)
            continue

    # Anlamlı olanlar önce, sonra ağırlık × büyüklük
    results.sort(
        key=lambda m: (m["is_significant"], m["weight"] * abs(m["change_pct"])),
        reverse=True,
    )
    return results


def _build_session_context(start_utc: datetime) -> Dict[str, Any]:
    """Seans etiketi + açılış yakınlığı bilgisi (DST doğru)."""
    try:
        from services.session_context_service import get_session_context
        ctx = get_session_context(start_utc)
    except Exception:
        logger.debug("[MarketEvent] session context failed", exc_info=True)
        return {}

    session = str(ctx.get("current_session") or "closed")
    meta = _SESSION_META.get(session, _SESSION_META["closed"])
    minutes_to_open = ctx.get("minutes_to_us_open")

    proximity_tr = proximity_en = None
    if isinstance(minutes_to_open, (int, float)):
        m = int(minutes_to_open)
        if 0 < m <= 45:
            proximity_tr = f"NY açılışına {m} dk"
            proximity_en = f"{m}m to NY open"
        elif -45 <= m <= 0:
            proximity_tr = f"NY açılışından {abs(m)} dk sonra"
            proximity_en = f"{abs(m)}m after NY open"

    return {
        "session": session,
        "emoji": meta["emoji"],
        "label_tr": meta["tr"],
        "label_en": meta["en"],
        "ny_time": ctx.get("ny_time"),
        "is_holiday": bool(ctx.get("is_holiday")),
        "is_half_day": bool(ctx.get("is_half_day")),
        "session_overlap": bool(ctx.get("session_overlap")),
        "open_proximity_tr": proximity_tr,
        "open_proximity_en": proximity_en,
    }


def _fetch_calendar_events(
    symbol: str, start_utc: datetime, end_utc: datetime, pad_minutes: int = 45
) -> List[Dict[str, Any]]:
    """Mum penceresine (± pad) düşen ekonomik takvim + bilanço olayları."""
    try:
        from routers.economic_calendar_router import (
            generate_earnings_events_between,
            generate_economic_events_between,
        )
        from services.news_candle_matcher import symbols_match
    except Exception:
        logger.debug("[MarketEvent] calendar import failed", exc_info=True)
        return []

    window_start = start_utc - timedelta(minutes=pad_minutes)
    window_end = end_utc + timedelta(minutes=pad_minutes)
    events: List[Dict[str, Any]] = []

    try:
        for event in generate_economic_events_between(window_start, window_end):
            affected = event.get("affected_symbols") or []
            if affected and not any(symbols_match(symbol, s) for s in affected):
                continue
            events.append({
                "type": "economic",
                "id": event.get("id"),
                "timestamp": event.get("timestamp"),
                "title": event.get("title"),
                "title_tr": event.get("title_tr") or event.get("title"),
                "impact": event.get("impact"),
                "direction": event.get("predicted_direction", "neutral"),
                "detail_tr": event.get("impact_analysis_tr") or event.get("why_it_matters_tr") or "",
                "detail_en": event.get("impact_analysis") or event.get("why_it_matters") or "",
                "forecast": event.get("forecast"),
                "previous": event.get("previous"),
            })
    except Exception:
        logger.debug("[MarketEvent] economic events failed", exc_info=True)

    try:
        for event in generate_earnings_events_between(window_start, window_end):
            affected = event.get("affected_symbols") or []
            if affected and not any(symbols_match(symbol, s) for s in affected):
                continue
            events.append({
                "type": "earnings",
                "id": event.get("id"),
                "timestamp": event.get("timestamp"),
                "title": f"{event.get('company') or event.get('ticker')} Bilanço",
                "title_tr": f"{event.get('company_tr') or event.get('company') or event.get('ticker')} Bilanço",
                "impact": "High",
                "direction": event.get("predicted_direction", "neutral"),
                "detail_tr": event.get("analysis_tr") or "",
                "detail_en": event.get("analysis") or "",
                "forecast": event.get("eps_forecast"),
                "previous": event.get("previous_eps"),
            })
    except Exception:
        logger.debug("[MarketEvent] earnings events failed", exc_info=True)

    events.sort(key=lambda e: str(e.get("timestamp") or ""))
    return events


def _fetch_news_events(
    symbol: str, start_utc: datetime, end_utc: datetime, pad_minutes: int = 30
) -> List[Dict[str, Any]]:
    """enriched_news tablosundan pencereye düşen haberler (tablo boşsa []).

    Haber akışı henüz bağlı değil — Telegram dedektörü geldiğinde bu sorgu
    otomatik olarak sonuç döndürmeye başlar; kod değişikliği gerekmez.
    """
    try:
        from database.supabase_client import get_supabase_client
        from services.news_candle_matcher import get_matching_impact

        supabase = get_supabase_client()
        if supabase is None:
            return []

        # select("*"): Telegram entegrasyonunda şema değişirse sabit kolon
        # listesi sorguyu kırmasın (eksik kolonlar aşağıda .get ile toleranslı)
        result = (
            supabase.table("enriched_news")
            .select("*")
            .gte("timestamp", (start_utc - timedelta(minutes=pad_minutes)).isoformat())
            .lte("timestamp", (end_utc + timedelta(minutes=pad_minutes)).isoformat())
            .order("timestamp", desc=True)
            .limit(20)
            .execute()
        )
        rows = result.data if hasattr(result, "data") else (result or {}).get("data", [])
        news: List[Dict[str, Any]] = []
        for row in rows or []:
            impact = get_matching_impact(row.get("impacts", []), symbol)
            if not impact:
                continue
            news.append({
                "type": "news",
                "id": row.get("id"),
                "timestamp": row.get("timestamp"),
                "title": row.get("headline"),
                "title_tr": row.get("headline_tr") or row.get("headline"),
                "impact": row.get("urgency", "medium"),
                "direction": impact.get("direction", "neutral"),
                "detail_tr": impact.get("reasoning_tr") or row.get("summary_tr") or "",
                "detail_en": impact.get("reasoning") or row.get("summary_en") or "",
                "score": impact.get("score"),
                "url": row.get("url"),
                "source": row.get("source"),
            })
        # Çok-kaynak (RSS + Telegram) aynı haberi tekrarlayabilir → başlık dedup
        return _dedupe_news_items(news)
    except Exception:
        logger.debug("[MarketEvent] news fetch skipped (fail-open)", exc_info=True)
        return []


def _compose_explanation(
    symbol: str,
    tech: Dict[str, Any],
    session: Dict[str, Any],
    macro: List[Dict[str, Any]],
    events: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Deterministik TR/EN açıklama — kanıt yoksa uydurmaz, 'teknik akış' der."""
    display = SYMBOL_DISPLAY.get(symbol, symbol)
    direction = tech.get("direction", "flat")
    change_pct = tech.get("change_pct", 0.0)
    move_tr = "yükseldi" if direction == "up" else "geriledi" if direction == "down" else "yatay kaldı"
    move_en = "rose" if direction == "up" else "fell" if direction == "down" else "was flat"

    bullets_tr: List[str] = []
    bullets_en: List[str] = []
    sources: List[str] = []
    confidence = 25  # taban: sadece teknik gözlem

    # 1) Haber + takvim olayları (en güçlü kanıt)
    news_events = [e for e in events if e["type"] == "news"]
    cal_events = [e for e in events if e["type"] in ("economic", "earnings")]

    for ev in news_events[:3]:
        title = ev.get("title_tr") or ev.get("title") or ""
        bullets_tr.append(f"📰 {title}" + (f" — {ev['detail_tr']}" if ev.get("detail_tr") else ""))
        bullets_en.append(f"📰 {ev.get('title') or title}" + (f" — {ev['detail_en']}" if ev.get("detail_en") else ""))
        sources.append("news")
        confidence = max(confidence, 70)

    for ev in cal_events[:3]:
        icon = "📅" if ev["type"] == "economic" else "💼"
        title_tr = ev.get("title_tr") or ev.get("title") or ""
        extra_tr = f" — {ev['detail_tr']}" if ev.get("detail_tr") else ""
        extra_en = f" — {ev['detail_en']}" if ev.get("detail_en") else ""
        bullets_tr.append(f"{icon} {title_tr} bu mumun zaman aralığına denk geldi{extra_tr}")
        bullets_en.append(f"{icon} {ev.get('title') or title_tr} landed in this candle's window{extra_en}")
        sources.append(ev["type"])
        confidence = max(confidence, 60)

    # 2) Makro sürücüler — sadece mumun yönüyle TUTARLI + anlamlı olanlar öne
    aligned = [
        m for m in macro
        if m["is_significant"] and (
            (direction == "up" and m["impact_on_symbol"] == "bullish")
            or (direction == "down" and m["impact_on_symbol"] == "bearish")
        )
    ]
    conflicting = [
        m for m in macro
        if m["is_significant"] and m["impact_on_symbol"] != "neutral" and m not in aligned
    ]

    for m in aligned[:3]:
        sign = "+" if m["change_pct"] > 0 else ""
        bullets_tr.append(f"🌐 {m['label']} {sign}{m['change_pct']}% — {m['note_tr']}")
        bullets_en.append(f"🌐 {m['label']} {sign}{m['change_pct']}% — {m['note_en']}")
        sources.append(f"macro:{m['key']}")
        confidence = max(confidence, 45 + min(20, int(abs(m["change_pct"]) * 10)))

    if conflicting and not aligned and not news_events and not cal_events:
        m = conflicting[0]
        sign = "+" if m["change_pct"] > 0 else ""
        bullets_tr.append(
            f"⚠️ {m['label']} {sign}{m['change_pct']}% hareket etti ama mumun yönüyle çelişiyor — "
            "hareket makro kaynaklı görünmüyor"
        )
        bullets_en.append(
            f"⚠️ {m['label']} moved {sign}{m['change_pct']}% but conflicts with the candle direction — "
            "the move doesn't look macro-driven"
        )
        sources.append(f"macro-conflict:{m['key']}")

    # 3) Seans bağlamı
    if session:
        if session.get("open_proximity_tr"):
            bullets_tr.append(f"⏰ {session['open_proximity_tr']} — açılış volatilitesi tipiktir")
            bullets_en.append(f"⏰ {session['open_proximity_en']} — opening volatility is typical")
            sources.append("session")
            confidence = max(confidence, 40)
        if session.get("is_half_day"):
            bullets_tr.append("📆 Yarım gün (erken kapanış) — likidite ince")
            bullets_en.append("📆 Half trading day (early close) — thin liquidity")
            sources.append("session")

    # 4) Teknik gözlemler
    tech_parts_tr: List[str] = []
    tech_parts_en: List[str] = []
    rva = tech.get("range_vs_atr")
    if rva is not None:
        tech_parts_tr.append(f"mum aralığı 20-mum ATR'nin {rva}×'i")
        tech_parts_en.append(f"candle range is {rva}× the 20-bar ATR")
    if tech.get("range_percentile") is not None and tech["range_percentile"] >= 80:
        tech_parts_tr.append(f"son 100 mumun %{tech['range_percentile']}'inden büyük")
        tech_parts_en.append(f"larger than {tech['range_percentile']}% of the last 100 bars")
    vr = tech.get("volume_ratio")
    if vr is not None and vr >= 1.5:
        tech_parts_tr.append(f"hacim ortalamanın {vr}×'i")
        tech_parts_en.append(f"volume ran {vr}× average")
    gap = tech.get("gap_pct")
    if gap is not None and abs(gap) >= 0.15:
        gap_dir_tr = "yukarı" if gap > 0 else "aşağı"
        gap_dir_en = "up" if gap > 0 else "down"
        tech_parts_tr.append(f"%{abs(gap)} {gap_dir_tr} gap ile açıldı")
        tech_parts_en.append(f"opened with a {abs(gap)}% gap {gap_dir_en}")

    def _sentence(parts: List[str]) -> str:
        if not parts:
            return ""
        joined = "; ".join(parts)
        return joined[0].upper() + joined[1:] + "."

    technical_tr = _sentence(tech_parts_tr)
    technical_en = _sentence(tech_parts_en)

    # 5) Hiç katalizör yoksa dürüst kapanış
    if not bullets_tr:
        bullets_tr.append(
            "🔍 Bu zaman aralığında bilinen bir haber/makro katalizör tespit edilmedi — "
            "hareket pozisyonlama, likidite veya teknik akış kaynaklı olabilir"
        )
        bullets_en.append(
            "🔍 No known news/macro catalyst was detected in this window — "
            "the move may reflect positioning, liquidity, or technical flow"
        )
        sources.append("technical_flow")

    magnitude_tr = tech.get("magnitude_tr", "olağan")
    magnitude_en = tech.get("magnitude_en", "ordinary")
    summary_tr = (
        f"{display} bu mumda %{abs(change_pct):.2f} {move_tr} — {magnitude_tr} bir hareket."
    )
    summary_en = (
        f"{display} {move_en} {abs(change_pct):.2f}% in this candle — a(n) {magnitude_en} move."
    )

    return {
        "summary_tr": summary_tr,
        "summary_en": summary_en,
        "bullets_tr": bullets_tr,
        "bullets_en": bullets_en,
        "technical_tr": technical_tr,
        "technical_en": technical_en,
        "confidence": min(95, confidence),
        "sources": sorted(set(sources)),
    }


async def get_candle_context(
    symbol: str,
    timestamp_s: int,
    timeframe: str = "1h",
    lang: str = "tr",
) -> Dict[str, Any]:
    """Bir mumun tam 'Ne oldu?' bağlamını üretir.

    Args:
        symbol: Sembol (frontend adları da kabul: NDX, DAX, XAUUSD, USOIL).
        timestamp_s: Mumun UNIX saniye zaman damgası (mum açılışı).
        timeframe: Mum periyodu (5m/15m/30m/1h/4h/1d).
        lang: Tercih dili (tr/en) — her iki dil de payload'da döner.

    Returns:
        Fail-open dict; success=False yalnızca mum hiç bulunamazsa.
    """
    sym = canonical_symbol(symbol)
    tf_minutes = _timeframe_minutes(timeframe)
    target_ms = int(timestamp_s) * 1000

    cache_key = f"ctx:{sym}:{timestamp_s}:{timeframe}"
    cached = _cache_get(cache_key, _CONTEXT_TTL_S)
    if cached is not None:
        return cached

    try:
        from services.data_fetcher import fetch_ohlc_data
        candles = await fetch_ohlc_data(sym, timeframe=timeframe.lower(), limit=500)
    except Exception:
        logger.exception("[MarketEvent] candle fetch failed for %s", sym)
        candles = []

    if not candles:
        return {"success": False, "error": "no_candle_data", "symbol": sym}

    idx = _find_candle_index(candles, target_ms, tf_minutes)
    if idx < 0:
        return {"success": False, "error": "candle_not_found", "symbol": sym}

    candle = candles[idx]
    start_utc = datetime.fromtimestamp(int(candle["timestamp"]) / 1000, tz=timezone.utc)
    end_utc = start_utc + timedelta(minutes=tf_minutes)

    tech = _compute_technicals(candles, idx)
    session = _build_session_context(start_utc)
    macro = _build_macro_context(sym, start_utc, end_utc)
    events = _fetch_calendar_events(sym, start_utc, end_utc)
    events = _fetch_news_events(sym, start_utc, end_utc) + events
    explanation = _compose_explanation(sym, tech, session, macro, events)

    result = {
        "success": True,
        "symbol": sym,
        "symbol_display": SYMBOL_DISPLAY.get(sym, sym),
        "timeframe": timeframe,
        "candle": {
            "timestamp": int(candle["timestamp"]) // 1000,
            "start_utc": start_utc.isoformat(),
            "end_utc": end_utc.isoformat(),
            **{k: tech[k] for k in ("open", "high", "low", "close", "volume",
                                      "change_pct", "range_pct", "direction", "gap_pct")},
        },
        "significance": {
            "is_significant": tech["is_significant"],
            "magnitude": tech["magnitude"],
            "magnitude_tr": tech["magnitude_tr"],
            "magnitude_en": tech["magnitude_en"],
            "range_vs_atr": tech["range_vs_atr"],
            "range_percentile": tech["range_percentile"],
            "volume_ratio": tech["volume_ratio"],
            "body_ratio": tech["body_ratio"],
        },
        "session": session,
        "macro": macro,
        "events": events,
        "explanation": explanation,
    }
    _cache_put(cache_key, result)
    return result


# ── Marker üretimi ────────────────────────────────────────────────────────────

_MACRO_SPIKE_THRESHOLDS: Dict[str, float] = {
    "DXY": 0.35, "VIX": 5.0, "US10Y": 2.0, "SPX": 0.8,
    "STOXX": 0.9, "EURUSD": 0.4, "COPPER": 1.2, "USDJPY": 0.6,
}


def _macro_spike_markers(
    symbol: str, start_utc: datetime, end_utc: datetime, limit: int = 20
) -> List[Dict[str, Any]]:
    """Sembolle ilişkili makro serilerde saatlik 'spike' işaretçileri."""
    relations = _MACRO_RELATIONS.get(symbol, [])
    if not relations:
        return []
    try:
        from services import macro_data_service
    except Exception:
        return []

    markers: List[Dict[str, Any]] = []
    for rel in relations:
        key = rel["key"]
        threshold = _MACRO_SPIKE_THRESHOLDS.get(key, rel["threshold_pct"] * 1.6)
        try:
            df = macro_data_service.get_history(key, "H1")
            if df is None or df.empty or len(df) < 2:
                continue
            closes = df["close"]
            window = closes[(df.index >= start_utc) & (df.index <= end_utc)]
            before = closes[df.index < start_utc]
            prev = float(before.iloc[-1]) if len(before) else None
            for ts, value in window.items():
                if prev is not None and prev != 0:
                    change = (float(value) - prev) / prev * 100
                    if abs(change) >= threshold:
                        rising = change > 0
                        impact_sign = rel["relation"] * (1 if rising else -1)
                        direction = "bullish" if impact_sign > 0 else "bearish"
                        markers.append({
                            "id": f"macro:{key}:{int(ts.timestamp())}",
                            "time": ts.isoformat(),
                            "position": "belowBar" if direction == "bullish" else "aboveBar",
                            "color": "#38bdf8",
                            "shape": "circle",
                            "text": "⚡",
                            "size": 1.4,
                            "headline": f"{rel['label']} {'+' if rising else ''}{change:.2f}% (1s)",
                            "headline_en": f"{rel['label']} {'+' if rising else ''}{change:.2f}% (1h)",
                            "direction": direction,
                            "score": min(10, max(5, round(abs(change) / threshold * 5))),
                            "urgency": "high" if abs(change) >= threshold * 1.6 else "medium",
                            "catalyst_type": "macro",
                            "is_economic_event": False,
                            "is_earnings_event": False,
                            "event_name": f"{key} spike",
                            "event_id": None,
                            "reasoning_tr": rel["note_tr"].format(
                                dir_tr="yükseldi" if rising else "geriledi",
                                dir_en="rose" if rising else "fell",
                                dir2_tr="pozitif" if rising else "negatif",
                                dir2_en="positive" if rising else "negative",
                                press_tr="aşağı yönlü" if direction == "bearish" else "yukarı yönlü",
                                press_en="downward" if direction == "bearish" else "upward",
                                press2_tr="arttı" if direction == "bullish" else "azaldı",
                                press2_en="increased" if direction == "bullish" else "decreased",
                                press2_ters_tr="azaldı" if direction == "bearish" else "arttı",
                                press2_ters_en="decreased" if direction == "bearish" else "increased",
                            ),
                            "importance_level": "high" if abs(change) >= threshold * 1.6 else "medium",
                            "importance_score": min(95, int(60 + abs(change) / threshold * 15)),
                            "importance_reason": None,
                            "ai_confidence": 0,
                            "url": "",
                        })
                prev = float(value)
        except Exception:
            logger.debug("[MarketEvent] spike scan failed for %s", key, exc_info=True)
            continue

    markers.sort(key=lambda m: m.get("importance_score", 0), reverse=True)
    return markers[:limit]


async def _anomaly_markers(
    symbol: str, timeframe: str, start_utc: datetime, limit: int = 12
) -> List[Dict[str, Any]]:
    """Sembolün kendi mumlarında büyük-hareket (range ≥ 2.2×ATR20) işaretçileri."""
    try:
        from services.data_fetcher import fetch_ohlc_data
        candles = await fetch_ohlc_data(symbol, timeframe=timeframe.lower(), limit=500)
    except Exception:
        return []
    if len(candles) < 30:
        return []

    start_ms = int(start_utc.timestamp() * 1000)
    markers: List[Dict[str, Any]] = []
    for idx in range(21, len(candles)):
        candle = candles[idx]
        ts = int(candle.get("timestamp", 0) or 0)
        if ts < start_ms:
            continue
        tech = _compute_technicals(candles, idx)
        rva = tech.get("range_vs_atr")
        if rva is None or rva < 2.2:
            continue
        direction = tech.get("direction", "flat")
        dt = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
        change = tech.get("change_pct", 0)
        markers.append({
            "id": f"anomaly:{symbol}:{ts}",
            "time": dt.isoformat(),
            "position": "belowBar" if direction == "up" else "aboveBar",
            "color": "#a78bfa",
            "shape": "circle",
            "text": "💥",
            "size": 1.5,
            "headline": f"Olağandışı mum: %{abs(change):.2f} ({rva}× ATR)",
            "headline_en": f"Unusual candle: {abs(change):.2f}% ({rva}× ATR)",
            "direction": "bullish" if direction == "up" else "bearish",
            "score": min(10, max(6, round(rva * 2.5))),
            "urgency": "high" if rva >= 3.0 else "medium",
            "catalyst_type": "anomaly",
            "is_economic_event": False,
            "is_earnings_event": False,
            "event_name": "Volatility anomaly",
            "event_id": None,
            "reasoning_tr": f"Mum aralığı 20-mum ATR'nin {rva} katı — sıra dışı volatilite. Tıklayıp katalizörü inceleyin.",
            "importance_level": "high" if rva >= 3.0 else "medium",
            "importance_score": min(95, int(55 + rva * 10)),
            "importance_reason": None,
            "ai_confidence": 0,
            "url": "",
        })

    markers.sort(key=lambda m: m.get("importance_score", 0), reverse=True)
    return markers[:limit]


async def get_event_markers(
    symbol: str,
    hours: int = 168,
    timeframe: str = "1h",
    max_markers: int = 80,
) -> Dict[str, Any]:
    """Grafik işaretçileri: takvim + haber + makro spike + volatilite anomalisi.

    Haber/takvim kısmı mevcut chart-markers mantığını yeniden kullanır (DRY);
    üzerine makro spike ve sembol anomali işaretçileri eklenir.
    """
    sym = canonical_symbol(symbol)
    cache_key = f"mkr:{sym}:{hours}:{timeframe}:{max_markers}"
    cached = _cache_get(cache_key, _MARKERS_TTL_S)
    if cached is not None:
        return cached

    start_utc = datetime.now(timezone.utc) - timedelta(hours=hours)
    end_utc = datetime.now(timezone.utc)

    markers: List[Dict[str, Any]] = []

    # 1) Haber + takvim (mevcut endpoint mantığı — fail-open)
    try:
        from routers.rss_router import get_chart_news_markers
        base = await get_chart_news_markers(symbol=sym, hours=min(hours, 2160), min_impact_score=5, max_markers=max_markers)
        if isinstance(base, dict) and base.get("success"):
            markers.extend(base.get("markers", []))
    except Exception:
        logger.debug("[MarketEvent] base markers failed (fail-open)", exc_info=True)

    # 1b) Takvim güvenlik ağı: rss chart-markers (enriched_news sorgusu) çökerse
    # takvim işaretçileri de kaybolmasın — üreteçlerden doğrudan doldur.
    if not any(m.get("catalyst_type") in ("economic", "earnings") for m in markers):
        markers.extend(_calendar_fallback_markers(sym, start_utc, end_utc))

    # 2) Makro spike'lar
    markers.extend(_macro_spike_markers(sym, start_utc, end_utc))

    # 3) Sembol volatilite anomalileri
    markers.extend(await _anomaly_markers(sym, timeframe, start_utc))

    # Dedup: (id, time) VE haber başlığı (çok-kaynak çakışması — RSS + Telegram
    # aynı haberi farklı ID ile getirebilir; en önemli kopya kalır)
    seen_ids = set()
    seen_headlines: Dict[str, int] = {}
    deduped: List[Dict[str, Any]] = []
    for marker in sorted(markers, key=lambda m: (m.get("importance_score", 0)), reverse=True):
        key = (marker.get("id"), marker.get("time"))
        if key in seen_ids:
            continue
        if marker.get("catalyst_type") in (None, "news"):
            hkey = _headline_key(marker.get("headline_en") or marker.get("headline"))
            if hkey and hkey in seen_headlines:
                continue
            if hkey:
                seen_headlines[hkey] = 1
        seen_ids.add(key)
        deduped.append(marker)

    deduped = deduped[:max_markers]
    deduped.sort(key=lambda m: str(m.get("time") or ""))

    result = {
        "success": True,
        "symbol": sym,
        "count": len(deduped),
        "markers": deduped,
    }
    _cache_put(cache_key, result)
    return result


def _calendar_fallback_markers(
    symbol: str, start_utc: datetime, end_utc: datetime
) -> List[Dict[str, Any]]:
    """Takvim olaylarını doğrudan üreteçlerden marker'a çevirir (rss yolu çökerse)."""
    markers: List[Dict[str, Any]] = []
    for event in _fetch_calendar_events(symbol, start_utc, end_utc, pad_minutes=0):
        impact_label = str(event.get("impact") or "Medium").lower()
        importance = {"high": 90, "medium": 68, "low": 45}.get(impact_label, 60)
        if importance < 60:
            continue
        direction = str(event.get("direction") or "neutral")
        is_economic = event.get("type") == "economic"
        markers.append({
            "id": f"calfb:{event.get('id')}:{event.get('timestamp')}",
            "time": event.get("timestamp"),
            "position": "aboveBar",
            "color": "#f59e0b" if is_economic else "#3b82f6",
            "shape": "circle",
            "text": "📅" if is_economic else "💼",
            "size": 1.4,
            "headline": event.get("title_tr") or event.get("title"),
            "headline_en": event.get("title"),
            "direction": direction,
            "score": max(4, min(10, round(importance / 10))),
            "urgency": "high" if importance >= 72 else "medium",
            "catalyst_type": "economic" if is_economic else "earnings",
            "is_economic_event": is_economic,
            "is_earnings_event": not is_economic,
            "event_name": event.get("title"),
            "event_id": event.get("id"),
            "reasoning_tr": event.get("detail_tr") or "",
            "importance_level": "high" if importance >= 72 else "medium",
            "importance_score": importance,
            "importance_reason": None,
            "ai_confidence": 0,
            "url": "",
        })
    return markers
