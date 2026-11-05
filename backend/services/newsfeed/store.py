"""Kalıcı yazım: toplu, ana akışı bekletmez, tablo yoksa bellekte çalışmaya devam eder (fail-open).

Yazım hikâyeyi GECİKTİRMEZ: başlık önce bellek + canlı yayına düşer, veritabanı arkadan gelir. 2026-08 disk krizinden
ders: `news_stories`/`news_sightings` için saklama süresi zorunludur (`NEWSFEED_RETENTION_DAYS`).
"""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger(__name__)

FLUSH_INTERVAL_S = 2.0
FLUSH_MAX_ROWS = 200
TABLE_RETRY_S = 600.0
PRUNE_INTERVAL_S = 6 * 3600
RETENTION_DAYS_DEFAULT = 90
QUEUE_MAX = 5000


def iso(ts: float | None) -> str | None:
    """Epoch → ISO-8601 UTC."""
    return datetime.fromtimestamp(ts, timezone.utc).isoformat() if ts else None


class NewsStore:
    """`news_stories` + `news_sightings` + (isteğe bağlı) eski panel tablosu `enriched_news` yazarı."""

    def __init__(self) -> None:
        self._stories: dict[str, dict[str, Any]] = {}
        self._sightings: list[dict[str, Any]] = []
        self._legacy: list[dict[str, Any]] = []
        self._disabled_until = 0.0
        self._last_prune = 0.0
        self.stats: dict[str, Any] = {"flushes": 0, "rows": 0, "errors": 0, "last_error": None, "persist_ok": None}
        self.legacy_bridge = os.getenv("NEWSFEED_LEGACY_BRIDGE", "1") != "0"
        self.retention_days = int(os.getenv("NEWSFEED_RETENTION_DAYS", str(RETENTION_DAYS_DEFAULT)))

    def queue_story(self, row: dict[str, Any]) -> None:
        if len(self._stories) < QUEUE_MAX:
            self._stories[row["id"]] = row

    def queue_sighting(self, row: dict[str, Any]) -> None:
        if len(self._sightings) < QUEUE_MAX:
            self._sightings.append(row)

    def queue_legacy(self, row: dict[str, Any]) -> None:
        if self.legacy_bridge and len(self._legacy) < QUEUE_MAX:
            self._legacy.append(row)

    @staticmethod
    def _client():
        from database.supabase_client import get_supabase_client
        return get_supabase_client()

    def _flush_sync(self, stories: list[dict], sightings: list[dict], legacy: list[dict]) -> None:
        client = self._client()
        if client is None:
            raise RuntimeError("supabase yok")
        if stories:
            self._check(client.table("news_stories").upsert(stories, on_conflict="id"))
        if sightings:
            self._check(client.table("news_sightings").upsert(sightings, on_conflict="story_id,source_id"))
        for row in legacy:
            client.table("enriched_news").insert_ignore(row, on_conflict="id")

    @staticmethod
    def _check(res: Any) -> None:
        if isinstance(res, dict) and res.get("error"):
            raise RuntimeError(str(res["error"])[:300])

    async def flush(self, loop_time: float) -> None:
        """Birikeni yazar; tablo yoksa TABLE_RETRY_S boyunca denemez, veriyi bellekte bırakıp kuyruğu sınırlar."""
        if loop_time < self._disabled_until or not (self._stories or self._sightings or self._legacy):
            return
        stories = list(self._stories.values())[:FLUSH_MAX_ROWS]
        # Kuyrukta bekleyen hikâye varken görülmeleri yazma: yabancı anahtar sırası bozulmasın.
        sightings = [] if len(self._stories) > FLUSH_MAX_ROWS else self._sightings[:FLUSH_MAX_ROWS]
        legacy = self._legacy[:FLUSH_MAX_ROWS]
        try:
            await asyncio.to_thread(self._flush_sync, stories, sightings, legacy)
        except Exception as exc:  # noqa: BLE001 — kalıcı yazım haber akışını asla durdurmaz
            self.stats.update(errors=self.stats["errors"] + 1, last_error=str(exc)[:300], persist_ok=False)
            self._disabled_until = loop_time + TABLE_RETRY_S
            logger.warning("[newsfeed] kalıcı yazım başarısız, %ss sonra yeniden denenecek: %s", TABLE_RETRY_S, exc)
            return
        for row in stories:
            self._stories.pop(row["id"], None)
        del self._sightings[:len(sightings)]
        del self._legacy[:len(legacy)]
        self.stats.update(flushes=self.stats["flushes"] + 1, rows=self.stats["rows"] + len(stories) + len(sightings),
                          persist_ok=True, last_error=None)

    def _prune_sync(self) -> None:
        client = self._client()
        if client is None:
            return
        cutoff = (datetime.now(timezone.utc) - timedelta(days=self.retention_days)).isoformat()
        client.table("news_sightings").lt("first_seen_at", cutoff).delete()
        client.table("news_stories").lt("first_seen_at", cutoff).delete()

    async def prune_if_due(self, loop_time: float) -> None:
        """Saklama süresini aşan satırları siler (yalnız kendi iki tablosu; enriched_news'e dokunmaz)."""
        if loop_time - self._last_prune < PRUNE_INTERVAL_S:
            return
        self._last_prune = loop_time
        try:
            await asyncio.to_thread(self._prune_sync)
        except Exception as exc:  # noqa: BLE001
            logger.warning("[newsfeed] saklama temizliği başarısız: %s", exc)

    def recent_sightings_sync(self, days: int = 7, limit: int = 20000) -> list[dict[str, Any]]:
        """Açılışta karneyi geri yüklemek için son canlı görülmeler."""
        client = self._client()
        if client is None:
            return []
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        res = (client.table("news_sightings").select("*").gte("first_seen_at", since).eq("seeded", False)
               .order("first_seen_at").limit(limit).execute())
        return (res.get("data") if isinstance(res, dict) else getattr(res, "data", None)) or []
