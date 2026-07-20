from __future__ import annotations

from datetime import datetime, timezone
from datetime import UTC

from config import settings
from services.data_fetcher import fetch_latest_price
from utils.market_hours import is_new_york_market_open
import httpx
import json


def _strip_markdown_fences(text: str) -> str:
    cleaned = (text or "").strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()


def _build_prompt(sym: str, current_price: float | None, headlines: list[dict], lang: str) -> str:
    headline_lines = "\n".join(
        [f"- {h.get('title', '')} ({h.get('source', '')})" for h in headlines[:10]]
    ) if headlines else "- No recent headlines available"
    language_line = (
        "Write all human-readable strings in Turkish."
        if (lang or "en").lower().startswith("tr")
        else "Write all human-readable strings in English."
    )
    return f"""
You are a market analyst. Using ONLY the provided data, output STRICT JSON (no markdown, no commentary) matching this schema:
{{
  "sentiment": "BULLISH" | "BEARISH" | "NEUTRAL",
  "confidence": number,
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


def _attach_metadata(parsed: dict, market_data_summary: dict, headlines: list[dict], status: str | None) -> dict:
    parsed["market_data_summary"] = market_data_summary
    parsed["model_status"] = status
    parsed["headlines"] = headlines
    return parsed


def _fallback_response(market_data_summary: dict, headlines: list[dict], reason: str, model_status: str) -> dict:
    return {
        "sentiment": "NEUTRAL",
        "confidence": 0.55,
        "probability_up": 40,
        "probability_down": 35,
        "probability_sideways": 25,
        "key_factors": [
            {
                "factor": "Sentiment analysis fallback",
                "impact": "neutral",
                "weight": 0.5,
                "reasoning": reason,
            }
        ],
        "analysis": reason,
        "recommendation": "HOLD",
        "market_data_summary": market_data_summary,
        "model_status": model_status,
        "headlines": headlines,
    }


async def _call_anthropic_sentiment(prompt: str) -> dict:
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": settings.anthropic_api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-3-haiku-20240307",
                "max_tokens": 900,
                "temperature": 0.1,
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
        return json.loads(_strip_markdown_fences(text))


async def _call_deepseek_sentiment(prompt: str) -> dict:
    if not is_new_york_market_open():
        raise RuntimeError("DeepSeek disabled outside New York market hours")

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
        return json.loads(_strip_markdown_fences(text))


async def run_claude_sentiment(symbol: str = "NDX.INDX", lang: str = "en") -> dict:
    """
    Uses cached RSS sentiment when available.
    If cache is cold, it falls back to Claude (Anthropic) or DeepSeek using available headlines.
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
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
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

    # News provider removed — a Telegram news detector will be wired in later.
    # Provider sentiment runs on whatever headlines the caller supplied (often none).
    if headlines is None:
        headlines = []

    prompt = _build_prompt(sym, current_price, headlines, lang)

    # BİRİNCİL: Claude Code CLI + SONNET (abonelikten, API key yok).
    from services.claude_cli import call_claude_cli, claude_cli_available
    cli_error = "claude CLI yok"
    if claude_cli_available():
        try:
            market_data_summary["news_source"] = "claude_code_cli"
            text = await call_claude_cli(
                "Sen finansal duygu analisti bir asistansın. Yalnız istenen JSON'u döndür.",
                prompt, model="sonnet", timeout=90,
            )
            if not text:
                raise RuntimeError("claude CLI boş yanıt")
            parsed = json.loads(_strip_markdown_fences(text))
            return _attach_metadata(parsed, market_data_summary, headlines, None)
        except Exception as exc:
            cli_error = str(exc)

    # YEDEK: Anthropic API (yalnız CLI yoksa + kredi varsa)
    anthropic_error = "ANTHROPIC_API_KEY missing"
    if settings.anthropic_api_key:
        try:
            market_data_summary["news_source"] = "anthropic_api"
            parsed = await _call_anthropic_sentiment(prompt)
            return _attach_metadata(parsed, market_data_summary, headlines, None)
        except Exception as exc:
            anthropic_error = str(exc)

    reason = f"Claude CLI unavailable: {cli_error}. Anthropic API unavailable: {anthropic_error}."
    return _fallback_response(market_data_summary, headlines, reason, "provider_fallback")
