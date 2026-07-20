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

    # Çeviri = düşük seviye iş → Claude Code CLI + HAIKU (hızlı/ucuz, abonelikten).
    # CLI yoksa orijinal metne düş (fail-open; API key artık kullanılmıyor).
    from services.claude_cli import call_claude_cli, claude_cli_available
    if not missing or not claude_cli_available():
        for i in missing_idx:
            out[i] = texts[i]
        return out

    system_prompt = (
        "You are a precise translator. Return STRICT JSON only: an array of "
        "strings, same length and order as the input. No commentary. Preserve "
        "tickers/symbols and numbers as-is."
    )
    user_prompt = (
        f"Translate the following list of texts into {lang.upper()}.\n\n"
        f"Input JSON:\n{json.dumps(missing, ensure_ascii=False)}"
    )

    try:
        text = await call_claude_cli(system_prompt, user_prompt, model="haiku", timeout=60)
        if not text:
            raise ValueError("claude CLI boş/yok")
        # CLI bazen ```json fence ekleyebilir — soyup parse et
        if "```" in text:
            text = text.split("```json")[-1].split("```")[0] if "```json" in text else text.split("```")[1]
        translated = json.loads(text.strip())
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



