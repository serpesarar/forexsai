"""Claude Code CLI köprüsü — panelin TÜM AI çağrıları için tek kapı.

Claude Decider (claude_decider/decide.py) ile AYNI mekanizma: ``claude`` CLI'ı
subprocess ile çağırır. Bu Claude Code'dur → kullanıcının ABONELİĞİNDEN gider;
Anthropic API key / kredi / "cloud IP" GEREKMEZ.

Kullanım:
    from services.claude_cli import call_claude_cli, claude_cli_available
    text = await call_claude_cli(system, user, model="sonnet")   # async
    text = call_claude_cli_sync(system, user, model="haiku")     # sync

Model kısa adları CLI'da geçerli: "haiku" | "sonnet" | "opus".
'claude' CLI kurulu+girişli DEĞİLSE None döner (çağıran yedeğe düşebilir).
"""
from __future__ import annotations

import asyncio
import json
import logging
import shutil
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)

_CLAUDE_BIN: Optional[str] = None
_CHECKED = False


def claude_cli_available() -> bool:
    """'claude' CLI PATH'te var mı (subprocess erişebilir mi)."""
    global _CLAUDE_BIN, _CHECKED
    if not _CHECKED:
        _CLAUDE_BIN = shutil.which("claude")
        _CHECKED = True
        if _CLAUDE_BIN:
            logger.info("[claude-cli] bulundu: %s (abonelikten, API key gerekmez)", _CLAUDE_BIN)
        else:
            logger.info("[claude-cli] 'claude' CLI yok — servisler Anthropic API yedeğine düşer")
    return _CLAUDE_BIN is not None


def call_claude_cli_sync(system_prompt: str, user_prompt: str,
                         model: str = "sonnet", timeout: int = 180) -> Optional[str]:
    """Claude Code CLI'ı subprocess ile çağır (senkron). Metin döner, hata → None."""
    if not claude_cli_available():
        return None
    cmd = ["claude", "--dangerously-skip-permissions", "-p",
           "--model", model, "--output-format", "json"]
    prompt = f"{system_prompt}\n\n{user_prompt}" if system_prompt else user_prompt
    try:
        r = subprocess.run(cmd, input=prompt, capture_output=True,
                           text=True, timeout=timeout)
    except FileNotFoundError:
        return None
    except subprocess.TimeoutExpired:
        logger.warning("[claude-cli] zaman aşımı (%ss, model=%s)", timeout, model)
        return None
    if r.returncode != 0:
        logger.warning("[claude-cli] exit %s (model=%s): %s", r.returncode, model, (r.stderr or "")[:200])
        return None
    # --output-format json → {"result": "...", "total_cost_usd":..., "duration_ms":...}
    try:
        meta = json.loads(r.stdout)
        return (meta.get("result") or "").strip() or None
    except json.JSONDecodeError:
        return (r.stdout or "").strip() or None


async def call_claude_cli(system_prompt: str, user_prompt: str,
                          model: str = "sonnet", timeout: int = 180) -> Optional[str]:
    """call_claude_cli_sync'in async sarmalayıcısı (event loop'u bloklamaz)."""
    return await asyncio.to_thread(
        call_claude_cli_sync, system_prompt, user_prompt, model, timeout
    )
