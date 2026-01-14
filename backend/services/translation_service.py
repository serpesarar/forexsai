from __future__ import annotations

import json
from threading import Lock
from typing import List

import httpx

from config import settings


_cache: dict[tuple[str, str], str] = {}
_lock = Lock()


async def translate_texts(texts: List[str], target_lang: str) -> List[str]:
    """
    Batch-translate texts using Anthropic when target_lang != 'en'.
    Uses a simple in-memory cache to reduce repeated cost.
    """
    lang = (target_lang or "en").lower()
    if lang == "en":
        return texts

    # resolve cache hits
    out: List[str] = []
    missing: List[str] = []
    missing_idx: List[int] = []
    with _lock:
        for i, t in enumerate(texts):
            key = (lang, t)
            if key in _cache:
                out.append(_cache[key])
            else:
                out.append("")  # placeholder
                missing.append(t)
                missing_idx.append(i)

    if not missing or not settings.anthropic_api_key:
        # If no key, fall back to original English titles.
        for i in missing_idx:
            out[i] = texts[i]
        return out

    prompt = f"""
Translate the following list of texts into {lang.upper()}.
Return STRICT JSON only as an array of strings, same length and order.
Do not add commentary. Preserve tickers/symbols and numbers as-is.

Input JSON:
{json.dumps(missing, ensure_ascii=False)}
""".strip()

    try:
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
                    "max_tokens": 900,
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
            translated = json.loads(text)
            if not isinstance(translated, list) or len(translated) != len(missing):
                raise ValueError("Invalid translation response shape")

        with _lock:
            for src, tr in zip(missing, translated):
                _cache[(lang, src)] = str(tr)
            for idx, tr in zip(missing_idx, translated):
                out[idx] = str(tr)
        return out
    except Exception:
        # Fallback: original texts
        for i in missing_idx:
            out[i] = texts[i]
        return out



