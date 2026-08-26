"""Claude Code CLI köprüsü — panelin TÜM AI çağrıları için tek kapı.

Claude Decider (claude_decider/decide.py) ile AYNI mekanizma: ``claude`` CLI'ı
subprocess ile çağırır. Bu Claude Code'dur → kullanıcının ABONELİĞİNDEN gider;
Anthropic API key / kredi / "cloud IP" GEREKMEZ.

Kullanım:
    from services.claude_cli import call_claude_cli, claude_cli_available
    text = await call_claude_cli(system, user, model="sonnet")   # async
    text = call_claude_cli_sync(system, user, model="haiku")     # sync

Model kısa adları CLI'da geçerli: "haiku" | "sonnet" | "opus".
Düşünme eforu ``--effort`` ile ayarlanır (varsayılan "high", CLAUDE_CLI_EFFORT ile ezilir).
'claude' CLI kurulu+girişli DEĞİLSE None döner (çağıran yedeğe düşebilir).
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import shutil
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)

# 2026-08-21: panelin TÜM AI çağrıları Sonnet 5 + yüksek düşünme eforu.
# Opus kotayı hızlı tüketiyordu; derinlik model boyutu yerine efordan gelir.
DEFAULT_EFFORT = os.getenv("CLAUDE_CLI_EFFORT", "high")
_UNKNOWN_OPT = re.compile(r"unknown option|unrecognized option|--effort", re.I)

_CLAUDE_BIN: Optional[str] = None
_CHECKED = False
_SANDBOX: Optional[str] = None


def _sandbox() -> Optional[str]:
    """CLI'ın çalışacağı BOŞ dizin — CLAUDE.md otomatik keşfini engeller.

    2026-08-26 ölçümü: aynı çağrı repo kökünde 55k cache-creation token/$0.34,
    boş dizinde 11k/$0.071 (~4.7×). Panelin AI çağrıları kendi prompt'unu
    taşır; CLAUDE.md hiçbir şey katmaz, yalnız kota yer.
    Kapatmak için: CLAUDE_CLI_SANDBOX_CWD=0.
    """
    global _SANDBOX
    if os.getenv("CLAUDE_CLI_SANDBOX_CWD", "1") != "1":
        return None
    if _SANDBOX is None:
        import tempfile
        from pathlib import Path
        d = Path(tempfile.gettempdir()) / "forexsai_cli_sandbox"
        try:
            d.mkdir(parents=True, exist_ok=True)
            _SANDBOX = str(d)
        except OSError:
            _SANDBOX = ""          # fail-open: eski davranış (cwd miras)
    return _SANDBOX or None


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
                         model: str = "sonnet", timeout: int = 180,
                         effort: str = DEFAULT_EFFORT) -> Optional[str]:
    """Claude Code CLI'ı subprocess ile çağır (senkron). Metin döner, hata → None."""
    if not claude_cli_available():
        return None
    cmd = ["claude", "--dangerously-skip-permissions", "-p",
           "--model", model, "--output-format", "json"]
    if effort:
        cmd += ["--effort", effort]
    prompt = f"{system_prompt}\n\n{user_prompt}" if system_prompt else user_prompt
    try:
        # cwd=_sandbox(): CLAUDE.md otomatik yüklenmesin (çağrı başına ~$0.27 israf)
        r = subprocess.run(cmd, input=prompt, capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=timeout,
                           cwd=_sandbox())
    except FileNotFoundError:
        return None
    except subprocess.TimeoutExpired:
        logger.warning("[claude-cli] zaman aşımı (%ss, model=%s)", timeout, model)
        return None
    if r.returncode != 0:
        # Eski CLI --effort'u bilmeyebilir → bir kez efor'suz tekrar dene (sessiz ölüm olmasın)
        if effort and _UNKNOWN_OPT.search(r.stderr or ""):
            logger.info("[claude-cli] --effort desteklenmiyor, efor'suz tekrar")
            return call_claude_cli_sync(system_prompt, user_prompt, model, timeout, effort="")
        logger.warning("[claude-cli] exit %s (model=%s): %s", r.returncode, model, (r.stderr or "")[:200])
        return None
    # --output-format json → {"result": "...", "total_cost_usd":..., "duration_ms":...}
    try:
        meta = json.loads(r.stdout)
        return (meta.get("result") or "").strip() or None
    except json.JSONDecodeError:
        return (r.stdout or "").strip() or None


async def call_claude_cli(system_prompt: str, user_prompt: str,
                          model: str = "sonnet", timeout: int = 180,
                          effort: str = DEFAULT_EFFORT) -> Optional[str]:
    """call_claude_cli_sync'in async sarmalayıcısı (event loop'u bloklamaz)."""
    return await asyncio.to_thread(
        call_claude_cli_sync, system_prompt, user_prompt, model, timeout, effort
    )
