"""Native NASDAQ daily-bias debate engine (MiroShark-style, self-contained).

Six agents, routed by importance (see :mod:`services.llm_router`):
  normal → DeepSeek Reasoner:  technical_structure, volatility, macro
  important → Kimi:            bull_case, bear_case, cio (final JSON verdict)

Flow:  context agents (parallel) → bull & bear (parallel) → CIO synthesis.
Output is the CIO verdict dict, shaped for ``daily_bias_service.normalize_cio_payload``
and the bias-test harness. Session-aware prompts fold in the Stage-D guidance.

NASDAQ-only. Any LLM/context failure in a context agent degrades gracefully;
only a CIO failure aborts the run (caller skips logging).
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from services import llm_router
from services import session_context_service as sc

logger = logging.getLogger(__name__)

_NDX = "NDX.INDX"


# ── Context gathering (best-effort; numbers help the agents reason) ────────────
def _c(candle: dict, *keys: str) -> Optional[float]:
    for k in keys:
        v = candle.get(k)
        if v is not None:
            try:
                return float(v)
            except (TypeError, ValueError):
                return None
    return None


_QQQ = "QQQ.US"   # NASDAQ-100 ETF — trades the US premarket (NDX cash doesn't)


async def _qqq_premarket() -> dict:
    """Best-effort QQQ premarket read: live price + % vs prior close.

    QQQ is the closest live proxy for NASDAQ direction before the cash open.
    Any missing piece → None (never fabricated). Fills the premarket gap that
    the NDX cash index can't cover.
    """
    out: dict[str, Any] = {"price": None, "premarket_change_pct": None, "prior_close": None}
    try:
        from services.data_fetcher import fetch_latest_price, fetch_ohlc_data
        out["price"] = await fetch_latest_price(_QQQ)
        daily = await fetch_ohlc_data(_QQQ, "1d", limit=5)
        prior_close = _c(daily[-2], "close", "c") if daily and len(daily) >= 2 else None
        out["prior_close"] = prior_close
        if out["price"] and prior_close:
            out["premarket_change_pct"] = round(
                (out["price"] - prior_close) / prior_close * 100.0, 3)
    except Exception as e:
        logger.debug("[debate] QQQ premarket unavailable: %s", e)
    return out


def _macro_gauges() -> dict:
    """DXY / VIX / US10Y snapshot from the existing macro service (fail-open)."""
    try:
        from services.macro_data_service import get_macro_dict
        m = get_macro_dict() or {}
        return {k: {"price": (m.get(k) or {}).get("price"),
                    "chg_1h": (m.get(k) or {}).get("change_1h_pct")}
                for k in ("dxy", "vix", "us10y")}
    except Exception as e:
        logger.debug("[debate] macro gauges unavailable: %s", e)
        return {}


async def _gather_context(symbol: str, now_utc: datetime) -> dict:
    ctx = await sc.enrich_price_context(now_utc)
    market: dict[str, Any] = {"session": ctx, "price": None, "prior_day": None,
                              "recent_range": None, "qqq": None, "macro": None}
    try:
        from services.data_fetcher import fetch_latest_price, fetch_ohlc_data
        market["price"] = await fetch_latest_price(symbol)
        daily = await fetch_ohlc_data(symbol, "1d", limit=10)
        if daily and len(daily) >= 2:
            prev = daily[-2]
            market["prior_day"] = {
                "high": _c(prev, "high", "h"), "low": _c(prev, "low", "l"),
                "close": _c(prev, "close", "c"), "open": _c(prev, "open", "o"),
            }
            highs = [_c(d, "high", "h") for d in daily[-5:] if _c(d, "high", "h")]
            lows = [_c(d, "low", "l") for d in daily[-5:] if _c(d, "low", "l")]
            if highs and lows:
                market["recent_range"] = {"5d_high": max(highs), "5d_low": min(lows)}
    except Exception as e:
        logger.warning("[debate] context fetch degraded: %s", e)

    # Side feeds (best-effort, nullable).
    market["qqq"] = await _qqq_premarket()
    market["macro"] = _macro_gauges()
    # Fill the session's premarket gap from QQQ when we have it.
    if market["qqq"] and market["qqq"].get("premarket_change_pct") is not None:
        ctx["us_premarket_change"] = market["qqq"]["premarket_change_pct"]
    return market


def _context_block(market: dict) -> str:
    s = market["session"]
    lines = [
        f"Symbol: NASDAQ 100 ({_NDX})",
        f"NY time: {s.get('ny_time')} | session: {s.get('current_session')} | "
        f"minutes_to_US_open: {s.get('minutes_to_us_open')}",
        f"session_overlap(09:30-11:30 ET): {s.get('session_overlap')} | "
        f"half_day: {s.get('is_half_day')} | holiday: {s.get('is_holiday')}",
        f"London session direction so far: {s.get('london_session_direction')}",
        f"Asia overnight change: {s.get('asia_overnight_change')} | "
        f"US premarket change: {s.get('us_premarket_change')}",
        f"Current price: {market.get('price')}",
    ]
    if market.get("prior_day"):
        pd = market["prior_day"]
        lines.append(f"Prior day O/H/L/C: {pd.get('open')}/{pd.get('high')}/"
                     f"{pd.get('low')}/{pd.get('close')}")
    if market.get("recent_range"):
        rr = market["recent_range"]
        lines.append(f"5-day range: {rr.get('5d_low')} – {rr.get('5d_high')}")
    q = market.get("qqq") or {}
    if q.get("price") is not None:
        lines.append(f"QQQ (premarket-live proxy): {q.get('price')} | "
                     f"premarket vs prior close: {q.get('premarket_change_pct')}%")
    mac = market.get("macro") or {}
    if mac:
        def _g(k):
            v = mac.get(k) or {}
            return f"{v.get('price')} ({v.get('chg_1h')}%/1h)"
        lines.append(f"Macro: DXY {_g('dxy')} | VIX {_g('vix')} | US10Y {_g('us10y')}")
    return "\n".join(lines)


# ── Agents ────────────────────────────────────────────────────────────────────
_AGENTS = {
    "technical_structure": (
        "normal",
        "You are the Technical Structure agent for NASDAQ 100 intraday bias. "
        "Assess trend, key support/resistance, and market structure. Use the QQQ "
        "premarket proxy (QQQ trades premarket; NDX cash does not) as your live "
        "read before the open. Evaluate the London session's direction and "
        "whether QQQ premarket confirms it — if London is strong but QQQ "
        "premarket is weak, flag that divergence: direction may flip at the open. "
        "Be concise (<150 words)."),
    "volatility": (
        "normal",
        "You are the Volatility agent for NASDAQ 100. Assess expected intraday "
        "volatility and chop risk. The session overlap (09:30-11:30 ET, "
        "London+US) is a high-volatility window. On a half day or holiday-eve, "
        "liquidity is thin and chop risk is high — reflect that in day_type. "
        "Be concise (<150 words)."),
    "macro": (
        "normal",
        "You are the Macro agent for NASDAQ 100. Read the live gauges provided: "
        "DXY (dollar — inverse risk), VIX (fear — high/rising = risk-off, bad for "
        "tech), US10Y (10y yield — rising rates pressure long-duration NASDAQ). "
        "Check whether Asia went risk-off overnight — that can carry into the US "
        "open. Weigh these together, don't cite one in isolation. <150 words."),
    "bull_case": (
        "important",
        "You are the Bull-case debater for NASDAQ 100 today. Argue the strongest "
        "evidence-based case for UP/bullish, using the context and the other "
        "agents' notes. No hype — cite concrete structure/levels. <180 words."),
    "bear_case": (
        "important",
        "You are the Bear-case debater for NASDAQ 100 today. Argue the strongest "
        "evidence-based case for DOWN/bearish, using the context and the other "
        "agents' notes. No hype — cite concrete structure/levels. <180 words."),
}

_CIO_SYSTEM = (
    "You are the CIO. Synthesize the agents and the bull/bear debate into ONE "
    "NASDAQ daily bias verdict. Consider the session chain Asia → London → US "
    "direction transfer, but remember the correlation is NOT constant — on rate "
    "shocks or sector divergence the London-NASDAQ link breaks. Treat "
    "correlation as evidence, never assume it.\n\n"
    "Return ONLY a JSON object with EXACTLY these keys:\n"
    "{\n"
    '  "nasdaq_daily_bias": "bullish|bearish|neutral|choppy",\n'
    '  "confidence": 0-100,\n'
    '  "expected_close": "positive|negative|flat|uncertain",\n'
    '  "trade_mode": "buy_dips_only|sell_rallies_only|range_scalp|wait_and_see",\n'
    '  "risk_level": "low|medium|high",\n'
    '  "main_support": number,\n'
    '  "main_resistance": number,\n'
    '  "invalid_if": "short text (a price level/condition)",\n'
    '  "reason_summary": "2-3 sentence rationale",\n'
    '  "agent_agreement": "high|mixed|low",\n'
    '  "risk_flags": ["..."],\n'
    '  "debate_winner": "bull|bear|balanced"\n'
    "}"
)


async def _run_agent(name: str, importance: str, system: str, user: str) -> str:
    try:
        content, provider = await llm_router.chat(system, user, importance=importance)
        logger.info("[debate] %s via %s (%d chars)", name, provider, len(content))
        return content.strip()
    except Exception as e:
        logger.warning("[debate] agent %s failed: %s", name, e)
        return f"({name} unavailable: {str(e)[:80]})"


async def run_debate(symbol: str = _NDX, now_utc: Optional[datetime] = None) -> dict:
    """Run the full debate and return the CIO verdict dict.

    Raises :class:`llm_router.LLMUnavailable` if the CIO step can't complete.
    """
    if symbol != _NDX:
        raise ValueError("bias debate engine is NASDAQ-only")
    now_utc = now_utc or datetime.now(timezone.utc)

    market = await _gather_context(symbol, now_utc)
    ctx_block = _context_block(market)

    # CORTEX — build today's situation (for episodic memory). Analog base-rate
    # INJECTION into the CIO prompt is opt-in (cortex_analog_inject) because the
    # backtest found no reliable directional edge; recording still runs so the
    # memory accumulates for Phase 2/3.
    situation, analog_block = None, ""
    try:
        from config import settings
        if settings.cortex_enabled:
            from services import cortex_memory as cortex
            situation = await cortex.build_situation(now_utc, market=market)
            if settings.cortex_analog_inject:
                analog = cortex.find_analogs(situation, k=settings.cortex_analog_k)
                analog_block = cortex.analogs_prompt_block(analog)
    except Exception as e:
        logger.warning("[debate] CORTEX situation/analog skipped: %s", e)

    # 1) Context agents in parallel.
    ctx_names = ["technical_structure", "volatility", "macro"]
    ctx_results = await asyncio.gather(*[
        _run_agent(n, _AGENTS[n][0], _AGENTS[n][1],
                   f"MARKET CONTEXT:\n{ctx_block}\n\nGive your assessment.")
        for n in ctx_names
    ])
    notes = dict(zip(ctx_names, ctx_results))
    notes_block = "\n\n".join(f"[{n}]\n{t}" for n, t in notes.items())

    # 2) Bull & bear debate in parallel (they see the context notes).
    debate_user = f"MARKET CONTEXT:\n{ctx_block}\n\nAGENT NOTES:\n{notes_block}"
    bull, bear = await asyncio.gather(
        _run_agent("bull_case", _AGENTS["bull_case"][0], _AGENTS["bull_case"][1], debate_user),
        _run_agent("bear_case", _AGENTS["bear_case"][0], _AGENTS["bear_case"][1], debate_user),
    )

    # Validated confluence playbook (OOS-tested rules) as prior evidence.
    rules_block = ""
    try:
        from config import settings
        if settings.cortex_rules_inject:
            from services.cortex_confluence_rules import rules_prompt_block
            rules_block = rules_prompt_block(symbol)
    except Exception as e:
        logger.debug("[debate] rules block skipped: %s", e)

    # 3) CIO synthesis → JSON verdict (important tier, JSON mode).
    #    Analog base rate + validated playbook given to the CIO as prior evidence.
    cio_user = (f"MARKET CONTEXT:\n{ctx_block}\n\n"
                + (f"{analog_block}\n\n" if analog_block else "")
                + (f"{rules_block}\n\n" if rules_block else "")
                + f"AGENT NOTES:\n{notes_block}\n\n"
                f"BULL CASE:\n{bull}\n\nBEAR CASE:\n{bear}\n\n"
                "Now output the final verdict JSON.")
    content, provider = await llm_router.chat(
        _CIO_SYSTEM, cio_user, importance="important", json_mode=True,
        temperature=0.2, max_tokens=1200)

    verdict = llm_router.extract_json(content)
    if not verdict or not verdict.get("nasdaq_daily_bias"):
        raise llm_router.LLMUnavailable("CIO returned no parseable verdict")

    verdict["_debate"] = {
        "cio_provider": provider,
        "context_notes": notes,
        "bull_case": bull,
        "bear_case": bear,
        "generated_at_utc": now_utc.isoformat(),
        "session": market["session"],
        "analog_block": analog_block or None,
    }
    # Attach the situation so record_run can persist a CORTEX episode with the
    # EXACT vector the analogs were computed against (consistency).
    if situation is not None:
        verdict["_cortex_situation"] = situation
    return verdict
