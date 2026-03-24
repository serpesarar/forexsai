from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from services.data_fetcher import fetch_eod_candles, fetch_intraday_candles, fetch_ohlc_data
from services.market_regime_service import detect_regime
from services.oil_analysis_service import generate_oil_analysis

logger = logging.getLogger(__name__)

CHOKEPOINTS = [
    {
        "id": "hormuz",
        "label": "Strait of Hormuz",
        "x": 75,
        "y": 38,
        "lat": 26.5,
        "lon": 56.5,
    },
    {
        "id": "singapore",
        "label": "Singapore Anchorage",
        "x": 86,
        "y": 69,
        "lat": 1.3,
        "lon": 103.8,
    },
    {
        "id": "us_gulf",
        "label": "US Gulf",
        "x": 24,
        "y": 45,
        "lat": 29.0,
        "lon": -93.0,
    },
    {
        "id": "rotterdam",
        "label": "Rotterdam",
        "x": 49,
        "y": 24,
        "lat": 51.95,
        "lon": 4.14,
    },
]


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, float(value)))


def _round(value: float, digits: int = 2) -> float:
    return round(float(value), digits)


def _safe_close(candle: Dict[str, Any]) -> float:
    return float(candle.get("close") or 0.0)


def _pct_change(candles: List[Dict[str, Any]], lookback: int) -> float:
    if not candles or len(candles) <= lookback:
        return 0.0
    start = _safe_close(candles[-(lookback + 1)])
    end = _safe_close(candles[-1])
    if start <= 0:
        return 0.0
    return ((end / start) - 1.0) * 100.0


def _atr_pct(candles: List[Dict[str, Any]], period: int = 14) -> float:
    if not candles or len(candles) < period + 1:
        return 1.2
    trs: List[float] = []
    for idx in range(1, len(candles)):
        current = candles[idx]
        previous = candles[idx - 1]
        high = float(current.get("high") or current.get("close") or 0.0)
        low = float(current.get("low") or current.get("close") or 0.0)
        prev_close = float(previous.get("close") or 0.0)
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        trs.append(tr)
    if not trs:
        return 1.2
    atr = sum(trs[-period:]) / min(period, len(trs))
    current_price = _safe_close(candles[-1])
    if current_price <= 0:
        return 1.2
    return (atr / current_price) * 100.0


def _bias_from_edge(edge: float) -> str:
    if edge >= 12:
        return "bullish"
    if edge <= -12:
        return "bearish"
    return "neutral"


def _market_structure_label(contango_score: float, backwardation_score: float) -> str:
    diff = backwardation_score - contango_score
    if diff >= 12:
        return "backwardation"
    if diff <= -12:
        return "contango"
    return "transition"


def _horizon_for_bias(bias: str, recession_probability: float, storage_pressure: float) -> str:
    if bias == "bearish" and (recession_probability >= 62 or storage_pressure >= 62):
        return "6m"
    if bias == "neutral":
        return "immediate"
    return "3m"


def _build_trade_plan(current_price: float, atr_pct: float, bias: str, confidence: float, rationale: str) -> Dict[str, Any]:
    atr_move = current_price * max(atr_pct / 100.0, 0.008)
    if bias == "bullish":
        entry = current_price - atr_move * 0.25
        stop = current_price - atr_move * 1.1
        target = current_price + atr_move * 2.2
        direction = "long"
    elif bias == "bearish":
        entry = current_price + atr_move * 0.25
        stop = current_price + atr_move * 1.1
        target = current_price - atr_move * 2.2
        direction = "short"
    else:
        return {
            "direction": "wait",
            "instrument": "CL_Futures",
            "entry": _round(current_price, 2),
            "stop_loss": None,
            "target": None,
            "risk_reward": None,
            "confidence": _round(confidence, 1),
            "rationale": rationale,
        }

    risk = abs(entry - stop)
    reward = abs(target - entry)
    rr = reward / risk if risk > 0 else 0.0
    return {
        "direction": direction,
        "instrument": "CL_Futures",
        "entry": _round(entry, 2),
        "stop_loss": _round(stop, 2),
        "target": _round(target, 2),
        "risk_reward": _round(rr, 2),
        "confidence": _round(confidence, 1),
        "rationale": rationale,
    }


def _status_label(score: float, high_good: bool = True) -> str:
    normalized = score if high_good else 100 - score
    if normalized >= 70:
        return "strong"
    if normalized >= 55:
        return "watch"
    if normalized >= 40:
        return "balanced"
    return "soft"


def _regime_to_dict(regime: Any) -> Dict[str, Any]:
    return {
        "type": str(regime.regime),
        "adx": _round(regime.adx, 1),
        "atr_ratio": _round(regime.atr_ratio, 2),
        "session": str(regime.session),
        "swing_structure": str(regime.swing_structure),
        "allowed_directions": list(regime.allowed_directions),
        "min_rr": _round(regime.min_rr, 2),
        "is_ath_zone": bool(regime.is_ath_zone),
        "current_price": _round(regime.current_price, 2),
    }


async def build_oil_baltic_intelligence() -> Dict[str, Any]:
    symbol = "USOIL.FOREX"
    generated_at = datetime.now(timezone.utc).isoformat()

    wti_5m = await fetch_intraday_candles(symbol, "5m", 180)
    wti_1h = await fetch_ohlc_data(symbol, "1h", 240)
    wti_eod = await fetch_eod_candles(symbol, 120)

    candles_for_core = wti_5m or wti_1h or wti_eod
    current_price = _safe_close(candles_for_core[-1]) if candles_for_core else 0.0

    if not candles_for_core or current_price <= 0:
        return {
            "generated_at": generated_at,
            "symbol": symbol,
            "available": False,
            "error": "Oil intelligence data is not available yet.",
            "source_health": [
                {"name": "WTI tape", "status": "offline", "mode": "live", "note": "DataHub has not warmed this symbol yet."},
                {"name": "Baltic indices", "status": "planned", "mode": "external", "note": "Awaiting direct source integration."},
                {"name": "AIS floating storage", "status": "planned", "mode": "external", "note": "Awaiting real vessel feed integration."},
            ],
        }

    regime = await detect_regime(symbol)
    oil_analysis = await generate_oil_analysis(candles_for_core, session=regime.session)

    change_4h = _pct_change(wti_5m, 48) if wti_5m else 0.0
    change_1d = _pct_change(wti_1h, 24) if wti_1h else _pct_change(wti_eod, 1)
    change_5d = _pct_change(wti_eod, 5)
    change_20d = _pct_change(wti_eod, 20)
    atr_pct = _atr_pct(wti_1h or wti_5m or wti_eod)

    layers = oil_analysis.get("layers") or {}
    fundamental = layers.get("fundamental") or {}
    micro = layers.get("microstructure") or {}
    temporal = layers.get("temporal") or {}
    macro = layers.get("macro") or {}

    eia = fundamental.get("eia") or {}
    eia_actual = eia.get("actual")
    eia_estimate = eia.get("estimate")
    geo_level = str(fundamental.get("geo_risk_level") or "low")
    geo_bonus = {"critical": 18, "high": 12, "medium": 6, "low": 0}.get(geo_level, 0)
    vwap_distance = float(((micro.get("vwap") or {}).get("distance_pct") or 0.0))
    micro_score = float(micro.get("score") or 0.0)
    composite_score = float(oil_analysis.get("composite_score") or 0.0)

    inventory_build = max(float(eia_actual or 0.0), 0.0)
    inventory_draw = abs(min(float(eia_actual or 0.0), 0.0))
    estimate_gap = 0.0
    if eia_actual is not None and eia_estimate is not None:
        estimate_gap = float(eia_actual) - float(eia_estimate)

    dirty_strength = _clamp(50 + change_5d * 3.4 + max(change_20d, 0.0) * 1.8 + max(vwap_distance, 0.0) * 9 + geo_bonus - inventory_build * 4.5)
    clean_weakness = _clamp(50 + inventory_build * 7.0 + max(-change_5d, 0.0) * 3.3 + max(-vwap_distance, 0.0) * 11 + max(estimate_gap, 0.0) * 4.0 - inventory_draw * 3.5)
    td3c_proxy = _clamp(50 + max(change_20d, 0.0) * 2.8 + max(change_4h, 0.0) * 5.0 + (5 if regime.session in {"asia", "london_oil"} else 0) - max(-change_5d, 0.0) * 4.5)
    storage_pressure = _clamp(50 + inventory_build * 9.5 + max(-change_5d, 0.0) * 5.2 + max(-vwap_distance, 0.0) * 12 + (8 if micro_score < 0 else 0) + max(0.0, 15 - composite_score) * 0.35)
    refinery_stress = _clamp(45 + max(dirty_strength - (100 - clean_weakness), 0.0) * 0.18 + inventory_build * 6.0 + (10 if regime.regime == "RANGING" else 0) - inventory_draw * 4.0)
    crack_spread_proxy = _clamp(55 - (refinery_stress - 50) * 0.7 + max(change_20d, 0.0) * 1.8 + inventory_draw * 3.0)
    gasoline_demand_proxy = _clamp(50 - inventory_build * 6.5 + max(change_5d, 0.0) * 4.2 + max(change_1d, 0.0) * 1.5 - max(-change_1d, 0.0) * 2.5)

    contango_score = _clamp(50 + (storage_pressure - 50) * 0.62 + (clean_weakness - 50) * 0.36 - max(change_20d, 0.0) * 1.2)
    backwardation_score = _clamp(50 + (dirty_strength - 50) * 0.52 + (gasoline_demand_proxy - 50) * 0.28 + inventory_draw * 4.0 - inventory_build * 5.0)
    market_structure = _market_structure_label(contango_score, backwardation_score)

    recession_probability = _clamp(
        50
        + (clean_weakness - 50) * 0.44
        + (storage_pressure - 50) * 0.31
        + (refinery_stress - 50) * 0.22
        + (6 if oil_analysis.get("direction") == "SELL" else -3)
        + (4 if regime.regime == "STRONG_TREND_DOWN" else 0)
    )

    physical_edge = (
        (dirty_strength - 50) * 0.22
        + (td3c_proxy - 50) * 0.16
        + (crack_spread_proxy - 50) * 0.14
        + (gasoline_demand_proxy - 50) * 0.10
        + composite_score * 0.30
        - (storage_pressure - 50) * 0.24
        - (recession_probability - 50) * 0.18
    )
    oil_bias = _bias_from_edge(physical_edge)
    confidence = _clamp(abs(physical_edge) * 1.8 + float(oil_analysis.get("confidence") or 50.0) * 0.42 - 12, 34, 88)
    time_horizon = _horizon_for_bias(oil_bias, recession_probability, storage_pressure)

    rationale_parts: List[str] = []
    if clean_weakness >= 60:
        rationale_parts.append(f"clean demand stress {clean_weakness:.0f}")
    if storage_pressure >= 60:
        rationale_parts.append(f"storage pressure {storage_pressure:.0f}")
    if dirty_strength >= 60:
        rationale_parts.append(f"dirty flow strength {dirty_strength:.0f}")
    if gasoline_demand_proxy >= 60:
        rationale_parts.append(f"gasoline demand proxy {gasoline_demand_proxy:.0f}")
    if not rationale_parts:
        rationale_parts.append("mixed physical proxies")
    rationale = " + ".join(rationale_parts[:3])

    trade_recommendation = _build_trade_plan(current_price, atr_pct, oil_bias, confidence, rationale)

    chokepoints = [
        {
            **CHOKEPOINTS[0],
            "signal": "supply shock" if geo_level in {"critical", "high"} else ("active flow" if dirty_strength >= 58 else "calm"),
            "bias": "bullish" if geo_level in {"critical", "high"} or dirty_strength >= 60 else "neutral",
            "intensity": _round(_clamp(48 + geo_bonus * 1.7 + max(change_1d, 0.0) * 5.5 - max(storage_pressure - 60, 0.0) * 0.4), 1),
            "narrative": "Geopolitical route stress and prompt crude pull can accelerate risk premium.",
        },
        {
            **CHOKEPOINTS[1],
            "signal": "floating storage" if storage_pressure >= 60 else ("watch" if storage_pressure >= 50 else "drawdown"),
            "bias": "bearish" if storage_pressure >= 55 else "neutral",
            "intensity": _round(storage_pressure, 1),
            "narrative": "Storage proxy rises when builds, weak tape and contango pressure align.",
        },
        {
            **CHOKEPOINTS[2],
            "signal": "import demand" if gasoline_demand_proxy >= 58 else ("soft demand" if gasoline_demand_proxy <= 42 else "balanced"),
            "bias": "bullish" if gasoline_demand_proxy >= 58 else ("bearish" if gasoline_demand_proxy <= 42 else "neutral"),
            "intensity": _round(_clamp(gasoline_demand_proxy + max(change_1d, 0.0) * 2.2), 1),
            "narrative": "Demand proxy blends inventory surprise, tape follow-through and short-term momentum.",
        },
        {
            **CHOKEPOINTS[3],
            "signal": "refinery stress" if refinery_stress >= 58 else ("processing ok" if crack_spread_proxy >= 55 else "watch"),
            "bias": "bearish" if refinery_stress >= 58 else ("bullish" if crack_spread_proxy >= 55 else "neutral"),
            "intensity": _round(_clamp((refinery_stress * 0.6) + (100 - crack_spread_proxy) * 0.4), 1),
            "narrative": "Dirty versus clean divergence is treated as a refinery willingness proxy.",
        },
    ]

    terminal_log = [
        f"[{generated_at[11:19]}] WTI {current_price:.2f} | 1D {change_1d:+.2f}% | 5D {change_5d:+.2f}%",
        f"[{generated_at[11:19]}] Proxy BDTI {dirty_strength:.0f} | Proxy BCTI weakness {clean_weakness:.0f} | TD3C proxy {td3c_proxy:.0f}",
        f"[{generated_at[11:19]}] Storage pressure {storage_pressure:.0f} | Contango risk {contango_score:.0f} | Backwardation pressure {backwardation_score:.0f}",
        f"[{generated_at[11:19]}] Refinery stress {refinery_stress:.0f} | Crack proxy {crack_spread_proxy:.0f} | Gasoline demand {gasoline_demand_proxy:.0f}",
        f"[{generated_at[11:19]}] Oil bias {oil_bias.upper()} | Confidence {confidence:.0f}% | Horizon {time_horizon}",
    ]

    return {
        "generated_at": generated_at,
        "symbol": symbol,
        "available": True,
        "price": {
            "current": _round(current_price, 2),
            "change_4h_pct": _round(change_4h, 2),
            "change_1d_pct": _round(change_1d, 2),
            "change_5d_pct": _round(change_5d, 2),
            "change_20d_pct": _round(change_20d, 2),
            "atr_pct": _round(atr_pct, 2),
        },
        "signal": {
            "market_regime": market_structure,
            "recession_probability": _round(recession_probability, 1),
            "oil_bias": oil_bias,
            "confidence": _round(confidence, 1),
            "time_horizon": time_horizon,
            "summary": rationale,
            "physical_score": _round(_clamp(50 + physical_edge), 1),
        },
        "baltic": {
            "bdti_proxy": _round(dirty_strength, 1),
            "bcti_proxy": _round(100 - clean_weakness, 1),
            "bcti_weakness": _round(clean_weakness, 1),
            "td3c_proxy": _round(td3c_proxy, 1),
            "dirty_clean_spread": _round(dirty_strength - clean_weakness, 1),
            "status": _status_label(dirty_strength - clean_weakness + 50),
        },
        "storage": {
            "floating_storage_proxy": _round(storage_pressure, 1),
            "contango_pressure": _round(contango_score, 1),
            "backwardation_pressure": _round(backwardation_score, 1),
            "inventory_actual": _round(float(eia_actual), 2) if eia_actual is not None else None,
            "inventory_estimate": _round(float(eia_estimate), 2) if eia_estimate is not None else None,
            "status": _status_label(storage_pressure, high_good=False),
        },
        "demand": {
            "refinery_stress": _round(refinery_stress, 1),
            "crack_spread_proxy": _round(crack_spread_proxy, 1),
            "gasoline_demand_proxy": _round(gasoline_demand_proxy, 1),
            "status": _status_label(gasoline_demand_proxy),
        },
        "regime": _regime_to_dict(regime),
        "trade_recommendation": trade_recommendation,
        "key_levels": {
            "vwap": _round(float(((micro.get("vwap") or {}).get("vwap") or 0.0)), 2),
            "poc": _round(float(((micro.get("volume_profile") or {}).get("poc") or 0.0)), 2),
            "vah": _round(float(((micro.get("volume_profile") or {}).get("vah") or 0.0)), 2),
            "val": _round(float(((micro.get("volume_profile") or {}).get("val") or 0.0)), 2),
            "ema20": _round(float(((micro.get("ema") or {}).get("ema20") or 0.0)), 2),
            "ema50": _round(float(((micro.get("ema") or {}).get("ema50") or 0.0)), 2),
        },
        "chokepoints": chokepoints,
        "terminal_log": terminal_log,
        "source_health": [
            {"name": "WTI price tape", "status": "live", "mode": "DataHub", "note": "Realtime cached oil price and candles are active."},
            {"name": "Oil regime overlay", "status": "live", "mode": "internal", "note": f"Session {regime.session} and regime {regime.regime} are active."},
            {"name": "EIA inventories", "status": "live" if eia else "partial", "mode": "EOD economic calendar", "note": "Inventory surprise feeds the physical demand layer when present."},
            {"name": "Baltic indices", "status": "proxy", "mode": "model proxy", "note": "Dirty / clean / TD3C values are estimated from price, flow and inventory structure until direct feed is connected."},
            {"name": "AIS floating storage", "status": "planned", "mode": "satellite/AIS", "note": "Waiting for aisstream.io or equivalent vessel feed integration."},
        ],
        "algorithm_notes": [
            "This v1 panel uses transparent physical-market proxies instead of pretending to have live Baltic or AIS feeds.",
            "Oil bias blends existing WTI structure, EIA surprise, regime state, storage pressure and dirty-vs-clean tanker divergence logic.",
            "Best future upgrade path: real BDTI/BCTI/TD3C feed, AIS stationary tanker counts, refinery utilization and front-vs-second-month term spread.",
        ],
        "oil_engine": {
            "direction": oil_analysis.get("direction"),
            "signal_type": oil_analysis.get("signal_type"),
            "confidence": oil_analysis.get("confidence"),
            "composite_score": oil_analysis.get("composite_score"),
            "reasons": oil_analysis.get("reasons") or [],
            "risks": oil_analysis.get("risks") or [],
            "modifiers": oil_analysis.get("modifiers") or [],
            "macro": {
                "dxy_change": macro.get("dxy_change"),
                "correlation": macro.get("correlation"),
                "geo_override": macro.get("geo_override"),
            },
            "temporal": {
                "is_eia_day": temporal.get("is_eia_day"),
                "is_rollover_zone": temporal.get("is_rollover_zone"),
            },
        },
    }
