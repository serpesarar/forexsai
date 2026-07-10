"""Native daily-bias debate engine (MiroShark-style, self-contained).

Six agents, routed by importance (see :mod:`services.llm_router`):
  normal → DeepSeek Reasoner:  technical_structure, volatility, macro
  important → Kimi:            bull_case, bear_case, cio (final JSON verdict)

Flow:  context agents (parallel) → multi-round bull/bear rebuttals → CIO.
Output is the CIO verdict dict, shaped for ``daily_bias_service.normalize_cio_payload``
and the bias-test harness.

MULTI-SYMBOL (2026-07-08): the engine is symbol-parametric. Each supported
instrument gets its own agent specialisations, validated-edge evidence (from
this project's leak-free confluence research + live-trading post-mortems) and
its own once-a-day decision window (scheduled in bias_auto_runner):

  NDX.INDX     08:00 & 09:45 ET   (unchanged NASDAQ flow, QQQ premarket proxy)
  XAUUSD       08:00 UTC          (Europe open; DXY/US10Y dual-macro driver)
  GDAXI.INDX   08:00 UTC          (XETRA open+1h; momentum/alignment driver)
  USOIL.FOREX  13:05 UTC          (pre-NY energy; inventory/whipsaw aware)

Any LLM/context failure in a context agent degrades gracefully; only a CIO
failure aborts the run (caller skips logging).
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
_XAU = "XAUUSD"
_DAX = "GDAXI.INDX"
_OIL = "USOIL.FOREX"


# ── Symbol profiles ────────────────────────────────────────────────────────────
# `evidence` = validated, leak-free findings from this project's research and
# live post-mortems. Injected to the debaters+CIO as PRIOR BASE RATES (not
# auto-signals) — the strongest lever we have against generic-LLM waffle.
SYMBOL_PROFILES: dict[str, dict] = {
    _NDX: {
        "display": "NASDAQ 100",
        "session_note": "US cash 09:30-16:00 ET; QQQ trades the premarket.",
        "drivers": "VIX (fear), US10Y (rates pressure long-duration tech), DXY.",
        "tech_extra": (
            "Use the QQQ premarket proxy (QQQ trades premarket; NDX cash does "
            "not) as your live read before the open. Evaluate the London "
            "session's direction and whether QQQ premarket confirms it — if "
            "London is strong but QQQ premarket is weak, flag that divergence."),
        "vol_extra": (
            "The session overlap (09:30-11:30 ET, London+US) is a "
            "high-volatility window. On a half day or holiday-eve, liquidity "
            "is thin and chop risk is high."),
        "macro_extra": (
            "DXY (dollar — inverse risk), US10Y (rising rates pressure "
            "long-duration NASDAQ). VIX — USE THE VALIDATED REGIME RULE, NOT "
            "FOLKLORE: our leak-free research (placebo p=0, OOS +17pp) shows "
            "VIX≥~18.4 (stress) historically FAVORS NDX UP over the next "
            "hours-day (oversold mean-reversion bounce), while calm low-VIX "
            "rallies are where shorts worked. A VIX SPIKE ALONE IS NOT A "
            "BEARISH SIGNAL for the day's close — do not map 'VIX up → "
            "risk-off → bearish'. Check whether Asia went risk-off overnight."),
        "evidence": (
            "VALIDATED NDX BASE RATES (leak-free research): equity indices are "
            "LONG-heavy — honest short ceiling is ~57-59% and ONLY in "
            "high-VIX stress + downward momentum; in calm markets shorts lose. "
            "Full indicator alignment (bull_score≥11/12) + short-term momentum "
            "leadership → 75-78% up over 6-24h. Do not call high-confidence "
            "bearish without a stress regime. LIVE CALIBRATION (Jul 2026): "
            "'gap/break below prior-day low → bearish continuation' calls "
            "FAILED repeatedly (the gaps FADED and NDX closed up; 0/3 on "
            "2026-07-08 alone). A prior-low break alone is NOT a validated "
            "short edge — require stress regime + US futures confirming down, "
            "otherwise stay neutral/choppy."),
        "cio_extra": (
            "Consider the session chain Asia → London → US direction transfer, "
            "but the correlation is NOT constant — on rate shocks or sector "
            "divergence the London-NASDAQ link breaks. Treat correlation as "
            "evidence, never assume it."),
    },
    _XAU: {
        "display": "GOLD (XAUUSD)",
        "session_note": "~24h OTC; most decisive flow Europe morning → NY; day effectively closes 17:00 NY.",
        "drivers": "DXY (inverse), US10Y real-rate proxy (inverse), risk-off flows (VIX).",
        "tech_extra": (
            "Gold is two-sided (unlike equity indices). Weigh the overnight "
            "Asia drift and the Europe-morning impulse. Key structure: prior "
            "day H/L, 5-day range edges — gold respects them more than "
            "indices do."),
        "vol_extra": (
            "Gold chops violently around US data hours (08:30/10:00 ET) and "
            "thins out after NY close. If the day is a US-data day, raise chop "
            "risk. London-NY overlap is the trend window."),
        "macro_extra": (
            "THE gold driver is the DXY + US10Y pair: BOTH falling = strong "
            "tailwind for gold; BOTH rising = strong headwind. One rising and "
            "one falling = mixed, lower conviction. VIX spikes add safe-haven "
            "bids. Weigh the PAIR, not either alone."),
        "evidence": (
            "VALIDATED GOLD BASE RATES (leak-free research + live post-mortems): "
            "gold is genuinely TWO-SIDED (both directions tradeable, unlike "
            "NDX/DAX). Confirmed leak-free edge: multi-TF bullish alignment + "
            "overnight-up carries ~70%+ up over the next day. Daily-swing "
            "Donchian-breakout BUY (with EMA200 filter) is the proven gold "
            "strategy (64.5% WR, +0.69R). CAUTION: gold intraday scalping has "
            "NO honest edge, and tight stops destroy otherwise-good calls — "
            "gold verdicts need WIDE invalidation levels, not tight ones. "
            "Macro same-day co-movement is NOT predictive (leak) — use "
            "regime/level logic, not 'DXY is down right now so gold up'."),
        "cio_extra": (
            "Gold rewards patience: prefer wider invalid_if levels (gold "
            "whips through tight ones). If DXY and US10Y disagree, cut "
            "confidence materially."),
    },
    _DAX: {
        "display": "DAX 40 (GDAXI)",
        "session_note": "XETRA cash 09:00-17:30 Berlin; decision runs at open+1h.",
        "drivers": "NDX/US futures correlation, EUR, Europe risk tone.",
        "tech_extra": (
            "DAX is an equity index that behaves like NDX's European cousin: "
            "momentum-continuation works, mean-reversion shorting does not. "
            "Read the first hour after the XETRA open (the decision runs at "
            "open+1h): opening drive direction + whether US futures agree."),
        "vol_extra": (
            "DAX volume is synthetic tick volume (weak signal) — do not lean "
            "on volume. Chop risk rises before US open (13:30 UTC) when DAX "
            "waits for US direction; afternoons often re-price to US futures."),
        "macro_extra": (
            "DAX follows global risk tone: US futures/NDX direction, EUR "
            "moves, and Europe-specific news. Rising US yields hit DAX too "
            "but less than NDX. A strong US-futures premarket bid usually "
            "lifts DAX afternoons."),
        "evidence": (
            "VALIDATED DAX BASE RATES (leak-free research + live post-mortems): "
            "LONG momentum/alignment works (~74-77% when short-term momentum "
            "agrees across TFs and price is stretched high in its band — "
            "preliminary, ~2.9y data). SHORT is structurally weak (best "
            "honest short combo ~67%; live pulse1-DAX ran 25% WR and is "
            "SUSPENDED). Synthetic volume and pivot S/R are weak references "
            "on DAX. Do not issue high-confidence bearish unless Europe is "
            "in clear stress with US futures confirming down."),
        "cio_extra": (
            "If US futures and the XETRA opening drive disagree, prefer "
            "neutral/choppy over forcing a direction. DAX afternoons are "
            "often decided by the US open, not by Europe."),
    },
    _OIL: {
        "display": "WTI CRUDE (USOIL)",
        "session_note": "NYMEX pit 09:00-14:30 ET (settle 14:30 ET); Wed 10:30 ET EIA inventories.",
        "drivers": "Inventories (EIA Wed), OPEC headlines, DXY, growth/risk tone.",
        "tech_extra": (
            "Oil is a whipsaw instrument: clean trends are rare intraday, "
            "false breakouts are common. Respect the prior-day settle and "
            "overnight range; a break that fails back inside the range is a "
            "reversal tell, not a continuation."),
        "vol_extra": (
            "If today is Wednesday, the 10:30 ET EIA inventory report is a "
            "volatility bomb — direction before it is low-conviction. OPEC "
            "headline risk can hit at any hour. Reflect these in risk_level "
            "and day_type."),
        "macro_extra": (
            "Oil drivers: inventory surprises (EIA Wednesdays), OPEC supply "
            "headlines, DXY (inverse, mildly), and global growth/risk tone "
            "(equities up + risk-on supports crude). US10Y matters less here."),
        "evidence": (
            "VALIDATED USOIL BASE RATES (leak-free research + live post-mortems): "
            "oil is whipsaw-dominant — most intraday breakout styles fail "
            "friction. Momentum-continuation BUY is the validated live entry; "
            "indicator-discrimination showed the SELL side is where indicators "
            "separate winners from losers best (oil sells need stronger "
            "confirmation, buys ride momentum). Live combo 'emel+pulse1+"
            "pulse2+smc' on USOIL ran toxic (27% WR) — stacked-model consensus "
            "is NOT edge on oil. Prefer momentum + level logic; distrust "
            "indicator pile-ups."),
        "cio_extra": (
            "On EIA Wednesdays cap confidence at ~60 before the 10:30 ET "
            "report. A verdict that fights the prevailing weekly momentum "
            "needs explicit evidence (inventory/OPEC), not chart shapes."),
    },
}


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


def _daily_from_1h(h1: list[dict]) -> list[dict]:
    """Group 1h candles into per-UTC-date OHLC bars (coarse but honest)."""
    days: dict[str, dict] = {}
    for c in h1 or []:
        ts = str(c.get("timestamp") or c.get("time") or "")
        day = ts[:10]
        o, h, l, cl = _c(c, "open", "o"), _c(c, "high", "h"), _c(c, "low", "l"), _c(c, "close", "c")
        if not day or cl is None:
            continue
        d = days.setdefault(day, {"timestamp": day, "open": o, "high": h, "low": l, "close": cl})
        d["high"] = max(d["high"] or h, h or d["high"]) if (h or d["high"]) else d["high"]
        d["low"] = min(d["low"] or l, l or d["low"]) if (l or d["low"]) else d["low"]
        d["close"] = cl
    return [days[k] for k in sorted(days)]


async def _gather_context(symbol: str, now_utc: datetime) -> dict:
    ctx = await sc.enrich_price_context(now_utc)
    market: dict[str, Any] = {"session": ctx, "price": None, "prior_day": None,
                              "recent_range": None, "qqq": None, "macro": None}
    try:
        from services.data_fetcher import fetch_latest_price, fetch_ohlc_data
        market["price"] = await fetch_latest_price(symbol)
        daily = await fetch_ohlc_data(symbol, "1d", limit=10)
        if not daily:
            # 1d feed dead (bridge streams none for NDX, sparse for others) →
            # derive coarse daily bars from 1h so agents see prior-day + range.
            daily = _daily_from_1h(await fetch_ohlc_data(symbol, "1h", limit=200))
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

    # Side feeds (best-effort, nullable). QQQ proxy is NDX-specific.
    if symbol == _NDX:
        market["qqq"] = await _qqq_premarket()
        if market["qqq"] and market["qqq"].get("premarket_change_pct") is not None:
            ctx["us_premarket_change"] = market["qqq"]["premarket_change_pct"]
    market["macro"] = _macro_gauges()
    return market


def _context_block(market: dict, symbol: str) -> str:
    prof = SYMBOL_PROFILES[symbol]
    s = market["session"]
    lines = [
        f"Symbol: {prof['display']} ({symbol})",
        f"Instrument session: {prof['session_note']}",
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


# ── Agents (built per symbol from the profile) ─────────────────────────────────
def _build_agents(symbol: str) -> dict[str, tuple[str, str]]:
    p = SYMBOL_PROFILES[symbol]
    name = p["display"]
    return {
        "technical_structure": (
            "normal",
            f"You are the Technical Structure agent for {name} intraday bias. "
            f"Assess trend, key support/resistance, and market structure. "
            f"{p['tech_extra']} Be concise (<150 words)."),
        "volatility": (
            "normal",
            f"You are the Volatility agent for {name}. Assess expected intraday "
            f"volatility and chop risk. {p['vol_extra']} Be concise (<150 words)."),
        "macro": (
            "normal",
            f"You are the Macro agent for {name}. Read the live gauges provided. "
            f"{p['macro_extra']} Weigh them together, don't cite one in "
            f"isolation. <150 words."),
        "bull_case": (
            "important",
            f"You are the Bull-case debater for {name} today. Argue the strongest "
            f"evidence-based case for UP/bullish, using the context and the other "
            f"agents' notes. {p['evidence']} No hype — cite concrete "
            f"structure/levels. <180 words."),
        "bear_case": (
            "important",
            f"You are the Bear-case debater for {name} today. Argue the strongest "
            f"evidence-based case for DOWN/bearish, using the context and the other "
            f"agents' notes. {p['evidence']} No hype — cite concrete "
            f"structure/levels. <180 words."),
    }


def _build_cio_system(symbol: str) -> str:
    p = SYMBOL_PROFILES[symbol]
    # NOTE: the verdict key stays "nasdaq_daily_bias" for ALL symbols — the
    # normalizer/harness/DB were built around it. It simply means "daily bias".
    return (
        f"You are the CIO. Synthesize the agents and the bull/bear debate into "
        f"ONE {p['display']} daily bias verdict. {p['cio_extra']}\n"
        f"Known drivers: {p['drivers']}\n"
        f"{p['evidence']}\n\n"
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
        "}\n\n"
        "CRITICAL: main_support and main_resistance MUST be real levels derived "
        "from the CURRENT PRICE given in the market context (within a few "
        "percent of it). NEVER invent price levels from memory/training data — "
        "if the context lacks enough structure to place levels, set them to null."
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
    """Run the full debate for `symbol` and return the CIO verdict dict.

    Raises :class:`llm_router.LLMUnavailable` if the CIO step can't complete,
    :class:`ValueError` for an unsupported symbol.
    """
    if symbol not in SYMBOL_PROFILES:
        raise ValueError(f"unsupported debate symbol: {symbol!r} "
                         f"(supported: {sorted(SYMBOL_PROFILES)})")
    now_utc = now_utc or datetime.now(timezone.utc)

    market = await _gather_context(symbol, now_utc)
    ctx_block = _context_block(market, symbol)
    agents = _build_agents(symbol)

    # CORTEX — episodic memory is NASDAQ-only by design (isolated store).
    situation, analog_block = None, ""
    if symbol == _NDX:
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
        _run_agent(n, agents[n][0], agents[n][1],
                   f"MARKET CONTEXT:\n{ctx_block}\n\nGive your assessment.")
        for n in ctx_names
    ])
    notes = dict(zip(ctx_names, ctx_results))
    notes_block = "\n\n".join(f"[{n}]\n{t}" for n, t in notes.items())

    # 2) Multi-round ADVERSARIAL debate — bull & bear rebut each other over N
    #    rounds so weak arguments get refuted and the real signal survives.
    try:
        from config import settings as _s
        rounds = max(1, int(getattr(_s, "debate_rounds", 3)))
    except Exception:
        rounds = 3
    base_user = f"MARKET CONTEXT:\n{ctx_block}\n\nAGENT NOTES:\n{notes_block}"
    transcript: list[tuple[int, str, str]] = []
    bull, bear = "", ""
    for r in range(1, rounds + 1):
        if r == 1:
            bu = base_user + "\n\nOpening argument for UP/bullish."
            beu = base_user + "\n\nOpening argument for DOWN/bearish."
        else:
            bu = (base_user + f"\n\nThe BEAR just argued:\n{bear}\n\nRebut the bear's "
                  "strongest point, concede anything genuinely valid, and sharpen your "
                  "bull case. <180 words.")
            beu = (base_user + f"\n\nThe BULL just argued:\n{bull}\n\nRebut the bull's "
                   "strongest point, concede anything genuinely valid, and sharpen your "
                   "bear case. <180 words.")
        bull, bear = await asyncio.gather(
            _run_agent("bull_case", agents["bull_case"][0], agents["bull_case"][1], bu),
            _run_agent("bear_case", agents["bear_case"][0], agents["bear_case"][1], beu),
        )
        transcript.append((r, bull, bear))
    debate_block = "\n\n".join(
        f"[ROUND {rn}]\nBULL: {b}\nBEAR: {be}" for rn, b, be in transcript)

    # Validated confluence playbook (OOS-tested rules) as prior evidence.
    rules_block = ""
    try:
        from config import settings
        if settings.cortex_rules_inject:
            from services.cortex_confluence_rules import rules_prompt_block
            rules_block = rules_prompt_block(symbol)
    except Exception as e:
        logger.debug("[debate] rules block skipped: %s", e)

    # ÖZ-KALİBRASYON: sistemin son tahminlerinin gerçekleşme karnesi (fail-open).
    # 2026-07-09 otopsisi: %30.8 doğruluk, boğa piyasasında art arda bearish — model
    # kendi karnesini görmediği için aynı önyargıyı tekrarlıyordu.
    track_block = ""
    try:
        from services.bias_test_service import recent_track_record
        track_block = recent_track_record()
    except Exception as e:
        logger.debug("[debate] track record skipped: %s", e)

    # 3) CIO synthesis → JSON verdict (important tier, JSON mode). Sees the FULL
    #    multi-round debate (both sides' rebuttals) + analog base rate + playbook.
    cio_user = (f"MARKET CONTEXT:\n{ctx_block}\n\n"
                + (f"{analog_block}\n\n" if analog_block else "")
                + (f"{rules_block}\n\n" if rules_block else "")
                + (f"{track_block}\n\n" if track_block else "")
                + f"AGENT NOTES:\n{notes_block}\n\n"
                f"FULL {rounds}-ROUND DEBATE (later rounds are rebuttals — weigh which "
                f"side's argument survived the rebuttals):\n{debate_block}\n\n"
                "Now output the final verdict JSON.")
    content, provider = await llm_router.chat(
        _build_cio_system(symbol), cio_user, importance="important", json_mode=True,
        temperature=0.2, max_tokens=1500)

    verdict = llm_router.extract_json(content)
    if not verdict or not verdict.get("nasdaq_daily_bias"):
        raise llm_router.LLMUnavailable("CIO returned no parseable verdict")

    # Sanity-clamp hallucinated levels: the first live run produced S/R ~34%
    # away from the real price (model recalled training-era index levels).
    # A support/resistance more than 10% from the live price is unusable and
    # would poison invalid_if monitoring — null it and flag.
    price = market.get("price")
    verdict["symbol"] = symbol
    verdict["price_at_decision"] = price
    if price:
        for key in ("main_support", "main_resistance"):
            try:
                v = float(verdict.get(key)) if verdict.get(key) is not None else None
            except (TypeError, ValueError):
                v = None
            if v is not None and abs(v - price) / price > 0.10:
                logger.warning("[debate] %s=%s is >10%% from price %s — clamped to null",
                               key, v, price)
                verdict[key] = None
                verdict["sr_clamped"] = True

    verdict["_debate"] = {
        "cio_provider": provider,
        "symbol": symbol,
        "context_notes": notes,
        "rounds": rounds,
        "transcript": [{"round": rn, "bull": b, "bear": be} for rn, b, be in transcript],
        "bull_case": bull,   # final round
        "bear_case": bear,   # final round
        "generated_at_utc": now_utc.isoformat(),
        "session": market["session"],
        "analog_block": analog_block or None,
    }
    # Attach the situation so record_run can persist a CORTEX episode with the
    # EXACT vector the analogs were computed against (consistency).
    if situation is not None:
        verdict["_cortex_situation"] = situation
    return verdict
