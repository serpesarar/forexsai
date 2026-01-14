from __future__ import annotations

from datetime import datetime

from config import settings
from services.marketaux_service import fetch_marketaux_headlines
from services.data_fetcher import fetch_latest_price
import httpx
import json


async def run_claude_sentiment(symbol: str = "NDX.INDX", lang: str = "en") -> dict:
    headlines = await fetch_marketaux_headlines(["NDX", "XAUUSD"])

    # Normalize symbol for price lookup
    sym = (symbol or "NDX.INDX").strip()
    if sym.upper() == "NASDAQ":
        sym = "NDX.INDX"
    current_price = await fetch_latest_price(sym)

    market_data_summary = {
        "symbol": sym,
        "current_price": current_price,
        "news_count": len(headlines),
        "news_source": "marketaux" if settings.marketaux_api_key else "unavailable",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    if not settings.anthropic_api_key:
        # Fallback deterministic sentiment if Claude key missing
        return {
            "sentiment": "NEUTRAL",
            "confidence": 0.55,
            "probability_up": 40,
            "probability_down": 35,
            "probability_sideways": 25,
            "key_factors": [
                {
                    "factor": "Headlines availability",
                    "impact": "neutral",
                    "weight": 0.4,
                    "reasoning": "ANTHROPIC_API_KEY missing; using fallback logic.",
                }
            ],
            "analysis": "Claude disabled; fallback sentiment used.",
            "recommendation": "HOLD",
            "market_data_summary": market_data_summary,
            "model_status": "ANTHROPIC_API_KEY missing",
            "headlines": headlines,
        }

    # Build a compact prompt with live data
    headline_lines = "\n".join([f"- {h.get('title','')} ({h.get('source','')})" for h in headlines[:10]])
    language_line = "Write all human-readable strings in Turkish." if (lang or "en").lower().startswith("tr") else "Write all human-readable strings in English."
    prompt = f"""
You are a market analyst. Using ONLY the provided data, output STRICT JSON (no markdown, no commentary) matching this schema:
{{
  "sentiment": "BULLISH" | "BEARISH" | "NEUTRAL",
  "confidence": number,  // 0..1
  "probability_up": integer, "probability_down": integer, "probability_sideways": integer,
  "key_factors": [{{"factor": string, "impact": "positive"|"negative"|"neutral", "weight": number, "reasoning": string}}],
  "analysis": string,
  "recommendation": string
}}

Instrument: {sym}
Live last price: {current_price}

Headlines:
{headline_lines}
{language_line}
""".strip()

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.anthropic_api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-3-haiku-20240307",
                    "max_tokens": 600,
                    "temperature": 0.2,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            resp.raise_for_status()
            data = resp.json()
            # Anthropics returns list content blocks; take first text block
            text = ""
            for block in data.get("content", []) or []:
                if block.get("type") == "text":
                    text = block.get("text", "")
                    break
            parsed = json.loads(text)
            # Attach metadata we maintain in our API response
            parsed["market_data_summary"] = market_data_summary
            parsed["model_status"] = None
            parsed["headlines"] = headlines
            return parsed
    except Exception as e:
        return {
            "sentiment": "NEUTRAL",
            "confidence": 0.55,
            "probability_up": 40,
            "probability_down": 35,
            "probability_sideways": 25,
            "key_factors": [
                {
                    "factor": "Claude request error",
                    "impact": "neutral",
                    "weight": 0.5,
                    "reasoning": str(e),
                }
            ],
            "analysis": "Claude request failed; fallback sentiment used.",
            "recommendation": "HOLD",
            "market_data_summary": market_data_summary,
            "model_status": "Claude request failed",
            "headlines": headlines,
        }
