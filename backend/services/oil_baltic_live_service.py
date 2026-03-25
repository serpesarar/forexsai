from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from services.baltic_index_service import get_baltic_snapshot
from services.data_fetcher import fetch_eod_candles, fetch_intraday_candles, fetch_ohlc_data
from services.mapbox_usage_guard import get_mapbox_web_load_status
from services.market_regime_service import detect_regime
from services.oil_analysis_service import generate_oil_analysis
from services.oil_maritime_data_service import get_chokepoint_metrics, get_recent_tankers, refresh_chokepoint_metrics
from database.supabase_client import get_auth_error, is_auth_failed

CHOKEPOINT_LAYOUT = {
    "strait_of_hormuz": {"id": "hormuz", "label": "Strait of Hormuz", "x": 75, "y": 38, "lat": 26.5, "lon": 56.5},
    "singapore_anchorage": {"id": "singapore", "label": "Singapore Anchorage", "x": 86, "y": 69, "lat": 1.3, "lon": 103.8},
    "us_gulf": {"id": "us_gulf", "label": "US Gulf", "x": 24, "y": 45, "lat": 29.0, "lon": -93.0},
    "rotterdam": {"id": "rotterdam", "label": "Rotterdam", "x": 49, "y": 24, "lat": 51.95, "lon": 4.14},
}


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, float(value)))


def _round(value: Optional[float], digits: int = 2) -> Optional[float]:
    if value is None:
        return None
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
        trs.append(max(high - low, abs(high - prev_close), abs(low - prev_close)))
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
    return {
        "direction": direction,
        "instrument": "CL_Futures",
        "entry": _round(entry, 2),
        "stop_loss": _round(stop, 2),
        "target": _round(target, 2),
        "risk_reward": _round(reward / risk if risk > 0 else 0.0, 2),
        "confidence": _round(confidence, 1),
        "rationale": rationale,
    }


def _normalize_baltic_value(value: Optional[float], baseline: float, spread: float, change_percent: Optional[float]) -> float:
    if value is None:
        return 50.0
    level_component = ((float(value) - baseline) / spread) * 18.0
    change_component = (float(change_percent or 0.0)) * 2.4
    return _clamp(50.0 + level_component + change_component)


def _build_chokepoints(metrics_map: Dict[str, Dict[str, Any]], fallback_signals: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for region, layout in CHOKEPOINT_LAYOUT.items():
        metric = metrics_map.get(region) or {}
        fallback = fallback_signals.get(region) or {}
        intensity = metric.get("congestion_score")
        if intensity is None:
            intensity = fallback.get("intensity", 50.0)
        signal = metric.get("signal") or fallback.get("signal") or "watch"
        bias = metric.get("pressure_bias") or fallback.get("bias") or "neutral"
        storage = metric.get("storage_estimate_mm_bbl")
        vessel_count = metric.get("vessel_count")
        narrative_parts = []
        if vessel_count is not None:
            narrative_parts.append(f"{int(vessel_count)} active tankers")
        if storage is not None and float(storage) > 0:
            narrative_parts.append(f"{float(storage):.2f}m bbl storage")
        if not narrative_parts:
            narrative_parts.append(fallback.get("narrative") or "Awaiting live tanker flow")
        items.append({
            **layout,
            "signal": signal,
            "bias": bias,
            "intensity": _round(float(intensity), 1),
            "narrative": " | ".join(narrative_parts),
            "vessel_count": vessel_count,
            "storage_estimate_mm_bbl": storage,
        })
    return items


async def build_oil_baltic_intelligence() -> Dict[str, Any]:
    symbol = "USOIL.FOREX"
    generated_at = datetime.now(timezone.utc).isoformat()

    wti_5m, wti_1h, wti_eod, regime, baltic_snapshot = await asyncio.gather(
        fetch_intraday_candles(symbol, "5m", 180),
        fetch_ohlc_data(symbol, "1h", 240),
        fetch_eod_candles(symbol, 120),
        detect_regime(symbol),
        get_baltic_snapshot(),
    )

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
                {"name": "Baltic indices", "status": "partial", "mode": "public web/cache", "note": "Indices can sync, but oil tape is not ready."},
                {"name": "AIS floating storage", "status": "planned", "mode": "aisstream", "note": "Collector needs AISSTREAM_API_KEY and runtime."},
            ],
        }

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
    estimate_gap = float(eia_actual) - float(eia_estimate) if eia_actual is not None and eia_estimate is not None else 0.0

    bdti_row = baltic_snapshot.get("BDTI") or {}
    bcti_row = baltic_snapshot.get("BCTI") or {}
    td3c_row = baltic_snapshot.get("TD3C") or {}

    bdti_live_score = _normalize_baltic_value(bdti_row.get("value"), 1000.0, 500.0, bdti_row.get("change_percent")) if bdti_row else None
    bcti_live_score = _normalize_baltic_value(bcti_row.get("value"), 800.0, 350.0, bcti_row.get("change_percent")) if bcti_row else None
    td3c_live_score = _normalize_baltic_value(td3c_row.get("value"), 35.0, 20.0, td3c_row.get("change_percent")) if td3c_row else None

    dirty_strength_proxy = _clamp(50 + change_5d * 3.4 + max(change_20d, 0.0) * 1.8 + max(vwap_distance, 0.0) * 9 + geo_bonus - inventory_build * 4.5)
    clean_weakness_proxy = _clamp(50 + inventory_build * 7.0 + max(-change_5d, 0.0) * 3.3 + max(-vwap_distance, 0.0) * 11 + max(estimate_gap, 0.0) * 4.0 - inventory_draw * 3.5)
    td3c_proxy = _clamp(50 + max(change_20d, 0.0) * 2.8 + max(change_4h, 0.0) * 5.0 + (5 if regime.session in {"asia", "london_oil"} else 0) - max(-change_5d, 0.0) * 4.5)

    dirty_strength = bdti_live_score if bdti_live_score is not None else dirty_strength_proxy
    bcti_strength = bcti_live_score if bcti_live_score is not None else _clamp(100 - clean_weakness_proxy)
    clean_weakness = _clamp(100 - bcti_strength)
    td3c_score = td3c_live_score if td3c_live_score is not None else td3c_proxy

    metrics_map = get_chokepoint_metrics()
    if not metrics_map and not is_auth_failed():
        refresh_chokepoint_metrics()
        metrics_map = get_chokepoint_metrics()
    tankers = get_recent_tankers(limit=120, freshness_hours=72)
    mapbox_guard = get_mapbox_web_load_status()

    storage_regions = [metrics_map.get("singapore_anchorage") or {}, metrics_map.get("rotterdam") or {}]
    floating_storage_vessels = sum(int(region.get("floating_storage_vessels") or 0) for region in storage_regions)
    floating_storage_mm_bbl = sum(float(region.get("storage_estimate_mm_bbl") or 0.0) for region in storage_regions)
    live_congestion = max([float((region.get("congestion_score") or 0.0)) for region in metrics_map.values()] or [0.0])

    storage_pressure_proxy = _clamp(50 + inventory_build * 9.5 + max(-change_5d, 0.0) * 5.2 + max(-vwap_distance, 0.0) * 12 + (8 if micro_score < 0 else 0) + max(0.0, 15 - composite_score) * 0.35)
    storage_pressure = _clamp(storage_pressure_proxy + floating_storage_vessels * 6.5 + floating_storage_mm_bbl * 1.8 + live_congestion * 0.15)
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
        + (td3c_score - 50) * 0.16
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
    if bdti_row:
        rationale_parts.append(f"BDTI {float(bdti_row.get('value') or 0):.0f}")
    if floating_storage_mm_bbl > 0:
        rationale_parts.append(f"storage {floating_storage_mm_bbl:.2f}m bbl")
    if clean_weakness >= 60:
        rationale_parts.append(f"clean weakness {clean_weakness:.0f}")
    if gasoline_demand_proxy >= 60:
        rationale_parts.append(f"gasoline proxy {gasoline_demand_proxy:.0f}")
    if not rationale_parts:
        rationale_parts.append("mixed physical inputs")
    rationale = " + ".join(rationale_parts[:3])

    fallback_signals = {
        "strait_of_hormuz": {
            "signal": "supply shock" if geo_level in {"critical", "high"} else ("active flow" if dirty_strength >= 58 else "calm"),
            "bias": "bullish" if geo_level in {"critical", "high"} or dirty_strength >= 60 else "neutral",
            "intensity": _clamp(48 + geo_bonus * 1.7 + max(change_1d, 0.0) * 5.5 - max(storage_pressure - 60, 0.0) * 0.4),
            "narrative": "Geopolitical route stress and prompt crude pull can accelerate risk premium.",
        },
        "singapore_anchorage": {
            "signal": "floating storage" if storage_pressure >= 60 else ("watch" if storage_pressure >= 50 else "drawdown"),
            "bias": "bearish" if storage_pressure >= 55 else "neutral",
            "intensity": storage_pressure,
            "narrative": "Storage pressure rises when anchored tanker counts and contango both increase.",
        },
        "us_gulf": {
            "signal": "import demand" if gasoline_demand_proxy >= 58 else ("soft demand" if gasoline_demand_proxy <= 42 else "balanced"),
            "bias": "bullish" if gasoline_demand_proxy >= 58 else ("bearish" if gasoline_demand_proxy <= 42 else "neutral"),
            "intensity": _clamp(gasoline_demand_proxy + max(change_1d, 0.0) * 2.2),
            "narrative": "Demand proxy blends inventory surprise and tape follow-through.",
        },
        "rotterdam": {
            "signal": "refinery stress" if refinery_stress >= 58 else ("processing ok" if crack_spread_proxy >= 55 else "watch"),
            "bias": "bearish" if refinery_stress >= 58 else ("bullish" if crack_spread_proxy >= 55 else "neutral"),
            "intensity": _clamp((refinery_stress * 0.6) + (100 - crack_spread_proxy) * 0.4),
            "narrative": "Dirty versus clean divergence proxies refinery willingness.",
        },
    }

    chokepoints = _build_chokepoints(metrics_map, fallback_signals)
    trade_recommendation = _build_trade_plan(current_price, atr_pct, oil_bias, confidence, rationale)

    baltic_status = "live" if bdti_row or bcti_row else "proxy"
    td3c_status = "live" if td3c_row else "proxy"
    ais_status = "unavailable" if is_auth_failed() else ("live" if metrics_map else "planned")
    ais_note = get_auth_error() or "Collector needs AISSTREAM_API_KEY and database cache access."

    terminal_log = [
        f"[{generated_at[11:19]}] WTI {current_price:.2f} | 1D {change_1d:+.2f}% | 5D {change_5d:+.2f}%",
        f"[{generated_at[11:19]}] BDTI {bdti_row.get('value', 'proxy')} | BCTI {bcti_row.get('value', 'proxy')} | TD3C {td3c_row.get('value', 'proxy')}",
        f"[{generated_at[11:19]}] Storage {floating_storage_mm_bbl:.2f}m bbl | Floating tankers {floating_storage_vessels} | Contango {contango_score:.0f}",
        f"[{generated_at[11:19]}] Dirty {dirty_strength:.0f} | Clean weakness {clean_weakness:.0f} | Demand {gasoline_demand_proxy:.0f}",
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
            "bcti_proxy": _round(bcti_strength, 1),
            "bcti_weakness": _round(clean_weakness, 1),
            "td3c_proxy": _round(td3c_score, 1),
            "dirty_clean_spread": _round(dirty_strength - clean_weakness, 1),
            "status": _status_label(dirty_strength - clean_weakness + 50),
            "bdti_value": _round(bdti_row.get("value"), 2) if bdti_row else None,
            "bcti_value": _round(bcti_row.get("value"), 2) if bcti_row else None,
            "td3c_value": _round(td3c_row.get("value"), 2) if td3c_row else None,
            "bdti_change_percent": _round(bdti_row.get("change_percent"), 2) if bdti_row else None,
            "bcti_change_percent": _round(bcti_row.get("change_percent"), 2) if bcti_row else None,
            "td3c_change_percent": _round(td3c_row.get("change_percent"), 2) if td3c_row else None,
            "source_mode": baltic_status,
            "td3c_source_mode": td3c_status,
        },
        "storage": {
            "floating_storage_proxy": _round(storage_pressure, 1),
            "contango_pressure": _round(contango_score, 1),
            "backwardation_pressure": _round(backwardation_score, 1),
            "inventory_actual": _round(float(eia_actual), 2) if eia_actual is not None else None,
            "inventory_estimate": _round(float(eia_estimate), 2) if eia_estimate is not None else None,
            "floating_storage_vessels": floating_storage_vessels,
            "floating_storage_mm_bbl": _round(floating_storage_mm_bbl, 2),
            "status": _status_label(storage_pressure, high_good=False),
            "source_mode": ais_status,
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
        "tankers": tankers,
        "mapbox_guard": mapbox_guard,
        "terminal_log": terminal_log,
        "source_health": [
            {"name": "WTI price tape", "status": "live", "mode": "DataHub", "note": "Realtime cached oil price and candles are active."},
            {"name": "Oil regime overlay", "status": "live", "mode": "internal", "note": f"Session {regime.session} and regime {regime.regime} are active."},
            {"name": "EIA inventories", "status": "live" if eia else "partial", "mode": "EOD economic calendar", "note": "Inventory surprise feeds the physical demand layer when present."},
            {"name": "Baltic indices", "status": baltic_status, "mode": "public web/cache", "note": "BDTI/BCTI sync from public source when available, otherwise cached or fallback-normalized."},
            {"name": "TD3C route", "status": td3c_status, "mode": "configured source/cache", "note": "TD3C stays optional until a stable free source is configured."},
            {"name": "AIS floating storage", "status": "live" if metrics_map else ("error" if is_auth_failed() else "planned"), "mode": "aisstream", "note": ais_note if is_auth_failed() else "Anchorage congestion upgrades the storage layer when collector data is present."},
            {"name": "Mapbox web load guard", "status": "live" if mapbox_guard.get("allow_live_map") else "partial", "mode": "monthly+daily budget", "note": f"{mapbox_guard.get('reason')} | month {mapbox_guard.get('month_used')}/{mapbox_guard.get('month_limit')} | day {mapbox_guard.get('day_used')}/{mapbox_guard.get('day_limit')}"},
        ],
        "algorithm_notes": [
            "The panel now reads Baltic index cache and chokepoint metrics from Supabase when available.",
            "If a source is unavailable, fallback is limited to the missing layer rather than the entire panel pretending everything is live.",
            "Best next upgrade path is stable TD3C feed coverage plus richer AIS static vessel metadata.",
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
