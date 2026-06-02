"""Marketaux servisi sistemden kaldırıldı (2026-06-02).

API quota dolduğu (402) ve değer üretmediği için tamamen devre dışı.
Çağrılan fonksiyonlar boş liste döner; bağımlı kod gracefully çalışır.
"""
from __future__ import annotations

from typing import Any, Dict, List


async def fetch_marketaux_headlines(symbols: List[str]) -> List[Dict[str, Any]]:
    """No-op: Marketaux kaldırıldı."""
    return []


def get_marketaux_health() -> Dict[str, Any]:
    return {"enabled": False, "reason": "removed"}
