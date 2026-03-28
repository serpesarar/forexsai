from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from dataclasses import asdict, is_dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from config import settings
from database.supabase_client import get_supabase_client
from services.comex_news_service import COMEXNewsService
from services.data_fetcher import fetch_intraday_candles
from services.deepseek_json_client import DEEPSEEK_MODEL, call_deepseek_json
from services.detailed_ai_analysis_service import build_context_pack
from services.economic_calendar_service import get_calendar_service
from services.market_regime_service import detect_regime
from services.oil_analysis_service import generate_oil_analysis
from services.unified_news_analyzer import get_unified_analyzer
from utils.json_helpers import parse_json_field

logger = logging.getLogger(__name__)

ANALYSIS_VERSION = "4.1.0"
PROMPT_VERSION = "ai_panel_v2_20260318"
CACHE_TTL_SECONDS = 3600
NY_TZ = ZoneInfo("America/New_York")

SYMBOL_PROFILES: Dict[str, Dict[str, Any]] = {
    "NDX.INDX": {
        "display_name": "NASDAQ-100",
        "short_label": "NASDAQ",
        "asset_class": "index",
        "calendar_symbol": "NDX",
        "session_name": "NYSE cash",
        "ny_session_start": 9 * 60 + 30,
        "ny_session_end": 16 * 60,
        "prompt_focus": "opening drive, index breadth proxies, volatility regime, breakout continuation versus mean reversion",
    },
    "XAUUSD": {
        "display_name": "Gold (XAU/USD)",
        "short_label": "XAUUSD",
        "asset_class": "metal",
        "calendar_symbol": "XAUUSD",
        "session_name": "NY metals",
        "ny_session_start": 8 * 60 + 20,
        "ny_session_end": 16 * 60,
        "prompt_focus": "dollar sensitivity, yields, safe-haven flow, COMEX catalysts, macro headline shock risk",
    },
    "USOIL.FOREX": {
        "display_name": "US Oil (WTI)",
        "short_label": "USOIL",
        "asset_class": "energy",
        "calendar_symbol": "USOIL",
        "session_name": "NYMEX core",
        "ny_session_start": 9 * 60,
        "ny_session_end": 14 * 60 + 30,
        "prompt_focus": "inventory and EIA timing, OPEC and geopolitical supply risk, dollar pressure, oil microstructure, physical oil logistics intelligence (Baltic indices, tanker flows, chokepoint congestion, floating storage)",
    },
    "GDAXI.INDX": {
        "display_name": "DAX",
        "short_label": "DAX",
        "asset_class": "index",
        "calendar_symbol": "DAX",
        "session_name": "Xetra cash",
        "ny_session_start": 3 * 60,
        "ny_session_end": 11 * 60 + 30,
        "prompt_focus": "European equity flow, Xetra cash momentum, macro sentiment spillover, trend continuation versus fade setups",
    },
}

SYMBOL_ALIASES = {
    "NASDAQ": "NDX.INDX",
    "NDX": "NDX.INDX",
    "NDX.INDX": "NDX.INDX",
    "XAU": "XAUUSD",
    "XAUUSD": "XAUUSD",
    "GOLD": "XAUUSD",
    "USOIL": "USOIL.FOREX",
    "WTI": "USOIL.FOREX",
    "USOIL.FOREX": "USOIL.FOREX",
    "DAX": "GDAXI.INDX",
    "GDAXI": "GDAXI.INDX",
    "GDAXI.INDX": "GDAXI.INDX",
}

_ANALYSIS_CACHE: Dict[str, tuple[datetime, Dict[str, Any]]] = {}

PANEL_PROMPT = """You generate the production JSON for a trading dashboard panel whose UI label is CLAUDE AI ANALYSIS. The actual provider is DeepSeek Reasoner.

Analyze only the supplied market pack. Do not invent data. If any data is missing, explicitly reduce confidence. Respect symbol-specific context:
- NDX.INDX and GDAXI.INDX: prioritize index trend, opening drive, macro risk, volatility regime, breakout vs mean reversion.
- XAUUSD: prioritize dollar/macro regime, safe-haven flow, COMEX-style event sensitivity, headline risk.
- USOIL.FOREX: prioritize inventory/OPEC/geopolitical risk, dollar impact, oil microstructure, EIA event timing.
- For USOIL.FOREX: When physical_oil_intelligence is present in the market pack, analyze the physical-financial divergence. Physical logistics data provides 30-60 day leading indicators. Key interpretation rules:
  * BCTI weakness > 70 → refined product demand stress (bearish leading signal for oil price)
  * Contango pressure > 65 → curve incentivizes floating storage (bearish structural)
  * Chokepoint congestion in Singapore/Rotterdam with rising vessel counts → supply buildup risk (bearish)
  * Strait of Hormuz low flow or geopolitical risk → supply shock potential (bullish risk premium)
  * Physical score diverging from technical regime → potential trend reversal signal
  * Recession probability > 60 combined with clean weakness → demand destruction warning (bearish)
  * Dirty/clean spread widening → refinery margin stress, forward demand concern
  Include a dedicated "physical_confirmation" note in your reasoning when this data materially affects direction or confidence. If physical and technical signals diverge, explain the divergence and how it impacts your conviction.
- If the symbol's New York-time primary session is closed, reduce conviction by one notch and avoid overstating trend persistence.
- Produce two distinct decisions from the same market pack: one for scalp execution (15-90m) and one for intraday execution (rest_of_session). They may disagree if the data supports that.
- Use the exact symbol profile, session state, ml_prediction, ta_snapshot, ta_summary, support/resistance, news, calendar, regime, and asset-specific extras provided in the market pack.
- If the evidence is mixed, explain the conflict in confidence_reasoning and lower confidence instead of forcing a trend call.

Return ONLY valid JSON with this exact shape:
{
  "headline": "short dashboard summary",
  "scalp_bias": {
    "direction": "BUY|SELL|HOLD|NO_TRADE",
    "confidence": 0,
    "expected_behavior": "uptrend|downtrend|range|mean_reversion|volatile",
    "summary": "",
    "time_horizon": "15-90m",
    "reasoning": [""]
  },
  "intraday_bias": {
    "direction": "BUY|SELL|HOLD|NO_TRADE",
    "confidence": 0,
    "expected_behavior": "uptrend|downtrend|range|mean_reversion|volatile",
    "summary": "",
    "time_horizon": "rest_of_session",
    "reasoning": [""]
  },
  "market_behavior": {
    "state": "uptrend|downtrend|range|mean_reversion|volatile",
    "summary": "",
    "expected_volatility": "LOW|MEDIUM|HIGH"
  },
  "entry_plan": {
    "strategy": "buy_dips|sell_rips|breakout_follow|fade_extremes|wait",
    "preferred_entry": 0,
    "entry_zone": {"low": 0, "high": 0},
    "stop_loss": 0,
    "take_profit": 0,
    "risk_reward": 0,
    "invalidation": ""
  },
  "key_levels": [
    {"label": "", "price": 0, "kind": "support|resistance|pivot|trigger|target", "source": "", "distance": ""}
  ],
  "bull_case": [""],
  "bear_case": [""],
  "macro_risk": {"level": "LOW|MEDIUM|HIGH", "summary": "", "drivers": [""]},
  "event_risk": {
    "level": "LOW|MEDIUM|HIGH",
    "summary": "",
    "events": [
      {"event_name": "", "impact": "LOW|MEDIUM|HIGH", "minutes_until": 0}
    ]
  },
  "invalidation": [""],
  "confidence_reasoning": "",
  "top_factors": [""],
  "counter_factors": [""],
  "data_quality": {"level": "HIGH|MEDIUM|LOW", "missing_inputs": [""], "notes": [""]}
}

Guidance:
- Keep prose concise and panel-friendly.
- Use NO_TRADE if event risk is extreme or evidence is too mixed.
- key_levels should include 4 to 8 actionable levels when possible.
- preferred_entry, stop_loss, take_profit, risk_reward can be null when there is no trade setup.
"""


def normalize_symbol(symbol: str) -> str:
    raw = (symbol or "").strip().upper()
    return SYMBOL_ALIASES.get(raw, raw)


def get_supported_ai_symbols() -> List[str]:
    return list(SYMBOL_PROFILES.keys())


def _json_default(value: Any) -> Any:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return asdict(value)
    if hasattr(value, "dict"):
        return value.dict()
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return str(value)



def _to_jsonable(value: Any) -> Any:
    return json.loads(json.dumps(value, default=_json_default))



def _clone(value: Dict[str, Any]) -> Dict[str, Any]:
    return _to_jsonable(value)



def _safe_list(value: Any) -> List[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]



def _float_or_none(value: Any) -> Optional[float]:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except Exception:
        return None



def _float_with_default(value: Any, default: float) -> float:
    parsed = _float_or_none(value)
    return parsed if parsed is not None else default



def _round_price(value: Any) -> Optional[float]:
    parsed = _float_or_none(value)
    return round(parsed, 2) if parsed is not None else None



def _coerce_direction(value: Any, default: str) -> str:
    allowed = {"BUY", "SELL", "HOLD", "NO_TRADE"}
    text = str(value or default).upper().strip()
    return text if text in allowed else default



def _coerce_behavior(value: Any, default: str) -> str:
    allowed = {"UPTREND", "DOWNTREND", "RANGE", "MEAN_REVERSION", "VOLATILE"}
    text = str(value or default).upper().strip().replace("-", "_").replace(" ", "_")
    return text.lower() if text in allowed else default



def _coerce_risk_level(value: Any, default: str) -> str:
    allowed = {"LOW", "MEDIUM", "HIGH"}
    text = str(value or default).upper().strip()
    return text if text in allowed else default



def _position_size_from_signal(direction: str, confidence: float, event_risk: str) -> str:
    if direction in {"HOLD", "NO_TRADE"}:
        return "No Trade"
    adjusted = confidence
    if event_risk == "HIGH":
        adjusted -= 12
    if adjusted >= 78:
        return "Large"
    if adjusted >= 62:
        return "Medium"
    return "Small"



def _minutes_until(timestamp: datetime) -> Optional[int]:
    if not isinstance(timestamp, datetime):
        return None
    now = datetime.now(timezone.utc)
    ts = timestamp if timestamp.tzinfo else timestamp.replace(tzinfo=timezone.utc)
    return int((ts - now).total_seconds() / 60)



def _get_market_state(symbol: str) -> Dict[str, Any]:
    profile = SYMBOL_PROFILES[symbol]
    now_utc = datetime.now(timezone.utc)
    now_ny = now_utc.astimezone(NY_TZ)
    minutes_now = now_ny.hour * 60 + now_ny.minute
    session_start = profile["ny_session_start"]
    session_end = profile["ny_session_end"]
    is_weekday = now_ny.weekday() < 5
    is_primary_session_open = is_weekday and session_start <= minutes_now <= session_end

    if not is_weekday:
        phase = "weekend"
    elif is_primary_session_open:
        phase = "open"
    elif minutes_now < session_start:
        phase = "pre"
    else:
        phase = "post"

    minutes_to_open = session_start - minutes_now if is_weekday and minutes_now < session_start else None
    minutes_to_close = session_end - minutes_now if is_primary_session_open else None

    return {
        "ny_time": now_ny.isoformat(),
        "utc_time": now_utc.isoformat(),
        "day_of_week": now_ny.strftime("%A"),
        "phase": phase,
        "session_name": profile["session_name"],
        "is_primary_session_open": is_primary_session_open,
        "minutes_to_open": minutes_to_open,
        "minutes_to_close": minutes_to_close,
        "is_us_cash_open": is_weekday and (9 * 60 + 30) <= minutes_now <= (16 * 60),
    }



def _oil_session_from_market_state(market_state: Dict[str, Any]) -> str:
    ny_time_raw = market_state.get("ny_time")
    if not ny_time_raw:
        return "nymex"
    now_ny = datetime.fromisoformat(ny_time_raw)
    minutes_now = now_ny.hour * 60 + now_ny.minute
    if now_ny.weekday() == 2 and (10 * 60) <= minutes_now <= (11 * 60 + 30):
        return "nymex_eia_window"
    if market_state.get("is_primary_session_open"):
        return "nymex"
    if 18 * 60 <= minutes_now or minutes_now <= 6 * 60:
        return "asia"
    return "nymex"



def _event_to_dict(event: Any) -> Dict[str, Any]:
    payload = _to_jsonable(event)
    timestamp_raw = payload.get("timestamp")
    minutes_until = None
    if timestamp_raw:
        try:
            ts = datetime.fromisoformat(str(timestamp_raw).replace("Z", "+00:00"))
            minutes_until = _minutes_until(ts)
        except Exception:
            minutes_until = None
    return {
        "id": payload.get("id"),
        "event_name": payload.get("event_name") or payload.get("title") or "",
        "impact": str(payload.get("impact") or "medium").upper(),
        "currency": payload.get("currency"),
        "timestamp": timestamp_raw,
        "minutes_until": minutes_until,
        "affected_symbols": _safe_list(payload.get("affected_symbols")),
    }



def _build_event_risk(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    ranked = sorted(
        [e for e in events if e.get("minutes_until") is not None],
        key=lambda item: abs(item.get("minutes_until") or 0),
    )
    level = "LOW"
    summary = "No immediate scheduled catalyst detected."
    focus_events: List[Dict[str, Any]] = []

    upcoming_high = [
        event for event in ranked
        if (event.get("minutes_until") or 10_000) >= 0 and event.get("impact") == "HIGH"
    ]
    upcoming_medium = [
        event for event in ranked
        if (event.get("minutes_until") or 10_000) >= 0 and event.get("impact") in {"HIGH", "MEDIUM"}
    ]

    if upcoming_high and (upcoming_high[0].get("minutes_until") or 10_000) <= 90:
        level = "HIGH"
        summary = f"{upcoming_high[0].get('event_name')} is close enough to distort directional conviction."
        focus_events = upcoming_high[:3]
    elif upcoming_medium and (upcoming_medium[0].get("minutes_until") or 10_000) <= 240:
        level = "MEDIUM"
        summary = f"{upcoming_medium[0].get('event_name')} can reshape intraday flows later in the session."
        focus_events = upcoming_medium[:3]
    else:
        recent_high = [
            event for event in ranked
            if (event.get("minutes_until") or -10_000) < 0 and abs(event.get("minutes_until") or 0) <= 120 and event.get("impact") == "HIGH"
        ]
        if recent_high:
            level = "MEDIUM"
            summary = f"{recent_high[0].get('event_name')} is still creating aftershock risk."
            focus_events = recent_high[:3]

    return {
        "level": level,
        "summary": summary,
        "events": focus_events,
    }



def _summarize_regime(regime: Any) -> Dict[str, Any]:
    if regime is None:
        return {}
    payload = _to_jsonable(regime)
    return {
        "regime": payload.get("regime"),
        "adx": payload.get("adx"),
        "confidence": payload.get("confidence"),
        "trend_direction": payload.get("trend_direction"),
        "session": payload.get("session"),
        "allowed_directions": _safe_list(payload.get("allowed_directions")),
    }



def _summarize_unified_news(impact: Any) -> Dict[str, Any]:
    if impact is None:
        return {}
    payload = _to_jsonable(impact)
    return {
        "sentiment_score": payload.get("sentiment_score"),
        "confidence": payload.get("confidence"),
        "direction_bias": payload.get("direction_bias"),
        "key_factors": _safe_list(payload.get("key_factors"))[:6],
        "conflicts": _safe_list(payload.get("conflicts"))[:4],
        "high_impact_events": _safe_list(payload.get("high_impact_events"))[:4],
        "ml_features": payload.get("ml_features") or {},
    }



def _summarize_comex(impact: Any) -> Dict[str, Any]:
    if impact is None:
        return {}
    payload = _to_jsonable(impact)
    recent_news = []
    for item in _safe_list(payload.get("recent_news"))[:4]:
        recent_news.append({
            "title": item.get("title"),
            "direction": item.get("direction"),
            "impact_score": item.get("impact_score"),
            "confidence": item.get("confidence"),
        })
    return {
        "overall_impact": payload.get("overall_impact"),
        "impact_score": payload.get("impact_score"),
        "confidence": payload.get("confidence"),
        "direction": payload.get("direction"),
        "should_block_trading": payload.get("should_block_trading"),
        "block_reason": payload.get("block_reason"),
        "recent_news": recent_news,
        "ml_features": payload.get("ml_features") or {},
    }



def _summarize_oil_analysis(impact: Any) -> Dict[str, Any]:
    if impact is None:
        return {}
    payload = _to_jsonable(impact)
    return {
        "composite_score": payload.get("composite_score"),
        "direction": payload.get("direction"),
        "signal_type": payload.get("signal_type"),
        "label": payload.get("label"),
        "confidence": payload.get("confidence"),
        "reasons": _safe_list(payload.get("reasons"))[:6],
        "risks": _safe_list(payload.get("risks"))[:6],
        "modifiers": _safe_list(payload.get("modifiers"))[:6],
        "key_levels": payload.get("key_levels") or {},
    }



def _collect_missing_inputs(context: Dict[str, Any], extras: Dict[str, Any]) -> List[str]:
    missing: List[str] = []
    ml = context.get("ml_prediction") or {}
    if not ml:
        missing.append("ml_prediction")
    if not (context.get("ta_snapshot") or {}).get("close"):
        missing.append("ta_snapshot.close")
    if not (context.get("volume") or {}).get("ratio"):
        missing.append("volume.ratio")
    if not extras.get("regime"):
        missing.append("market_regime")
    if not extras.get("unified_news"):
        missing.append("unified_news")
    if extras.get("symbol") == "XAUUSD" and not extras.get("comex_news"):
        missing.append("comex_news")
    if extras.get("symbol") == "USOIL.FOREX" and not extras.get("oil_analysis"):
        missing.append("oil_analysis")
    if extras.get("symbol") == "USOIL.FOREX" and not extras.get("physical_oil_context"):
        missing.append("physical_oil_intelligence")
    return missing



def _build_key_levels(context: Dict[str, Any], extras: Dict[str, Any], direction: str) -> List[Dict[str, Any]]:
    levels: List[Dict[str, Any]] = []
    for item in _safe_list((context.get("ml_prediction") or {}).get("key_levels"))[:6]:
        levels.append({
            "label": str(item.get("type") or "Level"),
            "price": _round_price(item.get("price")),
            "kind": "trigger",
            "source": "ml",
            "distance": str(item.get("distance") or ""),
        })

    nearest_support = _float_or_none(((context.get("levels") or {}).get("nearest_support")))
    nearest_resistance = _float_or_none(((context.get("levels") or {}).get("nearest_resistance")))
    if nearest_support is not None:
        levels.append({
            "label": "Nearest support",
            "price": round(nearest_support, 2),
            "kind": "support",
            "source": "context_pack",
            "distance": "",
        })
    if nearest_resistance is not None:
        levels.append({
            "label": "Nearest resistance",
            "price": round(nearest_resistance, 2),
            "kind": "resistance",
            "source": "context_pack",
            "distance": "",
        })

    oil_levels = (extras.get("oil_analysis") or {}).get("key_levels") or {}
    for label, price in oil_levels.items():
        parsed = _round_price(price)
        if parsed is None:
            continue
        levels.append({
            "label": str(label).upper(),
            "price": parsed,
            "kind": "pivot",
            "source": "oil_engine",
            "distance": "",
        })

    deduped: List[Dict[str, Any]] = []
    seen: set[tuple[str, Optional[float]]] = set()
    for item in levels:
        key = (str(item.get("label")), _float_or_none(item.get("price")))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped[:8]



def _behavior_from_context(context: Dict[str, Any], extras: Dict[str, Any]) -> str:
    regime = extras.get("regime") or {}
    regime_name = str(regime.get("regime") or "").upper()
    trend_direction = str(regime.get("trend_direction") or "").upper()
    volatility_level = str((context.get("volatility") or {}).get("level") or "NORMAL").upper()
    adx = _float_with_default((context.get("ta_summary") or {}).get("adx"), 20.0)
    rsi = _float_with_default((context.get("ta_summary") or {}).get("rsi"), 50.0)
    boll_z = _float_with_default((context.get("ta_snapshot") or {}).get("boll_zscore"), 0.0)
    event_risk = (extras.get("event_risk") or {}).get("level") or "LOW"

    if event_risk == "HIGH" or volatility_level == "HIGH":
        return "volatile"
    if "TREND_UP" in regime_name or trend_direction == "UP":
        return "uptrend"
    if "TREND_DOWN" in regime_name or trend_direction == "DOWN":
        return "downtrend"
    if adx < 20:
        return "range"
    if abs(boll_z) > 1.7 or rsi >= 68 or rsi <= 32:
        return "mean_reversion"
    return "range"



def _build_macro_risk(context: Dict[str, Any], extras: Dict[str, Any], behavior: str) -> Dict[str, Any]:
    drivers: List[str] = []
    volatility = context.get("volatility") or {}
    if str(volatility.get("level") or "").upper() == "HIGH":
        drivers.append("Volatility regime is elevated.")
    vix = _float_or_none(volatility.get("vix"))
    if vix is not None and vix >= 20:
        drivers.append(f"VIX proxy is elevated near {vix:.2f}.")

    unified = extras.get("unified_news") or {}
    confidence = _float_with_default(unified.get("confidence"), 0.0)
    direction_bias = str(unified.get("direction_bias") or "NEUTRAL").upper()
    if confidence >= 65:
        drivers.append(f"Unified news bias leans {direction_bias.lower()} with {confidence:.0f}% confidence.")
    for factor in _safe_list(unified.get("key_factors"))[:3]:
        drivers.append(str(factor))

    macro = context.get("macro") or {}
    dxy_price = _float_or_none((macro.get("dxy") or {}).get("price"))
    if dxy_price is not None:
        drivers.append(f"DXY proxy is at {dxy_price:.2f}.")

    level = "LOW"
    if len(drivers) >= 4 or behavior == "volatile":
        level = "HIGH"
    elif len(drivers) >= 2:
        level = "MEDIUM"

    summary = "Macro backdrop is relatively quiet."
    if level == "HIGH":
        summary = "Macro/news backdrop can overwhelm technical setups quickly."
    elif level == "MEDIUM":
        summary = "Macro factors matter, but they are not yet a full stop signal."

    return {
        "level": level,
        "summary": summary,
        "drivers": drivers[:5],
    }


def _fallback_panel_signal(context: Dict[str, Any], extras: Dict[str, Any]) -> Dict[str, Any]:
    ml = context.get("ml_prediction") or {}
    direction = _coerce_direction(ml.get("direction"), "HOLD")
    confidence = _float_with_default(ml.get("confidence"), 50.0)
    market_state = extras.get("market_state") or {}
    symbol = str(extras.get("symbol") or "")
    profile = SYMBOL_PROFILES.get(symbol, {})
    short_label = str(profile.get("short_label") or symbol or "market")
    session_name = str(market_state.get("session_name") or profile.get("session_name") or "primary session")
    minutes_to_open = market_state.get("minutes_to_open")
    behavior = _behavior_from_context(context, extras)
    event_risk = extras.get("event_risk") or {"level": "LOW", "summary": "No immediate scheduled catalyst detected.", "events": []}
    unified = extras.get("unified_news") or {}
    regime = extras.get("regime") or {}
    bull_case: List[str] = []
    bear_case: List[str] = []
    top_factors: List[str] = []
    counter_factors: List[str] = []
    has_live_price = _float_or_none((context.get("ta_snapshot") or {}).get("close")) not in {None, 0.0}
    has_levels = bool(_build_key_levels(context, extras, direction))

    trend_direction = str(regime.get("trend_direction") or "").upper()
    if trend_direction == "UP":
        bull_case.append("Higher-timeframe regime still favors upside continuation.")
        top_factors.append("Regime backdrop remains constructive.")
    elif trend_direction == "DOWN":
        bear_case.append("Higher-timeframe regime still favors downside continuation.")
        top_factors.append("Regime backdrop remains heavy.")

    news_bias = str(unified.get("direction_bias") or "NEUTRAL").upper()
    news_conf = _float_with_default(unified.get("confidence"), 0.0)
    if news_bias == direction and news_conf >= 55:
        confidence += 6
        top_factors.append(f"News flow broadly aligns with the {direction.lower()} thesis.")
    elif news_bias not in {"NEUTRAL", direction} and news_conf >= 55:
        confidence -= 8
        counter_factors.append("News flow disagrees with the base directional thesis.")

    if not market_state.get("is_primary_session_open"):
        confidence -= 7
        counter_factors.append("Primary session is closed, so follow-through risk is lower.")

    if not has_live_price:
        confidence -= 8
        wait_text = f"{short_label} is outside active price discovery." if minutes_to_open is None else f"{short_label} cash session reopens in about {minutes_to_open} minutes."
        top_factors.append(wait_text)
        counter_factors.append(f"Live price context is missing, so {short_label} conviction must stay muted.")
    if not has_levels:
        confidence -= 5
        counter_factors.append(f"Nearby {short_label} support/resistance structure is incomplete.")

    if event_risk.get("level") == "HIGH":
        confidence -= 12
        counter_factors.append(event_risk.get("summary") or "Scheduled catalyst risk is high.")
        if direction != "HOLD":
            direction = "HOLD"
    elif event_risk.get("level") == "MEDIUM":
        confidence -= 5
        counter_factors.append(event_risk.get("summary") or "Catalyst risk can distort intraday flows.")

    oil_analysis = extras.get("oil_analysis") or {}
    if oil_analysis:
        oil_direction = _coerce_direction(oil_analysis.get("direction"), direction)
        oil_conf = _float_with_default(oil_analysis.get("confidence"), 50.0)
        if oil_direction == direction:
            confidence = (confidence + oil_conf) / 2
            top_factors.append("Oil-specific engine agrees with the directional bias.")
        elif oil_direction not in {"HOLD", direction}:
            confidence -= 6
            counter_factors.append("Oil-specific engine is not aligned with the base bias.")

    physical_oil = extras.get("physical_oil_context") or {}
    if physical_oil:
        phys_bias = str(physical_oil.get("oil_bias") or "").lower()
        phys_score = _float_with_default(physical_oil.get("physical_score"), 50.0)
        recession_risk = _float_with_default(physical_oil.get("recession_probability"), 50.0)
        bcti_weakness = _float_with_default(physical_oil.get("bcti_weakness"), 50.0)
        contango_pres = _float_with_default(physical_oil.get("contango_pressure"), 50.0)

        phys_direction = "BUY" if phys_bias == "bullish" else ("SELL" if phys_bias == "bearish" else "HOLD")
        if phys_direction == direction and phys_direction != "HOLD":
            confidence += 5
            top_factors.append(f"Physical oil intelligence confirms {direction.lower()} bias (score {phys_score:.0f}).")
        elif phys_direction != "HOLD" and phys_direction != direction and direction not in {"HOLD", "NO_TRADE"}:
            confidence -= 8
            counter_factors.append(f"Physical oil intelligence diverges: physical bias is {phys_bias} vs technical {direction.lower()}.")

        if recession_risk >= 60:
            confidence -= 4
            counter_factors.append(f"Physical market recession probability elevated at {recession_risk:.0f}%.")
        if bcti_weakness >= 70:
            bear_case.append(f"Refined product demand stress is severe (BCTI weakness {bcti_weakness:.0f}).")
        if contango_pres >= 65:
            bear_case.append(f"Contango pressure ({contango_pres:.0f}) incentivizes floating storage — bearish structural.")

    comex_news = extras.get("comex_news") or {}
    if comex_news:
        comex_direction = _coerce_direction(comex_news.get("direction"), direction)
        if comex_news.get("should_block_trading"):
            direction = "NO_TRADE"
            confidence = min(confidence, 42)
            counter_factors.append(comex_news.get("block_reason") or "COMEX flow argues for standing aside.")
        elif comex_direction == direction:
            top_factors.append("COMEX news flow supports the prevailing bias.")

    behavior_summary = {
        "uptrend": "Trend continuation remains the base case while pullbacks hold.",
        "downtrend": "Trend continuation remains the base case while rallies fail.",
        "range": "Price is more likely to rotate between nearby support and resistance.",
        "mean_reversion": "Extended conditions raise the odds of a snap-back move.",
        "volatile": "Expect fast two-way movement and headline sensitivity.",
    }[behavior]
    if not has_live_price:
        if not market_state.get("is_primary_session_open"):
            behavior_summary = f"{short_label} is in {session_name} pre-session mode and still lacks live price discovery."
        else:
            behavior_summary = f"{short_label} is missing live price input, so intraday behavior cannot be trusted yet."

    scalp_direction = direction
    scalp_confidence = max(35.0, min(92.0, confidence - 4))
    rsi = _float_with_default((context.get("ta_summary") or {}).get("rsi"), 50.0)
    boll_z = _float_with_default((context.get("ta_snapshot") or {}).get("boll_zscore"), 0.0)
    if behavior == "mean_reversion":
        if rsi >= 68 or boll_z >= 1.8:
            scalp_direction = "SELL"
        elif rsi <= 32 or boll_z <= -1.8:
            scalp_direction = "BUY"

    if direction in {"HOLD", "NO_TRADE"}:
        scalp_direction = direction
        scalp_confidence = min(scalp_confidence, 55.0)

    if direction == "BUY":
        bull_case.extend(_safe_list(ml.get("reasoning"))[:2] or ["ML model still sees upside follow-through."])
        bear_case.extend([
            "Upside thesis fails if price loses nearby support with expanding volatility.",
            "Macro/event flow can still force a fast reversal.",
        ])
    elif direction == "SELL":
        bear_case.extend(_safe_list(ml.get("reasoning"))[:2] or ["ML model still sees downside follow-through."])
        bull_case.extend([
            "Short thesis fails if price reclaims nearby resistance with volume.",
            "Risk sentiment can force a squeeze higher.",
        ])
    else:
        bull_case.append("Support can still trigger a tactical rebound if catalysts stay quiet.")
        bear_case.append("Resistance or event risk can still reject any early bounce attempt.")

    for factor in _safe_list(unified.get("key_factors"))[:2]:
        text = str(factor)
        if direction == "SELL":
            bear_case.append(text)
        else:
            bull_case.append(text)

    confidence = max(35.0, min(92.0, confidence))

    preferred_entry = _round_price(ml.get("entry_price"))
    stop_loss = _round_price(ml.get("stop_price"))
    take_profit = _round_price(ml.get("target_price"))
    risk_reward = _float_or_none(ml.get("risk_reward"))
    entry_zone = None
    nearest_support = _float_or_none(((context.get("levels") or {}).get("nearest_support")))
    nearest_resistance = _float_or_none(((context.get("levels") or {}).get("nearest_resistance")))
    if direction == "BUY" and preferred_entry is not None:
        entry_zone = {
            "low": round(nearest_support if nearest_support is not None else preferred_entry * 0.998, 2),
            "high": preferred_entry,
        }
    elif direction == "SELL" and preferred_entry is not None:
        entry_zone = {
            "low": preferred_entry,
            "high": round(nearest_resistance if nearest_resistance is not None else preferred_entry * 1.002, 2),
        }

    strategy = "wait"
    if direction == "BUY":
        strategy = "buy_dips" if behavior in {"uptrend", "range"} else "breakout_follow"
    elif direction == "SELL":
        strategy = "sell_rips" if behavior in {"downtrend", "range"} else "breakout_follow"
    elif behavior == "mean_reversion":
        strategy = "fade_extremes"

    invalidation = []
    if nearest_support is not None:
        invalidation.append(f"Loss of support near {nearest_support:.2f} breaks the immediate long structure.")
    if nearest_resistance is not None:
        invalidation.append(f"Break above resistance near {nearest_resistance:.2f} invalidates the short thesis.")
    if event_risk.get("level") == "HIGH":
        invalidation.append("A nearby high-impact event can invalidate directional setups instantly.")
    if not invalidation:
        invalidation.append("Directional conviction is invalid if price action turns choppy around the entry zone.")

    missing_inputs = _collect_missing_inputs(context, extras)
    quality_level = "HIGH"
    if len(missing_inputs) >= 4:
        quality_level = "LOW"
    elif len(missing_inputs) >= 2:
        quality_level = "MEDIUM"

    macro_risk = _build_macro_risk(context, extras, behavior)
    key_levels = _build_key_levels(context, extras, direction)

    headline_direction = direction if direction not in {"HOLD", "NO_TRADE"} else behavior.replace("_", " ")
    headline = f"{headline_direction} bias with {event_risk.get('level', 'LOW').lower()} event risk"
    if not has_live_price:
        if not market_state.get("is_primary_session_open"):
            headline = f"{short_label} pre-session: waiting for live price discovery"
        else:
            headline = f"{short_label}: live price feed incomplete, stay selective"

    return {
        "headline": headline,
        "scalp_bias": {
            "direction": scalp_direction,
            "confidence": round(scalp_confidence, 1),
            "expected_behavior": behavior,
            "summary": behavior_summary,
            "time_horizon": "15-90m",
            "reasoning": (top_factors or _safe_list(ml.get("reasoning"))[:3])[:4],
        },
        "intraday_bias": {
            "direction": direction,
            "confidence": round(confidence, 1),
            "expected_behavior": behavior,
            "summary": behavior_summary,
            "time_horizon": "rest_of_session",
            "reasoning": (_safe_list(ml.get("reasoning"))[:4] or top_factors[:4]),
        },
        "market_behavior": {
            "state": behavior,
            "summary": behavior_summary,
            "expected_volatility": _coerce_risk_level((context.get("volatility") or {}).get("level"), "MEDIUM"),
        },
        "entry_plan": {
            "strategy": strategy,
            "preferred_entry": preferred_entry if direction not in {"HOLD", "NO_TRADE"} else None,
            "entry_zone": entry_zone if direction not in {"HOLD", "NO_TRADE"} else None,
            "stop_loss": stop_loss if direction not in {"HOLD", "NO_TRADE"} else None,
            "take_profit": take_profit if direction not in {"HOLD", "NO_TRADE"} else None,
            "risk_reward": round(risk_reward, 2) if risk_reward is not None and direction not in {"HOLD", "NO_TRADE"} else None,
            "invalidation": invalidation[0],
        },
        "key_levels": key_levels,
        "bull_case": bull_case[:5],
        "bear_case": bear_case[:5],
        "macro_risk": macro_risk,
        "event_risk": event_risk,
        "invalidation": invalidation[:4],
        "confidence_reasoning": f"Base conviction starts from ML confidence and is adjusted for regime, news alignment, session status, and event proximity.",
        "top_factors": (top_factors or ["ML signal remains the main directional anchor."])[:5],
        "counter_factors": (counter_factors or ["No major counter-factor beyond normal noise."])[:5],
        "data_quality": {
            "level": quality_level,
            "missing_inputs": missing_inputs,
            "notes": ["Fallback synthesis used when structured DeepSeek output is unavailable."],
        },
    }



def _normalize_bias(raw: Any, fallback: Dict[str, Any], default_horizon: str) -> Dict[str, Any]:
    payload = raw if isinstance(raw, dict) else {}
    return {
        "direction": _coerce_direction(payload.get("direction"), fallback.get("direction", "HOLD")),
        "confidence": round(max(0.0, min(100.0, _float_with_default(payload.get("confidence"), _float_with_default(fallback.get("confidence"), 50.0)))), 1),
        "expected_behavior": _coerce_behavior(payload.get("expected_behavior"), fallback.get("expected_behavior", "range")),
        "summary": str(payload.get("summary") or fallback.get("summary") or ""),
        "time_horizon": str(payload.get("time_horizon") or fallback.get("time_horizon") or default_horizon),
        "reasoning": [str(item) for item in _safe_list(payload.get("reasoning") or fallback.get("reasoning"))[:5]],
    }



def _normalize_entry_plan(raw: Any, fallback: Dict[str, Any]) -> Dict[str, Any]:
    payload = raw if isinstance(raw, dict) else {}
    entry_zone_raw = payload.get("entry_zone") if isinstance(payload.get("entry_zone"), dict) else fallback.get("entry_zone")
    entry_zone = None
    if isinstance(entry_zone_raw, dict):
        low = _round_price(entry_zone_raw.get("low"))
        high = _round_price(entry_zone_raw.get("high"))
        if low is not None or high is not None:
            entry_zone = {"low": low, "high": high}
    return {
        "strategy": str(payload.get("strategy") or fallback.get("strategy") or "wait"),
        "preferred_entry": _round_price(payload.get("preferred_entry")) if payload.get("preferred_entry") is not None else fallback.get("preferred_entry"),
        "entry_zone": entry_zone,
        "stop_loss": _round_price(payload.get("stop_loss")) if payload.get("stop_loss") is not None else fallback.get("stop_loss"),
        "take_profit": _round_price(payload.get("take_profit")) if payload.get("take_profit") is not None else fallback.get("take_profit"),
        "risk_reward": round(_float_with_default(payload.get("risk_reward"), _float_with_default(fallback.get("risk_reward"), 0.0)), 2) if (payload.get("risk_reward") is not None or fallback.get("risk_reward") is not None) else None,
        "invalidation": str(payload.get("invalidation") or fallback.get("invalidation") or ""),
    }



def _normalize_key_levels(raw: Any, fallback: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    levels = raw if isinstance(raw, list) else fallback
    normalized: List[Dict[str, Any]] = []
    for item in levels[:8]:
        if not isinstance(item, dict):
            continue
        normalized.append({
            "label": str(item.get("label") or "Level"),
            "price": _round_price(item.get("price")),
            "kind": str(item.get("kind") or "trigger"),
            "source": str(item.get("source") or "analysis"),
            "distance": str(item.get("distance") or ""),
        })
    return normalized or fallback



def _normalize_risk(raw: Any, fallback: Dict[str, Any]) -> Dict[str, Any]:
    payload = raw if isinstance(raw, dict) else {}
    return {
        "level": _coerce_risk_level(payload.get("level"), fallback.get("level", "LOW")),
        "summary": str(payload.get("summary") or fallback.get("summary") or ""),
        "drivers": [str(item) for item in _safe_list(payload.get("drivers") or fallback.get("drivers"))[:5]],
    }



def _normalize_event_risk(raw: Any, fallback: Dict[str, Any]) -> Dict[str, Any]:
    payload = raw if isinstance(raw, dict) else {}
    events = payload.get("events") if isinstance(payload.get("events"), list) else fallback.get("events")
    normalized_events: List[Dict[str, Any]] = []
    for item in _safe_list(events)[:4]:
        if not isinstance(item, dict):
            continue
        normalized_events.append({
            "event_name": str(item.get("event_name") or item.get("title") or ""),
            "impact": _coerce_risk_level(item.get("impact"), "MEDIUM"),
            "minutes_until": int(item.get("minutes_until")) if item.get("minutes_until") is not None else None,
        })
    return {
        "level": _coerce_risk_level(payload.get("level"), fallback.get("level", "LOW")),
        "summary": str(payload.get("summary") or fallback.get("summary") or ""),
        "events": normalized_events or fallback.get("events") or [],
    }



def _normalize_data_quality(raw: Any, fallback: Dict[str, Any]) -> Dict[str, Any]:
    payload = raw if isinstance(raw, dict) else {}
    return {
        "level": _coerce_risk_level(payload.get("level"), fallback.get("level", "MEDIUM")),
        "missing_inputs": [str(item) for item in _safe_list(payload.get("missing_inputs") or fallback.get("missing_inputs"))[:8]],
        "notes": [str(item) for item in _safe_list(payload.get("notes") or fallback.get("notes"))[:5]],
    }



def _normalize_panel_signal(raw: Optional[Dict[str, Any]], context: Dict[str, Any], extras: Dict[str, Any]) -> Dict[str, Any]:
    fallback = _fallback_panel_signal(context, extras)
    if not isinstance(raw, dict):
        return fallback

    payload = raw.get("panel_signal") if isinstance(raw.get("panel_signal"), dict) else raw
    if not isinstance(payload, dict):
        return fallback

    return {
        "headline": str(payload.get("headline") or fallback.get("headline") or ""),
        "scalp_bias": _normalize_bias(payload.get("scalp_bias"), fallback.get("scalp_bias") or {}, "15-90m"),
        "intraday_bias": _normalize_bias(payload.get("intraday_bias"), fallback.get("intraday_bias") or {}, "rest_of_session"),
        "market_behavior": {
            "state": _coerce_behavior((payload.get("market_behavior") or {}).get("state"), ((fallback.get("market_behavior") or {}).get("state") or "range")),
            "summary": str(((payload.get("market_behavior") or {}).get("summary") or (fallback.get("market_behavior") or {}).get("summary") or "")),
            "expected_volatility": _coerce_risk_level(((payload.get("market_behavior") or {}).get("expected_volatility")), ((fallback.get("market_behavior") or {}).get("expected_volatility") or "MEDIUM")),
        },
        "entry_plan": _normalize_entry_plan(payload.get("entry_plan"), fallback.get("entry_plan") or {}),
        "key_levels": _normalize_key_levels(payload.get("key_levels"), fallback.get("key_levels") or []),
        "bull_case": [str(item) for item in _safe_list(payload.get("bull_case") or fallback.get("bull_case"))[:5]],
        "bear_case": [str(item) for item in _safe_list(payload.get("bear_case") or fallback.get("bear_case"))[:5]],
        "macro_risk": _normalize_risk(payload.get("macro_risk"), fallback.get("macro_risk") or {}),
        "event_risk": _normalize_event_risk(payload.get("event_risk"), fallback.get("event_risk") or {}),
        "invalidation": [str(item) for item in _safe_list(payload.get("invalidation") or fallback.get("invalidation"))[:4]],
        "confidence_reasoning": str(payload.get("confidence_reasoning") or fallback.get("confidence_reasoning") or ""),
        "top_factors": [str(item) for item in _safe_list(payload.get("top_factors") or fallback.get("top_factors"))[:5]],
        "counter_factors": [str(item) for item in _safe_list(payload.get("counter_factors") or fallback.get("counter_factors"))[:5]],
        "data_quality": _normalize_data_quality(payload.get("data_quality"), fallback.get("data_quality") or {}),
    }



def _build_prompt_payload(context: Dict[str, Any], extras: Dict[str, Any]) -> Dict[str, Any]:
    unified_news = extras.get("unified_news") or {}
    comex_news = extras.get("comex_news") or {}
    oil_analysis = extras.get("oil_analysis") or {}
    headlines = []
    for item in _safe_list(((context.get("news") or {}).get("headlines")))[:6]:
        if not isinstance(item, dict):
            continue
        headlines.append({
            "title": item.get("title"),
            "source": item.get("source"),
            "published_at": item.get("published_at"),
        })

    return {
        "symbol_profile": SYMBOL_PROFILES[extras["symbol"]],
        "market_state": extras.get("market_state") or {},
        "ml_prediction": context.get("ml_prediction") or {},
        "ta_snapshot": context.get("ta_snapshot") or {},
        "ta_summary": context.get("ta_summary") or {},
        "levels": {
            "nearest_support": (context.get("levels") or {}).get("nearest_support"),
            "nearest_resistance": (context.get("levels") or {}).get("nearest_resistance"),
            "ml_key_levels": _safe_list(((context.get("ml_prediction") or {}).get("key_levels")))[:6],
        },
        "volume": context.get("volume") or {},
        "volatility": context.get("volatility") or {},
        "macro": context.get("macro") or {},
        "market_structure": context.get("market_structure") or {},
        "liquidity_zones": context.get("liquidity_zones") or {},
        "divergences": context.get("divergences") or {},
        "regime": extras.get("regime") or {},
        "news": {
            "headline_count": (context.get("news") or {}).get("count"),
            "headlines": headlines,
            "unified": unified_news,
            "comex": comex_news,
        },
        "oil_engine": oil_analysis,
        "physical_oil_intelligence": extras.get("physical_oil_context") or {},
        "economic_calendar": {
            "flags": context.get("economic_calendar") or {},
            "recent_or_upcoming": extras.get("calendar_events") or [],
            "risk": extras.get("event_risk") or {},
        },
        "mtf_advanced": context.get("mtf_advanced") or {},
    }



def _build_prompt_execution_brief(prompt_payload: Dict[str, Any]) -> str:
    profile = prompt_payload.get("symbol_profile") or {}
    market_state = prompt_payload.get("market_state") or {}
    ml_prediction = prompt_payload.get("ml_prediction") or {}
    ta_snapshot = prompt_payload.get("ta_snapshot") or {}
    ta_summary = prompt_payload.get("ta_summary") or {}
    levels = prompt_payload.get("levels") or {}
    volume = prompt_payload.get("volume") or {}
    volatility = prompt_payload.get("volatility") or {}
    regime = prompt_payload.get("regime") or {}
    event_risk = ((prompt_payload.get("economic_calendar") or {}).get("risk") or {})

    return "\n".join([
        f"Symbol under analysis: {profile.get('display_name')} ({profile.get('short_label')}) [{profile.get('asset_class')}].",
        f"Symbol-specific focus: {profile.get('prompt_focus')}.",
        f"Primary session: {market_state.get('session_name')} | phase={market_state.get('phase')} | primary_open={market_state.get('is_primary_session_open')} | minutes_to_open={market_state.get('minutes_to_open')} | minutes_to_close={market_state.get('minutes_to_close')}.",
        f"ML baseline: direction={ml_prediction.get('direction')} confidence={ml_prediction.get('confidence')} entry={ml_prediction.get('entry_price')} target={ml_prediction.get('target_price')} stop={ml_prediction.get('stop_price')}.",
        f"Technical snapshot: close={ta_snapshot.get('close')} ema20={ta_snapshot.get('ema_20')} ema50={ta_snapshot.get('ema_50')} ema200={ta_snapshot.get('ema_200')} rsi14={ta_snapshot.get('rsi_14')} macd_hist={ta_snapshot.get('macd_hist')} atr14={ta_snapshot.get('atr_14')} boll_z={ta_snapshot.get('boll_zscore')}.",
        f"Technical summary: atr_pct={ta_summary.get('atr_pct')} bollinger_width={ta_summary.get('bollinger_width')} adx={ta_summary.get('adx')} stoch_k={ta_summary.get('stoch_k')}.",
        f"Structure and levels: nearest_support={levels.get('nearest_support')} nearest_resistance={levels.get('nearest_resistance')} ml_key_levels={levels.get('ml_key_levels')}.",
        f"Flow context: volume_status={volume.get('status')} volume_ratio={volume.get('ratio')} volatility_level={volatility.get('level')} regime={regime.get('regime')} regime_trend={regime.get('trend_direction')}.",
        f"Catalyst map: event_risk={event_risk.get('level')} event_summary={event_risk.get('summary')}.",
        _build_physical_oil_brief(prompt_payload.get("physical_oil_intelligence") or {}),
        "Task: produce symbol-specific scalp_bias and intraday_bias using the supplied technical and macro evidence only, and keep the reasoning actionable for a live dashboard.",
    ])



def _build_physical_oil_brief(physical: Dict[str, Any]) -> str:
    if not physical:
        return ""
    return (
        f"Physical oil intelligence: physical_score={physical.get('physical_score', 'N/A')} "
        f"oil_bias={physical.get('oil_bias', 'N/A')} "
        f"recession_probability={physical.get('recession_probability', 'N/A')} "
        f"bcti_weakness={physical.get('bcti_weakness', 'N/A')} "
        f"contango_pressure={physical.get('contango_pressure', 'N/A')} "
        f"storage_pressure={physical.get('storage_pressure', 'N/A')} "
        f"dirty_clean_spread={physical.get('dirty_clean_spread', 'N/A')} "
        f"chokepoint_alerts={physical.get('chokepoint_summary', 'none')}."
    )


def _summarize_physical_oil_context(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Extract compact physical oil signals for AI prompt context."""
    if not raw or not raw.get("available"):
        return {}

    signal = raw.get("signal") or {}
    baltic = raw.get("baltic") or {}
    storage = raw.get("storage") or {}
    demand = raw.get("demand") or {}
    chokepoints = raw.get("chokepoints") or []

    chokepoint_alerts = []
    for cp in chokepoints:
        if cp.get("bias") != "neutral" or float(cp.get("intensity") or 0) >= 60:
            chokepoint_alerts.append(
                f"{cp.get('label', '?')}: {cp.get('signal', 'watch')} ({cp.get('bias', 'neutral')}, intensity={cp.get('intensity', 0)})"
            )

    return {
        "physical_score": signal.get("physical_score"),
        "oil_bias": signal.get("oil_bias"),
        "confidence": signal.get("confidence"),
        "recession_probability": signal.get("recession_probability"),
        "market_regime": signal.get("market_regime"),
        "time_horizon": signal.get("time_horizon"),
        "bdti_proxy": baltic.get("bdti_proxy"),
        "bcti_weakness": baltic.get("bcti_weakness"),
        "td3c_proxy": baltic.get("td3c_proxy"),
        "dirty_clean_spread": baltic.get("dirty_clean_spread"),
        "baltic_status": baltic.get("source_mode") or baltic.get("status"),
        "storage_pressure": storage.get("floating_storage_proxy"),
        "contango_pressure": storage.get("contango_pressure"),
        "backwardation_pressure": storage.get("backwardation_pressure"),
        "floating_storage_vessels": storage.get("floating_storage_vessels"),
        "floating_storage_mm_bbl": storage.get("floating_storage_mm_bbl"),
        "refinery_stress": demand.get("refinery_stress"),
        "crack_spread_proxy": demand.get("crack_spread_proxy"),
        "gasoline_demand_proxy": demand.get("gasoline_demand_proxy"),
        "chokepoint_summary": "; ".join(chokepoint_alerts) if chokepoint_alerts else "all neutral",
        "chokepoints": [
            {
                "label": cp.get("label"),
                "signal": cp.get("signal"),
                "bias": cp.get("bias"),
                "intensity": cp.get("intensity"),
                "vessel_count": cp.get("vessel_count"),
            }
            for cp in chokepoints
        ],
    }


async def _collect_physical_oil_context() -> Dict[str, Any]:
    """Collect physical oil market intelligence from Baltic panel for AI context."""
    try:
        from services.oil_baltic_live_service import build_oil_baltic_intelligence
        raw = await build_oil_baltic_intelligence()
        return _summarize_physical_oil_context(raw)
    except Exception as exc:
        logger.warning("Physical oil context collection failed: %s", exc)
        return {}


async def _collect_oil_analysis(symbol: str, market_state: Dict[str, Any]) -> Dict[str, Any]:
    candles_task = fetch_intraday_candles(symbol, "5m", 240)
    dxy_task = fetch_intraday_candles("DXY.INDX", "5m", 240)
    ndx_task = fetch_intraday_candles("NDX.INDX", "5m", 240)
    wti_candles, dxy_candles, ndx_candles = await asyncio.gather(candles_task, dxy_task, ndx_task)
    if not wti_candles:
        try:
            from services.data_hub import _fetch_candles_from_api

            wti_candles = await _fetch_candles_from_api(symbol, "5m", limit=240)
            if not dxy_candles:
                dxy_candles = await _fetch_candles_from_api("DXY.INDX", "5m", limit=240)
            if not ndx_candles:
                ndx_candles = await _fetch_candles_from_api("NDX.INDX", "5m", limit=240)
        except Exception as exc:
            logger.debug("Oil analysis direct candle fallback failed for %s: %s", symbol, exc)
    if not wti_candles:
        return {}
    oil_session = _oil_session_from_market_state(market_state)
    result = await generate_oil_analysis(
        wti_candles=wti_candles,
        session=oil_session,
        dxy_candles=dxy_candles or None,
        spx_candles=ndx_candles or None,
        news_sentiment=None,
    )
    return _summarize_oil_analysis(result)



async def _collect_symbol_extras(symbol: str, context: Dict[str, Any]) -> Dict[str, Any]:
    market_state = _get_market_state(symbol)
    analyzer = get_unified_analyzer()
    calendar_service = get_calendar_service()

    tasks: List[Any] = [
        detect_regime(symbol),
        analyzer.get_unified_impact(symbol),
        calendar_service.get_events_for_symbol(SYMBOL_PROFILES[symbol]["calendar_symbol"], hours_back=24),
    ]

    needs_comex = symbol == "XAUUSD"
    needs_oil = symbol == "USOIL.FOREX"

    if needs_comex:
        tasks.append(COMEXNewsService().get_comex_impact(use_ai=bool(getattr(settings, "groq_api_key", ""))))
    if needs_oil:
        tasks.append(_collect_oil_analysis(symbol, market_state))
        tasks.append(_collect_physical_oil_context())

    results = await asyncio.gather(*tasks, return_exceptions=True)
    regime_result = results[0] if not isinstance(results[0], Exception) else None
    unified_news_result = results[1] if not isinstance(results[1], Exception) else None
    events_result = results[2] if not isinstance(results[2], Exception) else []

    for item in results:
        if isinstance(item, Exception):
            logger.warning("AI panel extra dependency failed for %s: %s", symbol, item)

    calendar_events = [_event_to_dict(event) for event in _safe_list(events_result)[:6]]
    event_risk = _build_event_risk(calendar_events)

    index = 3
    comex_summary: Dict[str, Any] = {}
    oil_summary: Dict[str, Any] = {}
    physical_oil_context: Dict[str, Any] = {}
    if needs_comex:
        comex_summary = _summarize_comex(results[index] if not isinstance(results[index], Exception) else None)
        index += 1
    if needs_oil:
        oil_summary = results[index] if isinstance(results[index], dict) else {}
        index += 1
        physical_oil_context = results[index] if isinstance(results[index], dict) else {}

    return {
        "symbol": symbol,
        "market_state": market_state,
        "regime": _summarize_regime(regime_result),
        "unified_news": _summarize_unified_news(unified_news_result),
        "calendar_events": calendar_events,
        "event_risk": event_risk,
        "comex_news": comex_summary,
        "oil_analysis": oil_summary,
        "physical_oil_context": physical_oil_context,
    }



async def _request_panel_signal(prompt_payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    execution_brief = _build_prompt_execution_brief(prompt_payload)
    full_prompt = f"{PANEL_PROMPT}\n\nExecution brief:\n{execution_brief}\n\nMarket pack:\n{json.dumps(prompt_payload, ensure_ascii=False, indent=2)}"
    return await call_deepseek_json(
        full_prompt,
        api_key=getattr(settings, "deepseek_api_key", None) or None,
        enforce_market_hours=False,
        max_tokens=1600,
        timeout_seconds=55,
    )



def _context_fingerprint(context: Dict[str, Any], extras: Dict[str, Any]) -> str:
    source = {
        "ml_prediction": context.get("ml_prediction"),
        "ta_snapshot": context.get("ta_snapshot"),
        "ta_summary": context.get("ta_summary"),
        "levels": context.get("levels"),
        "volume": context.get("volume"),
        "volatility": context.get("volatility"),
        "market_state": extras.get("market_state"),
        "event_risk": extras.get("event_risk"),
        "regime": extras.get("regime"),
        "unified_news": extras.get("unified_news"),
        "comex_news": extras.get("comex_news"),
        "oil_analysis": extras.get("oil_analysis"),
        "physical_oil_context": extras.get("physical_oil_context"),
    }
    encoded = json.dumps(source, default=_json_default, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:20]



def _with_cache_hit(result: Dict[str, Any], cache_hit: bool) -> Dict[str, Any]:
    cloned = _clone(result)
    claude_analysis = cloned.get("claude_analysis") or {}
    analysis_meta = claude_analysis.get("analysis_meta") or {}
    analysis_meta["cache_hit"] = cache_hit
    claude_analysis["analysis_meta"] = analysis_meta
    cloned["claude_analysis"] = claude_analysis
    return cloned



def _mark_served_from_stale_cache(result: Dict[str, Any]) -> Dict[str, Any]:
    cloned = _with_cache_hit(result, True)
    claude_analysis = cloned.get("claude_analysis") or {}
    analysis_meta = claude_analysis.get("analysis_meta") or {}
    analysis_meta["stale_cache"] = True
    claude_analysis["analysis_meta"] = analysis_meta
    cloned["claude_analysis"] = claude_analysis
    return cloned



def _get_memory_cached(symbol: str, allow_stale: bool = False) -> Optional[Dict[str, Any]]:
    cached = _ANALYSIS_CACHE.get(symbol)
    if not cached:
        return None
    expires_at, payload = cached
    if expires_at <= datetime.now(timezone.utc):
        if allow_stale:
            return _mark_served_from_stale_cache(payload)
        _ANALYSIS_CACHE.pop(symbol, None)
        return None
    return _with_cache_hit(payload, True)



def _set_memory_cached(symbol: str, payload: Dict[str, Any]) -> None:
    _ANALYSIS_CACHE[symbol] = (
        datetime.now(timezone.utc) + timedelta(seconds=CACHE_TTL_SECONDS),
        _clone(payload),
    )



def _read_db_cache(symbol: str, allow_stale: bool = False) -> Optional[Dict[str, Any]]:
    client = get_supabase_client()
    if client is None:
        return None
    try:
        response = client.table("ai_panel_analysis_cache").select("response_payload,expires_at").eq("symbol", symbol).limit(1).execute()
        rows = response.get("data") or []
        if not rows:
            return None
        row = rows[0]
        expires_at_raw = row.get("expires_at")
        if expires_at_raw:
            expires_at = datetime.fromisoformat(str(expires_at_raw).replace("Z", "+00:00"))
            if expires_at <= datetime.now(timezone.utc):
                if not allow_stale:
                    return None
        payload = parse_json_field(row.get("response_payload"), {})
        if isinstance(payload, dict) and payload.get("ml_prediction") and payload.get("claude_analysis"):
            _set_memory_cached(symbol, payload)
            if expires_at_raw and allow_stale:
                expires_at = datetime.fromisoformat(str(expires_at_raw).replace("Z", "+00:00"))
                if expires_at <= datetime.now(timezone.utc):
                    return _mark_served_from_stale_cache(payload)
            return _with_cache_hit(payload, True)
    except Exception as exc:
        logger.debug("AI panel DB cache read skipped for %s: %s", symbol, exc)
    return None



def _persist_prompt_version() -> None:
    client = get_supabase_client()
    if client is None:
        return
    payload = {
        "version": PROMPT_VERSION,
        "provider": "deepseek",
        "model": DEEPSEEK_MODEL,
        "prompt_template": PANEL_PROMPT,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        client.table("ai_panel_prompt_versions").upsert(payload, on_conflict="version")
    except Exception as exc:
        logger.debug("AI panel prompt version persist skipped: %s", exc)



def _persist_result(symbol: str, result: Dict[str, Any], context: Dict[str, Any], extras: Dict[str, Any]) -> None:
    client = get_supabase_client()
    if client is None:
        return

    _persist_prompt_version()
    now_iso = datetime.now(timezone.utc).isoformat()
    expires_at = (datetime.now(timezone.utc) + timedelta(seconds=CACHE_TTL_SECONDS)).isoformat()
    fingerprint = _context_fingerprint(context, extras)
    analysis_meta = ((result.get("claude_analysis") or {}).get("analysis_meta") or {})
    panel_signal = ((result.get("claude_analysis") or {}).get("panel_signal") or {})

    cache_row = {
        "symbol": symbol,
        "analysis_version": ANALYSIS_VERSION,
        "prompt_version": PROMPT_VERSION,
        "provider": "deepseek",
        "model": analysis_meta.get("model") or DEEPSEEK_MODEL,
        "market_session": analysis_meta.get("market_session") or ((extras.get("market_state") or {}).get("session_name") or ""),
        "market_open": bool(analysis_meta.get("market_open")),
        "expires_at": expires_at,
        "context_fingerprint": fingerprint,
        "context_summary": {
            "market_state": extras.get("market_state"),
            "event_risk": extras.get("event_risk"),
            "regime": extras.get("regime"),
            "unified_news": extras.get("unified_news"),
        },
        "response_payload": result,
        "updated_at": now_iso,
    }
    history_row = {
        "symbol": symbol,
        "analysis_version": ANALYSIS_VERSION,
        "prompt_version": PROMPT_VERSION,
        "provider": "deepseek",
        "model": analysis_meta.get("model") or DEEPSEEK_MODEL,
        "cache_hit": False,
        "market_open": bool(analysis_meta.get("market_open")),
        "market_session": analysis_meta.get("market_session") or ((extras.get("market_state") or {}).get("session_name") or ""),
        "direction": (result.get("claude_analysis") or {}).get("claude_direction"),
        "confidence": (result.get("claude_analysis") or {}).get("claude_confidence"),
        "event_risk_level": ((panel_signal.get("event_risk") or {}).get("level") or "LOW"),
        "context_fingerprint": fingerprint,
        "signal_snapshot": panel_signal,
        "context_payload": {
            "context_pack_version": context.get("context_pack_version"),
            "ml_prediction": context.get("ml_prediction"),
            "ta_snapshot": context.get("ta_snapshot"),
            "ta_summary": context.get("ta_summary"),
            "levels": context.get("levels"),
            "volume": context.get("volume"),
            "volatility": context.get("volatility"),
            "market_state": extras.get("market_state"),
            "regime": extras.get("regime"),
            "unified_news": extras.get("unified_news"),
            "comex_news": extras.get("comex_news"),
            "oil_analysis": extras.get("oil_analysis"),
            "calendar_events": extras.get("calendar_events"),
        },
        "response_payload": result,
        "created_at": now_iso,
    }

    try:
        client.table("ai_panel_analysis_cache").upsert(cache_row, on_conflict="symbol")
    except Exception as exc:
        logger.debug("AI panel cache persist skipped for %s: %s", symbol, exc)

    try:
        client.table("ai_panel_analysis_history").insert(history_row)
    except Exception as exc:
        logger.debug("AI panel history persist skipped for %s: %s", symbol, exc)



def _build_compatibility_result(symbol: str, context: Dict[str, Any], panel_signal: Dict[str, Any], model_used: str, extras: Dict[str, Any]) -> Dict[str, Any]:
    intraday = panel_signal.get("intraday_bias") or {}
    scalp = panel_signal.get("scalp_bias") or {}
    entry_plan = panel_signal.get("entry_plan") or {}
    event_risk = panel_signal.get("event_risk") or {}
    market_state = extras.get("market_state") or {}
    direction = _coerce_direction(intraday.get("direction"), "HOLD")
    compatibility_direction = "HOLD" if direction == "NO_TRADE" else direction
    confidence = _float_with_default(intraday.get("confidence"), 50.0)
    ml_direction = str((context.get("ml_prediction") or {}).get("direction") or "HOLD")
    generated_at = datetime.now(timezone.utc).isoformat()

    analysis_meta = {
        "analysis_version": ANALYSIS_VERSION,
        "prompt_version": PROMPT_VERSION,
        "provider": "deepseek",
        "model": model_used,
        "cache_hit": False,
        "market_open": bool(market_state.get("is_primary_session_open")),
        "market_session": market_state.get("session_name"),
        "generated_at": generated_at,
        "expires_at": (datetime.now(timezone.utc) + timedelta(seconds=CACHE_TTL_SECONDS)).isoformat(),
        "context_pack_version": context.get("context_pack_version"),
    }

    market_context = {
        "ny_time": market_state.get("ny_time"),
        "phase": market_state.get("phase"),
        "session_name": market_state.get("session_name"),
        "regime": extras.get("regime") or {},
        "event_risk_level": event_risk.get("level"),
        "volatility_level": (context.get("volatility") or {}).get("level"),
    }

    data_sources = {
        "context_pack": True,
        "market_regime": bool(extras.get("regime")),
        "unified_news": bool(extras.get("unified_news")),
        "economic_calendar": True,
        "comex_news": bool(extras.get("comex_news")),
        "oil_analysis": bool(extras.get("oil_analysis")),
        "physical_oil": bool(extras.get("physical_oil_context")),
    }

    bull_case = [str(item) for item in _safe_list(panel_signal.get("bull_case"))[:5]]
    bear_case = [str(item) for item in _safe_list(panel_signal.get("bear_case"))[:5]]
    counter_factors = [str(item) for item in _safe_list(panel_signal.get("counter_factors"))[:5]]
    top_factors = [str(item) for item in _safe_list(panel_signal.get("top_factors"))[:5]]

    return {
        "symbol": symbol,
        "ml_direction": ml_direction,
        "claude_direction": compatibility_direction,
        "claude_confidence": round(confidence, 1),
        "agreement": compatibility_direction == ml_direction,
        "general_assessment": " ".join(
            part for part in [
                str(panel_signal.get("headline") or "").strip(),
                str((panel_signal.get("market_behavior") or {}).get("summary") or "").strip(),
                str(panel_signal.get("confidence_reasoning") or "").strip(),
            ] if part
        ),
        "strengths": bull_case,
        "weaknesses": bear_case,
        "recommended_entry": _float_with_default(entry_plan.get("preferred_entry"), _float_with_default((context.get("ml_prediction") or {}).get("entry_price"), 0.0)),
        "recommended_sl": _float_with_default(entry_plan.get("stop_loss"), _float_with_default((context.get("ml_prediction") or {}).get("stop_price"), 0.0)),
        "recommended_tp": _float_with_default(entry_plan.get("take_profit"), _float_with_default((context.get("ml_prediction") or {}).get("target_price"), 0.0)),
        "position_size_suggestion": _position_size_from_signal(direction, confidence, str(event_risk.get("level") or "LOW")),
        "key_observations": top_factors,
        "risk_factors": counter_factors,
        "timestamp": generated_at,
        "model_used": model_used,
        "panel_signal": panel_signal,
        "analysis_meta": analysis_meta,
        "market_context": market_context,
        "data_sources": data_sources,
        "scalp_direction": scalp.get("direction"),
        "scalp_confidence": scalp.get("confidence"),
        "physical_oil_intelligence": extras.get("physical_oil_context") or None,
    }



async def get_ai_panel_analysis(symbol: str, force_refresh: bool = False) -> Dict[str, Any]:
    normalized_symbol = normalize_symbol(symbol)
    if normalized_symbol not in SYMBOL_PROFILES:
        raise ValueError(f"Unsupported AI analysis symbol: {symbol}")

    market_state = _get_market_state(normalized_symbol)
    market_open = bool(market_state.get("is_primary_session_open"))

    fresh_memory = _get_memory_cached(normalized_symbol)
    fresh_db = None if fresh_memory is not None else _read_db_cache(normalized_symbol)

    if not force_refresh:
        if fresh_memory is not None:
            return fresh_memory
        if fresh_db is not None:
            return fresh_db
        if not market_open:
            stale_memory = _get_memory_cached(normalized_symbol, allow_stale=True)
            if stale_memory is not None:
                return stale_memory
            stale_db = _read_db_cache(normalized_symbol, allow_stale=True)
            if stale_db is not None:
                return stale_db
    elif not market_open:
        stale_memory = fresh_memory or _get_memory_cached(normalized_symbol, allow_stale=True)
        if stale_memory is not None:
            return stale_memory
        stale_db = fresh_db or _read_db_cache(normalized_symbol, allow_stale=True)
        if stale_db is not None:
            return stale_db

    try:
        context = await build_context_pack(normalized_symbol)
        extras = await _collect_symbol_extras(normalized_symbol, context)
        prompt_payload = _build_prompt_payload(context, extras)
        raw_panel_signal = await _request_panel_signal(prompt_payload)
        panel_signal = _normalize_panel_signal(raw_panel_signal, context, extras)
        model_used = str((raw_panel_signal or {}).get("ai_model") or DEEPSEEK_MODEL if raw_panel_signal else "panel-fallback-engine")

        result = {
            "ml_prediction": context.get("ml_prediction") or {},
            "claude_analysis": _build_compatibility_result(normalized_symbol, context, panel_signal, model_used, extras),
            "ta_snapshot": context.get("ta_snapshot") or {},
        }

        _set_memory_cached(normalized_symbol, result)
        _persist_result(normalized_symbol, result, context, extras)
        return result
    except Exception as exc:
        logger.exception("AI panel analysis refresh failed for %s", normalized_symbol)
        stale_memory = _get_memory_cached(normalized_symbol, allow_stale=True)
        if stale_memory is not None:
            return stale_memory
        stale_db = _read_db_cache(normalized_symbol, allow_stale=True)
        if stale_db is not None:
            return stale_db
        raise exc
