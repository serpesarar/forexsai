import json
import logging
import os
import re
from typing import Any, Dict, Optional

import aiohttp

from utils.market_hours import get_new_york_market_hours_label, is_new_york_market_open


logger = logging.getLogger(__name__)

# DeepSeek's smartest reasoning model. As of mid-2026 the V4 series is out:
#   deepseek-v4-pro    — top-tier reasoning (default, used here)
#   deepseek-v4-flash  — faster/cheaper variant — DO NOT use for analysis
#   deepseek-reasoner  — legacy R1 series (still works, less capable)
# Override via DEEPSEEK_MODEL env var on Railway when a newer model ships.
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-pro")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"


def _try_parse_json_object(candidate: str) -> Optional[Dict[str, Any]]:
    if not candidate:
        return None

    try:
        parsed = json.loads(candidate)
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        pass

    fixed = candidate.strip()
    open_brackets = fixed.count("[") - fixed.count("]")
    open_braces = fixed.count("{") - fixed.count("}")

    if open_brackets > 0:
        fixed += "]" * open_brackets
    if open_braces > 0:
        fixed += "}" * open_braces

    fixed = re.sub(r",\s*([}\]])", r"\1", fixed)

    try:
        parsed = json.loads(fixed)
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        return None


def extract_json_object(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None

    candidates = [text.strip()]

    fenced_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, flags=re.IGNORECASE)
    if fenced_match:
        candidates.append(fenced_match.group(1).strip())

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidates.append(text[start : end + 1].strip())

    seen = set()
    for candidate in candidates:
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        parsed = _try_parse_json_object(candidate)
        if parsed is not None:
            return parsed

    return None


async def call_deepseek_json(
    prompt: str,
    *,
    api_key: Optional[str] = None,
    enforce_market_hours: bool = True,
    max_tokens: int = 1000,
    temperature: Optional[float] = None,
    timeout_seconds: int = 45,
) -> Optional[Dict[str, Any]]:
    key = api_key or os.getenv("DEEP_SEEKR1", "")
    if not key:
        return None

    if enforce_market_hours and not is_new_york_market_open():
        logger.info(
            "DeepSeek request skipped outside New York market hours (%s)",
            get_new_york_market_hours_label(),
        )
        return None

    retry_instruction = "Return exactly one valid JSON object only. Do not use markdown fences, code blocks, or explanatory text. Ensure all strings are properly escaped and closed."
    prompt_attempts = [prompt, f"{prompt}\n\n{retry_instruction}"]

    for attempt, prompt_text in enumerate(prompt_attempts, start=1):
        payload: Dict[str, Any] = {
            "model": DEEPSEEK_MODEL,
            "messages": [{"role": "user", "content": prompt_text}],
            "max_tokens": max_tokens,
        }
        if temperature is not None:
            payload["temperature"] = temperature

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    DEEPSEEK_API_URL,
                    headers={
                        "Authorization": f"Bearer {key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=timeout_seconds),
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.warning("DeepSeek request failed with status %s on attempt %s: %s", response.status, attempt, error_text[:400])
                        continue

                    data = await response.json()

            message = ((data.get("choices") or [{}])[0].get("message") or {})
            content = str(message.get("content") or "")
            parsed = extract_json_object(content)
            if parsed is None:
                logger.warning("DeepSeek response could not be parsed into JSON on attempt %s: %s", attempt, content[:400])
                continue

            reasoning = message.get("reasoning_content")
            if reasoning:
                parsed.setdefault("_reasoning", reasoning)
            parsed.setdefault("ai_model", DEEPSEEK_MODEL)
            return parsed
        except Exception:
            logger.exception("DeepSeek JSON request failed on attempt %s", attempt)

    return None