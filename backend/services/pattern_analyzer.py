from __future__ import annotations

from datetime import datetime
from typing import Dict

from config import settings
import json
import httpx

from services.data_fetcher import fetch_latest_price
from services.data_fetcher import fetch_eod_candles


async def _run_single_timeframe(symbol: str, timeframe: str, lang: str, current_price_value: float, series_json: str) -> dict:
    language_line = (
        "Write all human-readable strings in Turkish."
        if (lang or "en").lower().startswith("tr")
        else "Write all human-readable strings in English."
    )
    prompt = f"""
You are a technical analyst. Return STRICT JSON only (no markdown) in this schema:
{{
  "detected_patterns": [{{"pattern_name": string, "pattern_source": string, "completion_percentage": integer, "signal":"bullish"|"bearish"|"neutral", "entry": number, "stop_loss": number, "target": number, "confidence": number, "reasoning": string}}],
  "summary": string,
  "recommendation": "BUY"|"SELL"|"HOLD"
}}

Instrument: {symbol}
Timeframe: {timeframe}
Live last price (may be 0 if unavailable): {current_price_value}

Price series (last 100 candles, JSON list of {{d,c}} where c=close):
{series_json}

Use this data to infer key patterns. Keep strings concise and JSON-valid.
{language_line}
""".strip()

    async with httpx.AsyncClient(timeout=25.0) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": settings.anthropic_api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-3-haiku-20240307",
                "max_tokens": 700,
                "temperature": 0.2,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        resp.raise_for_status()
        data = resp.json()
        text = ""
        for block in data.get("content", []) or []:
            if block.get("type") == "text":
                text = block.get("text", "")
                break
        return json.loads(text)


async def run_claude_pattern_analysis(symbol: str, timeframes: list[str], lang: str = "en") -> dict:
    current_price = await fetch_latest_price(symbol)
    current_price_value = float(current_price) if current_price is not None else 0.0
    eod = await fetch_eod_candles(symbol, limit=100)
    series = [{"d": r.get("date"), "c": r.get("close")} for r in eod]
    series_json = json.dumps(series, ensure_ascii=False)

    if not settings.anthropic_api_key:
        # Minimal fallback without hallucinating hardcoded prices
        analyses: Dict[str, dict] = {}
        for timeframe in timeframes:
            analyses[timeframe] = {
                "detected_patterns": [],
                "summary": f"{timeframe} timeframe pattern analysis unavailable (ANTHROPIC_API_KEY missing).",
                "recommendation": "HOLD",
            }
        return {
            "analyses": analyses,
            "current_price": current_price_value,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "model_status": "ANTHROPIC_API_KEY missing",
        }

    try:
        analyses: Dict[str, dict] = {}
        # Call Claude per timeframe to avoid large JSON responses that can break parsing.
        for tf in timeframes:
            try:
                one = await _run_single_timeframe(
                    symbol=symbol,
                    timeframe=tf,
                    lang=lang,
                    current_price_value=current_price_value,
                    series_json=series_json,
                )
                analyses[tf] = {
                    "detected_patterns": one.get("detected_patterns", []) or [],
                    "summary": one.get("summary", "") or "",
                    "recommendation": one.get("recommendation", "HOLD") or "HOLD",
                }
            except Exception as e:
                analyses[tf] = {
                    "detected_patterns": [],
                    "summary": f"{tf} timeframe pattern analysis failed: {e}",
                    "recommendation": "HOLD",
                }
        return {
            "analyses": analyses,
            "current_price": current_price_value,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "model_status": None,
        }
    except Exception as e:
        analyses: Dict[str, dict] = {}
        for timeframe in timeframes:
            analyses[timeframe] = {
                "detected_patterns": [],
                "summary": f"{timeframe} timeframe pattern analysis failed: {e}",
                "recommendation": "HOLD",
            }
        return {
            "analyses": analyses,
            "current_price": current_price_value,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "model_status": "Claude request failed",
        }
