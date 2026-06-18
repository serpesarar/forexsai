"""
Oil Analysis Service — "Black Gold Pulse"
WTI Crude Oil 4-layer analysis engine.

Layer 1: DXY-Driven Macro (35% weight)
Layer 2: Fundamental Flow — EIA, OPEC, Geopolitical (30% weight)
Layer 3: Microstructure — VWAP, Volume Profile, CVD (35% weight)
Layer 4: Temporal Modifiers — Seasonality, EIA day, Rollover
"""

from __future__ import annotations

import logging
import math
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

# Psychological price levels where options pinning occurs
OIL_PSYCHOLOGICAL_LEVELS = [55.0, 60.0, 65.0, 70.0, 75.0, 80.0, 85.0, 90.0, 95.0, 100.0]

# Seasonality bias map (month → score modifier)
# Based on historical WTI patterns: summer driving season bullish, winter heating
SEASONALITY_MAP = {
    1: -5,   # January — post-holiday demand drop
    2: -10,  # February — seasonal low (long opportunity)
    3: 5,    # March — refinery maintenance → supply tightens
    4: 10,   # April — driving season prep (bullish)
    5: 15,   # May — driving season start
    6: 10,   # June — peak summer (but nearing top)
    7: -5,   # July — July 4th demand peak then fade
    8: 0,    # August — transition
    9: -5,   # September — hurricane season uncertainty
    10: 10,  # October — heating oil season start (bullish)
    11: 5,   # November — winter prep
    12: 0,   # December — year-end positioning
}

# Geopolitical risk keywords and their severity scores
GEO_RISK_KEYWORDS = {
    "critical": ["hormuz", "strait of hormuz", "saudi aramco attack", "oil embargo",
                 "opec emergency", "persian gulf blockade"],
    "high": ["iran sanction", "russia oil ban", "iran israel", "houthi attack",
             "red sea", "oil supply disruption", "pipeline attack", "libya shutdown"],
    "medium": ["opec cut", "opec meeting", "venezuela", "nigeria oil",
               "iraq oil", "oil production cut", "refinery outage"],
    "low": ["oil inventory", "crude stockpile", "gasoline demand",
            "drilling rig count", "shale production"]
}


# ═══════════════════════════════════════════════════════════════════════════════
# LAYER 1: DXY-DRIVEN MACRO (35% weight)
# ═══════════════════════════════════════════════════════════════════════════════

async def calculate_dxy_impact(
    wti_candles: List[Dict],
    dxy_candles: Optional[List[Dict]] = None,
    spx_candles: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """
    Calculate DXY-driven macro score for WTI.
    DXY and WTI have strong inverse correlation (~-0.8).
    If both rise simultaneously = geopolitical risk premium.
    """
    score = 0
    reasons = []
    risks = []

    if not wti_candles or len(wti_candles) < 20:
        return {"score": 0, "reasons": ["Insufficient WTI data"], "risks": [],
                "dxy_change": 0, "correlation": 0, "geo_override": False}

    wti_closes = np.array([c["close"] for c in wti_candles[-20:]], dtype=np.float64)
    wti_change_pct = (wti_closes[-1] / wti_closes[0] - 1) * 100

    dxy_change_pct = 0.0
    correlation = 0.0
    geo_override = False

    # DXY Impact (Primary Driver)
    if dxy_candles and len(dxy_candles) >= 20:
        dxy_closes = np.array([c["close"] for c in dxy_candles[-20:]], dtype=np.float64)
        dxy_change_pct = (dxy_closes[-1] / dxy_closes[0] - 1) * 100

        # Rolling correlation
        if len(wti_closes) == len(dxy_closes):
            correlation = float(np.corrcoef(wti_closes, dxy_closes)[0, 1])

        if dxy_change_pct > 0.3:
            score -= 20
            reasons.append(f"DXY güçleniyor ({dxy_change_pct:+.2f}%) — petrol baskı altında")
        elif dxy_change_pct < -0.3:
            score += 20
            reasons.append(f"DXY zayıflıyor ({dxy_change_pct:+.2f}%) — petrol destekleniyor")
        else:
            reasons.append(f"DXY nötr ({dxy_change_pct:+.2f}%)")

        # Geopolitical Override Detection
        if dxy_change_pct > 0.2 and wti_change_pct > 0.5:
            geo_override = True
            score += 10  # Risk premium bonus
            risks.append("⚠️ DXY↑ + WTI↑ = Jeopolitik risk primi aktif (normal ters korelasyon bozuldu)")
    else:
        reasons.append("DXY verisi mevcut değil")

    # S&P 500 Risk Appetite Check
    if spx_candles and len(spx_candles) >= 10:
        spx_closes = np.array([c["close"] for c in spx_candles[-10:]], dtype=np.float64)
        spx_change = (spx_closes[-1] / spx_closes[0] - 1) * 100

        if spx_change > 0.5 and wti_change_pct > 1.0:
            score += 10
            reasons.append(f"Risk-on onaylandı (S&P {spx_change:+.1f}%, WTI {wti_change_pct:+.1f}%)")
        elif spx_change < -0.5 and wti_change_pct > 1.0:
            score -= 5
            risks.append("S&P düşerken WTI yükseliyor — arz korkusu, sürdürülebilirlik riskli")

    return {
        "score": score,
        "reasons": reasons,
        "risks": risks,
        "dxy_change": round(dxy_change_pct, 2),
        "wti_change": round(wti_change_pct, 2),
        "correlation": round(correlation, 3),
        "geo_override": geo_override,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# LAYER 2: FUNDAMENTAL FLOW (30% weight)
# ═══════════════════════════════════════════════════════════════════════════════

async def fetch_eia_inventory() -> Optional[Dict[str, Any]]:
    """
    EIA Crude Oil Inventories.

    Disabled: the previous economic-events data source has been retired and no
    replacement is wired yet. Returns None so callers degrade gracefully.
    TODO: re-wire to a new economic-calendar source if this signal is needed.
    """
    return None


def _parse_float(val) -> Optional[float]:
    """Safely parse a value to float."""
    if val is None:
        return None
    try:
        return float(str(val).replace(",", "").replace("M", "").replace("B", ""))
    except (ValueError, TypeError):
        return None


def calculate_eia_impact(
    actual: Optional[float],
    estimate: Optional[float],
    previous: Optional[float],
) -> Tuple[int, str]:
    """
    Score EIA inventory surprise.
    Negative actual = drawdown (bullish), Positive = build (bearish).
    """
    if actual is None or estimate is None:
        return 0, "EIA verisi mevcut değil"

    surprise = actual - estimate

    if surprise < -2.0:
        return 30, f"Büyük stok düşüşü sürprizi: {actual:.1f}M vs beklenti {estimate:.1f}M (çok boğa)"
    elif surprise < -0.5:
        return 15, f"Stok düşüşü: {actual:.1f}M vs beklenti {estimate:.1f}M (boğa)"
    elif surprise > 2.0:
        return -30, f"Büyük stok artışı sürprizi: {actual:.1f}M vs beklenti {estimate:.1f}M (çok ayı)"
    elif surprise > 0.5:
        return -15, f"Stok artışı: {actual:.1f}M vs beklenti {estimate:.1f}M (ayı)"
    else:
        return 0, f"Beklentiye uygun: {actual:.1f}M vs {estimate:.1f}M"


async def calculate_fundamental_score(
    session: str,
    news_sentiment: Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    Calculate fundamental flow score combining EIA + geopolitical risk.
    """
    score = 0
    reasons = []
    risks = []
    eia_data = None

    # EIA Inventory Impact
    eia = await fetch_eia_inventory()
    if eia:
        eia_data = eia
        eia_score, eia_comment = calculate_eia_impact(
            eia["actual"], eia["estimate"], eia["previous"]
        )
        score += eia_score
        reasons.append(f"EIA: {eia_comment}")
    else:
        reasons.append("EIA verisi alınamadı")

    # EIA Day Warning
    now = datetime.now(timezone.utc)
    if now.weekday() == 2:  # Wednesday
        if now.hour < 15:
            risks.append("⚠️ EIA bugün 15:30 UTC'de açıklanacak — dikkatli pozisyon al")
        elif session == "nymex_eia_window":
            risks.append("🔴 EIA AÇIKLAMA ZAMANI — yüksek volatilite bekleniyor")

    # Geopolitical Risk from news
    geo_level = "low"
    geo_score = 0
    if news_sentiment:
        sentiment_text = str(news_sentiment).lower()
        for level, keywords in GEO_RISK_KEYWORDS.items():
            for kw in keywords:
                if kw in sentiment_text:
                    geo_level = level
                    break
            if geo_level != "low":
                break

        geo_scores = {"critical": 25, "high": 15, "medium": 5, "low": 0}
        geo_score = geo_scores.get(geo_level, 0)
        score += geo_score
        if geo_level in ("critical", "high"):
            risks.append(f"Jeopolitik risk: {geo_level.upper()} — 48 saat sonra erime riski")
        elif geo_level == "medium":
            reasons.append("Jeopolitik risk: ORTA — haberleri takip et")

    return {
        "score": score,
        "reasons": reasons,
        "risks": risks,
        "eia": eia_data,
        "geo_risk_level": geo_level,
        "geo_score": geo_score,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# LAYER 3: MICROSTRUCTURE (35% weight)
# ═══════════════════════════════════════════════════════════════════════════════

def calculate_nymex_vwap(candles: List[Dict]) -> Dict[str, float]:
    """
    Calculate VWAP anchored to NYMEX session (14:30 UTC / 09:30 EST).
    If no session data available, use all candles.
    """
    if not candles or len(candles) < 5:
        return {"vwap": 0, "distance_pct": 0}

    # Use all available candles for VWAP calculation
    total_pv = 0.0
    total_vol = 0.0
    for c in candles:
        typical = (c["high"] + c["low"] + c["close"]) / 3
        vol = max(c.get("volume", 0), 1)
        total_pv += typical * vol
        total_vol += vol

    vwap = total_pv / total_vol if total_vol > 0 else candles[-1]["close"]
    current = candles[-1]["close"]
    distance_pct = (current / vwap - 1) * 100 if vwap > 0 else 0

    return {"vwap": round(vwap, 2), "distance_pct": round(distance_pct, 3)}


def calculate_volume_profile(
    candles: List[Dict],
    bin_size: float = 0.25,
) -> Dict[str, Any]:
    """
    Calculate Volume Profile: POC (Point of Control), VAH, VAL.
    Uses $0.25 price bins for WTI.
    """
    if not candles or len(candles) < 10:
        return {"poc": 0, "vah": 0, "val": 0, "at_poc": False}

    # Build volume profile
    profile: Dict[float, float] = {}
    for c in candles:
        level = round(c["close"] / bin_size) * bin_size
        vol = c.get("volume", 0)
        profile[level] = profile.get(level, 0) + vol

    if not profile:
        return {"poc": 0, "vah": 0, "val": 0, "at_poc": False}

    # POC = price level with highest volume
    poc = max(profile.keys(), key=lambda k: profile[k])

    # Value Area (70% of total volume)
    total_vol = sum(profile.values())
    sorted_levels = sorted(profile.items(), key=lambda x: x[1], reverse=True)
    cumulative = 0.0
    va_levels = []
    for level, vol in sorted_levels:
        cumulative += vol
        va_levels.append(level)
        if cumulative >= total_vol * 0.7:
            break

    vah = max(va_levels) if va_levels else poc
    val = min(va_levels) if va_levels else poc

    current = candles[-1]["close"]
    at_poc = abs(current - poc) < bin_size * 2

    return {
        "poc": round(poc, 2),
        "vah": round(vah, 2),
        "val": round(val, 2),
        "at_poc": at_poc,
    }


def calculate_synthetic_cvd(candles: List[Dict], lookback: int = 20) -> Dict[str, Any]:
    """
    Estimate Cumulative Volume Delta from OHLC data.
    Uses close vs open to estimate buying/selling pressure.
    """
    if not candles or len(candles) < lookback:
        return {"cvd_trend": "neutral", "divergence": None, "score": 0}

    recent = candles[-lookback:]
    deltas = []
    for c in recent:
        vol = c.get("volume", 0)
        if c["close"] > c["open"]:
            deltas.append(vol * 0.6)  # Buying pressure
        elif c["close"] < c["open"]:
            deltas.append(-vol * 0.6)  # Selling pressure
        else:
            deltas.append(0)

    cvd = np.cumsum(deltas)
    half = len(cvd) // 2
    recent_cvd = np.mean(cvd[half:])
    prev_cvd = np.mean(cvd[:half])

    price_change = recent[-1]["close"] - recent[0]["close"]

    cvd_trend = "rising" if recent_cvd > prev_cvd else "falling"
    divergence = None
    score = 0

    if price_change > 0 and recent_cvd < prev_cvd:
        divergence = "bearish"
        score = -15
    elif price_change < 0 and recent_cvd > prev_cvd:
        divergence = "bullish"
        score = 15

    return {
        "cvd_trend": cvd_trend,
        "divergence": divergence,
        "score": score,
    }


def calculate_ema_regime(candles: List[Dict]) -> Dict[str, Any]:
    """Calculate EMA 20/50/200 regime for trend detection."""
    if not candles or len(candles) < 50:
        return {"regime": "neutral", "score": 0, "ema20": 0, "ema50": 0}

    closes = np.array([c["close"] for c in candles], dtype=np.float64)
    current = closes[-1]

    def ema(data, period):
        alpha = 2 / (period + 1)
        result = np.zeros_like(data)
        result[0] = data[0]
        for i in range(1, len(data)):
            result[i] = alpha * data[i] + (1 - alpha) * result[i - 1]
        return result

    ema20 = ema(closes, 20)[-1]
    ema50 = ema(closes, 50)[-1]

    score = 0
    regime = "neutral"

    if current > ema20 > ema50:
        score = 15
        regime = "bullish"
    elif current < ema20 < ema50:
        score = -15
        regime = "bearish"
    elif current > ema50:
        score = 5
        regime = "weak_bullish"
    elif current < ema50:
        score = -5
        regime = "weak_bearish"

    # 200 EMA test (major support/resistance)
    if len(candles) >= 200:
        ema200 = ema(closes, 200)[-1]
        if abs(current - ema200) / ema200 < 0.005:  # Within 0.5% of 200 EMA
            score *= 2  # Double weight at 200 EMA test
            regime += "_200ema_test"

    return {
        "regime": regime,
        "score": score,
        "ema20": round(ema20, 2),
        "ema50": round(ema50, 2),
    }


def calculate_microstructure_score(candles: List[Dict]) -> Dict[str, Any]:
    """
    Combined microstructure analysis: VWAP + Volume Profile + CVD + EMA.
    """
    score = 0
    reasons = []
    risks = []

    # VWAP
    vwap_data = calculate_nymex_vwap(candles)
    if vwap_data["vwap"] > 0:
        if vwap_data["distance_pct"] > 0.5:
            score += 15
            reasons.append(f"VWAP üzerinde (+{vwap_data['distance_pct']:.2f}%) — kurumsal alış")
        elif vwap_data["distance_pct"] < -0.5:
            score -= 15
            reasons.append(f"VWAP altında ({vwap_data['distance_pct']:.2f}%) — kurumsal satış")
        else:
            reasons.append(f"VWAP'ta ({vwap_data['vwap']}) — pivot bölgesi")

    # Volume Profile
    vp = calculate_volume_profile(candles)
    current_price = candles[-1]["close"] if candles else 0
    if vp["poc"] > 0:
        if vp["at_poc"]:
            reasons.append(f"POC'ta (${vp['poc']}) — manyetik etki, mean reversion")
        elif current_price > vp["vah"]:
            score += 10
            reasons.append(f"VAH (${vp['vah']}) üzerinde — breakout modu")
        elif current_price < vp["val"]:
            score -= 10
            reasons.append(f"VAL (${vp['val']}) altında — breakdown modu")

    # CVD Divergence
    cvd = calculate_synthetic_cvd(candles)
    score += cvd["score"]
    if cvd["divergence"] == "bearish":
        risks.append("CVD ayı sapması — dağıtım paterni tespit edildi")
    elif cvd["divergence"] == "bullish":
        reasons.append("CVD boğa sapması — birikim paterni tespit edildi")

    # EMA Regime
    ema = calculate_ema_regime(candles)
    score += ema["score"]
    if "bullish" in ema["regime"]:
        reasons.append(f"EMA yapısı boğa (EMA20={ema['ema20']}, EMA50={ema['ema50']})")
    elif "bearish" in ema["regime"]:
        reasons.append(f"EMA yapısı ayı (EMA20={ema['ema20']}, EMA50={ema['ema50']})")

    # Psychological Levels
    for level in OIL_PSYCHOLOGICAL_LEVELS:
        if abs(current_price - level) < 0.50:
            risks.append(f"Psikolojik seviye ${level} yakınında — opsiyon pinning riski")
            break

    return {
        "score": score,
        "reasons": reasons,
        "risks": risks,
        "vwap": vwap_data,
        "volume_profile": vp,
        "cvd": cvd,
        "ema": ema,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# LAYER 4: TEMPORAL MODIFIERS
# ═══════════════════════════════════════════════════════════════════════════════

def calculate_temporal_modifier(session: str) -> Dict[str, Any]:
    """
    Calculate temporal modifiers: seasonality, EIA day, rollover.
    """
    now = datetime.now(timezone.utc)
    score = 0
    modifiers = []

    # Seasonality
    seasonal_score = SEASONALITY_MAP.get(now.month, 0)
    score += seasonal_score
    if seasonal_score > 5:
        modifiers.append(f"Mevsimsel boğa eğilimi (Ay {now.month}: +{seasonal_score})")
    elif seasonal_score < -5:
        modifiers.append(f"Mevsimsel ayı eğilimi (Ay {now.month}: {seasonal_score})")

    # EIA Day Detection
    if now.weekday() == 2:  # Wednesday
        modifiers.append("📊 EIA rapor günü — 15:30 UTC öncesi pozisyon azalt")
        if session == "nymex_eia_window":
            score -= 10  # Reduce confidence during EIA
            modifiers.append("🔴 EIA açıklama penceresi — yeni pozisyon AÇMA")

    # Rollover Warning (simple: day 15-25 of month)
    if 15 <= now.day <= 25:
        modifiers.append("Vade sonu yaklaşıyor — pinning riski, kontrol et")

    # Time-of-day adjustments
    if session == "asia":
        score -= 5
        modifiers.append("Asya seansı — düşük hacim, sahte kırılım riski")
    elif session == "nymex":
        modifiers.append("NYMEX ana seans — en yüksek likidite")

    return {
        "score": score,
        "modifiers": modifiers,
        "seasonality": seasonal_score,
        "is_eia_day": now.weekday() == 2,
        "is_rollover_zone": 15 <= now.day <= 25,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# COMPOSITE ENGINE — BLACK GOLD PULSE SCORE
# ═══════════════════════════════════════════════════════════════════════════════

def interpret_composite_score(score: float) -> Dict[str, Any]:
    """Convert composite score to signal direction and label."""
    if score >= 70:
        return {"direction": "BUY", "signal_type": "CONFIRM", "label": "STRONG LONG",
                "emoji": "🟢", "confidence": min(95, 50 + score / 2)}
    elif score >= 40:
        return {"direction": "BUY", "signal_type": "SCOUT", "label": "LONG BIAS",
                "emoji": "🟢", "confidence": min(80, 40 + score / 2)}
    elif score >= 10:
        return {"direction": "BUY", "signal_type": "SCOUT", "label": "CAUTIOUS LONG",
                "emoji": "🟡", "confidence": min(60, 30 + score / 2)}
    elif score > -10:
        return {"direction": "HOLD", "signal_type": "HOLD", "label": "NEUTRAL",
                "emoji": "🟡", "confidence": 50}
    elif score > -40:
        return {"direction": "SELL", "signal_type": "SCOUT", "label": "CAUTIOUS SHORT",
                "emoji": "🟡", "confidence": min(60, 30 + abs(score) / 2)}
    elif score > -70:
        return {"direction": "SELL", "signal_type": "SCOUT", "label": "SHORT BIAS",
                "emoji": "🔴", "confidence": min(80, 40 + abs(score) / 2)}
    else:
        return {"direction": "SELL", "signal_type": "CONFIRM", "label": "STRONG SHORT",
                "emoji": "🔴", "confidence": min(95, 50 + abs(score) / 2)}


async def generate_oil_analysis(
    wti_candles: List[Dict],
    session: str = "nymex",
    dxy_candles: Optional[List[Dict]] = None,
    spx_candles: Optional[List[Dict]] = None,
    news_sentiment: Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    Main entry point: generate full Black Gold Pulse analysis.
    Returns composite score, direction, layers breakdown.
    """
    # Layer 1: DXY Macro (35%)
    macro = await calculate_dxy_impact(wti_candles, dxy_candles, spx_candles)

    # Layer 2: Fundamental (30%)
    fundamental = await calculate_fundamental_score(session, news_sentiment)

    # Layer 3: Microstructure (35%)
    micro = calculate_microstructure_score(wti_candles)

    # Layer 4: Temporal modifiers
    temporal = calculate_temporal_modifier(session)

    # Composite Score
    composite = (
        macro["score"] * 0.35
        + fundamental["score"] * 0.30
        + micro["score"] * 0.35
        + temporal["score"]
    )

    # Signal interpretation
    signal = interpret_composite_score(composite)

    # Merge all reasons and risks
    all_reasons = macro["reasons"] + fundamental["reasons"] + micro["reasons"]
    all_risks = macro["risks"] + fundamental["risks"] + micro["risks"]
    all_modifiers = temporal["modifiers"]

    current_price = wti_candles[-1]["close"] if wti_candles else 0

    return {
        "composite_score": round(composite, 1),
        "direction": signal["direction"],
        "signal_type": signal["signal_type"],
        "label": signal["label"],
        "confidence": round(signal["confidence"], 1),
        "emoji": signal["emoji"],
        "current_price": round(current_price, 2),
        # Layer breakdowns
        "layers": {
            "macro": {
                "score": macro["score"],
                "weight": "35%",
                "dxy_change": macro["dxy_change"],
                "wti_change": macro["wti_change"],
                "correlation": macro["correlation"],
                "geo_override": macro["geo_override"],
            },
            "fundamental": {
                "score": fundamental["score"],
                "weight": "30%",
                "eia": fundamental["eia"],
                "geo_risk_level": fundamental["geo_risk_level"],
            },
            "microstructure": {
                "score": micro["score"],
                "weight": "35%",
                "vwap": micro["vwap"],
                "volume_profile": micro["volume_profile"],
                "cvd": micro["cvd"],
                "ema": micro["ema"],
            },
            "temporal": {
                "score": temporal["score"],
                "seasonality": temporal["seasonality"],
                "is_eia_day": temporal["is_eia_day"],
                "is_rollover_zone": temporal["is_rollover_zone"],
            },
        },
        # Aggregated insights
        "reasons": all_reasons,
        "risks": all_risks,
        "modifiers": all_modifiers,
        # Key levels
        "key_levels": {
            "vwap": micro["vwap"]["vwap"],
            "poc": micro["volume_profile"]["poc"],
            "vah": micro["volume_profile"]["vah"],
            "val": micro["volume_profile"]["val"],
            "ema20": micro["ema"]["ema20"],
            "ema50": micro["ema"]["ema50"],
        },
    }
