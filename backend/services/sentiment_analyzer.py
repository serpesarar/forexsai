from __future__ import annotations

from datetime import datetime

from config import settings
from services.marketaux_service import fetch_marketaux_headlines
from services.data_fetcher import fetch_latest_price
import httpx
import json


async def run_claude_sentiment(symbol: str = "NDX.INDX", lang: str = "en") -> dict:
    """
    DEPRECATED: Use RSS aggregator sentiment instead (more efficient, cost-optimized)
    This function now returns RSS-based sentiment without extra DeepSeek calls
    """
    # Normalize symbol for price lookup
    sym = (symbol or "NDX.INDX").strip()
    if sym.upper() == "NASDAQ":
        sym = "NDX.INDX"
    current_price = await fetch_latest_price(sym)
    
    # Initialize headlines (prevent NameError)
    headlines = []

    # Get recent news from RSS (already analyzed by DeepSeek)
    from services.redis_client import cache_get
    rss_sentiment = cache_get(f"rss_sentiment:{sym}") or {}

    market_data_summary = {
        "symbol": sym,
        "current_price": current_price,
        "news_count": rss_sentiment.get("news_count", 0),
        "news_source": "rss_aggregator",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    # Skip DeepSeek - use RSS sentiment data (already analyzed)
    if rss_sentiment:
        return {
            "sentiment": rss_sentiment.get("sentiment", "NEUTRAL"),
            "confidence": rss_sentiment.get("confidence", 0.6),
            "probability_up": rss_sentiment.get("probability_up", 35),
            "probability_down": rss_sentiment.get("probability_down", 30),
            "probability_sideways": rss_sentiment.get("probability_sideways", 35),
            "key_factors": rss_sentiment.get("key_factors", []),
            "analysis": "Using RSS-aggregated sentiment (DeepSeek already analyzed)",
            "recommendation": rss_sentiment.get("recommendation", "HOLD"),
            "market_data_summary": market_data_summary,
            "model_status": "rss_optimized",
            "headlines": [],
        }

    # Fallback if no RSS data
    if not settings.deepseek_api_key:
        # Fallback deterministic sentiment if DeepSeek key missing
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
                    "reasoning": "DEEP_SEEKR1 key missing; using fallback logic.",
                }
            ],
            "analysis": "DeepSeek disabled; fallback sentiment used.",
            "recommendation": "HOLD",
            "market_data_summary": market_data_summary,
            "model_status": "DEEP_SEEKR1 missing",
            "headlines": headlines,
        }

    # Fetch headlines if needed for DeepSeek analysis
    if not headlines:
        try:
            headlines = await fetch_marketaux_headlines(sym)
        except Exception:
            headlines = []
    
    # Build a compact prompt with live data
    headline_lines = "\n".join([f"- {h.get('title','')} ({h.get('source','')})" for h in headlines[:10]]) if headlines else "- No recent headlines available"
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
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.deepseek.com/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.deepseek_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "deepseek-reasoner",
                    "max_tokens": 600,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            resp.raise_for_status()
            data = resp.json()
            text = data["choices"][0]["message"]["content"]
            # Clean markdown if present
            text = text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
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
                    "factor": "DeepSeek request error",
                    "impact": "neutral",
                    "weight": 0.5,
                    "reasoning": str(e),
                }
            ],
            "analysis": "DeepSeek request failed; fallback sentiment used.",
            "recommendation": "HOLD",
            "market_data_summary": market_data_summary,
            "model_status": "DeepSeek request failed",
            "headlines": headlines,
        }
