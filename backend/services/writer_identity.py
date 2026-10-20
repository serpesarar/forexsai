"""prediction_logs satırını HANGİ dağıtımın yazdığını gösteren kimlik etiketi.

2026-10-20 yazar denetimi: aynı tabloya Railway (`upbeat-flow-production`),
MT5 kutusu ve zaman zaman yerel backend yazıyor; satırlarda hangisinin
yazdığı yoktu — "güncel kodun üretemeyeceği satır" şüphesi ancak Supabase
edge loglarının IP'leriyle çözülebildi. Artık her satır ``factors.writer``
taşır: ``{"host": "railway:<servis>/<ortam>" | "<hostname>", "sha": "<8 hane>"}``.

Analiz: ``factors->'writer'->>'host'`` ile grupla; ``sha`` dağıtılan kodun
sürümünü verir (eski deploy hemen görünür).
"""
from __future__ import annotations

import os
import socket
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Dict

#: Yerel kopyada git sha'sını okumak için süre tavanı (sn) — açılışta bir kez.
_GIT_TIMEOUT_S = 2.0
_SHA_LEN = 8
_UNKNOWN = "unknown"


def _host_label() -> str:
    service = os.getenv("RAILWAY_SERVICE_NAME")
    if service:
        env_name = os.getenv("RAILWAY_ENVIRONMENT_NAME", "")
        return f"railway:{service}/{env_name}" if env_name else f"railway:{service}"
    explicit = os.getenv("WRITER_HOST")
    if explicit:
        return explicit
    try:
        return socket.gethostname() or _UNKNOWN
    except Exception:
        return _UNKNOWN


def _git_sha() -> str:
    sha = os.getenv("RAILWAY_GIT_COMMIT_SHA") or os.getenv("GIT_COMMIT_SHA")
    if sha:
        return sha[:_SHA_LEN]
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=Path(__file__).resolve().parent,
            capture_output=True, text=True, timeout=_GIT_TIMEOUT_S,
        )
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()[:_SHA_LEN]
    except Exception:
        pass
    return _UNKNOWN


@lru_cache(maxsize=1)
def writer_identity() -> Dict[str, str]:
    """Süreç ömrü boyunca sabit yazar kimliği (önbellekli)."""
    return {"host": _host_label(), "sha": _git_sha()}
