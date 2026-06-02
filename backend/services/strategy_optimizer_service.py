"""
Strategy Auto-Optimization Loop
================================
Sophisticated algorithm that calculates per-symbol risk scores and
auto-selects the best strategy based on live market conditions + historical performance.

Risk Score Components (per symbol, 0-100):
  1. VIX Fear Index          (20%) — global fear gauge, symbol-adjusted
  2. Trend Clarity (ADX+DI)  (20%) — is there a clear tradeable trend?
  3. Volatility Health (ATR)  (15%) — is volatility in a sweet spot?
  4. Choppiness Index         (15%) — trending vs ranging detection
  5. Session Quality          (15%) — best trading hours per symbol
  6. News/Event Proximity     (15%) — upcoming high-impact events

Auto-Optimization:
  - Pulls prediction_logs performance per strategy per symbol
  - Calculates: win_rate, profit_factor, avg_pips, max_drawdown
  - Bayesian composite score selects best strategy
  - Position sizing based on risk score
"""
from __future__ import annotations

import logging
import math
import numpy as np
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

TRACKED_SYMBOLS = ["NDX.INDX", "XAUUSD", "GDAXI.INDX", "USOIL.FOREX"]

SYMBOL_LABELS = {
    "NDX.INDX": "NASDAQ",
    "XAUUSD": "XAUUSD",
    "GDAXI.INDX": "DAX",
    "USOIL.FOREX": "US OIL",
}

# Component weights for final risk score
RISK_WEIGHTS = {
    "vix":        0.20,
    "trend":      0.20,
    "volatility": 0.15,
    "choppiness": 0.15,
    "session":    0.15,
    "news":       0.15,
}

# Session quality scores per symbol per session
SESSION_SCORES: Dict[str, Dict[str, int]] = {
    "NDX.INDX": {
        "asia": 15, "london": 45, "overlap_london_ny": 90,
        "newyork": 85, "xetra": 40, "xetra_us_overlap": 75,
        "nymex": 60, "london_oil": 40, "nymex_eia_window": 30,
        "closed": 5,
    },
    "XAUUSD": {
        "asia": 40, "london": 80, "overlap_london_ny": 90,
        "newyork": 70, "xetra": 65, "xetra_us_overlap": 85,
        "nymex": 50, "london_oil": 70, "nymex_eia_window": 30,
        "closed": 10,
    },
    "GDAXI.INDX": {
        "asia": 10, "london": 60, "overlap_london_ny": 70,
        "newyork": 45, "xetra": 90, "xetra_us_overlap": 95,
        "nymex": 35, "london_oil": 55, "nymex_eia_window": 20,
        "closed": 5,
    },
    "USOIL.FOREX": {
        "asia": 20, "london": 50, "overlap_london_ny": 75,
        "newyork": 70, "xetra": 40, "xetra_us_overlap": 65,
        "nymex": 90, "london_oil": 65, "nymex_eia_window": 95,
        "closed": 5,
    },
}

# VIX regime adjustments per symbol type
# equity_like: high VIX = bad (NASDAQ, DAX)
# safe_haven: high VIX = opportunity (XAUUSD)
# commodity: high VIX = high vol, mixed (US OIL)
SYMBOL_VIX_TYPE = {
    "NDX.INDX": "equity",
    "XAUUSD": "safe_haven",
    "GDAXI.INDX": "equity",
    "USOIL.FOREX": "commodity",
}

ALL_STRATEGIES = ["ultra_safe", "balanced", "full_power", "aggressive", "nasdaq_precision"]


# ═══════════════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class RiskComponent:
    name: str
    score: float        # 0-100
    weight: float       # 0-1
    label: str          # human readable
    detail: str = ""    # extra info


@dataclass
class SymbolRisk:
    symbol: str
    label: str
    overall_score: float              # 0-100 weighted composite
    risk_level: str                   # OPTIMAL / FAVORABLE / MODERATE / HIGH_RISK / DANGER
    components: List[RiskComponent] = field(default_factory=list)
    regime: str = "TRANSITION"
    session: str = "unknown"
    recommended_strategy: str = "balanced"
    recommended_position_pct: float = 1.0   # 0-2 (percentage of normal size)
    trend_direction: str = "NEUTRAL"


@dataclass
class StrategyScore:
    strategy: str
    symbol: str
    win_rate: float
    total_signals: int
    wins: int
    losses: int
    avg_profit_pips: float
    avg_loss_pips: float
    profit_factor: float
    max_consecutive_losses: int
    composite_score: float     # 0-100 Bayesian composite
    is_recommended: bool = False


@dataclass
class OptimizationResult:
    timestamp: str
    symbols: List[SymbolRisk]
    strategy_scores: Dict[str, List[StrategyScore]]   # symbol -> list of scored strategies
    global_risk_score: float                            # 0-100 overall market risk
    global_risk_level: str
    optimization_notes: List[str] = field(default_factory=list)
    vix_price: Optional[float] = None
    vix_regime: str = "NORMAL"
    market_open: bool = True


# ═══════════════════════════════════════════════════════════════════════════════
# RISK COMPONENT CALCULATORS
# ═══════════════════════════════════════════════════════════════════════════════

def _score_vix(vix_price: Optional[float], symbol: str) -> RiskComponent:
    """Score VIX fear index, adjusted per symbol type."""
    if vix_price is None or vix_price <= 0:
        return RiskComponent("vix", 50, RISK_WEIGHTS["vix"], "VIX Unknown", "No VIX data")

    vix_type = SYMBOL_VIX_TYPE.get(symbol, "equity")

    # Base VIX score (equity perspective: low VIX = good)
    if vix_price < 12:
        base = 92
        regime = "EXTREME_LOW"
    elif vix_price < 16:
        base = 82
        regime = "LOW"
    elif vix_price < 20:
        base = 68
        regime = "NORMAL"
    elif vix_price < 25:
        base = 45
        regime = "ELEVATED"
    elif vix_price < 30:
        base = 28
        regime = "HIGH"
    elif vix_price < 40:
        base = 15
        regime = "VERY_HIGH"
    else:
        base = 5
        regime = "EXTREME"

    # Symbol-type adjustments
    if vix_type == "safe_haven":
        # Gold benefits from fear — invert partially
        # High VIX = gold demand up = opportunity
        if vix_price > 25:
            base = min(85, base + 40)   # High VIX is GOOD for gold
        elif vix_price > 20:
            base = min(80, base + 20)
        # Very low VIX = less gold demand
        if vix_price < 14:
            base = max(30, base - 20)
    elif vix_type == "commodity":
        # Oil: high VIX = chaotic, moderate VIX = ok
        if vix_price > 30:
            base = max(15, base - 5)    # Very high VIX is bad for oil too
        elif 18 < vix_price < 28:
            base = min(70, base + 10)   # Moderate fear = vol opportunities

    return RiskComponent(
        "vix", round(base, 1), RISK_WEIGHTS["vix"],
        f"VIX {regime}",
        f"VIX={vix_price:.1f} ({regime})"
    )


def _score_trend(adx: float, di_spread: float, structure: str) -> RiskComponent:
    """Score trend clarity using ADX + DI spread + swing structure."""
    # ADX component (0-50 points)
    if adx >= 35:
        adx_pts = 48
    elif adx >= 25:
        adx_pts = 38
    elif adx >= 20:
        adx_pts = 25
    elif adx >= 15:
        adx_pts = 15
    else:
        adx_pts = 5

    # DI spread component (0-30 points)
    if di_spread >= 20:
        di_pts = 28
    elif di_spread >= 12:
        di_pts = 20
    elif di_spread >= 6:
        di_pts = 10
    else:
        di_pts = 2

    # Structure component (0-20 points)
    struct_pts = {"bullish": 18, "bearish": 18, "neutral": 5}.get(structure, 5)

    score = min(100, adx_pts + di_pts + struct_pts)

    if score >= 75:
        label = "STRONG TREND"
    elif score >= 50:
        label = "MODERATE TREND"
    elif score >= 30:
        label = "WEAK TREND"
    else:
        label = "NO TREND"

    return RiskComponent(
        "trend", round(score, 1), RISK_WEIGHTS["trend"],
        label,
        f"ADX={adx:.1f} DI_spread={di_spread:.1f} struct={structure}"
    )


def _score_volatility(atr_ratio: float) -> RiskComponent:
    """Score volatility health — sweet spot is 0.8-1.3."""
    if 0.85 <= atr_ratio <= 1.25:
        score = 85    # Sweet spot
    elif 0.7 <= atr_ratio <= 1.5:
        score = 65    # Acceptable
    elif 0.5 <= atr_ratio <= 1.8:
        score = 40    # Elevated
    elif atr_ratio > 1.8:
        score = max(5, 30 - (atr_ratio - 1.8) * 20)  # Too volatile
    else:
        score = max(10, 50 - (0.5 - atr_ratio) * 60)  # Too quiet

    score = max(0, min(100, score))

    if score >= 70:
        label = "HEALTHY"
    elif score >= 45:
        label = "ELEVATED"
    elif score >= 25:
        label = "HIGH VOL"
    else:
        label = "EXTREME"

    return RiskComponent(
        "volatility", round(score, 1), RISK_WEIGHTS["volatility"],
        label,
        f"ATR_ratio={atr_ratio:.2f}"
    )


def _score_choppiness(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> RiskComponent:
    """
    Choppiness Index (CI): measures whether market is trending or choppy.
    CI = 100 * LOG10(SUM(ATR, period) / (highest_high - lowest_low)) / LOG10(period)
    CI > 61.8 = choppy, CI < 38.2 = trending
    """
    n = len(closes)
    if n < period + 2:
        return RiskComponent("choppiness", 40, RISK_WEIGHTS["choppiness"], "UNKNOWN", "Insufficient data")

    # True Range
    tr = np.maximum(
        highs[1:] - lows[1:],
        np.maximum(np.abs(highs[1:] - closes[:-1]), np.abs(lows[1:] - closes[:-1]))
    )

    if len(tr) < period:
        return RiskComponent("choppiness", 40, RISK_WEIGHTS["choppiness"], "UNKNOWN", "Insufficient TR data")

    atr_sum = float(np.sum(tr[-period:]))
    highest = float(np.max(highs[-period:]))
    lowest = float(np.min(lows[-period:]))
    hl_range = highest - lowest

    if hl_range <= 0 or atr_sum <= 0:
        return RiskComponent("choppiness", 40, RISK_WEIGHTS["choppiness"], "UNKNOWN", "Flat market")

    ci = 100.0 * math.log10(atr_sum / hl_range) / math.log10(period)
    ci = max(0, min(100, ci))

    # Invert: low CI = trending = good for trading
    if ci < 38.2:
        score = 88    # Trending — great
    elif ci < 45:
        score = 72
    elif ci < 50:
        score = 55
    elif ci < 55:
        score = 40
    elif ci < 61.8:
        score = 25
    else:
        score = 10    # Very choppy — avoid

    if score >= 65:
        label = "TRENDING"
    elif score >= 40:
        label = "TRANSITIONING"
    else:
        label = "CHOPPY"

    return RiskComponent(
        "choppiness", round(score, 1), RISK_WEIGHTS["choppiness"],
        label,
        f"CI={ci:.1f}"
    )


def _score_session(symbol: str) -> RiskComponent:
    """Score current market session quality for this symbol."""
    from services.market_regime_service import _detect_session
    session = _detect_session(symbol)
    scores = SESSION_SCORES.get(symbol, {})
    score = scores.get(session, 30)

    if score >= 80:
        label = "PRIME TIME"
    elif score >= 60:
        label = "GOOD SESSION"
    elif score >= 40:
        label = "OK SESSION"
    elif score >= 20:
        label = "QUIET SESSION"
    else:
        label = "OFF HOURS"

    return RiskComponent(
        "session", score, RISK_WEIGHTS["session"],
        label,
        f"session={session}"
    )


def _score_news_proximity() -> RiskComponent:
    """
    Score based on upcoming high-impact news proximity.
    Uses economic calendar data if available, else defaults to safe score.
    """
    # Try to check COMEX/news service for upcoming events
    score = 65  # Default: no imminent high-impact events
    label = "CLEAR"
    detail = "No high-impact events detected"

    try:
        now = datetime.now(timezone.utc)
        hour = now.hour
        weekday = now.weekday()

        # Known high-impact windows (simplified heuristic)
        # NFP: First Friday of month, 13:30 UTC
        # FOMC: ~18:00 UTC on meeting days (8 per year)
        # CPI: ~13:30 UTC, usually 10th-13th of month
        # ECB: ~12:45 UTC on meeting days

        is_first_friday = weekday == 4 and now.day <= 7
        is_cpi_window = 10 <= now.day <= 14 and weekday < 5
        is_fomc_window = weekday == 2 and now.day >= 15  # Rough heuristic

        # EIA Wednesday 15:30 UTC
        is_eia = weekday == 2 and 15 <= hour <= 16

        if is_first_friday and 12 <= hour <= 15:
            score = 10
            label = "NFP RISK"
            detail = "Non-Farm Payrolls window"
        elif is_first_friday and 10 <= hour <= 12:
            score = 25
            label = "PRE-NFP"
            detail = "NFP approaching"
        elif is_fomc_window and 17 <= hour <= 20:
            score = 8
            label = "FOMC RISK"
            detail = "FOMC decision window"
        elif is_cpi_window and 12 <= hour <= 14:
            score = 15
            label = "CPI RISK"
            detail = "CPI release window"
        elif is_eia:
            score = 35
            label = "EIA RISK"
            detail = "EIA Oil Inventory report"
        elif weekday >= 5:
            score = 10
            label = "WEEKEND"
            detail = "Markets closed"
        elif hour < 7 or hour >= 21:
            score = 40
            label = "OFF HOURS"
            detail = "Low liquidity period"
        else:
            score = 75
            label = "CLEAR"
            detail = "No major events nearby"

    except Exception as e:
        logger.warning(f"News proximity scoring error: {e}")

    return RiskComponent(
        "news", score, RISK_WEIGHTS["news"],
        label,
        detail
    )


# ═══════════════════════════════════════════════════════════════════════════════
# RISK LEVEL CLASSIFIER
# ═══════════════════════════════════════════════════════════════════════════════

def _classify_risk(score: float) -> str:
    if score >= 75:
        return "OPTIMAL"
    elif score >= 60:
        return "FAVORABLE"
    elif score >= 42:
        return "MODERATE"
    elif score >= 25:
        return "HIGH_RISK"
    else:
        return "DANGER"


def _position_sizing(risk_score: float) -> float:
    """Calculate recommended position size multiplier (0.0 - 2.0)."""
    if risk_score >= 80:
        return 1.5     # Increase size in optimal conditions
    elif risk_score >= 65:
        return 1.0     # Normal size
    elif risk_score >= 50:
        return 0.7     # Reduce size
    elif risk_score >= 35:
        return 0.4     # Significant reduction
    elif risk_score >= 20:
        return 0.2     # Minimal size
    else:
        return 0.0     # Don't trade


# ═══════════════════════════════════════════════════════════════════════════════
# AUTO-OPTIMIZATION: STRATEGY SCORING
# ═══════════════════════════════════════════════════════════════════════════════

async def _score_strategies(symbol: str, days: int = 14) -> List[StrategyScore]:
    """
    Query prediction_logs and score each strategy's historical performance.
    Uses Bayesian approach: blend prior (50% default) with observed data.
    """
    from database.supabase_client import get_client

    scores: List[StrategyScore] = []
    client = get_client()
    if not client:
        # Return default scores
        for strat in ALL_STRATEGIES:
            scores.append(StrategyScore(
                strategy=strat, symbol=symbol,
                win_rate=50.0, total_signals=0, wins=0, losses=0,
                avg_profit_pips=0, avg_loss_pips=0, profit_factor=1.0,
                max_consecutive_losses=0, composite_score=50.0,
            ))
        return scores

    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    try:
        result = client.table("prediction_logs").select(
            "strategy,status,targets_hit,highest_profit_pips,lowest_drawdown_pips,ml_direction,ml_confidence"
        ).eq("symbol", symbol).gte("created_at", cutoff).neq("status", "active").execute()

        rows = result if isinstance(result, list) else []
    except Exception as e:
        logger.warning(f"Strategy scoring query error for {symbol}: {e}")
        rows = []

    # Group by strategy
    strat_data: Dict[str, List[dict]] = {s: [] for s in ALL_STRATEGIES}
    for row in rows:
        strat = row.get("strategy", "balanced")
        if strat in strat_data:
            strat_data[strat].append(row)
        else:
            strat_data.setdefault("balanced", []).append(row)

    for strat, signals in strat_data.items():
        total = len(signals)
        wins = sum(1 for s in signals if s.get("status") == "completed")
        losses = sum(1 for s in signals if s.get("status") == "stopped")
        expired = sum(1 for s in signals if s.get("status") == "expired")

        # Win rate with Bayesian prior (prior = 50%, weight = 10 virtual samples)
        prior_wins = 5
        prior_total = 10
        bayesian_wr = ((wins + prior_wins) / (total + prior_total)) * 100

        # Profit/loss stats
        profits = [float(s.get("highest_profit_pips") or 0) for s in signals if s.get("status") == "completed"]
        losses_pips = [abs(float(s.get("lowest_drawdown_pips") or 0)) for s in signals if s.get("status") == "stopped"]

        avg_profit = float(np.mean(profits)) if profits else 0
        avg_loss = float(np.mean(losses_pips)) if losses_pips else 1

        # Profit factor
        total_profit = sum(profits)
        total_loss = sum(losses_pips) if losses_pips else 1
        pf = total_profit / max(total_loss, 0.01)
        pf = min(pf, 10)  # Cap at 10

        # Max consecutive losses
        max_consec = 0
        current_consec = 0
        for s in signals:
            if s.get("status") == "stopped":
                current_consec += 1
                max_consec = max(max_consec, current_consec)
            else:
                current_consec = 0

        # Composite score: weighted combination
        # - Win rate (40%): Bayesian win rate
        # - Profit factor (30%): capped, log-scaled
        # - Sample confidence (20%): more data = more confidence
        # - Drawdown penalty (10%): penalize high consecutive losses

        wr_score = bayesian_wr  # 0-100
        pf_score = min(100, max(0, (math.log10(max(pf, 0.1)) + 1) * 50))  # log scale
        sample_score = min(100, total * 5)  # 20 signals = 100
        dd_penalty = max(0, 100 - max_consec * 15)  # Each consecutive loss = -15

        composite = (
            wr_score * 0.40 +
            pf_score * 0.30 +
            sample_score * 0.20 +
            dd_penalty * 0.10
        )

        scores.append(StrategyScore(
            strategy=strat,
            symbol=symbol,
            win_rate=round(bayesian_wr, 1),
            total_signals=total,
            wins=wins,
            losses=losses,
            avg_profit_pips=round(avg_profit, 2),
            avg_loss_pips=round(avg_loss, 2),
            profit_factor=round(pf, 2),
            max_consecutive_losses=max_consec,
            composite_score=round(composite, 1),
        ))

    # Mark best strategy
    if scores:
        best = max(scores, key=lambda s: s.composite_score)
        best.is_recommended = True

    return scores


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN: RUN OPTIMIZATION
# ═══════════════════════════════════════════════════════════════════════════════

async def run_optimization(days: int = 14) -> OptimizationResult:
    """
    Main entry point. Computes risk scores for all symbols and optimizes strategies.
    """
    from services.data_hub import get_macro
    from services.market_regime_service import detect_regime, _detect_session
    from services.market_data_service import get_ohlcv_data

    timestamp = datetime.now(timezone.utc).isoformat()

    # ── 1. Get macro data (VIX, DXY, etc.) ──
    macro = get_macro()
    vix_data = macro.get("vix", {})
    vix_price = vix_data.get("price")

    if vix_price is None or vix_price == 0:
        # Fallback: try direct fetch
        try:
            from services.data_fetcher import fetch_latest_price
            vix_raw = await fetch_latest_price("VIX.INDX")
            vix_price = float(vix_raw) if vix_raw else None
        except Exception:
            vix_price = None

    vix_regime = "UNKNOWN"
    if vix_price:
        if vix_price < 14:
            vix_regime = "LOW"
        elif vix_price < 20:
            vix_regime = "NORMAL"
        elif vix_price < 28:
            vix_regime = "ELEVATED"
        elif vix_price < 38:
            vix_regime = "HIGH"
        else:
            vix_regime = "EXTREME"

    # ── 2. Compute per-symbol risk scores ──
    symbols_result: List[SymbolRisk] = []
    all_strategy_scores: Dict[str, List[StrategyScore]] = {}
    notes: List[str] = []

    # Pre-calculate shared components
    news_component = _score_news_proximity()

    for symbol in TRACKED_SYMBOLS:
        try:
            # Get regime data
            regime = await detect_regime(symbol)
            session = _detect_session(symbol)

            # Get OHLCV for choppiness calc
            ohlcv = await get_ohlcv_data(symbol, "1H", limit=60)
            if ohlcv and len(ohlcv) >= 20:
                highs = np.array([c["high"] for c in ohlcv], dtype=np.float64)
                lows = np.array([c["low"] for c in ohlcv], dtype=np.float64)
                closes = np.array([c["close"] for c in ohlcv], dtype=np.float64)
            else:
                highs = np.array([1.0])
                lows = np.array([1.0])
                closes = np.array([1.0])

            # ── Calculate all risk components ──
            comp_vix = _score_vix(vix_price, symbol)
            comp_trend = _score_trend(regime.adx, regime.details.get("di_spread", 10), regime.swing_structure)
            comp_vol = _score_volatility(regime.atr_ratio)
            comp_chop = _score_choppiness(highs, lows, closes)
            comp_session = _score_session(symbol)

            components = [comp_vix, comp_trend, comp_vol, comp_chop, comp_session, news_component]

            # Weighted sum
            overall = sum(c.score * c.weight for c in components)
            overall = round(max(0, min(100, overall)), 1)

            risk_level = _classify_risk(overall)
            pos_size = _position_sizing(overall)

            # Trend direction
            if regime.swing_structure == "bullish":
                trend_dir = "BULLISH"
            elif regime.swing_structure == "bearish":
                trend_dir = "BEARISH"
            else:
                trend_dir = "NEUTRAL"

            # ── Strategy optimization ──
            strat_scores = await _score_strategies(symbol, days)
            all_strategy_scores[symbol] = strat_scores

            recommended = next((s.strategy for s in strat_scores if s.is_recommended), "balanced")

            # Override: if risk is DANGER, force ultra_safe
            if risk_level == "DANGER":
                recommended = "ultra_safe"
                notes.append(f"{SYMBOL_LABELS[symbol]}: Forced ultra_safe due to DANGER risk level")

            symbols_result.append(SymbolRisk(
                symbol=symbol,
                label=SYMBOL_LABELS[symbol],
                overall_score=overall,
                risk_level=risk_level,
                components=components,
                regime=regime.regime,
                session=session,
                recommended_strategy=recommended,
                recommended_position_pct=pos_size,
                trend_direction=trend_dir,
            ))

        except Exception as e:
            logger.error(f"Risk calculation error for {symbol}: {e}")
            symbols_result.append(SymbolRisk(
                symbol=symbol,
                label=SYMBOL_LABELS[symbol],
                overall_score=40,
                risk_level="MODERATE",
                components=[],
                regime="UNKNOWN",
                session="unknown",
            ))

    # ── 3. Global risk score ──
    if symbols_result:
        global_score = round(sum(s.overall_score for s in symbols_result) / len(symbols_result), 1)
    else:
        global_score = 50.0

    global_level = _classify_risk(global_score)

    # Check market open
    now = datetime.now(timezone.utc)
    is_weekend = now.weekday() >= 5
    market_open = not is_weekend

    if is_weekend:
        notes.append("Markets closed — weekend")

    return OptimizationResult(
        timestamp=timestamp,
        symbols=symbols_result,
        strategy_scores=all_strategy_scores,
        global_risk_score=global_score,
        global_risk_level=global_level,
        optimization_notes=notes,
        vix_price=vix_price,
        vix_regime=vix_regime,
        market_open=market_open,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# SERIALIZER
# ═══════════════════════════════════════════════════════════════════════════════

def serialize_result(result: OptimizationResult) -> Dict[str, Any]:
    """Convert to JSON-serializable dict."""
    return {
        "timestamp": result.timestamp,
        "global_risk_score": result.global_risk_score,
        "global_risk_level": result.global_risk_level,
        "vix_price": result.vix_price,
        "vix_regime": result.vix_regime,
        "market_open": result.market_open,
        "optimization_notes": result.optimization_notes,
        "symbols": [
            {
                "symbol": s.symbol,
                "label": s.label,
                "overall_score": s.overall_score,
                "risk_level": s.risk_level,
                "regime": s.regime,
                "session": s.session,
                "recommended_strategy": s.recommended_strategy,
                "recommended_position_pct": s.recommended_position_pct,
                "trend_direction": s.trend_direction,
                "components": [
                    {
                        "name": c.name,
                        "score": c.score,
                        "weight": c.weight,
                        "label": c.label,
                        "detail": c.detail,
                    }
                    for c in s.components
                ],
            }
            for s in result.symbols
        ],
        "strategy_scores": {
            sym: [
                {
                    "strategy": ss.strategy,
                    "win_rate": ss.win_rate,
                    "total_signals": ss.total_signals,
                    "wins": ss.wins,
                    "losses": ss.losses,
                    "avg_profit_pips": ss.avg_profit_pips,
                    "avg_loss_pips": ss.avg_loss_pips,
                    "profit_factor": ss.profit_factor,
                    "max_consecutive_losses": ss.max_consecutive_losses,
                    "composite_score": ss.composite_score,
                    "is_recommended": ss.is_recommended,
                }
                for ss in scores
            ]
            for sym, scores in result.strategy_scores.items()
        },
    }
