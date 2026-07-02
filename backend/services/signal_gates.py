"""Merkezi sinyal kapıları — 2026-07-01 gösterge denetimi uygulaması.

Kaynak analiz: GOSTERGE_UYGUNLUK_ANALIZ_RAPORU_2026-07-01.md
Kanıt (60 gün prediction_logs):
  - XAUUSD SELL WR: pulse1 %19.1, pulse2 %20.3, pulse3 %19.7, smc %31.8
    (BUY tarafı %64-85) → trend/ATH ortamında SELL üretimi ana kayıp kaynağı.
  - EMEL'in ATH SELL bloğu ile XAUUSD %84.8 WR → koruma kanıtlı, genelleniyor.
  - GDAXI pulse1: düz %25 / inverse %38 WR → sinyal bilgi taşımıyor, askıda.
  - Saat etkisi: XAUUSD 20 UTC %37.9, 01-03 UTC ~%42; GDAXI 07-12 UTC %40-43.

Tüm kapılar fail-open tasarlanmıştır: veri/servis hatasında sinyali BLOKLAMAZ,
sadece loglar. Env bayrakları ile tek tek kapatılabilir.

Env bayrakları:
  XAU_TREND_SELL_GATE=1      → XAUUSD trend-yönü SELL kapısı (default açık)
  SESSION_GATES_ENABLED=1    → saat/seans kapıları (default açık)
  CALENDAR_GATE_ENABLED=1    → yüksek etkili takvim olayı ±30dk kapısı (default açık)
  GDAXI_PULSE1_ENABLED=0     → GDAXI'de pulse1 (default KAPALI/askıda)
  CALENDAR_GATE_MINUTES=30   → takvim penceresi (dakika)
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, List, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)

# ─── Sabitler ────────────────────────────────────────────────────────────────

_XAU_ALIASES = {"XAUUSD", "XAUUSD.FOREX", "GOLD"}

#: Yön kapılarının uygulandığı modeller (EMEL kendi ATH kapısına sahip,
#: ML/meta kendi eşiklerini yönetir — rapor bölüm 3/6).
TREND_GATED_MODELS = {"pulse1", "pulse2", "pulse3", "smc"}

#: Seans kapısı scalp-karakterli modellere uygulanır.
SESSION_GATED_MODELS = {"pulse1", "pulse2", "pulse3", "smc"}

#: Takvim kapısı: rapor aksiyon #9 (PULSE + EMEL + SMC).
CALENDAR_GATED_MODELS = {"pulse1", "pulse2", "pulse3", "smc", "emel"}

#: UTC saat → blok. Rapor bölüm 2 saatlik WR verisi.
#: XAUUSD: 20:00-20:59 (%37.9 WR) + 01:00-02:59 (~%42 WR, Asya gecesi)
#: GDAXI:  07:00-07:59 (Xetra açılış gürültüsü; sabah bandı %39.9-42.8 WR)
SESSION_BLOCK_HOURS_UTC = {
    "XAUUSD": (20, 1, 2),
    "GDAXI.INDX": (7,),
}

_H4_EMA_PERIOD = 50
_H4_MIN_CANDLES = 55


# ─── Yardımcılar ─────────────────────────────────────────────────────────────

def _flag(name: str, default: str = "1") -> bool:
    """Env bayrağı: '0' → kapalı, diğer her şey → açık."""
    return os.getenv(name, default) != "0"


def _norm_symbol(symbol: str) -> str:
    return (symbol or "").upper().strip()


def _base_model(model_type: str) -> str:
    """'ml:balanced' → 'ml', 'pulse1' → 'pulse1'."""
    return (model_type or "").lower().strip().split(":")[0]


def _is_xau(symbol: str) -> bool:
    return _norm_symbol(symbol) in _XAU_ALIASES


def _ema(values: Sequence[float], period: int) -> Optional[float]:
    """TradingView uyumlu EMA (emel_pulse._calc_ema ile aynı yaklaşım)."""
    vals = [float(v) for v in values if v is not None]
    if len(vals) < period:
        return None
    alpha = 2.0 / (period + 1.0)
    ema = sum(vals[:period]) / period
    for v in vals[period:]:
        ema = alpha * v + (1 - alpha) * ema
    return ema


# ─── Kapı 1: GDAXI pulse1 askıya alma ────────────────────────────────────────

def pulse1_symbol_enabled(symbol: str) -> bool:
    """GDAXI'de pulse1 askıda (60g: 446W/1339L, inverse dahi %38 WR).

    GDAXI_PULSE1_ENABLED=1 ile tekrar açılabilir.
    """
    if _norm_symbol(symbol) == "GDAXI.INDX":
        return _flag("GDAXI_PULSE1_ENABLED", "0")
    return True


# ─── Kapı 2: XAUUSD trend-yönü SELL kapısı ──────────────────────────────────

async def xau_trend_sell_gate(
    symbol: str,
    direction: str,
    regime: Any = None,
) -> Tuple[bool, Optional[str]]:
    """XAUUSD'de trend/ATH ortamında counter-trend SELL'i blokla.

    EMEL'in kanıtlanmış ATH-SELL bloğunun (XAUUSD %84.8 WR) genellemesi.
    Blok koşulu (sırayla):
      1. Rejim STRONG_TREND_DOWN ise → SELL serbest (trend yönü).
      2. Rejim STRONG_TREND_UP veya is_ath_zone ise → SELL blok.
      3. H4 kapanış > H4 EMA50 ise → SELL blok (H4 trend up).
    Veri alınamazsa fail-open (blok yok).

    Returns:
        (allowed, reason): allowed=False ise reason blok açıklamasıdır.
    """
    if not _flag("XAU_TREND_SELL_GATE"):
        return True, None
    if direction != "SELL" or not _is_xau(symbol):
        return True, None

    try:
        if regime is None:
            from services.market_regime_service import detect_regime
            regime = await detect_regime(symbol)

        regime_name = str(getattr(regime, "regime", "") or "").upper()
        is_ath = bool(getattr(regime, "is_ath_zone", False))

        if regime_name == "STRONG_TREND_DOWN":
            return True, None
        if is_ath or regime_name == "STRONG_TREND_UP":
            return False, (
                f"XAU SELL kapısı: {'ATH bölgesi' if is_ath else 'STRONG_TREND_UP'} "
                "— counter-trend SELL blok (rapor aksiyon #2)"
            )

        # H4 trend kontrolü
        from services.market_data_service import get_ohlcv_data
        candles = await get_ohlcv_data(symbol, timeframe="4h", limit=_H4_MIN_CANDLES + 10)
        if candles and len(candles) >= _H4_MIN_CANDLES:
            closes = [c.get("close") for c in candles]
            ema50_h4 = _ema(closes, _H4_EMA_PERIOD)
            last_close = float(closes[-1]) if closes[-1] is not None else None
            if ema50_h4 is not None and last_close is not None and last_close > ema50_h4:
                return False, (
                    f"XAU SELL kapısı: H4 trend up (close {last_close:.2f} > "
                    f"EMA50 {ema50_h4:.2f}) — counter-trend SELL blok"
                )
    except Exception as exc:  # fail-open
        logger.debug(f"xau_trend_sell_gate fail-open ({symbol}): {exc}")

    return True, None


# ─── Kapı 3: Seans/saat kapısı ───────────────────────────────────────────────

def session_gate(symbol: str, now: Optional[datetime] = None) -> Tuple[bool, Optional[str]]:
    """Düşük-WR saat pencerelerinde yeni sinyal üretimini blokla.

    Returns:
        (allowed, reason)
    """
    if not _flag("SESSION_GATES_ENABLED"):
        return True, None

    sym = _norm_symbol(symbol)
    if sym in _XAU_ALIASES:
        sym = "XAUUSD"
    blocked_hours = SESSION_BLOCK_HOURS_UTC.get(sym)
    if not blocked_hours:
        return True, None

    hour = (now or datetime.now(timezone.utc)).hour
    if hour in blocked_hours:
        return False, (
            f"Seans kapısı: {sym} için {hour:02d}:00-{hour:02d}:59 UTC düşük-WR "
            "penceresi (rapor bölüm 2.4) — yeni sinyal blok"
        )
    return True, None


# ─── Kapı 4: Ekonomik takvim kapısı ─────────────────────────────────────────

async def calendar_gate(symbol: str) -> Tuple[bool, Optional[str]]:
    """Yüksek etkili takvim olayı ±CALENDAR_GATE_MINUTES içinde sinyal blok.

    Fail-open: takvim servisi hata verirse blok uygulanmaz.
    """
    if not _flag("CALENDAR_GATE_ENABLED"):
        return True, None

    try:
        minutes = int(os.getenv("CALENDAR_GATE_MINUTES", "30"))
    except ValueError:
        minutes = 30

    try:
        from services.economic_calendar_service import get_calendar_service
        events = await get_calendar_service().get_upcoming_high_impact_events(
            minutes_ahead=minutes
        )
        sym = _norm_symbol(symbol)
        for ev in events or []:
            affected = [
                _norm_symbol(s) for s in (getattr(ev, "affected_symbols", None) or [])
            ]
            hit = sym in affected or (
                sym in _XAU_ALIASES and any(a in _XAU_ALIASES for a in affected)
            )
            if hit:
                ev_name = getattr(ev, "event_name", None) or "high-impact event"
                return False, (
                    f"Takvim kapısı: {ev_name} ±{minutes}dk penceresi — yeni sinyal blok"
                )
    except Exception as exc:  # fail-open
        logger.debug(f"calendar_gate fail-open ({symbol}): {exc}")

    return True, None


# ─── Birleşik uygulayıcı ─────────────────────────────────────────────────────

async def apply_signal_gates(
    symbol: str,
    direction: str,
    model_type: str,
    regime: Any = None,
) -> Tuple[str, List[str]]:
    """Tüm kapıları sırasıyla uygula; bloklanırsa yönü HOLD'a düşür.

    Panel endpoint'leri (UI tutarlılığı) ve prediction_logger (güvenlik ağı)
    tarafından ortak kullanılır — idempotenttir.

    Args:
        symbol: Panel sembolü (örn. "XAUUSD", "GDAXI.INDX").
        direction: "BUY" | "SELL" | diğer (dokunulmaz).
        model_type: "pulse1" | "pulse2" | "pulse3" | "smc" | "emel" | "ml:*" ...
        regime: Varsa RegimeResult (tekrar tespit maliyetini önler).

    Returns:
        (yeni_direction, notlar): Bloklanırsa ("HOLD", [sebepler]).
    """
    notes: List[str] = []
    if direction not in ("BUY", "SELL"):
        return direction, notes

    base = _base_model(model_type)

    # 1) GDAXI pulse1 askıda
    if base == "pulse1" and not pulse1_symbol_enabled(symbol):
        notes.append("GDAXI pulse1 askıda (60g WR %25; GDAXI_PULSE1_ENABLED=1 ile açılır)")
        return "HOLD", notes

    # 2) XAU trend-yönü SELL kapısı
    if base in TREND_GATED_MODELS:
        allowed, reason = await xau_trend_sell_gate(symbol, direction, regime=regime)
        if not allowed:
            notes.append(reason or "XAU SELL kapısı")
            return "HOLD", notes

    # 3) Seans kapısı
    if base in SESSION_GATED_MODELS:
        allowed, reason = session_gate(symbol)
        if not allowed:
            notes.append(reason or "Seans kapısı")
            return "HOLD", notes

    # 4) Takvim kapısı
    if base in CALENDAR_GATED_MODELS:
        allowed, reason = await calendar_gate(symbol)
        if not allowed:
            notes.append(reason or "Takvim kapısı")
            return "HOLD", notes

    return direction, notes
