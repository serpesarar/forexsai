"""Model router for the bias debate engine.

Routes each agent call to a provider by importance:
  * ``important`` (CIO, debate, key reasoning) → Kimi (Moonshot)  — trusted more
  * ``normal``    (data/context agents)        → DeepSeek Reasoner

Both are OpenAI-compatible chat APIs, so one httpx path serves both. If the
preferred provider has no key, it falls back to the other; if neither is
configured, :class:`LLMUnavailable` is raised (callers fail open / skip).
"""
from __future__ import annotations

import json
import logging
import re
from typing import Optional

import httpx

from config import settings

logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(90.0, connect=10.0)


class LLMUnavailable(RuntimeError):
    """No usable provider (missing API keys) or the call failed."""


def _provider_for(importance: str) -> list[tuple[str, str, str, str]]:
    """Ordered (name, key, base_url, model) candidates for an importance tier."""
    kimi = ("kimi", settings.kimi_api_key, settings.kimi_base_url, settings.kimi_model)
    deepseek = ("deepseek", settings.deepseek_api_key,
                settings.deepseek_base_url, settings.deepseek_model)
    order = [kimi, deepseek] if importance == "important" else [deepseek, kimi]
    return [c for c in order if c[1]]   # keep only those with a key


def extract_json(text: str) -> Optional[dict]:
    """Best-effort: parse *text* as JSON, else grab the first {...} block."""
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            return None
    return None


async def chat(
    system: str,
    user: str,
    importance: str = "normal",
    json_mode: bool = False,
    temperature: float = 0.4,
    max_tokens: int = 1600,
) -> tuple[str, str]:
    """Return (content, provider_name). Raises LLMUnavailable on total failure."""
    candidates = _provider_for(importance)
    if not candidates:
        raise LLMUnavailable("no DeepSeek or Kimi API key configured")

    last_err: Optional[Exception] = None
    for name, key, base, model in candidates:
        url = base.rstrip("/") + "/chat/completions"
        payload: dict = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        # Thinking/reasoning models (deepseek-reasoner, Kimi k2.6/k2.7 "thinking")
        # reject custom temperature ("only 1 allowed") and response_format, and
        # they spend tokens on hidden reasoning BEFORE the answer — so give them
        # generous headroom or `content` comes back empty.
        ml = model.lower()
        is_reasoner = any(t in ml for t in ("reasoner", "thinking", "k2.6", "k2.7"))
        if is_reasoner:
            payload["max_tokens"] = max(max_tokens, 6000)   # reasoning + answer
        else:
            payload["max_tokens"] = max_tokens
            payload["temperature"] = temperature
            if json_mode:
                payload["response_format"] = {"type": "json_object"}
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                resp = await client.post(
                    url, json=payload,
                    headers={"Authorization": f"Bearer {key}"})
                resp.raise_for_status()
                data = resp.json()
            content = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
            if content:
                return content, name
            last_err = LLMUnavailable(f"{name} empty response")
        except Exception as e:  # try next candidate
            last_err = e
            logger.warning("[llm-router] %s call failed: %s", name, str(e)[:200])

    raise LLMUnavailable(f"all providers failed: {last_err}")


def routing_status() -> dict:
    """Diagnostic — which providers are configured for each tier."""
    return {
        "important": [c[0] for c in _provider_for("important")] or ["NONE"],
        "normal": [c[0] for c in _provider_for("normal")] or ["NONE"],
        "kimi_configured": bool(settings.kimi_api_key),
        "deepseek_configured": bool(settings.deepseek_api_key),
        "kimi_model": settings.kimi_model,
        "deepseek_model": settings.deepseek_model,
    }
