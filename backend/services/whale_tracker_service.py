"""
Whale Tracker Service
=====================
Combines COT Report data + Open Interest analysis + positioning momentum
to produce a unified "Whale Pressure" score for each tracked symbol.

The whale_pressure score ranges from -1.0 (extreme bearish whale activity)
to +1.0 (extreme bullish whale accumulation).

Features provided to ML:
  - whale_pressure (-1.0 to +1.0)
  - cot_commercials_net
  - cot_speculators_net
  - cot_whale_ratio (commercials_net / total_oi)
  - oi_change_1w_pct
  - spec_positioning_percentile (0-100)
  - crowded_trade_risk (bool)
  - whale_accumulation (bool)

Data sources (all FREE):
  - CFTC COT Report (weekly, Friday release)
  - Open Interest from COT data itself
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, List, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

# Tracked symbols - All 4 main symbols
TRACKED_SYMBOLS = ["XAUUSD", "NASDAQ", "DAX", "USOIL"]

# In-memory cache
_whale_cache: Dict[str, Dict] = {}
_CACHE_TTL = timedelta(minutes=30)


@dataclass
class WhaleAlert:
    """A detected whale activity event."""
    symbol: str
    alert_type: str        # NEW_LARGE_POSITION, CROWDED_TRADE, SMART_MONEY_SHIFT, OI_SURGE
    direction: str         # bullish, bearish, neutral
    severity: str          # low, medium, high, critical
    message: str
    impact_score: int      # 0-100
    detected_at: str
    details: Dict[str, Any]


@dataclass
class WhaleSnapshot:
    """Complete whale activity snapshot for a symbol."""
    symbol: str
    whale_pressure: float          # -1.0 to +1.0
    pressure_label: str            # "Strong Bearish", "Bearish", "Neutral", "Bullish", "Strong Bullish"
    # COT positioning
    commercials_net: int
    commercials_net_change: int
    speculators_net: int
    speculators_net_change: int
    spec_long_percent: float
    spec_positioning_percentile: float
    total_open_interest: int
    oi_change_pct: float
    # Derived signals
    crowded_trade_risk: bool
    whale_accumulation: bool       # Commercials building position
    smart_money_direction: str     # "buying", "selling", "neutral"
    # COT signal
    cot_signal: str
    cot_reason: str
    confidence_adjustment: float
    # Alerts
    active_alerts: List[Dict]
    # Meta
    report_date: str
    data_source: str
    last_updated: str


# ═══════════════════════════════════════════════════════════════════
# Whale Pressure Calculation
# ═══════════════════════════════════════════════════════════════════

def _calculate_whale_pressure(
    commercials_net: int,
    speculators_net: int,
    spec_long_pct: float,
    spec_percentile: float,
    oi_change_pct: float,
    total_oi: int,
    comm_net_change: int,
    spec_net_change: int,
    symbol: str,
) -> float:
    """
    Calculate whale pressure score from -1.0 (extreme bearish) to +1.0 (extreme bullish).
    
    Components:
    1. Commercial positioning (smart money) — weight 0.35
    2. Speculator crowding (contrarian) — weight 0.30
    3. OI momentum (new money flow) — weight 0.20
    4. Week-over-week positioning shift — weight 0.15
    """
    score = 0.0

    # ── 1. Commercial positioning (Smart Money direction) ──
    # Commercials are hedgers; when they reduce shorts = bullish
    whale_ratio = commercials_net / max(total_oi, 1)
    
    if symbol in ("XAUUSD", "SILVER"):
        # Gold/Silver: Commercials are typically net short (hedging production)
        # Less negative = more bullish (reducing hedges = expecting higher prices)
        if whale_ratio > -0.10:
            score += 0.35   # Very bullish: commercials barely short
        elif whale_ratio > -0.20:
            score += 0.15   # Moderately bullish
        elif whale_ratio < -0.40:
            score -= 0.20   # Very bearish: heavy commercial hedging
        elif whale_ratio < -0.30:
            score -= 0.10   # Moderately bearish
    else:
        # Equities: Commercials net long = bullish
        if whale_ratio > 0.05:
            score += 0.30
        elif whale_ratio > 0:
            score += 0.15
        elif whale_ratio < -0.10:
            score -= 0.25
        elif whale_ratio < -0.05:
            score -= 0.10

    # ── 2. Speculator crowding (Contrarian signal) ──
    # Extreme speculator positioning = trend exhaustion
    if spec_percentile > 90 or spec_long_pct > 85:
        score -= 0.30   # Extremely crowded long → bearish contrarian
    elif spec_percentile > 75 or spec_long_pct > 75:
        score -= 0.15   # Crowded → mildly bearish
    elif spec_percentile < 10 or spec_long_pct < 25:
        score += 0.30   # Extreme pessimism → bullish contrarian
    elif spec_percentile < 25 or spec_long_pct < 40:
        score += 0.15   # Below average → mildly bullish

    # ── 3. OI momentum (new money entering) ──
    if oi_change_pct > 10:
        # Large new positions — direction depends on commercial positioning
        if commercials_net > 0 or comm_net_change > 0:
            score += 0.20   # New money + smart money buying
        else:
            score -= 0.10   # New money but smart money selling
    elif oi_change_pct < -10:
        # Liquidation
        score -= 0.15

    # ── 4. Week-over-week shift ──
    if comm_net_change > 10000:
        score += 0.15   # Commercials increasing longs / reducing shorts
    elif comm_net_change < -10000:
        score -= 0.15   # Commercials increasing shorts
    
    if spec_net_change > 20000:
        score -= 0.05   # Specs piling in (contrarian negative at extremes)
    elif spec_net_change < -20000:
        score += 0.05   # Specs exiting (contrarian positive)

    return max(-1.0, min(1.0, round(score, 3)))


def _pressure_label(pressure: float) -> str:
    """Convert pressure float to human label."""
    if pressure >= 0.5:
        return "Strong Bullish"
    elif pressure >= 0.2:
        return "Bullish"
    elif pressure <= -0.5:
        return "Strong Bearish"
    elif pressure <= -0.2:
        return "Bearish"
    return "Neutral"


def _detect_alerts(
    symbol: str,
    spec_long_pct: float,
    spec_percentile: float,
    oi_change_pct: float,
    comm_net_change: int,
    spec_net_change: int,
    whale_pressure: float,
) -> List[WhaleAlert]:
    """Detect noteworthy whale activity events."""
    alerts: List[WhaleAlert] = []
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    # Crowded trade warning
    if spec_long_pct > 80 or spec_percentile > 90:
        alerts.append(WhaleAlert(
            symbol=symbol,
            alert_type="CROWDED_TRADE",
            direction="bearish",
            severity="high",
            message=f"Speculators {spec_long_pct:.0f}% long (P{spec_percentile:.0f}) — crowded, reversal risk elevated",
            impact_score=min(100, int(spec_long_pct)),
            detected_at=now,
            details={"spec_long_pct": spec_long_pct, "percentile": spec_percentile},
        ))

    # Extreme pessimism (contrarian bullish)
    if spec_long_pct < 25 or spec_percentile < 10:
        alerts.append(WhaleAlert(
            symbol=symbol,
            alert_type="EXTREME_PESSIMISM",
            direction="bullish",
            severity="high",
            message=f"Speculators only {spec_long_pct:.0f}% long (P{spec_percentile:.0f}) — extreme fear, contrarian bullish",
            impact_score=min(100, int(100 - spec_long_pct)),
            detected_at=now,
            details={"spec_long_pct": spec_long_pct, "percentile": spec_percentile},
        ))

    # OI surge
    if abs(oi_change_pct) > 10:
        direction = "bullish" if oi_change_pct > 0 and comm_net_change > 0 else "bearish"
        alerts.append(WhaleAlert(
            symbol=symbol,
            alert_type="OI_SURGE",
            direction=direction,
            severity="medium",
            message=f"Open Interest surged {oi_change_pct:+.1f}% — new large positions detected",
            impact_score=min(100, int(abs(oi_change_pct) * 5)),
            detected_at=now,
            details={"oi_change_pct": oi_change_pct},
        ))

    # Smart money shift
    if abs(comm_net_change) > 20000:
        direction = "bullish" if comm_net_change > 0 else "bearish"
        alerts.append(WhaleAlert(
            symbol=symbol,
            alert_type="SMART_MONEY_SHIFT",
            direction=direction,
            severity="high",
            message=f"Commercials shifted {comm_net_change:+,} contracts — smart money {'accumulating' if comm_net_change > 0 else 'distributing'}",
            impact_score=min(100, int(abs(comm_net_change) / 500)),
            detected_at=now,
            details={"comm_net_change": comm_net_change},
        ))

    return alerts


# ═══════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════

async def get_whale_snapshot(symbol: str) -> WhaleSnapshot:
    """Get full whale tracking snapshot for a symbol."""
    from services.cot_report_service import fetch_cot_data

    # Check cache
    cache_key = symbol.upper()
    cached = _whale_cache.get(cache_key)
    if cached:
        try:
            age = datetime.now(timezone.utc) - datetime.fromisoformat(cached["ts"].replace("Z", "+00:00"))
            if age < _CACHE_TTL:
                return WhaleSnapshot(**cached["data"])
        except Exception:
            pass

    cot = await fetch_cot_data(symbol)

    # Calculate whale pressure
    pressure = _calculate_whale_pressure(
        commercials_net=cot.commercials_net,
        speculators_net=cot.speculators_net,
        spec_long_pct=cot.spec_long_percent,
        spec_percentile=cot.spec_positioning_percentile,
        oi_change_pct=cot.oi_change_pct,
        total_oi=cot.total_open_interest,
        comm_net_change=cot.commercials_net_change,
        spec_net_change=cot.speculators_net_change,
        symbol=cot.symbol,
    )

    # Detect alerts
    alerts = _detect_alerts(
        symbol=cot.symbol,
        spec_long_pct=cot.spec_long_percent,
        spec_percentile=cot.spec_positioning_percentile,
        oi_change_pct=cot.oi_change_pct,
        comm_net_change=cot.commercials_net_change,
        spec_net_change=cot.speculators_net_change,
        whale_pressure=pressure,
    )

    # Determine smart money direction
    if cot.commercials_net_change > 5000:
        sm_dir = "buying"
    elif cot.commercials_net_change < -5000:
        sm_dir = "selling"
    else:
        sm_dir = "neutral"

    snapshot = WhaleSnapshot(
        symbol=cot.symbol,
        whale_pressure=pressure,
        pressure_label=_pressure_label(pressure),
        commercials_net=cot.commercials_net,
        commercials_net_change=cot.commercials_net_change,
        speculators_net=cot.speculators_net,
        speculators_net_change=cot.speculators_net_change,
        spec_long_percent=cot.spec_long_percent,
        spec_positioning_percentile=cot.spec_positioning_percentile,
        total_open_interest=cot.total_open_interest,
        oi_change_pct=cot.oi_change_pct,
        crowded_trade_risk=cot.spec_long_percent > 80 or cot.spec_positioning_percentile > 90,
        whale_accumulation=cot.commercials_net_change > 10000,
        smart_money_direction=sm_dir,
        cot_signal=cot.signal,
        cot_reason=cot.reason,
        confidence_adjustment=cot.confidence_adjustment,
        active_alerts=[asdict(a) for a in alerts],
        report_date=cot.report_date,
        data_source=cot.data_source,
        last_updated=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )

    # Cache
    _whale_cache[cache_key] = {
        "data": asdict(snapshot),
        "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }

    return snapshot


async def get_whale_dashboard() -> Dict:
    """Get whale tracking data for all symbols — used by the frontend panel."""
    snapshots = {}
    for sym in TRACKED_SYMBOLS:
        try:
            snap = await get_whale_snapshot(sym)
            snapshots[sym] = asdict(snap)
        except Exception as e:
            logger.warning(f"Whale snapshot failed for {sym}: {e}")

    # Aggregate alerts
    all_alerts = []
    for sym_data in snapshots.values():
        all_alerts.extend(sym_data.get("active_alerts", []))
    all_alerts.sort(key=lambda a: a.get("impact_score", 0), reverse=True)

    return {
        "symbols": snapshots,
        "alerts": all_alerts[:10],  # Top 10 alerts
        "tracked_symbols": TRACKED_SYMBOLS,
        "last_updated": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


async def get_whale_features(symbol: str) -> Dict[str, Any]:
    """
    Generate whale features for ML model integration.
    Returns a flat dict suitable for feature engineering.
    """
    snap = await get_whale_snapshot(symbol)

    return {
        "whale_pressure": snap.whale_pressure,
        "cot_commercials_net": snap.commercials_net,
        "cot_speculators_net": snap.speculators_net,
        "cot_whale_ratio": snap.commercials_net / max(snap.total_open_interest, 1),
        "oi_change_1w_pct": snap.oi_change_pct,
        "spec_long_pct": snap.spec_long_percent,
        "spec_positioning_percentile": snap.spec_positioning_percentile,
        "crowded_trade_risk": snap.crowded_trade_risk,
        "whale_accumulation": snap.whale_accumulation,
        "cot_confidence_adjustment": snap.confidence_adjustment,
        "smart_money_direction": snap.smart_money_direction,
        "num_alerts": len(snap.active_alerts),
    }
